# World Happiness Report MySQL 分析记录

这份材料记录我在 Python 清洗完成后，如何继续用 MySQL 做数据分析。Python 负责处理原始 CSV 的脏数据和字段统一问题，MySQL 负责基于清洗后的标准表做分析查询。

```text
projects/world-happiness-report/outputs/tables/world_happiness_clean_2015_2019.csv
```

## 本次练习目标

我把这部分作为同一个项目里的 SQL 分析层，主要练习：

1. 建表和导入清洗后的宽表或长表。
2. 检查数据质量。
3. 写 Top / Bottom 排名。
4. 写年度趋势、地区对比、变化分析。
5. 用窗口函数做分层、排序和异常排查。
6. 用 SQL 产出可以写进报告的分析结果。

我使用 MySQL 8.0 口径写脚本，因为里面用到了 `WITH` 公共表表达式和 `ROW_NUMBER()`、`NTILE()` 等窗口函数。

## 文件

```text
projects/world-happiness-report/mysql/
  README.md
  world_happiness_mysql_analysis.sql
```

## 运行前准备

1. 先用 Python 生成清洗表：

```powershell
python projects/world-happiness-report/run_all.py
```

2. 打开 MySQL Workbench、DBeaver、DataGrip 或命令行客户端。

3. 如果使用 `LOAD DATA LOCAL INFILE`，MySQL 客户端和服务端需要允许本地导入：

```sql
SET GLOBAL local_infile = 1;
```

如果权限不允许，可以用 MySQL Workbench 的 Table Data Import Wizard 导入同一个 CSV，然后继续运行后面的分析查询。

SQL 脚本中的导入路径使用仓库内相对路径示例：

```sql
LOAD DATA LOCAL INFILE 'projects/world-happiness-report/outputs/tables/world_happiness_clean_2015_2019.csv'
```

如果 MySQL 客户端不支持相对路径，我会把它替换成本机绝对路径。

## 数据表口径

SQL 脚本会创建一张表：

```text
world_happiness
```

字段含义：

| 字段 | 含义 |
|---|---|
| year | 年份 |
| country | 国家或地区 |
| region | 地区 |
| rank_no | 幸福指数排名，避免使用 rank 作为字段名 |
| score | 幸福分数 |
| gdp | 人均 GDP 相关指标 |
| social_support | 社会支持 |
| life_expectancy | 健康预期寿命 |
| freedom | 自由度 |
| generosity | 慷慨程度 |
| corruption | 腐败感知 |

## 分析主线

### 1. 数据质量检查

先回答数据是否能用：

- 总行数是否为 782。
- 年份是否覆盖 2015-2019。
- `region` 是否缺失 8 条。
- `corruption` 是否缺失 1 条。
- `year + country` 是否重复。

这是企业分析中必须先做的步骤。没有质量检查，后面的 Top / Bottom 和趋势都可能建立在错误数据上。

### 2. 2019 年 Top / Bottom

用窗口函数对 2019 年国家幸福分数排序。预期结果：

- 2019 最高：Finland
- 2019 最低：South Sudan

这类查询在企业里对应：

- Top 门店
- Bottom 商品
- 高价值客户
- 低表现地区

### 3. 2015-2019 变化分析

只比较 2015 和 2019 都出现的国家，避免新增国家或缺失国家污染变化结论。预期结果：

- 上升最多：Benin
- 下降最多：Venezuela

这类查询对应企业里的活动前后对比、同比变化、经营改善和风险预警。

### 4. 地区表现分析

按地区汇总 2019 年平均幸福分数，同时保留国家数量。保留样本数很重要，因为不同地区国家数量差异很大。

### 5. 相关性分析

MySQL 没有直接的 `corr()` 函数，所以脚本用皮尔逊相关系数公式计算：

```text
corr(x, y) = cov(x, y) / (std(x) * std(y))
```

这一步是我把统计口径拆成 SQL 聚合计算的练习。

注意：相关性不是因果关系。我在结论里只能写“GDP 与幸福分数呈较强正相关”，不能写成“GDP 导致幸福分数提高”。

### 6. 异常排查

脚本使用 `NTILE(4)` 把 GDP 和幸福分数分别分成四档，找出 GDP 较高但幸福分数不高的国家。这类分析更接近企业里的诊断问题：

- 为什么高投入地区产出不高？
- 为什么高流量渠道转化不高？
- 为什么高客单用户复购不高？

## 我的复写顺序

我后面复盘这份 SQL 时，会按这个顺序重新写一遍：

1. 先只写建表和导入。
2. 再写数据质量检查。
3. 写 2019 Top / Bottom。
4. 写 2015-2019 变化分析。
5. 写地区汇总。
6. 最后写相关性和异常排查。

每写完一段，我会检查三个问题：

1. 这个查询回答什么业务问题？
2. 这个指标的口径是什么？
3. 这个结果有没有可能被缺失值、样本数或字段口径影响？
