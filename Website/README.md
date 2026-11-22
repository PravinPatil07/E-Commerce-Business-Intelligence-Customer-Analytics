# E-Commerce BI Dashboard (Flask)

A web dashboard on top of your analytics project. It reads from the SQLite database
(`sales` table) and the RFM output (`customer_rfm.csv`).

## Project layout

```
<your project root>/
├── database/ecommerce_analytics.db     <- read by the dashboard
├── reports/rfm_analysis/customer_rfm.csv   <- read by the RFM page
├── data/  reports/  sql/  ...
└── dashboard/                          <- this folder
    ├── app.py            Flask routes + template filters
    ├── analytics.py      all KPI calculations (pandas)
    ├── config.py         paths and settings
    ├── requirements.txt
    ├── templates/        base, overview, sales, products, customers, rfm, macros
    └── static/           css/style.css, js/main.js
```

## Setup

```bash
cd <your project root>/dashboard
python -m venv venv
venv\Scripts\activate            # Windows (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Configuration (optional)

Paths default to the folder layout above. Override with environment variables if needed:

| Variable        | Default                                              |
|-----------------|------------------------------------------------------|
| ECOM_DB_PATH    | `<root>/database/ecommerce_analytics.db`             |
| ECOM_SALES_TABLE| `sales`                                              |
| ECOM_RFM_PATH   | `<root>/reports/rfm_analysis/customer_rfm.csv`       |
| ECOM_CURRENCY   | `£`                                                  |
| SECRET_KEY      | `dev-change-me` (set a real value for deployment)    |

PowerShell example:
```powershell
$env:ECOM_DB_PATH = "D:\E-Commerce Business Intelligence & Customer Analytics\database\ecommerce_analytics.db"
python app.py
```

## Pages and KPI definitions

| Page      | Contents |
|-----------|----------|
| Overview  | Total Revenue, Total Orders, Total Customers, AOV, Total Units, Revenue per Customer, ASP, Orders per Customer; monthly revenue & orders chart; top 5 products and customers |
| Sales     | Monthly revenue, orders, customers, AOV, MoM revenue and order growth; revenue by weekday and hour; year × month revenue heatmap |
| Products  | Revenue, units, orders, customers, avg revenue per unit, rank, revenue contribution; top-10 chart; searchable table |
| Customers | Total, repeat, one-time customers, repeat %; revenue, orders, AOV, revenue ranking; top-100 table |
| RFM       | Customer count per segment, segment revenue and contribution, avg recency/frequency/monetary per segment |

The year filter in the top bar applies to Overview, Sales, Products and Customers.
RFM is a snapshot from the CSV, so it has no year filter.

## Notes

- Tables sort when you click a column header and filter as you type in the search box.
- The product table shows the top 500 products to keep the page fast.
- `GET /api/kpis?year=2011` returns the overview KPIs as JSON.
