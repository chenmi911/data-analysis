from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import chi2_contingency, f_oneway, levene, shapiro, ttest_ind


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "data" / "raw" / "yulu_bike_sharing_dataset.csv"
FIGURES_DIR = PROJECT_DIR / "outputs" / "figures"


def main() -> None:
    df = pd.read_csv(DATA_PATH, parse_dates=["datetime"])
    categorical_columns = ["season", "holiday", "workingday", "weather"]
    df[categorical_columns] = df[categorical_columns].astype("category")

    print("数据维度:", df.shape)
    print("缺失值总数:", int(df.isna().sum().sum()))
    print("重复 datetime:", int(df["datetime"].duplicated().sum()))
    print("count 与 casual + registered 是否一致:",
          bool((df["count"] == df["casual"] + df["registered"]).all()))
    print("天气类别样本量:", df["weather"].value_counts().sort_index().to_dict())

    # workingday 按天定义；先汇总每日租车量，避免把同日小时当成独立样本。
    daily_data = (
        df.assign(date=df["datetime"].dt.date)
        .groupby("date", as_index=False)
        .agg(workingday=("workingday", "first"), daily_count=("count", "sum"))
    )
    daily_summary = daily_data.groupby("workingday", observed=True)["daily_count"].agg(
        ["mean", "std", "count"]
    )
    workday = daily_data.loc[daily_data["workingday"] == 1, "daily_count"]
    non_workday = daily_data.loc[daily_data["workingday"] == 0, "daily_count"]
    t_stat, workday_p = ttest_ind(workday, non_workday, equal_var=False)
    print("\n每日总租车量:")
    print(daily_summary)
    print(f"Welch t = {t_stat:.3f}, p = {workday_p:.4f}")

    # 方差不齐时用 Welch ANOVA；Shapiro 结果只作诊断，大样本下很敏感。
    season_groups = [
        df.loc[df["season"] == season, "count"]
        for season in [1, 2, 3, 4]
    ]
    shapiro_results = {
        season: shapiro(df.loc[df["season"] == season, "count"])
        for season in [1, 2, 3, 4]
    }
    season_levene = levene(*season_groups)
    season_welch = f_oneway(*season_groups, equal_var=False)
    print("\n季节 Shapiro 结果:", shapiro_results)
    print("季节 Levene:", season_levene)
    print("季节 Welch ANOVA:", season_welch)

    # 天气 4 只有一条记录，无法估计组内方差，不纳入 Welch ANOVA。
    weather_groups = [
        df.loc[df["weather"] == weather, "count"]
        for weather in [1, 2, 3]
    ]
    weather_levene = levene(*weather_groups)
    weather_welch = f_oneway(*weather_groups, equal_var=False)
    print("\n天气 1–3 Levene:", weather_levene)
    print("天气 1–3 Welch ANOVA:", weather_welch)

    # 天气 4 的单条记录会造成极小期望频数，因此从卡方检验中排除。
    common_weather = df[df["weather"].isin([1, 2, 3])]
    contingency_table = pd.crosstab(common_weather["season"], common_weather["weather"])
    chi2, chi2_p, dof, expected = chi2_contingency(contingency_table)
    cramers_v = np.sqrt(
        chi2
        / (
            contingency_table.to_numpy().sum()
            * min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)
        )
    )
    print("\n季节 × 天气 1–3 卡方检验:")
    print(f"chi2 = {chi2:.2f}, df = {dof}, p = {chi2_p:.3g}")
    print(f"最小期望频数 = {expected.min():.2f}, Cramér's V = {cramers_v:.3f}")

    # 类别图展示各类别的小时记录数，不代表类别间的需求量。
    continuous_columns = [
        "temp", "atemp", "humidity", "windspeed", "casual", "registered", "count"
    ]
    fig, axes = plt.subplots(4, 2, figsize=(15, 20))
    axes = axes.flatten()
    for ax, column in zip(axes, continuous_columns):
        sns.histplot(df[column], ax=ax, kde=True)
        ax.set(title=f"Distribution of {column}", xlabel=column, ylabel="Hourly records")
    fig.delaxes(axes[-1])
    fig.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "hourly_distributions.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes = axes.flatten()
    for ax, column in zip(axes, categorical_columns):
        sns.countplot(data=df, x=column, ax=ax, color="#4C78A8")
        ax.set(title=f"Hourly records by {column}", xlabel=column, ylabel="Hours")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "category_hour_counts.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
