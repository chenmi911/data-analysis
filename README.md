# 个人数据分析项目集

这里记录我独立完成的数据分析练习。每个项目尽量保留一条可读、可复现的路径：项目说明与结论（Markdown）、Python 数据处理/分析代码，以及 SQL 汇总或分析脚本。目录组织参考 [TurboWay/bigdata_analyse 的 AgeOfBarbarians 项目](https://github.com/TurboWay/bigdata_analyse/tree/main/AgeOfBarbarians)。

## 项目目录

| 项目 | 业务问题 | 方法与结论 | 项目说明 | Python | SQL |
|---|---|---|---|---|---|
| Cookie Cats A/B 测试 | 是否把首个等待门槛从第 30 关后移到第 40 关？ | D7 留存双比例检验与置信区间；游戏局数分布比较。gate_40 的 D7 留存低 0.82 个百分点，不建议直接推广。 | [README](projects/cookie-cats-ab-test/README.md) | [Python 分析](projects/cookie-cats-ab-test/python/cookie_cats_ab_test_python_commented.py) | [MySQL 分析](projects/cookie-cats-ab-test/sql/cookie_cats_mysql_ab_test.sql) |
| Yulu 共享单车案例 | 历史小时租车量与工作日、季节和天气有哪些关联？ | 日级工作日比较、Welch ANOVA、卡方检验。数据实际来自 Washington, D.C. Capital Bikeshare，不能作为 Yulu 印度业务结论。 | [README](projects/yulu-bike-demand/README.md) | [Python 分析](projects/yulu-bike-demand/python/yulu_bike_demand_analysis.py) | [SQL 汇总](projects/yulu-bike-demand/sql/yulu_bike_demand_analysis.sql) |
| Superstore 零售经营 | 销售、利润、折扣、区域、品类和客户价值表现如何？ | pandas 清洗 + MySQL 经营分析与 RFM；发现高折扣及部分子品类利润风险。 | [README](projects/superstore-business-analysis/README.md) | [Python 清洗](projects/superstore-business-analysis/python/analysis_superstore.py) | [MySQL 分析](projects/superstore-business-analysis/sql/superstore_mysql_analysis.sql) |

## 环境

```powershell
pip install -r requirements.txt
```

原始数据按各项目说明放入 `data/raw/`；原始文件不统一提交到仓库。Superstore 清洗后的订单表目前随项目保存，可用于 SQL 分析。

## 快速运行

```powershell
python projects/cookie-cats-ab-test/python/cookie_cats_ab_test_python_commented.py
python projects/yulu-bike-demand/python/yulu_bike_demand_analysis.py
python projects/superstore-business-analysis/python/analysis_superstore.py
```

MySQL 脚本需要 MySQL 8.0+ 与 `local_infile`，具体命令见各项目 README。Cookie Cats 与 Superstore Python 脚本需要各自的原始 CSV；Yulu 脚本会生成分布图和类别频数图。

## 结论边界

统计显著性不自动代表业务价值或因果关系。每个项目说明中记录了数据范围、指标口径、关键假设和当前数据无法回答的问题。
