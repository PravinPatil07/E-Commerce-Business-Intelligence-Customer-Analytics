import pandas as pd
from flask import Flask, jsonify, render_template, request

import analytics as an
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


# ---------------------------------------------------------------------------
# Jinja filters
# ---------------------------------------------------------------------------
@app.template_filter("money")
def money(value, decimals=0):
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}{Config.CURRENCY_SYMBOL}{abs(value):,.{decimals}f}"


@app.template_filter("num")
def num(value, decimals=0):
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}"


@app.template_filter("pct")
def pct(value, decimals=1, signed=False):
    if value is None:
        return "—"
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


# ---------------------------------------------------------------------------
# Year filter (shared by all sales/product/customer pages)
# ---------------------------------------------------------------------------
def selected_year():
    raw = request.args.get("year", "").strip()
    return int(raw) if raw.isdigit() else None


@app.context_processor
def inject_filters():
    return {"years": an.get_years(), "selected_year": selected_year()}


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.route("/")
def overview():
    df = an.filter_sales(selected_year())
    return render_template(
        "overview.html",
        kpis=an.overview_kpis(df),
        monthly=an.to_records(an.monthly_sales(df)),
        top_products=an.to_records(an.product_table(df).head(5)),
        top_customers=an.to_records(an.customer_table(df).head(5)),
    )


@app.route("/sales")
def sales():
    df = an.filter_sales(selected_year())
    return render_template(
        "sales.html",
        monthly=an.to_records(an.monthly_sales(df)),
        weekday=an.to_records(an.sales_by_weekday(df)),
        hourly=an.to_records(an.sales_by_hour(df)),
        matrix=an.revenue_year_month_matrix(df),
    )


@app.route("/products")
def products():
    df = an.filter_sales(selected_year())
    table = an.product_table(df)
    records = an.to_records(table)
    return render_template(
        "products.html",
        products=records[:500],               # table limit keeps the page fast
        total_products=len(records),
        top_product=records[0] if records else None,
        top10=records[:10],
    )


@app.route("/customers")
def customers():
    df = an.filter_sales(selected_year())
    table = an.customer_table(df)
    return render_template(
        "customers.html",
        summary=an.customer_summary(table),
        customers=an.to_records(table.head(100)),
    )


@app.route("/rfm")
def rfm():
    return render_template("rfm.html", rfm=an.rfm_summary())


@app.route("/outlook")
def outlook():
    d = Config.ML_OUTPUT_DIR
    required = ["forecast_monthly.csv", "forecast_summary.csv",
                "churn_risk.csv", "churn_metrics.csv"]
    if not all((d / f).exists() for f in required):
        # Training hasn't been run yet; the template shows the instructions
        return render_template("outlook.html", ready=False)

    # Actual monthly history (sales data) and forecasts (ML output)
    hist = an.monthly_sales(an.load_sales())
    fc = pd.read_csv(d / "forecast_monthly.csv")
    fc["label"] = fc["month"].str[:7]
    summary = pd.read_csv(d / "forecast_summary.csv")
    risk = pd.read_csv(d / "churn_risk.csv").sort_values("churn_probability", ascending=False)
    metrics = pd.read_csv(d / "churn_metrics.csv", index_col=0)["value"].to_dict()

    def chart_payload(metric):
        f = fc[fc["metric"] == metric]
        h = hist[["YearMonth", metric]]
        last = float(h[metric].iloc[-1])
        n_hist, n_fc = len(h), len(f)
        return {
            "labels": list(h["YearMonth"]) + list(f["label"]),
            "actual": [float(v) for v in h[metric]] + [None] * n_fc,
            # Forecast line starts at the last actual point so the two connect
            "forecast": [None] * (n_hist - 1) + [last] + [float(v) for v in f["forecast"]],
            "lower": [None] * n_hist + [float(v) for v in f["lower"]],
            "upper": [None] * n_hist + [float(v) for v in f["upper"]],
        }

    return render_template(
        "outlook.html",
        ready=True,
        summary=an.to_records(summary),
        charts={"revenue": chart_payload("revenue"), "orders": chart_payload("orders")},
        risk=an.to_records(risk.head(50)),
        churn_metrics=metrics,
        churn_count_high=int((risk["churn_probability"] >= 0.5).sum()),
        churn_total=len(risk),
    )


# ---------------------------------------------------------------------------
# JSON endpoint (handy for other tools or future front-end work)
# ---------------------------------------------------------------------------
@app.route("/api/kpis")
def api_kpis():
    return jsonify(an.overview_kpis(an.filter_sales(selected_year())))


if __name__ == "__main__":
    app.run(debug=True)