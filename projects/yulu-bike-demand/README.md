# Yulu 案例：共享单车需求探索

## 项目问题与数据边界

练习场景以 Yulu 的共享电动单车业务为背景，分析天气、季节和工作日条件与小时租车量的关系。不过，当前 CSV 的 10,886 条记录、字段结构和时间范围与 Kaggle **Bike Sharing Demand** 训练数据一致；该数据来源于美国华盛顿特区的 Capital Bikeshare，而不是已核实的 Yulu 印度运营数据。因此结果只用于演示分析方法，不能作为 Yulu 实际需求或印度市场结论。

数据覆盖 2011-01-01 至 2012-12-19，包含小时租车量 `count` 及 `casual`、`registered` 分项。数据没有收入字段，也没有建立预测模型，因此不能解释收入下降或评估预测准确率。

## 分析顺序与方法

1. 检查记录数、缺失值、重复时间戳和 `count = casual + registered` 的字段关系。
2. 绘制连续字段分布和类别记录数。类别记录数反映各条件在样本中的小时数量，不等于需求。
3. `workingday` 是日期级字段，先汇总每日总租车量，再用 Welch 独立样本 t 检验比较两类日期。该检验假设日期独立；相邻日期可能相关，所以作为探索性证据。
4. 季节与天气的单因素比较使用 Welch ANOVA，因为组间方差不齐。小时观测可能存在时间相关性，且未控制其他变量，因此不作因果解读。
5. 天气 4 只有 1 条记录，不能估计方差；天气 ANOVA 仅比较类别 1–3。季节与天气类别的卡方检验也排除天气 4，避免期望频数过小。
6. 卡方检验同时报告 Cramér's V，避免把大样本下的小 p 值误读为强关联。

## 结果

- 数据有 10,886 条小时记录，无缺失、无重复 `datetime`，且 `count` 与两个用户类型租车量之和一致。
- 汇总到 456 个日期后，工作日平均日租车量约为 4,600，非工作日约为 4,516；Welch t 检验 p≈0.6646。样本不足以确认两类日期的平均日总量不同，但这不等于证明相同。
- 季节 Welch ANOVA：F≈335.09，p≈4.84×10⁻²⁰¹；至少一个季节的平均小时租车量不同。该整体检验不能指出具体季节对。
- 天气 1–3 Welch ANOVA：F≈140.90，p≈1.20×10⁻⁵⁸；至少一个类别的平均小时租车量不同。天气 4 仅一条记录，不纳入推断。
- 季节与天气 1–3 的分布存在统计关联（χ²≈46.10，df=6，p≈2.83×10⁻⁸），但 Cramér's V≈0.046，关联强度较弱。

## 业务含义与限制

这些历史数据支持继续按季节和天气细分需求，但不支持直接决定 Yulu 的车辆调度量。季节、天气及其他时间因素相互关联，单因素检验没有估计独立影响；小时数据的时间相关性也可能使常规 p 值偏小。具体运营建议需要目标市场的当前数据、点位和收入信息，因果结论则需要更合适的时间序列或实验设计。

## 运行

将 Kaggle 竞赛的训练文件放入 `data/raw/`，命名为 `yulu_bike_sharing_dataset.csv`。原始数据不随仓库分发。

```powershell
pip install -r requirements.txt
python projects/yulu-bike-demand/python/yulu_bike_demand_analysis.py
```

脚本会在项目目录下生成 `outputs/figures/` 中的两张图。

MySQL 8.0+ 可运行 SQL 汇总：

```powershell
mysql --local-infile=1 -uroot -p --execute="source projects/yulu-bike-demand/sql/yulu_bike_demand_analysis.sql"
```

SQL 提供数据核对和描述性汇总；Welch 检验与卡方检验由 Python 脚本计算。

## 项目文件

- [Python 分析与图表](python/yulu_bike_demand_analysis.py)
- [SQL 数据核对与汇总](sql/yulu_bike_demand_analysis.sql)
- [原始数据说明](data/raw/README.md)

数据来源：[Kaggle Bike Sharing Demand](https://www.kaggle.com/competitions/bike-sharing-demand)；竞赛页面说明数据来自 Washington, D.C. 的 Capital Bikeshare。
