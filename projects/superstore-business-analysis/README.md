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
- `docs/superstore_findings.md`
