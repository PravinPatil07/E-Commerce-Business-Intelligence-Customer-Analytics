"""
Train all models and write results for the dashboard.

Run from the dashboard folder:
    python -m ml.train_all

Outputs (reports/ml/ and models/):
    forecast_monthly.csv   next 3 months of revenue and orders, with 80% range
    forecast_summary.csv   chosen model, backtest error, trend per metric
    forecast_backtest.csv  every model's backtest error
    churn_risk.csv         every customer's churn probability and reasons
    churn_metrics.csv      holdout evaluation of the churn model
    models/churn_model.joblib
"""
import joblib
import pandas as pd

import analytics as an
from config import Config
from ml import churn, features, forecast


def main():
    out = Config.ML_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    Config.ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading sales data...")
    df = an.load_sales()

    print("Forecasting revenue and orders...")
    monthly = features.monthly_series(df)
    fc, summary, backtest = forecast.run_forecasts(monthly, horizon=3)
    fc.to_csv(out / "forecast_monthly.csv", index=False)
    summary.to_csv(out / "forecast_summary.csv", index=False)
    backtest.to_csv(out / "forecast_backtest.csv", index=False)
    print(summary.to_string(index=False))

    print("Training churn model...")
    model, metrics = churn.train(df)
    pd.Series(metrics).to_csv(out / "churn_metrics.csv", header=["value"])
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in metrics.items()})

    print("Scoring current customers...")
    scores = churn.score_current(df, model)
    try:
        rfm = an.load_rfm()[["CustomerID", "CustomerSegment"]].rename(
            columns={"CustomerID": "customer_id", "CustomerSegment": "segment"}
        )
        scores = scores.merge(rfm, on="customer_id", how="left")
    except FileNotFoundError:
        print("RFM file not found, skipping segment column.")
    scores.to_csv(out / "churn_risk.csv", index=False)

    joblib.dump({"model": model, "features": churn.FEATURES},
                Config.ML_MODEL_DIR / "churn_model.joblib")
    print(f"Done. Results written to {out}")


if __name__ == "__main__":
    main()
