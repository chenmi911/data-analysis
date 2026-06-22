#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Describe: 数据可视化

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
FIGURE_DIR = PROJECT_DIR / "outputs" / "figures"


def read_table(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / f"{name}.csv")


def style_axes(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def chart_2019_top_bottom() -> None:
    top10 = read_table("2019_top10")
    bottom10 = read_table("2019_bottom10")
    data = pd.concat([top10.assign(group="Top 10"), bottom10.assign(group="Bottom 10")])
    data = data.sort_values("score")

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = ["#b84545" if group == "Bottom 10" else "#286a8f" for group in data["group"]]
    ax.barh(data["country"], data["score"], color=colors)
    style_axes(ax, "2019 Happiness Score: Top 10 and Bottom 10", "Score", "Country")

    for i, value in enumerate(data["score"]):
        ax.text(value + 0.04, i, f"{value:.3f}", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "chart_2019_top_bottom.png", dpi=180)
    plt.close(fig)


def chart_yearly_avg_trend() -> None:
    trend = read_table("yearly_avg_score")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(trend["year"], trend["avg_score"], marker="o", color="#286a8f", linewidth=2.4)
    style_axes(ax, "Average Happiness Score Trend, 2015-2019", "Year", "Average score")
    ax.set_xticks(trend["year"])

    for x, y in zip(trend["year"], trend["avg_score"]):
        ax.text(x, y + 0.006, f"{y:.3f}", ha="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "chart_yearly_avg_trend.png", dpi=180)
    plt.close(fig)


def chart_region_2019_avg() -> None:
    data = read_table("region_2019_summary").sort_values("avg_score")

    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.barh(data["region"], data["avg_score"], color="#4f8f6b")
    style_axes(ax, "2019 Average Happiness Score by Region", "Average score", "Region")

    for i, row in enumerate(data.itertuples()):
        ax.text(row.avg_score + 0.04, i, f"{row.avg_score:.2f}  n={row.countries}", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "chart_region_2019_avg.png", dpi=180)
    plt.close(fig)


def chart_2019_score_vs_key_indicators() -> None:
    clean_data = read_table("world_happiness_clean_2015_2019")
    data_2019 = clean_data[clean_data["year"] == 2019].copy()

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    chart_specs = [
        ("gdp", "GDP per capita"),
        ("social_support", "Social support"),
        ("life_expectancy", "Healthy life expectancy"),
    ]

    for ax, (metric, label) in zip(axes, chart_specs):
        ax.scatter(data_2019[metric], data_2019["score"], alpha=0.72, color="#286a8f", s=30)
        valid = data_2019[[metric, "score"]].dropna()
        coef = np.polyfit(valid[metric], valid["score"], 1)
        xs = np.linspace(valid[metric].min(), valid[metric].max(), 100)
        ax.plot(xs, coef[0] * xs + coef[1], color="#b84545", linewidth=1.8)
        corr = valid[metric].corr(valid["score"])
        style_axes(ax, f"{label}\nr = {corr:.3f}", label, "Score")

    fig.suptitle("2019 Happiness Score vs Key Indicators", fontsize=15, fontweight="bold", y=1.04)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "chart_2019_score_vs_key_indicators.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    chart_2019_top_bottom()
    chart_yearly_avg_trend()
    chart_region_2019_avg()
    chart_2019_score_vs_key_indicators()
    print("Visualize finished")


if __name__ == "__main__":
    main()
