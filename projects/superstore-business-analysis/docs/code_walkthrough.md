# 代码逐段讲解

## 1. 项目文件分工

这个项目把 Python 和 SQL 分开：

| 文件 | 作用 |
|---|---|
| `src/analysis_superstore.py` | 读取原始 CSV，清洗字段和日期，检查异常，输出清洗后的 CSV |
| `sql/superstore_mysql_analysis.sql` | 建表、导入清洗后的 CSV，并完成经营分析、折扣分析和 RFM 分层 |
| `docs/analysis_process.md` | 解释为什么这样分析 |
| `docs/conclusions.md` | 汇总主要发现、业务建议和分析边界 |

这个分工的重点是：Python 不混 SQL，SQL 不重新做原始数据清洗。

## 2. Python 路径和输入输出

脚本开头使用 `Path` 管理路径：

```python
RAW_PATH = Path(r"D:\temp\dataset\superstore\Sample - Superstore.csv")
PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_DIR / "data" / "superstore_orders_clean.csv"
REJECTED_PATH = PROJECT_DIR / "data" / "superstore_rejected_rows.csv"
```

这样做的原因是：

- 原始数据来自本机数据集目录。
- 输出文件固定写回项目内的 `data/`。
- 后续 MySQL 只读取项目内清洗后的 CSV。

## 3. 为什么手写字段映射

原始字段里有空格和连字符，例如 `Order Date`、`Sub-Category`。这些字段直接进 SQL 会增加引用成本，所以先统一成 snake_case。

```python
RENAME_DICT = {
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Sub-Category": "sub_category",
    "Sales": "sales",
    "Profit": "profit",
}
```

这里手写映射比自动替换更啰嗦，但可读性更高，也能明确每个字段的业务含义。

## 4. CSV 读取和日期处理

```python
df = pd.read_csv(RAW_PATH, encoding="cp1252")
df["order_date"] = pd.to_datetime(df["order_date"], format="%m/%d/%Y", errors="coerce")
df["ship_date"] = pd.to_datetime(df["ship_date"], format="%m/%d/%Y", errors="coerce")
```

原始 CSV 不是 UTF-8，因此用 `cp1252`。日期转换时加 `errors="coerce"`，如果有无法解析的日期，会变成缺失值，后续会进入异常检查。

## 5. 派生字段

```python
df["ship_days"] = (df["ship_date"] - df["order_date"]).dt.days
df["profit_margin"] = np.where(df["sales"] != 0, df["profit"] / df["sales"], np.nan)
```

`ship_days` 用来保留履约时效信息。`profit_margin` 用利润除以销售额，但先判断 `sales != 0`，避免除零错误。

## 6. 异常检查和实际处理

脚本先定义关键字段：

```python
required_cols = [
    "order_id",
    "order_date",
    "ship_date",
    "customer_id",
    "product_id",
    "sales",
    "quantity",
    "discount",
    "profit",
]
```

再构造异常条件：

```python
invalid_mask = (
    df[required_cols].isna().any(axis=1)
    | (df["ship_date"] < df["order_date"])
    | (df["sales"] <= 0)
    | (df["quantity"] <= 0)
    | (df["discount"] < 0)
    | (df["discount"] > 1)
)
```

处理方式是：

```python
rejected_df = df[invalid_mask].copy()
clean_df = df[~invalid_mask].drop_duplicates().copy()
```

也就是异常行单独留痕，正常行进入清洗表。这次数据实际异常行为 0，所以清洗后仍然是 9994 行。

## 7. 输出文件

```python
clean_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8", lineterminator="\n")
rejected_df.to_csv(REJECTED_PATH, index=False, encoding="utf-8", lineterminator="\n")
```

输出两个文件：

- `superstore_orders_clean.csv`：MySQL 分析使用的清洗表。
- `superstore_rejected_rows.csv`：异常行留痕，即使当前为空也保留文件。

## 8. SQL 建表和导入

SQL 先创建数据库和表：

```sql
CREATE DATABASE IF NOT EXISTS practice DEFAULT CHARACTER SET utf8mb4;
USE practice;
DROP TABLE IF EXISTS superstore_orders_clean;
```

然后用 `LOAD DATA LOCAL INFILE` 导入 Python 输出的 CSV：

```sql
LOAD DATA LOCAL INFILE 'projects/superstore-business-analysis/data/superstore_orders_clean.csv'
INTO TABLE superstore_orders_clean
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;
```

这一步保持了 Python 和 MySQL 的分层：MySQL 不直接读取原始文件，只接收清洗后的分析表。

## 9. 经营总览 SQL

年度经营总览使用：

```sql
SUM(sales)
SUM(profit)
SUM(profit) / SUM(sales)
COUNT(DISTINCT order_id)
```

这里利润率用 `SUM(profit) / SUM(sales)`，而不是简单 `AVG(profit_margin)`。原因是整体利润率应该用总利润除以总销售额，不能让每一行的权重相同。

月度分析使用 `LAG()`：

```sql
LAG(total_sales) OVER (ORDER BY order_month)
```

这样可以计算销售额和利润的环比变化。

## 10. 区域、品类和折扣分析

区域和子品类分析主要使用 `GROUP BY`。子品类按利润排序，可以发现销售规模背后的亏损项。

折扣分析使用 `CASE WHEN` 分桶：

```sql
CASE
    WHEN discount = 0 THEN '0'
    WHEN discount <= 0.1 THEN '0-10%'
    WHEN discount <= 0.2 THEN '10%-20%'
    WHEN discount <= 0.3 THEN '20%-30%'
    ELSE '>30%'
END AS discount_band
```

再计算利润率和亏损率：

```sql
ROUND(SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS loss_rate
```

这样能回答“折扣是否带来利润风险”，而不是只看促销带来的销售额。

## 11. RFM 分层

RFM 先按客户聚合：

```sql
DATEDIFF((SELECT MAX(order_date) FROM superstore_orders_clean), MAX(order_date)) AS recency_days,
COUNT(DISTINCT order_id) AS frequency,
SUM(sales) AS monetary
```

再用 `NTILE(5)` 打分：

```sql
6 - NTILE(5) OVER (ORDER BY recency_days) AS r_score,
NTILE(5) OVER (ORDER BY frequency) AS f_score,
NTILE(5) OVER (ORDER BY monetary) AS m_score
```

R 分数要反向处理，因为 `recency_days` 越小代表越近购买，价值越高。

最后用 `CASE WHEN` 生成客户类型，例如：

- 高价值客户
- 重点发展客户
- 新近低频客户
- 流失风险客户
- 高消费低利润客户
- 低价值沉默客户

## 12. 复盘重点

这个项目复盘时重点讲三点：

1. Python 只做清洗和留痕，不做业务聚合。
2. SQL 负责指标口径、窗口函数、折扣分桶和客户分层。
3. 结论不只看销售额，而是同时看利润、折扣、客户价值和数据限制。
