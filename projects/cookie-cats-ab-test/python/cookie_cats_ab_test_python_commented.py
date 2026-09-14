from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

import matplotlib.pyplot as plt

# ============================================================
# 1. 数据读取
# ============================================================
DATA_PATH = Path("data/raw/cookie_cats.csv")
df = pd.read_csv(DATA_PATH)
print("数据维度：", df.shape)
print("\n前 5 行：")
print(df.head())
print("\n数据类型：")
print(df.dtypes)
# ============================================================
# 2. 数据清洗
# ============================================================
def convert_retention(series):
    """
    将 TRUE/FALSE 转换成 1/0
    """
    return (
        series
        .astype(str)
        .str.strip()
        .str.lower()
        .map({
            "true": 1,
            "false": 0,
            "1": 1,
            "0": 0
        })
    )

df["retention_1"] = convert_retention(df["retention_1"])
df["retention_7"] = convert_retention(df["retention_7"])
# ============================================================
# 3. 数据质量检查
# ============================================================
quality_check = {
    "row_count": len(df),
    "unique_users": df["userid"].nunique(),
    "duplicate_userid_rows": (
        len(df) - df["userid"].nunique()
    ),
    "missing_userid": df["userid"].isna().sum(),
    "missing_version": df["version"].isna().sum(),
    "missing_sum_gamerounds": df["sum_gamerounds"].isna().sum(),
    "missing_retention_1": df["retention_1"].isna().sum(),
    "missing_retention_7": df["retention_7"].isna().sum(),
    "min_sum_gamerounds": df["sum_gamerounds"].min(),
    "max_sum_gamerounds": df["sum_gamerounds"].max()
}

quality_df = pd.Series(quality_check, name="value")

print(quality_df)

# ============================================================
# 4. 检查实验组
# ============================================================
# 检查两组人数比例

group_summary = (
    df.groupby("version")
      .agg(
          users=("userid", "count")
      )
      .reset_index()
)

group_summary["user_share"] = (
    group_summary["users"] / len(df)
)

print(group_summary)


# ============================================================
# 5. 定义 Control 和 Treatment
# ============================================================
CONTROL = "gate_30"
TREATMENT = "gate_40"

control = df[df["version"] == CONTROL].copy()
treatment = df[df["version"] == TREATMENT].copy()
# ============================================================
# 6. 留存率描述统计
# ============================================================
retention_summary = (
    df.groupby("version")
      .agg(
          users=("userid", "count"),
          D1_retention=("retention_1", "mean"),
          D7_retention=("retention_7", "mean")
      )
      .reset_index()
)

print(retention_summary)

# ============================================================
# 7. Game Rounds 描述统计
# ============================================================
# sum_gamerounds 是右偏数据。
game_rounds_summary = (
    df.groupby("version")["sum_gamerounds"]
      .agg(
          users="count",
          mean="mean",
          min="min",
          max="max",
          p50=lambda x: x.quantile(0.50),
          p75=lambda x: x.quantile(0.75),
          p90=lambda x: x.quantile(0.90),
          p95=lambda x: x.quantile(0.95),
          p99=lambda x: x.quantile(0.99)
      )
      .reset_index()
)
print(game_rounds_summary)

# ============================================================
# 8. Treatment Effect：D7 Retention
# ============================================================

control_d7 = control["retention_7"].mean()
treatment_d7 = treatment["retention_7"].mean()

absolute_diff = treatment_d7 - control_d7
relative_diff = absolute_diff / control_d7

print("\n================ Treatment Effect ================\n")
print(f"Control D7 Retention   : {control_d7:.4%}")
print(f"Treatment D7 Retention : {treatment_d7:.4%}")
print(f"Absolute Difference    : {absolute_diff:.4%}")
print(f"Relative Difference    : {relative_diff:.4%}")

# ============================================================
# 9. 两比例 Z Test
# ============================================================
# 原假设 H0：p_T = p_C

control_success = control["retention_7"].sum()
treatment_success = treatment["retention_7"].sum()

control_n = len(control)
treatment_n = len(treatment)

z_stat, p_value = proportions_ztest(
    count=[
        treatment_success,
        control_success
    ],
    nobs=[
        treatment_n,
        control_n
    ],
    alternative="two-sided"
)

print("\n================ D7 两比例 Z Test ================\n")

print(f"Control successes   : {control_success}")
print(f"Treatment successes : {treatment_success}")
print(f"Control N           : {control_n}")
print(f"Treatment N         : {treatment_n}")
print(f"Z-statistic         : {z_stat:.4f}")
print(f"P-value             : {p_value:.6f}")


# ============================================================
# 10. 95% Confidence Interval
# ============================================================
se_ci = np.sqrt(
    treatment_d7 * (1 - treatment_d7) / treatment_n
    +
    control_d7 * (1 - control_d7) / control_n
)

z_critical = 1.96

ci_low = absolute_diff - z_critical * se_ci
ci_high = absolute_diff + z_critical * se_ci

print("\n================ 95% Confidence Interval ================\n")

print(f"Effect   : {absolute_diff:.4%}")
print(f"CI Low   : {ci_low:.4%}")
print(f"CI High  : {ci_high:.4%}")


# ============================================================
# 11. 用函数统一计算 D1 / D7 A/B Test
# ============================================================

def ab_test_proportion(
    df,
    metric,
    control_group="gate_30",
    treatment_group="gate_40"
):
    control = (
        df.loc[
            df["version"] == control_group,
            metric
        ]
        .dropna()
    )

    treatment = (
        df.loc[
            df["version"] == treatment_group,
            metric
        ]
        .dropna()
    )

    control_n = len(control)
    treatment_n = len(treatment)

    control_success = control.sum()
    treatment_success = treatment.sum()

    control_rate = control.mean()
    treatment_rate = treatment.mean()

    # Treatment Effect
    absolute_diff = treatment_rate - control_rate

    relative_diff = (
        absolute_diff / control_rate
    )

    # Two-proportion Z Test
    z_stat, p_value = proportions_ztest(
        count=[
            treatment_success,
            control_success
        ],
        nobs=[
            treatment_n,
            control_n
        ],
        alternative="two-sided"
    )

    # Confidence Interval
    se_ci = np.sqrt(
        treatment_rate * (1 - treatment_rate) / treatment_n
        +
        control_rate * (1 - control_rate) / control_n
    )

    ci_low = absolute_diff - 1.96 * se_ci
    ci_high = absolute_diff + 1.96 * se_ci

    return {
        "metric": metric,
        "control_n": control_n,
        "treatment_n": treatment_n,
        "control_rate": control_rate,
        "treatment_rate": treatment_rate,
        "absolute_diff": absolute_diff,
        "relative_diff": relative_diff,
        "z_stat": z_stat,
        "p_value": p_value,
        "ci95_low": ci_low,
        "ci95_high": ci_high
    }


results = []

for metric in ["retention_1", "retention_7"]:
    results.append(
        ab_test_proportion(
            df=df,
            metric=metric,
            control_group=CONTROL,
            treatment_group=TREATMENT
        )
    )

ab_results = pd.DataFrame(results)

print("\n================ A/B Test 汇总 ================\n")
print(ab_results)


# ============================================================
# 12. Game Rounds：Mean Difference
# ============================================================

control_mean = control["sum_gamerounds"].mean()
treatment_mean = treatment["sum_gamerounds"].mean()

mean_diff = treatment_mean - control_mean

print("\n================ Game Rounds Mean Difference ================\n")

print(f"Control Mean   : {control_mean:.2f}")
print(f"Treatment Mean : {treatment_mean:.2f}")
print(f"Difference     : {mean_diff:.2f}")


# ============================================================
# 13. Game Rounds 分布可视化
# ============================================================

plt.figure(figsize=(10, 5))

plt.hist(
    control["sum_gamerounds"],
    bins=100,
    alpha=0.5,
    label=CONTROL
)

plt.hist(
    treatment["sum_gamerounds"],
    bins=100,
    alpha=0.5,
    label=TREATMENT
)

plt.xlabel("Game Rounds")
plt.ylabel("Number of Users")
plt.title("Distribution of Game Rounds")

plt.legend()
plt.tight_layout()
plt.show()


# ============================================================
# 14. D7 Retention 可视化
# ============================================================

plot_data = (
    retention_summary
    .set_index("version")[["D7_retention"]]
)

plot_data.plot(
    kind="bar",
    figsize=(7, 5),
    legend=False
)

plt.ylabel("D7 Retention")
plt.xlabel("Experiment Group")
plt.title("D7 Retention: Gate 30 vs Gate 40")

plt.tight_layout()
plt.show()


# ============================================================
# 15. 业务决策：主辅指标 + 口径 + 分层（不是只看一个留存）
# ============================================================

alpha = 0.05


def per_metric_reading(row):
    if row["p_value"] < alpha and row["ci95_high"] < 0:
        return "显著变差（负向证据）"
    if row["p_value"] < alpha and row["ci95_low"] > 0:
        return "显著变好（正向证据）"
    return "无显著差异"

for _, r in ab_results.iterrows():
    print(
        f"{r['metric']:<12} "
        f"gate_30={r['control_rate']:.4%}  gate_40={r['treatment_rate']:.4%}  "
        f"diff={r['absolute_diff']:+.4%}  相对={r['relative_diff']:+.2%}  "
        f"z={r['z_stat']:.3f}  p={r['p_value']:.5f}  "
        f"95%CI=[{r['ci95_low']:.4%}, {r['ci95_high']:.4%}]  "
        f"=> {per_metric_reading(r)}"
    )

d7 = ab_results[ab_results["metric"] == "retention_7"].iloc[0]

# ---- 15.2 口径提醒：多少人根本没碰到门槛 ----
# 前 14 天里，多数玩家没打到 30 / 40 关。门槛位置并不影响这些人，
# 他们却被计入全体分母——所以全体平均效应会被稀释，容易误读成"影响很小"。

control_never_gate = (control["sum_gamerounds"] < 30).mean()
treatment_never_gate = (treatment["sum_gamerounds"] < 40).mean()

print("\n================ 口径：多少人没碰到门槛 ================\n")
print(f"gate_30 中没打到 30 关的比例 : {control_never_gate:.4%}")
print(f"gate_40 中没打到 40 关的比例 : {treatment_never_gate:.4%}")

control_reached = control[control["sum_gamerounds"] >= 30].copy()
treatment_reached = treatment[treatment["sum_gamerounds"] >= 40].copy()
df_reached = pd.concat([control_reached, treatment_reached], ignore_index=True)

r7_reached = ab_test_proportion(df_reached, "retention_7")
r1_reached = ab_test_proportion(df_reached, "retention_1")

print("\n============ 到达各自门槛的玩家（只作诊断，不作结论） ============\n")
print(f"到达者 7 日留存 : gate_30={r7_reached['control_rate']:.4%} "
      f"(n={r7_reached['control_n']}) vs gate_40={r7_reached['treatment_rate']:.4%} "
      f"(n={r7_reached['treatment_n']})  diff={r7_reached['absolute_diff']:+.4%}  p={r7_reached['p_value']:.5f}")
print(f"到达者 1 日留存 : gate_30={r1_reached['control_rate']:.4%} "
      f"vs gate_40={r1_reached['treatment_rate']:.4%}  diff={r1_reached['absolute_diff']:+.4%}  p={r1_reached['p_value']:.5f}")

control_ge40 = control[control["sum_gamerounds"] >= 40].copy()
treatment_ge40 = treatment[treatment["sum_gamerounds"] >= 40].copy()
df_ge40 = pd.concat([control_ge40, treatment_ge40], ignore_index=True)
r7_ge40 = ab_test_proportion(df_ge40, "retention_7")

print("\n============ 稳健性：两组都打到 ≥40 局的玩家 ============\n")
print(f"7 日留存 : gate_30={r7_ge40['control_rate']:.4%} (n={r7_ge40['control_n']}) "
      f"vs gate_40={r7_ge40['treatment_rate']:.4%} (n={r7_ge40['treatment_n']})  "
      f"diff={r7_ge40['absolute_diff']:+.4%}  p={r7_ge40['p_value']:.5f}")

expected_d7 = d7["control_rate"] * len(treatment)
actual_d7 = d7["treatment_rate"] * len(treatment)

print("\n================ 实际意义（业务量级） ================\n")
print(f"D7 相对变化        : {d7['relative_diff']:+.2%}")
print(f"期望 D7 留存数     : {expected_d7:.0f} 人（若都按 gate_30 留存率）")
print(f"实际 D7 留存数     : {actual_d7:.0f} 人")
print(f"差额               : 约 {expected_d7 - actual_d7:.0f} 名 D7 留存用户，"
      f"约占实验组 {(expected_d7 - actual_d7) / len(treatment):.2%}")

# ---- 15.6 按规则给出结论 ----

primary_worse = d7["p_value"] < alpha and d7["ci95_high"] < 0
primary_better = d7["p_value"] < alpha and d7["ci95_low"] > 0

print("\n================ 最终业务结论 ================\n")

if primary_worse:
    print(
        "主指标 7 日留存显著受损（p<0.05 且 95% CI 全为负）；"
        "辅助指标 1 日留存方向同负，Game Rounds 分位数无增益，"
        "没有能抵消主指标损失的证据。"
    )
    print("→ 建议保持 gate_30，不推广 gate_40。")
    print("  依据是决策规则 + 多指标一致性 + 全体(ITT)口径，而不是单个 p 值。")
elif primary_better:
    print(
        "主指标 7 日留存显著为正，且没有辅助指标显著受损："
        "主指标层面可以接受，可进入结合商业化数据的下一步评估。"
    )
else:
    print(
        "主指标 7 日留存没有显著差异，属于'暂无定论'："
        "应扩大样本或补充指标后再判断，而不是强行下结论。"
    )

print(f"\n关键数字：D7 effect={d7['absolute_diff']:.4%}, p={d7['p_value']:.6f}, "
      f"95%CI=[{d7['ci95_low']:.4%}, {d7['ci95_high']:.4%}]")

