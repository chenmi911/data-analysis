from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data" / "raw"
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
FIGURE_DIR = PROJECT_DIR / "outputs" / "figures"

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
    frames = []
    raw_summary_rows = []
    column_map_rows = []
    region_map = {}

    for file in sorted(DATA_DIR.glob("*.csv")):
        raw = pd.read_csv(file)
        year = int(file.stem)
        rename_map = RENAME_MAPS[file.name]

        raw_summary_rows.append(
            {
                "year": year,
                "file": file.name,
                "rows": len(raw),
                "cols": len(raw.columns),
                "raw_columns": " | ".join(raw.columns),
            }
        )

        for raw_col, standard_col in rename_map.items():
            column_map_rows.append(
                {
                    "year": year,
                    "file": file.name,
                    "raw_column": raw_col,
                    "standard_column": standard_col,
                }
            )

        df = raw.rename(columns=rename_map)
        df["year"] = year

        if "region" in df.columns:
            current_region = df.dropna(subset=["region"]).set_index("country")["region"]
            region_map.update(current_region.to_dict())

        for col in STANDARD_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan

        frames.append(df[STANDARD_COLUMNS])

    clean = pd.concat(frames, ignore_index=True)
    clean["region"] = clean["region"].fillna(clean["country"].map(region_map))

    raw_summary = pd.DataFrame(raw_summary_rows)
    column_map = pd.DataFrame(column_map_rows)
    return clean, raw_summary, column_map


def build_tables(clean: pd.DataFrame) -> dict[str, pd.DataFrame]:
    tables = {}

    tables["missing_summary"] = (
        clean.isna().sum().reset_index().rename(columns={"index": "field", 0: "missing_count"})
    )
    tables["region_missing_countries"] = clean.loc[
        clean["region"].isna(), ["year", "country"]
    ].sort_values(["country", "year"])
    tables["quality_summary"] = pd.DataFrame(
        [
            {
                "total_rows": len(clean),
                "total_columns": len(clean.columns),
                "unique_countries": clean["country"].nunique(),
                "duplicate_country_year_rows": clean.duplicated(["year", "country"]).sum(),
                "min_year": clean["year"].min(),
                "max_year": clean["year"].max(),
            }
        ]
    )

    sub2019 = clean[clean["year"] == 2019].copy()
    table_cols = [
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
    tables["2019_top10"] = sub2019.nlargest(10, "score")[table_cols]
    tables["2019_bottom10"] = sub2019.nsmallest(10, "score")[table_cols]

    countries_2015 = set(clean.loc[clean["year"] == 2015, "country"])
    countries_2019 = set(clean.loc[clean["year"] == 2019, "country"])
    common_countries = sorted(countries_2015 & countries_2019)
    delta = clean[
        clean["country"].isin(common_countries) & clean["year"].isin([2015, 2019])
    ].pivot(index="country", columns="year", values="score")
    delta["delta_2019_vs_2015"] = delta[2019] - delta[2015]
    tables["score_delta_2019_vs_2015"] = delta.reset_index().sort_values(
        "delta_2019_vs_2015", ascending=False
    )

    tables["yearly_avg_score"] = clean.groupby("year", as_index=False).agg(
        avg_score=("score", "mean"),
        countries=("country", "nunique"),
    )
    tables["region_year_mean_score"] = (
        clean.dropna(subset=["region"])
        .groupby(["year", "region"], as_index=False)["score"]
        .mean()
        .sort_values(["year", "score"], ascending=[True, False])
    )
    tables["region_2019_summary"] = (
        clean[(clean["year"] == 2019) & clean["region"].notna()]
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

    metrics = ["gdp", "social_support", "life_expectancy", "freedom", "generosity", "corruption"]
    corr_rows = []
    for year, year_df in clean.groupby("year"):
        corr = year_df[["score"] + metrics].corr(numeric_only=True)["score"].drop("score")
        for metric, value in corr.items():
            corr_rows.append({"year": year, "metric": metric, "corr_with_score": value})
    tables["correlation_by_year"] = pd.DataFrame(corr_rows)

    overall_corr = (
        clean[["score"] + metrics]
        .corr(numeric_only=True)["score"]
        .drop("score")
        .sort_values(ascending=False)
        .reset_index()
    )
    overall_corr.columns = ["metric", "corr_with_score"]
    tables["correlation_overall"] = overall_corr

    return tables


def save_tables(clean: pd.DataFrame, raw_summary: pd.DataFrame, column_map: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(TABLE_DIR / "world_happiness_clean_2015_2019.csv", index=False, encoding="utf-8-sig")
    raw_summary.to_csv(TABLE_DIR / "raw_file_summary.csv", index=False, encoding="utf-8-sig")
    column_map.to_csv(TABLE_DIR / "standardized_column_map.csv", index=False, encoding="utf-8-sig")

    for name, table in tables.items():
        table.to_csv(TABLE_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")


def style_axes(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def build_charts(clean: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    top10 = tables["2019_top10"]
    bottom10 = tables["2019_bottom10"]
    rank_df = pd.concat([top10.assign(group="Top 10"), bottom10.assign(group="Bottom 10")])
    rank_df = rank_df.sort_values("score")

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = ["#b84545" if group == "Bottom 10" else "#286a8f" for group in rank_df["group"]]
    ax.barh(rank_df["country"], rank_df["score"], color=colors)
    style_axes(ax, "2019 Happiness Score: Top 10 and Bottom 10", "Score", "Country")
    for i, value in enumerate(rank_df["score"]):
        ax.text(value + 0.04, i, f"{value:.3f}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "chart_2019_top_bottom.png", dpi=180)
    plt.close(fig)

    trend = tables["yearly_avg_score"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(trend["year"], trend["avg_score"], marker="o", color="#286a8f", linewidth=2.4)
    style_axes(ax, "Average Happiness Score Trend, 2015-2019", "Year", "Average score")
    ax.set_xticks(trend["year"])
    for x, y in zip(trend["year"], trend["avg_score"]):
        ax.text(x, y + 0.006, f"{y:.3f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "chart_yearly_avg_trend.png", dpi=180)
    plt.close(fig)

    region_2019 = tables["region_2019_summary"].sort_values("avg_score")
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.barh(region_2019["region"], region_2019["avg_score"], color="#4f8f6b")
    style_axes(ax, "2019 Average Happiness Score by Region", "Average score", "Region")
    for i, row in enumerate(region_2019.itertuples()):
        ax.text(row.avg_score + 0.04, i, f"{row.avg_score:.2f}  n={row.countries}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "chart_region_2019_avg.png", dpi=180)
    plt.close(fig)

    sub2019 = clean[clean["year"] == 2019].copy()
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    chart_specs = [
        ("gdp", "GDP per capita"),
        ("social_support", "Social support"),
        ("life_expectancy", "Healthy life expectancy"),
    ]
    for ax, (metric, label) in zip(axes, chart_specs):
        ax.scatter(sub2019[metric], sub2019["score"], alpha=0.72, color="#286a8f", s=30)
        valid = sub2019[[metric, "score"]].dropna()
        coef = np.polyfit(valid[metric], valid["score"], 1)
        xs = np.linspace(valid[metric].min(), valid[metric].max(), 100)
        ax.plot(xs, coef[0] * xs + coef[1], color="#b84545", linewidth=1.8)
        corr = valid[metric].corr(valid["score"])
        style_axes(ax, f"{label}\nr = {corr:.3f}", label, "Score")
    fig.suptitle("2019 Happiness Score vs Key Indicators", fontsize=15, fontweight="bold", y=1.04)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "chart_2019_score_vs_key_indicators.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def validate_outputs(clean: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> None:
    if clean.shape != (782, 11):
        raise AssertionError(f"Expected clean shape (782, 11), got {clean.shape}")

    missing = tables["missing_summary"].set_index("field")["missing_count"]
    if int(missing["region"]) != 8:
        raise AssertionError(f"Expected 8 missing region rows, got {missing['region']}")
    if int(missing["corruption"]) != 1:
        raise AssertionError(f"Expected 1 missing corruption row, got {missing['corruption']}")

    top_2019 = tables["2019_top10"].iloc[0]["country"]
    bottom_2019 = tables["2019_bottom10"].iloc[0]["country"]
    if top_2019 != "Finland":
        raise AssertionError(f"Expected Finland as 2019 top country, got {top_2019}")
    if bottom_2019 != "South Sudan":
        raise AssertionError(f"Expected South Sudan as 2019 bottom country, got {bottom_2019}")

    delta = tables["score_delta_2019_vs_2015"]
    if delta.iloc[0]["country"] != "Benin":
        raise AssertionError("Expected Benin as largest score increase")
    if delta.sort_values("delta_2019_vs_2015").iloc[0]["country"] != "Venezuela":
        raise AssertionError("Expected Venezuela as largest score decrease")


def main() -> None:
    clean, raw_summary, column_map = load_and_standardize()
    tables = build_tables(clean)
    validate_outputs(clean, tables)
    save_tables(clean, raw_summary, column_map, tables)
    build_charts(clean, tables)

    print(f"Project directory: {PROJECT_DIR}")
    print(f"Clean table shape: {clean.shape[0]} rows, {clean.shape[1]} columns")
    print("\nMissing summary:")
    print(tables["missing_summary"].to_string(index=False))
    print("\n2019 top 5:")
    print(tables["2019_top10"][["rank", "country", "region", "score"]].head().to_string(index=False))
    print("\n2019 bottom 5:")
    print(tables["2019_bottom10"][["rank", "country", "region", "score"]].head().to_string(index=False))
    print("\nLargest 2015-2019 increases:")
    print(tables["score_delta_2019_vs_2015"].head(5).to_string(index=False))
    print("\nLargest 2015-2019 decreases:")
    print(
        tables["score_delta_2019_vs_2015"]
        .sort_values("delta_2019_vs_2015")
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
