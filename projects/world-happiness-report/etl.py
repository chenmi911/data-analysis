#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Describe: 数据清洗与标准化

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
DB_PATH = PROJECT_DIR / "outputs" / "world_happiness.db"

STANDARD_COLUMNS = [
    "year",
    "country",
    "region",
    "rank",
    "score",
    "gdp",
    "social_support",
    "life_expectancy",
    "freedom",
    "generosity",
    "corruption",
]

RENAME_MAPS = {
    "2015.csv": {
        "Country": "country",
        "Region": "region",
        "Happiness Rank": "rank",
        "Happiness Score": "score",
        "Economy (GDP per Capita)": "gdp",
        "Family": "social_support",
        "Health (Life Expectancy)": "life_expectancy",
        "Freedom": "freedom",
        "Trust (Government Corruption)": "corruption",
        "Generosity": "generosity",
    },
    "2016.csv": {
        "Country": "country",
        "Region": "region",
        "Happiness Rank": "rank",
        "Happiness Score": "score",
        "Economy (GDP per Capita)": "gdp",
        "Family": "social_support",
        "Health (Life Expectancy)": "life_expectancy",
        "Freedom": "freedom",
        "Trust (Government Corruption)": "corruption",
        "Generosity": "generosity",
    },
    "2017.csv": {
        "Country": "country",
        "Happiness.Rank": "rank",
        "Happiness.Score": "score",
        "Economy..GDP.per.Capita.": "gdp",
        "Family": "social_support",
        "Health..Life.Expectancy.": "life_expectancy",
        "Freedom": "freedom",
        "Generosity": "generosity",
        "Trust..Government.Corruption.": "corruption",
    },
    "2018.csv": {
        "Overall rank": "rank",
        "Country or region": "country",
        "Score": "score",
        "GDP per capita": "gdp",
        "Social support": "social_support",
        "Healthy life expectancy": "life_expectancy",
        "Freedom to make life choices": "freedom",
        "Generosity": "generosity",
        "Perceptions of corruption": "corruption",
    },
    "2019.csv": {
        "Overall rank": "rank",
        "Country or region": "country",
        "Score": "score",
        "GDP per capita": "gdp",
        "Social support": "social_support",
        "Healthy life expectancy": "life_expectancy",
        "Freedom to make life choices": "freedom",
        "Generosity": "generosity",
        "Perceptions of corruption": "corruption",
    },
}


def load_and_standardize() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data_list = []
    raw_summary_rows = []
    column_map_rows = []
    region_map = {}

    for path in sorted(DATA_DIR.glob("*.csv")):
        raw = pd.read_csv(path)
        year = int(path.stem)
        rename_map = RENAME_MAPS[path.name]

        raw_summary_rows.append(
            {
                "year": year,
                "file": path.name,
                "rows": len(raw),
                "cols": len(raw.columns),
                "raw_columns": " | ".join(raw.columns),
            }
        )

        for raw_col, standard_col in rename_map.items():
            column_map_rows.append(
                {
                    "year": year,
                    "file": path.name,
                    "raw_column": raw_col,
                    "standard_column": standard_col,
                }
            )

        data = raw.rename(columns=rename_map)
        data["year"] = year

        if "region" in data.columns:
            current_region = data.dropna(subset=["region"]).set_index("country")["region"]
            region_map.update(current_region.to_dict())

        for col in STANDARD_COLUMNS:
            if col not in data.columns:
                data[col] = np.nan

        data_list.append(data[STANDARD_COLUMNS])

    clean_data = pd.concat(data_list, ignore_index=True)
    clean_data["region"] = clean_data["region"].fillna(clean_data["country"].map(region_map))

    raw_summary = pd.DataFrame(raw_summary_rows)
    column_map = pd.DataFrame(column_map_rows)
    return clean_data, raw_summary, column_map


def save_clean_data(
    clean_data: pd.DataFrame,
    raw_summary: pd.DataFrame,
    column_map: pd.DataFrame,
) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    clean_data.to_csv(
        TABLE_DIR / "world_happiness_clean_2015_2019.csv",
        index=False,
        encoding="utf-8-sig",
    )
    raw_summary.to_csv(TABLE_DIR / "raw_file_summary.csv", index=False, encoding="utf-8-sig")
    column_map.to_csv(TABLE_DIR / "standardized_column_map.csv", index=False, encoding="utf-8-sig")

    with sqlite3.connect(DB_PATH) as conn:
        clean_data.to_sql("world_happiness", conn, index=False, if_exists="replace")


def main() -> pd.DataFrame:
    clean_data, raw_summary, column_map = load_and_standardize()
    save_clean_data(clean_data, raw_summary, column_map)

    print("ETL finished")
    print(f"clean rows: {len(clean_data)}")
    print(f"clean columns: {len(clean_data.columns)}")
    print(f"sqlite db: {DB_PATH}")
    return clean_data


if __name__ == "__main__":
    main()
