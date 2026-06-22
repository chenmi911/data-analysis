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

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
plt.style.use("seaborn-v0_8-whitegrid")

top10 = pd.read_csv(TABLE_DIR / "2019_top10.csv")
bottom10 = pd.read_csv(TABLE_DIR / "2019_bottom10.csv")
rank_data = pd.concat([top10.assign(group="Top 10"), bottom10.assign(group="Bottom 10")])
rank_data = rank_data.sort_values("score")

fig, ax = plt.subplots(figsize=(11, 7))
colors = ["#b84545" if group == "Bottom 10" else "#286a8f" for group in rank_data["group"]]
ax.barh(rank_data["country"], rank_data["score"], color=colors)
ax.set_title("2019 Happiness Score: Top 10 and Bottom 10", fontsize=13, fontweight="bold", loc="left", pad=12)
ax.set_xlabel("Score")
ax.set_ylabel("Country")
ax.grid(axis="x", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for i, value in enumerate(rank_data["score"]):
    ax.text(value + 0.04, i, f"{value:.3f}", va="center", fontsize=8)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "chart_2019_top_bottom.png", dpi=180)
plt.close(fig)

trend = pd.read_csv(TABLE_DIR / "yearly_avg_score.csv")
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(trend["year"], trend["avg_score"], marker="o", color="#286a8f", linewidth=2.4)
ax.set_title("Average Happiness Score Trend, 2015-2019", fontsize=13, fontweight="bold", loc="left", pad=12)
ax.set_xlabel("Year")
ax.set_ylabel("Average score")
ax.set_xticks(trend["year"])
ax.grid(axis="x", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for x, y in zip(trend["year"], trend["avg_score"]):
    ax.text(x, y + 0.006, f"{y:.3f}", ha="center", fontsize=8)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "chart_yearly_avg_trend.png", dpi=180)
plt.close(fig)

region_2019 = pd.read_csv(TABLE_DIR / "region_2019_summary.csv").sort_values("avg_score")
fig, ax = plt.subplots(figsize=(11, 6.5))
ax.barh(region_2019["region"], region_2019["avg_score"], color="#4f8f6b")
ax.set_title("2019 Average Happiness Score by Region", fontsize=13, fontweight="bold", loc="left", pad=12)
ax.set_xlabel("Average score")
ax.set_ylabel("Region")
ax.grid(axis="x", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for i, row in enumerate(region_2019.itertuples()):
    ax.text(row.avg_score + 0.04, i, f"{row.avg_score:.2f}  n={row.countries}", va="center", fontsize=8)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "chart_region_2019_avg.png", dpi=180)
plt.close(fig)

clean_data = pd.read_csv(TABLE_DIR / "world_happiness_clean_2015_2019.csv")
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
    ax.set_title(f"{label}\nr = {corr:.3f}", fontsize=13, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel(label)
    ax.set_ylabel("Score")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig.suptitle("2019 Happiness Score vs Key Indicators", fontsize=15, fontweight="bold", y=1.04)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "chart_2019_score_vs_key_indicators.png", dpi=180, bbox_inches="tight")
plt.close(fig)

print("Visualize finished")
