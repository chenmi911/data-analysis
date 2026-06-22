#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Describe: 数据分析表生成

from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
DB_PATH = PROJECT_DIR / "outputs" / "world_happiness.db"

METRICS = ["gdp", "social_support", "life_expectancy", "freedom", "generosity", "corruption"]


def read_clean_data() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("select * from world_happiness", conn)


def build_tables(clean_data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    tables = {}

    tables["missing_summary"] = (
        clean_data.isna().sum().reset_index().rename(columns={"index": "field", 0: "missing_count"})
    )
    tables["region_missing_countries"] = clean_data.loc[
        clean_data["region"].isna(), ["year", "country"]
    ].sort_values(["country", "year"])
    tables["quality_summary"] = pd.DataFrame(
        [
            {
                "total_rows": len(clean_data),
                "total_columns": len(clean_data.columns),
                "unique_countries": clean_data["country"].nunique(),
                "duplicate_country_year_rows": clean_data.duplicated(["year", "country"]).sum(),
                "min_year": clean_data["year"].min(),
                "max_year": clean_data["year"].max(),
            }
        ]
    )

    data_2019 = clean_data[clean_data["year"] == 2019].copy()
    output_cols = [
        "rank",
        "country",
        "region",
        "score",
        "gdp",
        "social_support",
        "life_expectancy",
        "freedom",
        "generosity",
        "corruption",
    ]
    tables["2019_top10"] = data_2019.nlargest(10, "score")[output_cols]
    tables["2019_bottom10"] = data_2019.nsmallest(10, "score")[output_cols]

    countries_2015 = set(clean_data.loc[clean_data["year"] == 2015, "country"])
    countries_2019 = set(clean_data.loc[clean_data["year"] == 2019, "country"])
    common_countries = sorted(countries_2015 & countries_2019)
    delta = clean_data[
        clean_data["country"].isin(common_countries) & clean_data["year"].isin([2015, 2019])
    ].pivot(index="country", columns="year", values="score")
    delta["delta_2019_vs_2015"] = delta[2019] - delta[2015]
    tables["score_delta_2019_vs_2015"] = delta.reset_index().sort_values(
        "delta_2019_vs_2015", ascending=False
    )

    tables["yearly_avg_score"] = clean_data.groupby("year", as_index=False).agg(
        avg_score=("score", "mean"),
        countries=("country", "nunique"),
    )
    tables["region_year_mean_score"] = (
        clean_data.dropna(subset=["region"])
        .groupby(["year", "region"], as_index=False)["score"]
        .mean()
        .sort_values(["year", "score"], ascending=[True, False])
    )
    tables["region_2019_summary"] = (
        clean_data[(clean_data["year"] == 2019) & clean_data["region"].notna()]
        .groupby("region", as_index=False)
        .agg(
            avg_score=("score", "mean"),
            countries=("country", "nunique"),
            avg_gdp=("gdp", "mean"),
            avg_social_support=("social_support", "mean"),
            avg_life_expectancy=("life_expectancy", "mean"),
        )
        .sort_values("avg_score", ascending=False)
    )

    corr_rows = []
    for year, year_data in clean_data.groupby("year"):
        corr = year_data[["score"] + METRICS].corr(numeric_only=True)["score"].drop("score")
        for metric, value in corr.items():
            corr_rows.append({"year": year, "metric": metric, "corr_with_score": value})
    tables["correlation_by_year"] = pd.DataFrame(corr_rows)

    overall_corr = (
        clean_data[["score"] + METRICS]
        .corr(numeric_only=True)["score"]
        .drop("score")
        .sort_values(ascending=False)
        .reset_index()
    )
    overall_corr.columns = ["metric", "corr_with_score"]
    tables["correlation_overall"] = overall_corr
    return tables


def save_tables(tables: dict[str, pd.DataFrame]) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(TABLE_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")


def validate_outputs(clean_data: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> None:
    if clean_data.shape != (782, 11):
        raise AssertionError(f"Expected clean shape (782, 11), got {clean_data.shape}")

    missing = tables["missing_summary"].set_index("field")["missing_count"]
    if int(missing["region"]) != 8:
        raise AssertionError(f"Expected 8 missing region rows, got {missing['region']}")
    if int(missing["corruption"]) != 1:
        raise AssertionError(f"Expected 1 missing corruption row, got {missing['corruption']}")

    if tables["2019_top10"].iloc[0]["country"] != "Finland":
        raise AssertionError("Expected Finland as 2019 top country")
    if tables["2019_bottom10"].iloc[0]["country"] != "South Sudan":
        raise AssertionError("Expected South Sudan as 2019 bottom country")

    delta = tables["score_delta_2019_vs_2015"]
    if delta.iloc[0]["country"] != "Benin":
        raise AssertionError("Expected Benin as largest score increase")
    if delta.sort_values("delta_2019_vs_2015").iloc[0]["country"] != "Venezuela":
        raise AssertionError("Expected Venezuela as largest score decrease")


def main() -> dict[str, pd.DataFrame]:
    clean_data = read_clean_data()
    tables = build_tables(clean_data)
    validate_outputs(clean_data, tables)
    save_tables(tables)

    print("Analysis finished")
    print(tables["missing_summary"].to_string(index=False))
    return tables


if __name__ == "__main__":
    main()
