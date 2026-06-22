#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Describe: 数据分析表生成

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
CLEAN_DATA_PATH = TABLE_DIR / "world_happiness_clean_2015_2019.csv"
METRICS = ["gdp", "social_support", "life_expectancy", "freedom", "generosity", "corruption"]

clean_data = pd.read_csv(CLEAN_DATA_PATH)

missing_summary = (
    clean_data.isna().sum().reset_index().rename(columns={"index": "field", 0: "missing_count"})
)
region_missing_countries = clean_data.loc[
    clean_data["region"].isna(), ["year", "country"]
].sort_values(["country", "year"])
quality_summary = pd.DataFrame(
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
top10_2019 = data_2019.nlargest(10, "score")[output_cols]
bottom10_2019 = data_2019.nsmallest(10, "score")[output_cols]

countries_2015 = set(clean_data.loc[clean_data["year"] == 2015, "country"])
countries_2019 = set(clean_data.loc[clean_data["year"] == 2019, "country"])
common_countries = sorted(countries_2015 & countries_2019)
score_delta_2019_vs_2015 = clean_data[
    clean_data["country"].isin(common_countries) & clean_data["year"].isin([2015, 2019])
].pivot(index="country", columns="year", values="score")
score_delta_2019_vs_2015["delta_2019_vs_2015"] = (
    score_delta_2019_vs_2015[2019] - score_delta_2019_vs_2015[2015]
)
score_delta_2019_vs_2015 = score_delta_2019_vs_2015.reset_index().sort_values(
    "delta_2019_vs_2015", ascending=False
)

yearly_avg_score = clean_data.groupby("year", as_index=False).agg(
    avg_score=("score", "mean"),
    countries=("country", "nunique"),
)
region_year_mean_score = (
    clean_data.dropna(subset=["region"])
    .groupby(["year", "region"], as_index=False)["score"]
    .mean()
    .sort_values(["year", "score"], ascending=[True, False])
)
region_2019_summary = (
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
correlation_by_year = pd.DataFrame(corr_rows)

correlation_overall = (
    clean_data[["score"] + METRICS]
    .corr(numeric_only=True)["score"]
    .drop("score")
    .sort_values(ascending=False)
    .reset_index()
)
correlation_overall.columns = ["metric", "corr_with_score"]

if clean_data.shape != (782, 11):
    raise AssertionError(f"Expected clean shape (782, 11), got {clean_data.shape}")

missing = missing_summary.set_index("field")["missing_count"]
if int(missing["region"]) != 8:
    raise AssertionError(f"Expected 8 missing region rows, got {missing['region']}")
if int(missing["corruption"]) != 1:
    raise AssertionError(f"Expected 1 missing corruption row, got {missing['corruption']}")
if top10_2019.iloc[0]["country"] != "Finland":
    raise AssertionError("Expected Finland as 2019 top country")
if bottom10_2019.iloc[0]["country"] != "South Sudan":
    raise AssertionError("Expected South Sudan as 2019 bottom country")
if score_delta_2019_vs_2015.iloc[0]["country"] != "Benin":
    raise AssertionError("Expected Benin as largest score increase")
if score_delta_2019_vs_2015.sort_values("delta_2019_vs_2015").iloc[0]["country"] != "Venezuela":
    raise AssertionError("Expected Venezuela as largest score decrease")

TABLE_DIR.mkdir(parents=True, exist_ok=True)
missing_summary.to_csv(TABLE_DIR / "missing_summary.csv", index=False, encoding="utf-8-sig")
region_missing_countries.to_csv(
    TABLE_DIR / "region_missing_countries.csv", index=False, encoding="utf-8-sig"
)
quality_summary.to_csv(TABLE_DIR / "quality_summary.csv", index=False, encoding="utf-8-sig")
top10_2019.to_csv(TABLE_DIR / "2019_top10.csv", index=False, encoding="utf-8-sig")
bottom10_2019.to_csv(TABLE_DIR / "2019_bottom10.csv", index=False, encoding="utf-8-sig")
score_delta_2019_vs_2015.to_csv(
    TABLE_DIR / "score_delta_2019_vs_2015.csv", index=False, encoding="utf-8-sig"
)
yearly_avg_score.to_csv(TABLE_DIR / "yearly_avg_score.csv", index=False, encoding="utf-8-sig")
region_year_mean_score.to_csv(
    TABLE_DIR / "region_year_mean_score.csv", index=False, encoding="utf-8-sig"
)
region_2019_summary.to_csv(TABLE_DIR / "region_2019_summary.csv", index=False, encoding="utf-8-sig")
correlation_by_year.to_csv(TABLE_DIR / "correlation_by_year.csv", index=False, encoding="utf-8-sig")
correlation_overall.to_csv(TABLE_DIR / "correlation_overall.csv", index=False, encoding="utf-8-sig")

print("Analysis finished")
print(missing_summary.to_string(index=False))
