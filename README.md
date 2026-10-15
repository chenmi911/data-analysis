# 数据分析项目集

每个项目目录以分析说明和 Python 文件为主；只有项目原本包含 SQL 分析时才保留 SQL 文件。项目组织参考 [TurboWay/bigdata_analyse](https://github.com/TurboWay/bigdata_analyse/tree/main/AgeOfBarbarians) 的单项目布局。

## 项目

| 项目 | 数据集 | 项目说明 | Python | SQL |
|---|---|---|---|---|
| Cookie Cats A/B 测试 | Kaggle [Mobile Games A/B Testing - Cookie Cats](https://www.kaggle.com/datasets/mursideyarkin/mobile-games-ab-testing-cookie-cats) | [分析说明](projects/cookie-cats-ab-test/cookie_cats_analysis.md) | [分析代码](projects/cookie-cats-ab-test/cookie_cats_analysis.py) | — |
| Yulu 共享单车案例 | Kaggle [Bike Sharing Demand](https://www.kaggle.com/competitions/bike-sharing-demand) | [分析说明](projects/yulu-bike-demand/yulu_analysis.md) | [分析代码](projects/yulu-bike-demand/yulu_analysis.py) | — |
| Superstore 零售分析 | Kaggle [Superstore Dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) | [分析说明](projects/superstore-business-analysis/superstore_analysis.md) | [数据清洗](projects/superstore-business-analysis/analysis_superstore.py) | [MySQL 分析](projects/superstore-business-analysis/superstore_mysql_analysis.sql) |

原始数据按项目 Markdown 中的说明放入对应 `data/raw/` 目录，不随仓库提交。

## 环境

```powershell
pip install -r requirements.txt
```

## 运行

```powershell
python projects/cookie-cats-ab-test/cookie_cats_analysis.py
python projects/yulu-bike-demand/yulu_analysis.py
python projects/superstore-business-analysis/analysis_superstore.py
```

Superstore 的 MySQL 脚本需要 MySQL 8.0+，运行命令见项目说明。
