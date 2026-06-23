# World Happiness Report 数据分析项目

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Cleaning%20%26%20EDA-150458?logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Charts-11557C)
![MySQL](https://img.shields.io/badge/MySQL-Analysis%20Practice-4479A1?logo=mysql&logoColor=white)
![Data Cleaning](https://img.shields.io/badge/Data%20Cleaning-Schema%20Normalization-2E8B57)
![Portfolio](https://img.shields.io/badge/Portfolio-Data%20Analysis-FF8C00)

## 项目定位

这个项目是我使用 2015-2019 年 World Happiness Report 数据做的一次数据分析学习记录。项目按一个完整流程组织：先用 Python/pandas 处理原始 CSV 的脏数据和字段口径问题，再用 MySQL 基于清洗后的标准表做分析查询，最后用 matplotlib 输出图表。

这次重点练的是企业数据分析中更基础也更常用的动作：字段口径统一、数据质量检查、分组对比、趋势分析、变化分析、相关性分析、图表表达和结论边界说明。

## 项目亮点

| 亮点 | 我练习的内容 |
|---|---|
| 多年份 CSV 合并 | 真实工作中常见的多期报表处理 |
| 字段口径统一 | 解决不同年份字段名不一致的问题 |
| 数据质量检查 | 缺失值、重复值、行列数、国家数量核验 |
| 业务化问题拆解 | 从“看数据”转为回答具体分析问题 |
| 图表支撑结论 | 每张图都对应一个明确业务问题 |
| 代码逐段讲解 | 方便我复盘清洗、分析和可视化流程 |

## Keywords

`Python` `Pandas` `MySQL` `SQL` `Matplotlib` `EDA` `Data Cleaning` `Data Visualization` `Correlation Analysis` `Trend Analysis` `Business Analytics` `World Happiness Report`

## 业务问题

假设业务方想快速了解不同国家和地区的社会经济环境，分析需要回答：

1. 2019 年幸福指数最高和最低的国家分别是谁？
2. 2015-2019 年哪些国家幸福分数变化最明显？
3. 不同地区的平均幸福指数有什么差异？
4. GDP、社会支持、健康预期寿命、自由度、腐败感知、慷慨程度与幸福分数的关系如何？
5. 这些结果能给海外市场研究提供什么启发？

## 数据说明

原始数据位于：

```text
data/raw/
  2015.csv
  2016.csv
  2017.csv
  2018.csv
  2019.csv
```

不同年份字段命名不一致，因此不能直接拼接。脚本会统一为以下字段：

| 字段 | 含义 |
|---|---|
| year | 年份 |
| country | 国家或地区 |
| region | 地区 |
| rank | 幸福指数排名 |
| score | 幸福分数 |
| gdp | 人均 GDP 相关指标 |
| social_support | 社会支持 |
| life_expectancy | 健康预期寿命 |
| freedom | 自由度 |
| generosity | 慷慨程度 |
| corruption | 腐败感知 |

## 项目结构

```text
projects/world-happiness-report/
  README.md
  data/raw/
  etl.py
  analyse.py
  visualize.py
  run_all.py
  src/analysis_world_happiness.py
  docs/analysis_process.md
  docs/code_walkthrough.md
  mysql/README.md
  mysql/world_happiness_mysql_analysis.sql
  outputs/tables/
  outputs/figures/
```

## 学习文档

- [分析过程说明](docs/analysis_process.md)：解释为什么这样分析，重点是业务逻辑和分析顺序。
- [代码逐段讲解](docs/code_walkthrough.md)：记录 Python 清洗、MySQL 分析和 Python 可视化的衔接过程。
- [MySQL 分析记录](mysql/README.md)：记录我基于清洗长表完成建表、导入、质量检查、排名、趋势、分组、相关性和异常诊断的 SQL。

## 运行方式

从仓库根目录运行：

```powershell
pip install -r requirements.txt
python projects/world-happiness-report/run_all.py
```

脚本会重新生成 `outputs/tables/` 和 `outputs/figures/` 下的所有分析结果。

兼容入口仍然保留：

```powershell
python projects/world-happiness-report/src/analysis_world_happiness.py
```

## 代码分工

| 文件 | 作用 |
|---|---|
| `etl.py` | Python 清洗脏数据：读取 5 个原始 CSV，统一字段，补齐地区，保存清洗表 |
| `analyse.py` | Python 生成图表所需的结果表，并保留关键校验 |
| `visualize.py` | 读取分析表并生成 4 张图表 |
| `run_all.py` | 串联 ETL、分析、可视化的主入口 |
| `src/analysis_world_happiness.py` | 兼容旧入口，内部调用 `run_all.py` |
| `mysql/world_happiness_mysql_analysis.sql` | MySQL 分析脚本：质量检查、排名、趋势、分组、相关性和异常诊断 |

## 数据质量结果

合并后数据规模：

- 行数：782
- 列数：11
- 覆盖国家/地区：170
- `year + country` 无重复

缺失值情况：

| 字段 | 缺失数 |
|---|---:|
| region | 8 |
| corruption | 1 |
| 其他核心字段 | 0 |

`region` 缺失主要来自 2017-2019 部分国家名称和 2015/2016 的国家名称不完全一致，例如 `Hong Kong S.A.R., China`、`Taiwan Province of China`、`Trinidad & Tobago`。本项目保留这些缺失，不静默手工修正。

## 核心图表

### 2019 年 Top / Bottom 国家

![2019 Happiness Score Top and Bottom](outputs/figures/chart_2019_top_bottom.png)

### 年度平均分趋势

![Average Happiness Score Trend](outputs/figures/chart_yearly_avg_trend.png)

### 2019 年地区平均分

![2019 Region Average Score](outputs/figures/chart_region_2019_avg.png)

### 关键指标关系

![Score vs Key Indicators](outputs/figures/chart_2019_score_vs_key_indicators.png)

## 关键发现

### 1. 高幸福分数国家集中在欧洲、北美和澳新地区

2019 年幸福指数最高的国家是 Finland，分数为 7.769。Top 10 中多个国家来自 Western Europe，例如 Denmark、Norway、Iceland、Netherlands、Switzerland 和 Sweden。

### 2. 低幸福分数国家多集中在撒哈拉以南非洲和部分冲突风险较高地区

2019 年幸福指数最低的是 South Sudan，分数为 2.853。Bottom 10 中多个国家来自 Sub-Saharan Africa，例如 Central African Republic、Tanzania、Rwanda、Malawi 和 Botswana。

### 3. 国家变化差异明显

只比较 2015 和 2019 都出现的国家后，Benin 的幸福分数上升最多，从 3.340 上升到 4.883，变化为 +1.543；Venezuela 下降最多，从 6.810 下降到 4.707，变化为 -2.103。

### 4. GDP、健康预期寿命、社会支持与幸福分数相关性较高

2019 年相关系数：

| 指标 | 与幸福分数相关系数 |
|---|---:|
| gdp | 0.794 |
| life_expectancy | 0.780 |
| social_support | 0.777 |
| freedom | 0.567 |
| corruption | 0.386 |
| generosity | 0.076 |

这说明 GDP、健康预期寿命和社会支持与幸福分数关系较强，但不能直接解释为因果关系。

## 输出文件

主要表格输出：

- `outputs/tables/world_happiness_clean_2015_2019.csv`
- `outputs/tables/missing_summary.csv`
- `outputs/tables/quality_summary.csv`
- `outputs/tables/2019_top10.csv`
- `outputs/tables/2019_bottom10.csv`
- `outputs/tables/score_delta_2019_vs_2015.csv`
- `outputs/tables/region_2019_summary.csv`
- `outputs/tables/correlation_by_year.csv`

主要图表输出：

- `outputs/figures/chart_2019_top_bottom.png`
- `outputs/figures/chart_yearly_avg_trend.png`
- `outputs/figures/chart_region_2019_avg.png`
- `outputs/figures/chart_2019_score_vs_key_indicators.png`

## 分析边界

- 本项目结论不能解释因果关系，只能说明相关关系和分布差异。
- World Happiness 数据是国家级聚合数据，样本量较小，地区均值和相关性结果都需要结合样本量解释。
- 部分解释变量本身就是幸福分数的组成指标，直接建模容易变成用组成项预测总分。
- 地区均值需要结合国家数解释，例如 North America 和 Australia and New Zealand 都只有 2 个国家样本。
