from pathlib import Path
# %% [markdown]
# 背景:  《Cookie Cats》是一款“三连棋”益智游戏，玩家需要连接相同颜色的方块来消除棋盘上的方块，从而赢得关卡。随着玩家在游戏中不断推进，他们会遇到一些关卡，需要等待一段时间才能继续游戏或进行应用内购买。本项目将分析一项A/B测试的结果，该测试将《Cookie Cats》中的第一个关卡从30级移到了40级。我们将重点分析这一改动对玩家留存率和游戏回合数的影响。
# %% [markdown]
# 数据来自 AB 测试期间安装游戏的90189名玩家#
# userid: 用于识别每位玩家的唯一编号#
# version: 玩家被分配到对照组, 测试组#
# sum_gamerounds: 玩家在安装后第一周内进行的游戏回合数#
# retention_1: 玩家是否在安装后1天返回游戏#
# retention_7: 玩家是否在安装后7天返回游戏
# %% [markdown]
# ### 分析问题与实验信息#
# 业务问题是：把第一个等待关卡从 30 级移到 40 级，是否会改善玩家留存和前期参与度？`retention_1`、`retention_7` 是用户级二元留存指标，`sum_gamerounds` 是安装后第一周的用户级回合数，可分别描述回访和参与程度。#
# 数据字典说明玩家被分到两个版本，但没有提供随机分配流程、实验起止日期或分配前用户特征。因此，后续组间差异只有在分配确实随机、每位用户只进入一组且观测口径一致时，才可作因果解释；这些设计条件不能仅凭当前 CSV 验证。
# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

# %%
# 数据文件
file_path = Path(__file__).resolve().parent / 'data' / 'raw' / 'cookie_cats.csv'

# %%
df = pd.read_csv(file_path)

df.head(), df.info(), df.shape, df.describe()

# %%
# 把bool值转换为1和0

df['retention_1'] = df['retention_1'].astype(int)
df['retention_7'] = df['retention_7'].astype(int)
# df['retention_1'] =df['retention_1'].map({True: 1, False: 0})

df.head(10)

# %%
control = df[df['version'] == 'gate_30'].copy()
treatment = df[df['version'] == 'gate_40'].copy()

# 检查两组人数比例
group_summary = df.groupby('version', as_index=False).agg(
    users=('userid', 'count')
)

group_summary['rate'] = group_summary['users'] / len(df)

# df['version'].value_counts(normalize=True)

group_summary

# %% [markdown]
# 两组样本量接近（gate_30：44,700；gate_40：45,489），这说明人数没有明显失衡，但人数接近本身不能证明随机化成功。后续把每行视为一位独立用户；重复用户或跨组用户会破坏这一分析单位。
# %%

plot_df = df.groupby("sum_gamerounds")["userid"].count()

# Plotting the distribution of players that played 0 to 100 game rounds
ax = plot_df.head(100).plot()
plt.title("The distribution of players", fontweight="bold", size=14)
plt.xlabel("total gamerounds", size=12)
plt.ylabel("number of player", size=12)
plt.show()

# %%
# 从未玩过的玩家
df[df['sum_gamerounds'] == 0][['userid']].count()

# %%
# 检查两组的留存率
retention_rate = df.groupby('version', as_index=False).agg(
    retention_1_rate=('retention_1', 'mean'),
    retention_7_rate=('retention_7', 'mean'),
)
retention_rate

# %%
df.describe([0.01, 0.05, 0.1, 0.2, 0.8, 0.9, 0.95, 0.99])[['sum_gamerounds']]

# %%
df.groupby('version').sum_gamerounds.agg(['mean', 'median', 'std', 'max', 'count'])

# %% [markdown]
# ### 留存率：比较用户比例#
# 这里检验第 7 日留存率的组间差异。原假设是两组留存率相等，备择假设是两组不相等（双侧检验）。留存是每位用户的 0/1 结果，且两组为独立用户时，两比例 z 检验适用；两组样本都很大，正态近似条件充足。#
# 同时报告 `gate_40 - gate_30` 的百分点差和近似 95% 置信区间，以呈现实效大小和不确定性。z 检验的计数顺序是 gate_30、gate_40，因此正 z 值表示 gate_30 留存率更高；打印差值时则使用 gate_40 减 gate_30，符号相反。第 1 日留存率在此作为背景描述，没有另行检验；若把多个指标都用于成败判断，需要考虑多重比较。
# %%
success_cnt = [control['retention_7'].sum(), treatment['retention_7'].sum()]
tcnt = [len(control), len(treatment)]

z_test, p_value = proportions_ztest(success_cnt, tcnt, alternative='two-sided')

control_rate = control['retention_7'].mean()
treatment_rate = treatment['retention_7'].mean()
diff = treatment_rate - control_rate
se = np.sqrt(control_rate * (1 - control_rate) / tcnt[0] + treatment_rate * (1 - treatment_rate) / tcnt[1])
ci_low, ci_high = diff - 1.96 * se, diff + 1.96 * se

print(f'gate_30 第7日留存率: {control_rate:.2%}')
print(f'gate_40 第7日留存率: {treatment_rate:.2%}')
print(f'差值（gate_40 - gate_30）: {diff:.2%}')
print(f'差值近似95%置信区间: [{ci_low:.2%}, {ci_high:.2%}]')
print(f'z = {z_test:.3f}, p = {p_value:.4f}')

# %% [markdown]
# ### 游戏回合数：比较偏态的用户级计数#
# 回合数右偏且存在极端高值，均值和标准差容易受少数用户影响。因此保留中位数等描述统计，并用 Mann–Whitney U 双侧检验比较两组分布位置。该检验不要求正态分布，但它检验的是秩/分布差异；只有两组分布形状相近时，才可近似解读为位置（如中位数）差异。它不直接检验均值，也不告诉我们差异是否有业务价值。
# %%
g30_gamerounds = df[df['version'] == 'gate_30']['sum_gamerounds']
g40_gamerounds = df[df['version'] == 'gate_40']['sum_gamerounds']

# gate_30和gate_40的sum_gamerounds明显右偏,有较多极端值,因此用mann-whitney u检验
u_stat, p_value = stats.mannwhitneyu(g30_gamerounds, g40_gamerounds, alternative='two-sided')

print(f'U = {u_stat:.1f}, p = {p_value:.4f}')

# %% [markdown]
# ### 结果与业务判断#
# 在这份数据中，gate_40 的第 7 日留存率低于 gate_30；若实验分配确实随机且指标口径一致，这一差异支持“移到 40 级没有改善留存，且可能降低留存”的判断。统计显著性不等于业务影响大小：这里的绝对差约为负 0.82 个百分点，需结合产品可接受的留存损失阈值评估。#
# 游戏回合数的 Mann–Whitney U 检验 p 值约为 0.050，处在常用 0.05 阈值附近；不应将其表述为明确差异，也不能据此宣称两组相同。结合当前留存结果，现有证据不支持仅为提升留存而上线 gate_40。数据没有收入、付费、关卡完成或长期留存指标，也缺少实验设计细节，因此不能判断整体商业收益或确认因果机制；若业务目标包含这些结果，应补充对应证据后再决策。
