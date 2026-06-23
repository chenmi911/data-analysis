# Python 与 MySQL 代码过程记录

这篇记录我在 World Happiness Report 项目里写代码的过程。当前项目不是单独的 Python 脚本，也不是单独的 SQL 脚本，而是一个完整流程：

```text
原始 CSV
→ Python：清洗脏数据，统一字段，合并成长表
→ MySQL：基于清洗表做质量检查、排名、趋势、分组、相关性和异常诊断
→ Python：读取结果表，输出图表
→ README：整理分析结论和边界
```

## 1. Python 清洗层

Python 部分主要解决原始数据不能直接分析的问题。这个数据集有 2015-2019 五个 CSV，但字段名不统一，部分年份没有 `region` 字段，直接拼接会得到一张口径混乱的表。

### 1.1 路径

```python
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
```

我没有写本机绝对路径，而是用脚本所在目录定位数据。这样项目换到别的机器上时，只要仓库结构不变，脚本仍然能运行。

### 1.2 标准字段

```python
STANDARD_COLUMNS = [
    "year",
    "country",
    "region",
    "rank",
    "score",
    "gdp",
    "social_support",
    "life_expectancy",
    "freedom",
    "generosity",
    "corruption",
]
```

我先定好最后要保留的 11 个字段。这样后面每一年都往同一套字段上对齐。

### 1.3 字段映射

```python
RENAME_MAPS = {
    "2015.csv": {
        "Country": "country",
        "Region": "region",
        "Happiness Rank": "rank",
        "Happiness Score": "score",
        "Economy (GDP per Capita)": "gdp",
        "Family": "social_support",
        "Health (Life Expectancy)": "life_expectancy",
        "Freedom": "freedom",
        "Trust (Government Corruption)": "corruption",
        "Generosity": "generosity",
    },
    ...
}
```

这一步是清洗规则。比如 `Happiness Score`、`Happiness.Score`、`Score` 实际都是幸福分数；`Family` 在这个数据里对应后面年份里的 `Social support`。这些映射必须显式写出来，不能靠猜。

### 1.4 逐个读取原始 CSV

```python
for path in sorted(DATA_DIR.glob("*.csv")):
    raw = pd.read_csv(path)
    year = int(path.stem)
    rename_map = RENAME_MAPS[path.name]
```

`path.stem` 可以从 `2019.csv` 里取出 `2019`。我用这个值补充 `year` 字段，后面才能做年度趋势和 2015-2019 变化分析。

### 1.5 保存原始文件审计信息

```python
raw_summary_rows.append(
    {
        "year": year,
        "file": path.name,
        "rows": len(raw),
        "cols": len(raw.columns),
        "raw_columns": " | ".join(raw.columns),
    }
)
```

这一步记录每个原始文件的行数、列数和原始字段。它不是分析结论，但能帮助我确认每个文件都被读入，也能回头检查字段统一是否合理。

### 1.6 字段统一和地区补齐

```python
data = raw.rename(columns=rename_map)
data["year"] = year

if "region" in data.columns:
    current_region = data.dropna(subset=["region"]).set_index("country")["region"]
    region_map.update(current_region.to_dict())
```

2015 和 2016 有比较完整的地区字段，后面年份不完整。我先用有地区的年份建立 `country -> region` 映射，再给后续年份补齐。

```python
for col in STANDARD_COLUMNS:
    if col not in data.columns:
        data[col] = np.nan

data_list.append(data[STANDARD_COLUMNS])
```

不同年份缺少的字段先补空值，再按统一列顺序放进 `data_list`。

### 1.7 合并和输出清洗表

```python
clean_data = pd.concat(data_list, ignore_index=True)
clean_data["region"] = clean_data["region"].fillna(clean_data["country"].map(region_map))
```

这里把五年数据纵向合并成长表。补不到地区的记录仍然保留缺失，不手工硬改。

```python
clean_data.to_csv(
    TABLE_DIR / "world_happiness_clean_2015_2019.csv",
    index=False,
    encoding="utf-8-sig",
)
```

这张清洗表是后面 MySQL 分析的输入，也是图表输出的基础数据。

## 2. MySQL 分析层

MySQL 脚本放在：

```text
projects/world-happiness-report/mysql/world_happiness_mysql_analysis.sql
```

Python 清洗完成后，我用 MySQL 继续做分析查询。这样分工更清楚：Python 处理脏数据和文件，SQL 负责分析口径。

### 2.1 建表

```sql
CREATE TABLE world_happiness (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `year` SMALLINT NOT NULL,
    country VARCHAR(120) NOT NULL,
    region VARCHAR(120) NULL,
    rank_no INT NOT NULL,
    score DECIMAL(6, 3) NOT NULL,
    gdp DECIMAL(8, 5) NULL,
    social_support DECIMAL(8, 5) NULL,
    life_expectancy DECIMAL(8, 5) NULL,
    freedom DECIMAL(8, 5) NULL,
    generosity DECIMAL(8, 5) NULL,
    corruption DECIMAL(8, 5) NULL
);
```

我把 `rank` 改成 `rank_no`，避免和 SQL 里的窗口函数关键字混在一起。数值字段用 `DECIMAL`，因为这些指标不需要特别复杂的浮点计算。

### 2.2 导入清洗表

```sql
LOAD DATA LOCAL INFILE 'projects/world-happiness-report/outputs/tables/world_happiness_clean_2015_2019.csv'
INTO TABLE world_happiness
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@year, @country, @region, @rank_no, @score, @gdp, @social_support, @life_expectancy, @freedom, @generosity, @corruption)
SET
    `year` = CAST(NULLIF(TRIM(BOTH '\r' FROM @year), '') AS UNSIGNED),
    country = NULLIF(TRIM(BOTH '\r' FROM @country), ''),
    region = NULLIF(TRIM(BOTH '\r' FROM @region), '');
```

这一步在 DBeaver 里可能需要打开 `local_infile` 和 JDBC 的 `allowLoadLocalInfile`。如果导入路径无法识别，我会改成本机绝对路径，或者直接用 DBeaver 的 CSV 导入向导。

### 2.3 数据质量检查

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT country) AS distinct_countries,
    MIN(`year`) AS min_year,
    MAX(`year`) AS max_year,
    SUM(CASE WHEN region IS NULL THEN 1 ELSE 0 END) AS missing_region_rows,
    SUM(CASE WHEN corruption IS NULL THEN 1 ELSE 0 END) AS missing_corruption_rows
FROM world_happiness;
```

这一步确认清洗表是否符合预期：

- 总行数：782
- 年份：2015-2019
- `region` 缺失：8
- `corruption` 缺失：1

### 2.4 2019 Top / Bottom

```sql
WITH ranked_2019 AS (
    SELECT
        country,
        region,
        score,
        ROW_NUMBER() OVER (ORDER BY score DESC) AS high_rank,
        ROW_NUMBER() OVER (ORDER BY score ASC) AS low_rank
    FROM world_happiness
    WHERE `year` = 2019
)
SELECT *
FROM ranked_2019
WHERE high_rank <= 10
   OR low_rank <= 10;
```

这一步回答 2019 年哪些国家幸福分数最高、哪些最低。预期最高是 Finland，最低是 South Sudan。

### 2.5 2015-2019 变化

```sql
WITH yearly_score AS (
    SELECT
        country,
        MAX(CASE WHEN `year` = 2015 THEN score END) AS score_2015,
        MAX(CASE WHEN `year` = 2019 THEN score END) AS score_2019
    FROM world_happiness
    WHERE `year` IN (2015, 2019)
    GROUP BY country
    HAVING score_2015 IS NOT NULL
       AND score_2019 IS NOT NULL
)
SELECT
    country,
    score_2015,
    score_2019,
    ROUND(score_2019 - score_2015, 3) AS delta_2019_vs_2015
FROM yearly_score
ORDER BY delta_2019_vs_2015 DESC;
```

我这里只比较 2015 和 2019 都出现的国家，避免新增或缺失国家影响变化分析。

### 2.6 地区分析

```sql
SELECT
    region,
    COUNT(DISTINCT country) AS countries,
    ROUND(AVG(score), 3) AS avg_score,
    ROUND(AVG(gdp), 3) AS avg_gdp,
    ROUND(AVG(social_support), 3) AS avg_social_support,
    ROUND(AVG(life_expectancy), 3) AS avg_life_expectancy
FROM world_happiness
WHERE `year` = 2019
  AND region IS NOT NULL
GROUP BY region
ORDER BY avg_score DESC;
```

地区均值必须同时看 `countries`，因为不同地区样本数不一样。

### 2.7 相关性分析

```sql
ROUND(
    (AVG(score * indicator_value) - AVG(score) * AVG(indicator_value))
    / NULLIF(STDDEV_POP(score) * STDDEV_POP(indicator_value), 0),
    3
) AS corr_with_score
```

MySQL 没有直接使用 pandas 那样的 `corr()`，所以我把皮尔逊相关系数拆成聚合公式计算。这里的结果只能说明相关关系，不能写成因果关系。

### 2.8 异常诊断

```sql
NTILE(4) OVER (ORDER BY gdp) AS gdp_quartile,
NTILE(4) OVER (ORDER BY score) AS score_quartile
```

我用四分位把 GDP 和幸福分数分层，找 GDP 档位较高但幸福分数档位不高的国家。这个查询更像诊断问题：指标投入或基础条件不低，但结果表现没有同步变好。

## 3. Python 图表层

`visualize.py` 读取 `outputs/tables/` 里的结果表，输出四张图：

```text
chart_2019_top_bottom.png
chart_yearly_avg_trend.png
chart_region_2019_avg.png
chart_2019_score_vs_key_indicators.png
```

我在图表层不重新清洗原始数据，只读取已经处理好的结果表。这样清洗、分析、展示三个部分的边界更清楚。

8. 把结论和边界写回 README。
