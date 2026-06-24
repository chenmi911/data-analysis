from pathlib import Path

import numpy as np
import pandas as pd


RAW_PATH = Path(r"D:\temp\dataset\superstore\Sample - Superstore.csv")
PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_DIR / "data" / "superstore_orders_clean.csv"
REJECTED_PATH = PROJECT_DIR / "data" / "superstore_rejected_rows.csv"


RENAME_DICT = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "Country": "country",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
}


def main() -> None:
    df = pd.read_csv(RAW_PATH, encoding="cp1252")
    print(f"原始数据: {df.shape[0]} 行, {df.shape[1]} 列")

    df = df.rename(columns=RENAME_DICT)
    df["order_date"] = pd.to_datetime(df["order_date"], format="%m/%d/%Y", errors="coerce")
    df["ship_date"] = pd.to_datetime(df["ship_date"], format="%m/%d/%Y", errors="coerce")

    df["ship_days"] = (df["ship_date"] - df["order_date"]).dt.days
    df["profit_margin"] = np.where(df["sales"] != 0, df["profit"] / df["sales"], np.nan)

    required_cols = [
        "order_id",
        "order_date",
        "ship_date",
        "customer_id",
        "product_id",
        "sales",
        "quantity",
        "discount",
        "profit",
    ]
    invalid_mask = (
        df[required_cols].isna().any(axis=1)
        | (df["ship_date"] < df["order_date"])
        | (df["sales"] <= 0)
        | (df["quantity"] <= 0)
        | (df["discount"] < 0)
        | (df["discount"] > 1)
    )
    rejected_df = df[invalid_mask].copy()
    clean_df = df[~invalid_mask].drop_duplicates().copy()

    print("\n数据检查:")
    print(f"缺失值总数: {df.isna().sum().sum()}")
    print(f"重复行数: {df.duplicated().sum()}")
    print(f"发货早于下单: {(df['ship_date'] < df['order_date']).sum()}")
    print(f"sales <= 0: {(df['sales'] <= 0).sum()}")
    print(f"quantity <= 0: {(df['quantity'] <= 0).sum()}")
    print(f"discount 不在 0 到 1: {((df['discount'] < 0) | (df['discount'] > 1)).sum()}")
    print(f"剔除异常行: {len(rejected_df)}")
    print(f"清洗后行数: {len(clean_df)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8", lineterminator="\n")
    rejected_df.to_csv(REJECTED_PATH, index=False, encoding="utf-8", lineterminator="\n")
    print(f"\n已输出清洗后的 CSV: {OUTPUT_PATH}")
    print(f"已输出异常行留痕 CSV: {REJECTED_PATH}")


if __name__ == "__main__":
    main()
