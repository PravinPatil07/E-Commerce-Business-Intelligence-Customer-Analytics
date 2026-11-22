"""
Monthly revenue and order forecasting.

Each candidate model is backtested on the last `holdout` months. The model with the
lowest MAPE is refit on the full history and used for the forecast. A model only
gets used if it beats the simple baselines, so the forecast is never worse than
a moving average on the backtest.
"""
import warnings

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:  # the baselines still work without statsmodels
    HAS_STATSMODELS = False

Z80 = 1.2816  # z-score for an 80% prediction interval


# ---------------------------------------------------------------------------
# Candidate models. Each returns (forecast array, in-sample one-step residuals).
# ---------------------------------------------------------------------------
def moving_average(y, horizon, window=3):
    y = np.asarray(y, float)
    resid = np.array([y[i] - y[i - window:i].mean() for i in range(window, len(y))])
    return np.repeat(y[-window:].mean(), horizon), resid


def seasonal_naive(y, horizon, season=12):
    """Same month last year. Falls back to moving average if there is < 1 year of data."""
    y = np.asarray(y, float)
    if len(y) <= season:
        return moving_average(y, horizon)
    pred = np.array([y[-season + (i % season)] for i in range(horizon)])
    resid = y[season:] - y[:-season]
    return pred, resid


def holt_winters(y, horizon):
    """Damped-trend exponential smoothing. Adds yearly seasonality once there are 2+ years."""
    if not HAS_STATSMODELS:
        raise RuntimeError("statsmodels is not installed")
    y = np.asarray(y, float)
    seasonal = len(y) >= 24
    model = ExponentialSmoothing(
        y,
        trend="add",
        damped_trend=True,
        seasonal="add" if seasonal else None,
        seasonal_periods=12 if seasonal else None,
        initialization_method="estimated",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = model.fit()
    return np.asarray(fit.forecast(horizon)), np.asarray(fit.resid)


MODELS = {
    "Moving average (3m)": moving_average,
    "Seasonal naive": seasonal_naive,
    "Holt-Winters": holt_winters,
}


def mape(actual, pred):
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    mask = actual != 0
    return float(np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100)


# ---------------------------------------------------------------------------
# Backtest and final forecast
# ---------------------------------------------------------------------------
def backtest(y, holdout: int = 6) -> pd.DataFrame:
    """Train on everything except the last `holdout` months, forecast those months."""
    y = np.asarray(y, float)
    if len(y) < holdout + 6:
        raise ValueError(f"Need at least {holdout + 6} months of history, got {len(y)}")
    train, test = y[:-holdout], y[-holdout:]

    rows = []
    for name, fn in MODELS.items():
        try:
            pred, _ = fn(train, holdout)
            rows.append({"model": name, "mape": mape(test, pred), "error": ""})
        except Exception as exc:  # a model that fails is skipped, not fatal
            rows.append({"model": name, "mape": np.nan, "error": str(exc)[:120]})
    return pd.DataFrame(rows).sort_values("mape", na_position="last").reset_index(drop=True)


def forecast_metric(series: pd.Series, horizon: int = 3, holdout: int = 6):
    """
    Returns (forecast DataFrame, backtest DataFrame, chosen model name).
    `series` is indexed by month start (see features.monthly_series).
    """
    y = series.to_numpy(dtype=float)
    bt = backtest(y, holdout)
    best = bt.iloc[0]["model"]
    if np.isnan(bt.iloc[0]["mape"]):
        raise RuntimeError("No model could be backtested")

    pred, resid = MODELS[best](y, horizon)
    sigma = float(np.std(resid, ddof=1)) if len(resid) > 2 else float(np.std(y, ddof=1))

    future_months = pd.date_range(series.index[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    out = pd.DataFrame({
        "month": future_months,
        "forecast": np.asarray(pred, float),
        "lower": np.maximum(np.asarray(pred, float) - Z80 * sigma, 0),
        "upper": np.asarray(pred, float) + Z80 * sigma,
    })
    return out, bt, best


def trend_label(forecast_avg: float, recent_avg: float, threshold_pct: float = 5.0) -> str:
    if not recent_avg:
        return "Unknown"
    change = (forecast_avg - recent_avg) / recent_avg * 100
    if change > threshold_pct:
        return "Growing"
    if change < -threshold_pct:
        return "Declining"
    return "Flat"


def run_forecasts(monthly: pd.DataFrame, horizon: int = 3):
    """
    Forecast every column in `monthly` (revenue, orders).
    Returns (long-format forecasts, summary table, backtest table).
    """
    forecasts, summaries, backtests = [], [], []
    for metric in ["revenue", "orders"]:
        fc, bt, best = forecast_metric(monthly[metric], horizon)
        fc.insert(0, "metric", metric)
        forecasts.append(fc)

        bt.insert(0, "metric", metric)
        backtests.append(bt)

        recent_avg = float(monthly[metric].tail(3).mean())
        forecast_avg = float(fc["forecast"].mean())
        best_row = bt.iloc[0]
        summaries.append({
            "metric": metric,
            "model": best,
            "backtest_mape": round(best_row["mape"], 2),
            "last_3m_avg": round(recent_avg, 2),
            "next_3m_avg_forecast": round(forecast_avg, 2),
            "change_pct": round((forecast_avg - recent_avg) / recent_avg * 100, 2) if recent_avg else None,
            "trend": trend_label(forecast_avg, recent_avg),
        })

    return pd.concat(forecasts, ignore_index=True), pd.DataFrame(summaries), pd.concat(backtests, ignore_index=True)
