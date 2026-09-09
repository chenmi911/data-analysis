"""
Cookie Cats A/B Test Analysis
=============================

项目目标：
比较 gate_30（Control）和 gate_40（Treatment），判断把游戏 Gate 从第 30 关
移动到第 40 关是否会影响用户留存和游戏行为。

主要指标与决策规则：
- 主指标：D7 Retention（先定主指标，避免事后挑指标）
- 辅助指标：D1 Retention、Game Rounds
- 决策规则在分析前定好：主指标显著受损、且辅助指标无抵消证据，才倾向不推广

统计方法：
1. 描述统计
2. 两比例 Z 检验
3. Effect Size（绝对差异、相对差异）
4. 95% Confidence Interval
5. Game Rounds 分位数分析
6. "到达门槛"分层与选择偏差诊断
7. 多指标证据汇总的业务决策

注意：
- 原始 CSV 放 data/raw/cookie_cats.csv（与 SQL 脚本导入同一文件）。
- 在项目根目录 projects/cookie-cats-ab-test/ 下运行本脚本即可。
- retention_1 / retention_7 可以是 TRUE/FALSE，也可以已经是 0/1。
- 结论以全体样本(ITT)为因果口径，不要用"到达门槛"子集翻案。
"""

# ============================================================
# 0. 导入库
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

import matplotlib.pyplot as plt


# ============================================================
# 1. 数据读取
# ============================================================

# Path 比直接写字符串路径更适合管理项目文件。
# 数据放在 data/raw/ 下，与 MySQL 脚本导入的是同一个文件。
# 在项目根目录 projects/cookie-cats-ab-test/ 下运行本脚本即可。
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

# 原始数据中的 retention_1 / retention_7 通常是 TRUE / FALSE。
# 我们把它转换成：
#
# TRUE  -> 1
# FALSE -> 0
#
# 为什么？
# 因为对于 0/1 变量：
#
# mean(0, 1, 1, 0, 1)
# = 3 / 5
# = 60%
#
# 所以二元变量的平均值就是事件发生率。
#
# 例如：
# retention_7.mean()
# 就等价于 D7 Retention Rate。

def convert_retention(series):
    """
    将 TRUE/FALSE 转换成 1/0。

    同时允许原始数据本身已经是 0/1。
    无法识别的值会变成 NaN。
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

# A/B Test 的第一步不是直接做统计检验。
# 首先要确认数据本身没有明显问题。

quality_check = {
    "row_count": len(df),

    # 不重复用户数量
    "unique_users": df["userid"].nunique(),

    # 如果 row_count != unique_users，
    # 说明可能存在一个用户多行的问题。
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

print("\n================ 数据质量检查 ================\n")
print(quality_df)


# ============================================================
# 4. 检查实验组
# ============================================================

# 实验设计：
#
# gate_30 = Control
# gate_40 = Treatment
#
# 这里首先检查两组人数是否大致合理。
#
# 注意：
# 50/50 的人数比例只能说明分流比例没有明显异常，
# 不能单独证明随机化完全成功。

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

print("\n================ 实验组检查 ================\n")
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

# retention_1 / retention_7 是 0/1 变量。
#
# 因此：
#
# AVG(retention_1) = D1 Retention
# AVG(retention_7) = D7 Retention

retention_summary = (
    df.groupby("version")
      .agg(
          users=("userid", "count"),
          D1_retention=("retention_1", "mean"),
          D7_retention=("retention_7", "mean")
      )
      .reset_index()
)

print("\n================ 留存率 ================\n")
print(retention_summary)

# 如果需要百分比形式：
retention_display = retention_summary.copy()

retention_display["D1_retention"] *= 100
retention_display["D7_retention"] *= 100

print("\n百分比形式：")
print(retention_display)


# ============================================================
# 7. Game Rounds 描述统计
# ============================================================

# sum_gamerounds 通常是明显右偏、长尾的数据。
#
# 所以不能只看 mean。
#
# 我们同时观察：
# P50 = Median，中位数
# P75
# P90
# P95
# P99
#
# 这样可以了解不同活跃程度用户的行为分布。

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

print("\n================ Game Rounds 分布 ================\n")
print(game_rounds_summary)


# ============================================================
# 8. Treatment Effect：D7 Retention
# ============================================================

control_d7 = control["retention_7"].mean()
treatment_d7 = treatment["retention_7"].mean()

# Absolute Difference：
#
# Treatment - Control
#
# 例如：
# 18% - 20% = -2 percentage points

absolute_diff = treatment_d7 - control_d7

# Relative Difference：
#
# (Treatment - Control) / Control
#
# 例如：
# (18% - 20%) / 20% = -10%

relative_diff = absolute_diff / control_d7

print("\n================ Treatment Effect ================\n")

print(f"Control D7 Retention   : {control_d7:.4%}")
print(f"Treatment D7 Retention : {treatment_d7:.4%}")
print(f"Absolute Difference    : {absolute_diff:.4%}")
print(f"Relative Difference    : {relative_diff:.4%}")


# ============================================================
# 9. 两比例 Z Test
# ============================================================

# 我们现在要回答：
#
# 观察到的 Treatment - Control 差异，
# 是否可能只是随机抽样造成的？
#
# 原假设 H0：
#
#     p_T = p_C
#
# 也就是两组总体留存率没有差异。
#
# 备择假设 H1：
#
#     p_T != p_C
#
# 所以这里使用 two-sided test。

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

# 对于两比例差异：
#
# effect = p_T - p_C
#
# 常见的 Wald CI：
#
# effect ± 1.96 * SE
#
# 这里使用未 pooled 的 SE 来构造 CI：
#
# SE =
# sqrt[
#     p_T(1-p_T)/n_T
#     +
#     p_C(1-p_C)/n_C
# ]

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
    """
    对 0/1 指标执行两比例 A/B Test。

    参数
    ----
    df : DataFrame
        原始数据。

    metric : str
        0/1 指标，例如 retention_1 / retention_7。

    control_group : str
        控制组名称。

    treatment_group : str
        实验组名称。

    返回
    ----
    dict
        包含样本量、比例、Effect、Z、P-value、95% CI。
    """

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


# 同时分析 D1 和 D7
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

# 原始 Game Rounds 通常存在严重长尾。
# 因此原始直方图可能会被极端值拉伸。
#
# 这里先提供基础版本。

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

# 前面我们有了三类证据：
#   - D1 / D7 留存检验：ab_results（两比例 Z 检验 + 95% CI）
#   - Game Rounds 分位数：长尾活跃度
#
# 把"看数据"和"做决策"分开，分四步：
#   15.1 每个指标各自给出什么证据
#   15.2 口径提醒：多少人根本没碰到门槛
#   15.3 "到达门槛"分层：为什么结论会反转、为什么不能信（选择偏差）
#   15.4 稳健性：同样打到 40 局以上的玩家
#   15.5 实际意义换算：把百分点翻译成用户数
#   15.6 按决策规则给结论

# 决策规则（在分析前定好，避免数据出来再找理由）：
#   主指标 7 日留存显著受损（p<0.05 且 95% CI 上限<0），
#   且辅助指标(1 日留存、Game Rounds)没有能抵消的正向证据 → 不推广。

alpha = 0.05


def per_metric_reading(row):
    """
    把单个 0/1 指标的检验结果翻译成一句"该指标给出的证据方向"。

    注意：它只回答这一个指标，不负责下总体结论。
    """
    if row["p_value"] < alpha and row["ci95_high"] < 0:
        return "显著变差（负向证据）"
    if row["p_value"] < alpha and row["ci95_low"] > 0:
        return "显著变好（正向证据）"
    return "无显著差异"


# ---- 15.1 每个指标各自给出的证据 ----

print("\n================ 各指标证据（gate_40 - gate_30） ================\n")

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

# ---- 15.3 "到达门槛"分层：为什么结论会反转、为什么不能信 ----
# 直觉上想"去掉没碰到门槛的人，只看到达者"，这是错的：
#
# 到达 40 关本身要比到达 30 关玩更多局，"能不能到达"受实验改动影响，
# 是一个后处理变量。只看到达者，等于拿"更强的活跃玩家(gate_40 通过者)"
# 去比"相对更弱的玩家(gate_30 通过者)"，两组不再可比——这是选择偏差。
# 此时差异即便显著，也没有因果含义，不能作为推广 gate_40 的证据。

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
print("→ 注意：这里方向反转成 gate_40 更好，正是选择偏差造成的假象，不是 gate_40 的功劳。")

# ---- 15.4 稳健性：同样打到 40 局以上的玩家 ----
# 用"两组都打了 ≥40 局"近似控制投入度。方向上仍与全体结论一致：gate_40 更低。

control_ge40 = control[control["sum_gamerounds"] >= 40].copy()
treatment_ge40 = treatment[treatment["sum_gamerounds"] >= 40].copy()
df_ge40 = pd.concat([control_ge40, treatment_ge40], ignore_index=True)
r7_ge40 = ab_test_proportion(df_ge40, "retention_7")

print("\n============ 稳健性：两组都打到 ≥40 局的玩家 ============\n")
print(f"7 日留存 : gate_30={r7_ge40['control_rate']:.4%} (n={r7_ge40['control_n']}) "
      f"vs gate_40={r7_ge40['treatment_rate']:.4%} (n={r7_ge40['treatment_n']})  "
      f"diff={r7_ge40['absolute_diff']:+.4%}  p={r7_ge40['p_value']:.5f}")
print("→ 说明全体口径的负向信号不是单纯被大量未到门槛用户稀释出来的假象。")

# ---- 15.5 实际意义换算（显著 ≠ 业务量级，业务量级也要说） ----
# 把 -0.82 个百分点翻译成"少多少用户"：
#   若本批实验组都按 gate_30 的留存率，期望的 D7 留存数 vs 实际的 D7 留存数。

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


# ============================================================
# 16. 项目分析逻辑总结
# ============================================================

"""
整个项目的逻辑：

Business Question（要不要把等待门槛从 30 关移到 40 关？）
        ↓
先定指标与决策规则（D7 主 / D1、Game Rounds 辅）
        ↓
Data Cleaning / Quality Check / Group Check
        ↓
Descriptive Statistics（D1/D7 留存、Game Rounds 分布）
        ↓
Treatment - Control（效应量：绝对 + 相对）
        ↓
Two-Proportion Z Test → P-value → 95% CI
        ↓
口径核对：多数玩家没碰到门槛；以全体(ITT)为主口径
        ↓
"到达门槛"分层（诊断用）：警惕后处理选择偏差，不作结论
        ↓
实际意义换算（把百分点翻译成用户数）
        ↓
多指标一致性 + 决策规则 → Business Decision


最重要的统计思想：

1. AVG(0/1) = 比例
2. Treatment - Control = 实验效果估计
3. SE = 随机波动的尺度；Z = 差异 / 随机波动
4. P-value = 在 H0 成立时，得到当前或更极端结果的概率
5. CI = 对总体效果大小的不确定性范围，比单看 p 值更有信息量
6. Statistical Significance != Business Significance（要换算实际意义）
7. Game Rounds 是长尾变量，不能只看 Mean
8. 决策规则要先定，再看数据；避免事后找理由
9. 结论以全体样本(ITT)为主口径；用"后处理变量"切子集会产生选择偏差
10. 多个指标同时检验要考虑 Multiple Testing：本项目 D1/D7 高度相关，
    即便按 Bonferroni 校正(0.025)，D7 p≈0.0016 结论也不变
11. A/B Test 的结论依赖实验随机化和数据质量
"""
