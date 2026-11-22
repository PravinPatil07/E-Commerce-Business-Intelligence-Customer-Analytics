import os
from pathlib import Path

# Website/ sits inside your project root (next to database/, reports/, data/, sql/)
ROOT_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")

    # SQLite database created by your pipeline
    DB_PATH = Path(os.getenv("ECOM_DB_PATH", ROOT_DIR / "database" / "ecommerce_analytics.db"))
    SALES_TABLE = os.getenv("ECOM_SALES_TABLE", "sales")

    # Customer-level RFM output produced by your RFM notebook/script
    RFM_PATH = Path(os.getenv(
        "ECOM_RFM_PATH",
        ROOT_DIR / "reports" / "rfm_analysis" / "customer_rfm.csv",
    ))

    # Machine-learning outputs (written by `python -m ml.train_all`)
    ML_OUTPUT_DIR = Path(os.getenv("ECOM_ML_DIR", ROOT_DIR / "reports" / "ml"))
    ML_MODEL_DIR = Path(os.getenv("ECOM_MODEL_DIR", ROOT_DIR / "models"))

    CURRENCY_SYMBOL = os.getenv("ECOM_CURRENCY", "£")