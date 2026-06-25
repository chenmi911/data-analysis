# Superstore Business Analysis

这个项目用 Superstore 订单明细训练企业经营分析流程。当前版本按简单分工来做：

- pandas：只读取原始 CSV、清洗字段、处理日期、导出干净 CSV。
- MySQL：建表、导入 CSV、完成年度/月度经营总览、区域与品类诊断、折扣影响分析。

## 数据源

原始文件：

```text
D:\temp\dataset\superstore\Sample - Superstore.csv
```

该 CSV 需要使用 `cp1252` 编码读取。

## 学习文档

- [分析过程说明](docs/analysis_process.md)：解释为什么这样清洗、为什么这样写 SQL、RFM 口径和业务分析顺序。
- [代码逐段讲解](docs/code_walkthrough.md)：记录 Python 清洗、MySQL 分析和 RFM 分层的具体实现逻辑。
- [经营分析结论](docs/conclusions.md)：集中说明主要发现、数据证据、业务建议和分析边界。
- [MySQL 分析 SQL](sql/superstore_mysql_analysis.sql)：建表、导入、经营总览、折扣分析和 RFM 客户分层。

## 运行方式

第一步：运行 Python，只生成清洗后的 CSV。

```powershell
python projects/superstore-business-analysis/src/analysis_superstore.py
```

第二步：运行 SQL，导入 MySQL 并分析。

```powershell
mysql --local-infile=1 -uroot -p --execute="source projects/superstore-business-analysis/sql/superstore_mysql_analysis.sql"
```

如果 MySQL 提示 `Loading local data is disabled`，先用 root 执行：

```powershell
mysql -uroot -p --execute="SET GLOBAL local_infile = 1"
```

## 输出

- `data/superstore_orders_clean.csv`
- `data/superstore_rejected_rows.csv`
- `sql/superstore_mysql_analysis.sql`
- `docs/analysis_process.md`
- `docs/code_walkthrough.md`
- `docs/conclusions.md`
