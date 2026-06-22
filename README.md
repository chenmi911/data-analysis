# data-analysis

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Cleaning%20%26%20EDA-150458?logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557C)
![Business Analytics](https://img.shields.io/badge/Business%20Analytics-Portfolio-FF8C00)
![Beginner Friendly](https://img.shields.io/badge/Beginner--Friendly-Code%20Walkthrough-6A5ACD)
[![CodeTriage](https://img.shields.io/badge/CodeTriage-open%20source%20helpers-2ea44f)](https://www.codetriage.com/chenmi911/data-analysis)

该 repo 是我的数据分析项目集合。每个项目会尽量包含清晰的业务背景、数据说明、分析流程、可复现代码、图表结果和复盘文档，用来训练真实数据分析工作中常见的能力。

当前项目从 World Happiness Report 开始，后续会继续补充销售分析、用户增长分析、利润分析、客户分层、留存分析、营销活动评估、库存与供应链分析、经营看板和异常诊断等更接近企业场景的案例。

如果这个仓库对你的数据分析学习、Python EDA 练习或作品集搭建有参考价值，可以给一个 Star。

## wish

通过不同数据集和业务场景的练习，逐步达到以下目标：

* 熟悉企业数据分析的基本工作流：取数、清洗、分析、可视化、结论输出。
* 理解不同业务场景的核心指标，例如销售额、利润率、转化率、留存率、库存周转、ROI。
* 提升 Python、pandas、可视化和报告写作能力。
* 训练从“数据现象”到“业务解释”再到“行动建议”的分析思维。
* 积累可以展示给实习、校招或项目面试的作品集。

## tip

* 目前主要使用 Python、pandas、matplotlib 和 Markdown。
* 每个项目都会尽量保留原始数据、清洗后数据、分析脚本、图表输出和详细说明。
* 项目重点不是堆模型，而是先把数据清洗、指标口径、分析过程和结论边界讲清楚。
* 当前阶段更适合练 EDA、业务拆解和可视化；机器学习会在合适的数据集上再加入。
* CodeTriage 官方动态徽章需要仓库先被 CodeTriage 收录；当前可先使用顶部入口 badge，收录后替换为：

```markdown
[![Open Source Helpers](https://www.codetriage.com/chenmi911/data-analysis/badges/users.svg)](https://www.codetriage.com/chenmi911/data-analysis)
```

> 数据分析项目最重要的不是“图多”，而是每一步都能回答一个明确问题：为什么要处理这个字段、为什么这样分组、这个图支撑什么结论、结论能不能落地。

## list

| 主题 | 处理方式 | 技术栈 | 项目入口 | 数据 |
|---|---|---|---|---|
| World Happiness Report 幸福指数分析 | 离线处理：ETL + EDA + 可视化 + 结论输出 | pandas + matplotlib + markdown | [项目说明](projects/world-happiness-report/README.md) / [代码讲解](projects/world-happiness-report/docs/code_walkthrough.md) | [raw csv](projects/world-happiness-report/data/raw) |
| Superstore 销售与利润分析 | 计划中：销售、利润、地区、品类、客户分层、经营看板 | pandas + Power BI | Coming soon | Coming soon |
| 用户增长与留存分析 | 计划中：新增、活跃、留存、漏斗、转化诊断 | pandas + cohort analysis | Coming soon | Coming soon |
| 营销活动效果评估 | 计划中：活动前后对比、ROI、分组表现、异常排查 | pandas + visualization | Coming soon | Coming soon |
| 库存与供应链分析 | 计划中：周转、缺货、滞销、补货建议 | pandas + dashboard | Coming soon | Coming soon |

## current project

### World Happiness Report 分析

业务场景：模拟咨询公司或国际业务部门的海外市场环境评估。分析目标不是做预测，而是回答：

* 哪些国家和地区幸福指数更高？
* 2015-2019 年哪些国家变化最明显？
* 地区之间是否存在明显差异？
* GDP、社会支持、健康预期寿命等指标与幸福分数的关系如何？
* 这些结果能为海外市场研究提供哪些参考？

学习文档：

* [项目说明与结论](projects/world-happiness-report/README.md)
* [分析过程说明](projects/world-happiness-report/docs/analysis_process.md)
* [Python 代码逐段讲解](projects/world-happiness-report/docs/code_walkthrough.md)

## preview

### 2019 年幸福指数 Top / Bottom

![2019 Happiness Score Top and Bottom](projects/world-happiness-report/outputs/figures/chart_2019_top_bottom.png)

### 2015-2019 年平均幸福指数趋势

![Average Happiness Score Trend](projects/world-happiness-report/outputs/figures/chart_yearly_avg_trend.png)

### 2019 年地区平均幸福指数

![2019 Region Average Score](projects/world-happiness-report/outputs/figures/chart_region_2019_avg.png)

### 关键指标与幸福分数关系

![Score vs Key Indicators](projects/world-happiness-report/outputs/figures/chart_2019_score_vs_key_indicators.png)

## quick start

```powershell
pip install -r requirements.txt
python projects/world-happiness-report/run_all.py
```

运行后会重新生成：

* 清洗后的长表
* 数据质量检查表
* Top / Bottom 国家表
* 分数变化表
* 地区汇总表
* 相关性结果表
* 4 张可视化图表

## skills

`Python` `pandas` `matplotlib` `EDA` `data cleaning` `data visualization` `business analytics` `portfolio project` `CSV analysis` `correlation analysis` `trend analysis` `data storytelling`

## recommended topics

建议在 GitHub About 区域添加：

```text
python
pandas
matplotlib
data-analysis
data-visualization
exploratory-data-analysis
business-analytics
analytics-portfolio
portfolio-project
world-happiness-report
csv-analysis
data-cleaning
data-storytelling
beginner-friendly
open-data
```

## refer

> 1. [World Happiness Report](https://worldhappiness.report/)
> 2. [World Happiness Report dataset on Kaggle](https://www.kaggle.com/datasets/unsdsn/world-happiness)
> 3. [pandas documentation](https://pandas.pydata.org/docs/)
> 4. [matplotlib documentation](https://matplotlib.org/stable/)
> 5. [GitHub repository style reference: TurboWay/bigdata_analyse](https://github.com/TurboWay/bigdata_analyse)

## license

Code and documents in this repository are released under the MIT License. Raw datasets keep their original data source licenses and terms.
