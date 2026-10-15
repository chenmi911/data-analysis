from pathlib import Path
# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind

# %% [markdown]
# Yulu希望了解共享单车需求与时间、天气等因素的关系。本 notebook 使用的是按小时汇总的历史租车数据，分析重点是描述哪些条件下小时租车量不同。#
# 原始业务问题还包括近期收入下降原因和需求预测准确度，但 CSV 没有收入字段，notebook 也没有建立或评估预测模型，因此这两项不能由当前分析回答。以下结论只适用于这份历史数据中的租车量。
# %%
# 读取数据
file_path = Path(__file__).resolve().parent / 'data' / 'raw' / 'yulu_bike_sharing_dataset.csv'
bike_sharing_data = pd.read_csv(file_path)

bike_sharing_data.head(), bike_sharing_data.info(), bike_sharing_data.describe()

# %% [markdown]
# 数据包含 10,886 条小时记录、12 个字段；原始检查显示没有缺失值。`datetime` 需要转换为日期时间类型，`season`、`holiday`、`workingday`、`weather` 是编码后的类别变量。#
# 每行代表一个小时：`casual` 和 `registered` 是该小时按用户类型统计的租车量，`count` 是该小时总租车量，不是每位用户的个人使用记录。
# %% [markdown]
# ## 探索小时租车量的差异#
# 分析顺序从时间与类别分布开始，再比较工作日、季节和天气条件下的租车量。这里的组间检验是探索性的：数据按小时连续记录，同一天的小时需求可能相关，p 值不能自动解释为因果影响。#
# 天气与季节、温度等变量也可能相互关联；单因素组间比较不能分离各因素的独立作用。
# %%
bike_sharing_data['datetime'] = pd.to_datetime(bike_sharing_data['datetime'])

categorical_columns = ['season', 'holiday', 'workingday', 'weather']

bike_sharing_data[categorical_columns] = bike_sharing_data[categorical_columns].astype('category')

miss_values = bike_sharing_data.isnull().sum()

data_types = bike_sharing_data.dtypes
missing_values_check = miss_values[miss_values>0]

data_types, missing_values_check

# %%
variables = ['temp', 'atemp', 'humidity', 'windspeed', 'casual', 'registered', 'count']

fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(15, 20))
# 把二位数组转为一维
axes = axes.flatten()

for i, col in enumerate(variables):
    sns.histplot(bike_sharing_data[col], ax=axes[i], kde=True)
    axes[i].set_title(f'Distribution of {col}', fontsize=14)
    axes[i].set_xlabel(col)
    axes[i].set_ylabel('Frequency')
    axes[i].grid(False)

if len(variables) % 2 != 0:
    fig.delaxes(axes[-1])

plt.tight_layout()
plt.show()

# %% [markdown]
# 1. 温度与体感温度分布相似且有多峰，可能与季节有关；这只是分布观察，不能据此判断温度的独立影响。# 2. 小时风速分布右偏；仅凭风速分布不能得出高风速会降低需求。# 3. casual 与 registered 的小时租车量均右偏；registered 的典型规模较大，但这些是每小时的分组总量，不代表单个用户行为。
# %%
categorical_variables = ['season', 'holiday', 'workingday', 'weather']

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(15, 10))
axes = axes.flatten()

for i, col in enumerate(categorical_variables):
    sns.countplot(x=col, data=bike_sharing_data, ax=axes[i], palette='Set2')
    axes[i].set_title(f'count of {col}', fontsize=14)
    axes[i].set_xlabel(col)
    axes[i].set_ylabel('count')

plt.tight_layout()
plt.show()

# %% [markdown]
# 这张图展示各类别在数据中的小时记录数，而不是各类别的租车需求。节假日和较差天气的记录较少，后续比较时应同时考虑组样本量；天气 4 尤其稀少。
# %% [markdown]
# ## 工作日与非工作日的需求比较#
# `workingday` 是按日期定义的，而一行数据代表一个小时。同一天的小时需求相关，若直接把小时行当作独立样本，会夸大有效样本量。因此先汇总每天总租车量，再比较工作日（1）和非工作日（0）的日总量。非工作日组同时包含周末和节假日。#
# 使用 Welch 独立样本 t 检验比较两组日均总量，不要求两组方差相等。该检验仍假设不同日期相互独立；连续日期可能存在时间相关，所以结果视为探索性证据。#
# - H₀：工作日与非工作日的平均日总租车量相等。# - H₁：两组平均日总租车量不相等。
# %%
daily_data = (
    bike_sharing_data.assign(date=bike_sharing_data['datetime'].dt.date)
    .groupby('date', as_index=False)
    .agg(workingday=('workingday', 'first'), daily_count=('count', 'sum'))
)

working_day_count = daily_data.loc[daily_data['workingday'] == 1, 'daily_count']
non_working_day_count = daily_data.loc[daily_data['workingday'] == 0, 'daily_count']

t_stat, p_value = ttest_ind(working_day_count, non_working_day_count, equal_var=False)

print(daily_data.groupby('workingday', observed=True)['daily_count'].agg(['mean', 'std', 'count']))
print(f'Welch t = {t_stat:.3f}, p = {p_value:.4f}')

# %% [markdown]
# 工作日和非工作日的样本日均总量分别约为 4,600 和 4,516，Welch t 检验 p≈0.665。按 0.05 显著性水平，当前数据不足以拒绝两组平均日总量相等的原假设；这不等于证明两组完全相同。#
# 该比较是未调整其他因素的探索性结果，也没有处理日期间可能存在的时间相关性，不能据此断言工作日状态对需求“没有影响”。
# %% [markdown]
# ## 季节间的小时租车量比较#
# 原假设是四个季节的平均小时租车量相同，备择假设是至少一个季节不同。每行是一个小时观测；使用 Welch ANOVA 是因为组间方差不齐时，它比假定方差齐性的经典 ANOVA 更合适。检验仍依赖观测独立等条件，而小时序列内可能相关，因此结果作为探索性组间证据，不作因果解释。#
# 整体检验显著只能说明至少有季节均值不同，不能指出具体哪些季节不同；本项目没有进行事后两两比较。
# %%
from scipy.stats import shapiro, levene, f_oneway
# 检查正态性
shapiro_test_seasons = {
    season: shapiro(bike_sharing_data.loc[bike_sharing_data['season'] == season, 'count'])
    for season in bike_sharing_data['season'].cat.categories
}

count_by_season = [bike_sharing_data[bike_sharing_data['season'] == season]['count']
                   for season in bike_sharing_data['season'].cat.categories]

# 检查方差齐性
levene_test = levene(*count_by_season)
# 检查均值是否相同
welch_anova_test = f_oneway(*count_by_season, equal_var=False)

shapiro_test_seasons, levene_test, welch_anova_test

# %% [markdown]
# 四季的 Shapiro 检验 p 值均很小，但大样本下该检验对轻微偏离也敏感。Levene 检验显示方差不齐，因此使用 Welch ANOVA。结果 F≈335.09，p≈4.84×10⁻²⁰¹，拒绝“四季平均小时租车量相同”的原假设。#
# 这是未调整天气、温度等因素的总体差异；不能据此单独归因于季节，也不能从整体检验确定具体季节对之间的差异。
# %% [markdown]
# ## 天气条件间的小时租车量比较#
# 检验 H₀：天气 1–3 的平均小时租车量相同；H₁：至少一类不同。天气 4 仅有 1 条记录，无法估计该组方差，因此不纳入推断性 ANOVA，单独作为样本不足的类别说明。天气 1–3 的方差不齐，使用 Welch ANOVA。#
# 即便样本量较大，小时记录的时间相关性仍限制常规检验的独立性假设；结果应视为探索性关联，而非天气的因果效应。
# %%
count_by_weather = [
    bike_sharing_data.loc[bike_sharing_data['weather'] == weather, 'count']
    for weather in [1, 2, 3]
]

levene_test_weather = levene(*count_by_weather)
welch_anova_test_weather = f_oneway(*count_by_weather, equal_var=False)

print('各天气类别样本量:', bike_sharing_data['weather'].value_counts().sort_index().to_dict())
levene_test_weather, welch_anova_test_weather

# %% [markdown]
# 天气 1–3 的 Levene 检验显示方差不齐；Welch ANOVA 结果 F≈140.90，p≈1.20×10⁻⁵⁸，说明至少一类天气的平均小时租车量不同。天气 4 只有一小时记录，不能据此推断该类天气下的典型需求。#
# 总体检验不说明具体哪些天气类别不同；而天气与季节等条件相关，组间差异不能解释为天气的独立因果作用。
# %% [markdown]
# ## 卡方检验：季节与天气类别是否相关#
# 原假设是季节与天气类别相互独立，备择假设是两者有关联。天气 4 只有 1 条记录，纳入后列联表的期望频数低于常用近似条件，因此本检验只比较天气 1–3。该检验说明类别分布是否相关，不表示季节会导致天气变化。
# %%
from scipy.stats import chi2_contingency

weather_data = bike_sharing_data[bike_sharing_data['weather'].isin([1, 2, 3])]
contingency_table = pd.crosstab(weather_data['season'], weather_data['weather'])

chi2, p_value, dof, expected = chi2_contingency(contingency_table)
cramers_v = np.sqrt(chi2 / (contingency_table.to_numpy().sum() * min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)))

chi2, p_value, dof, expected.min(), cramers_v

# %% [markdown]
# 在天气 1–3 的记录中，季节与天气类别的分布存在统计关联（χ²≈46.10，df=6，p≈2.83×10⁻⁸）；最小期望频数约 211.89，满足卡方近似所需的频数条件。Cramér's V≈0.046，关联强度较弱。大样本下显著的 p 值不代表关联很强。#
# 这提示季节间的租车量差异可能与天气构成部分重叠。该列联分析说明关联，不说明因果关系；天气 4 因只有一条记录未纳入检验。
# %% [markdown]
# ## 总结#
# - **工作日：** 汇总到日期后，工作日与非工作日的平均日总租车量差异没有统计显著证据（p≈0.665）。这不证明两者完全相同；非工作日包含周末与节假日，且日期间相关性未建模。# - **季节与天气：** Welch ANOVA 显示不同季节及天气 1–3 之间存在总体均值差异；季节与天气类别的关联显著但较弱。检验没有分离各因素的独立作用，也没有确定具体类别对的差异。天气 4 仅 1 条记录，结论不覆盖该类的稳定需求水平。# - **业务边界：** 这些结果可用于提出后续按季节和天气细分运营数据的方向，但不足以直接决定调车或营销规模。数据不含收入，且覆盖 2011–2012 年，不能解释近期收入下降或直接代表当前市场。项目也未训练预测模型，无法回答预测准确度问题。
