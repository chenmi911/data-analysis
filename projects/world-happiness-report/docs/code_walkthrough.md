# Python 代码逐段讲解

这个项目的代码已经从单脚本改成更接近项目集合仓库的结构：

```text
etl.py
analyse.py
analyse.sql
visualize.py
run_all.py
src/analysis_world_happiness.py
```

整体流程是：

```text
原始 CSV
→ etl.py：字段统一、合并、保存清洗表和 SQLite 表
→ analyse.py：生成分析结果表
→ visualize.py：生成图表
→ run_all.py：串联完整流程
```

## 1. `etl.py`：数据处理

`etl.py` 对应参考仓库里的数据清洗脚本。它负责把原始数据变成后续分析可以直接使用的标准表。

### 1.1 路径配置

```python
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
DB_PATH = PROJECT_DIR / "outputs" / "world_happiness.db"
```

这里不用本机绝对路径，而是以项目目录为基准。这样别人 clone 仓库后也能运行。

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

所有年份最终都整理成这 11 个字段。这样后续分析不需要再关心 2015、2016、2017、2018、2019 的字段名差异。

### 1.3 字段映射

```python
RENAME_MAPS = {
    "2015.csv": {
        "Country": "country",
        "Happiness Rank": "rank",
        "Happiness Score": "score",
        ...
    },
    ...
}
```

这是本项目最重要的清洗规则。不同年份同一含义的字段名称不同，例如：

| 标准字段 | 2015/2016 | 2017 | 2018/2019 |
|---|---|---|---|
| score | Happiness Score | Happiness.Score | Score |
| gdp | Economy (GDP per Capita) | Economy..GDP.per.Capita. | GDP per capita |
| social_support | Family | Family | Social support |

真实工作中，字段口径应该显式写出来，不能依赖模糊猜测。

### 1.4 读取、改名、补年份

```python
for path in sorted(DATA_DIR.glob("*.csv")):
    raw = pd.read_csv(path)
    year = int(path.stem)
    rename_map = RENAME_MAPS[path.name]
    data = raw.rename(columns=rename_map)
    data["year"] = year
```

这段代码逐个读取 CSV。`path.stem` 可以从 `2019.csv` 中取出 `2019`，作为年份字段。

### 1.5 记录原始文件信息

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

这一步是数据审计，用来证明每个文件读进来了多少行、多少列、原字段是什么。

### 1.6 用 2015/2016 补地区

```python
if "region" in data.columns:
    current_region = data.dropna(subset=["region"]).set_index("country")["region"]
    region_map.update(current_region.to_dict())
```

2015 和 2016 有 `region`，后面年份没有完整地区字段。这里建立：

```text
country -> region
```

后面用这个映射补齐 2017-2019 的地区。

### 1.7 合并成长表

```python
for col in STANDARD_COLUMNS:
    if col not in data.columns:
        data[col] = np.nan

data_list.append(data[STANDARD_COLUMNS])

clean_data = pd.concat(data_list, ignore_index=True)
clean_data["region"] = clean_data["region"].fillna(clean_data["country"].map(region_map))
```

这里保证每个年份的列结构一致，然后纵向合并。补不到地区的记录仍然保持缺失，不做静默修正。

### 1.8 保存清洗结果

```python
clean_data.to_csv(TABLE_DIR / "world_happiness_clean_2015_2019.csv", index=False, encoding="utf-8-sig")

with sqlite3.connect(DB_PATH) as conn:
    clean_data.to_sql("world_happiness", conn, index=False, if_exists="replace")
```

输出两类结果：

* CSV：方便直接查看和上传 GitHub。
* SQLite：方便用 SQL 查询，模仿参考仓库中“ETL 后进入数据库再分析”的方式。

## 2. `analyse.py`：分析结果表

`analyse.py` 负责把清洗后的数据变成多个分析结果表。

### 2.1 读取 SQLite 表

```python
with sqlite3.connect(DB_PATH) as conn:
    return pd.read_sql("select * from world_happiness", conn)
```

这里从 `world_happiness.db` 读取 `world_happiness` 表。这样分析层不用再关心原始 CSV。

### 2.2 缺失值检查

```python
tables["missing_summary"] = (
    clean_data.isna().sum().reset_index().rename(columns={"index": "field", 0: "missing_count"})
)
```

输出每个字段缺失多少条。这个项目的关键结果是：

* `region` 缺失 8 条。
* `corruption` 缺失 1 条。

### 2.3 数据质量总览

```python
tables["quality_summary"] = pd.DataFrame(
    [
        {
            "total_rows": len(clean_data),
            "total_columns": len(clean_data.columns),
            "unique_countries": clean_data["country"].nunique(),
            "duplicate_country_year_rows": clean_data.duplicated(["year", "country"]).sum(),
            "min_year": clean_data["year"].min(),
            "max_year": clean_data["year"].max(),
        }
    ]
)
```

这一步用于确认：

* 合并后总行数。
* 覆盖国家数量。
* 同一年同一国家是否重复。
* 年份范围是否正确。

### 2.4 Top / Bottom 排名

```python
data_2019 = clean_data[clean_data["year"] == 2019].copy()
tables["2019_top10"] = data_2019.nlargest(10, "score")[output_cols]
tables["2019_bottom10"] = data_2019.nsmallest(10, "score")[output_cols]
```

这类分析对应企业里的 Top 门店、Bottom 商品、Top 渠道、低表现地区等排名分析。

### 2.5 2015-2019 变化分析

```python
countries_2015 = set(clean_data.loc[clean_data["year"] == 2015, "country"])
countries_2019 = set(clean_data.loc[clean_data["year"] == 2019, "country"])
common_countries = sorted(countries_2015 & countries_2019)
```

先取共同国家，避免把新增国家和缺失国家混进变化分析。

```python
delta = clean_data[
    clean_data["country"].isin(common_countries) & clean_data["year"].isin([2015, 2019])
].pivot(index="country", columns="year", values="score")

delta["delta_2019_vs_2015"] = delta[2019] - delta[2015]
```

这相当于企业分析中的同比、环比或活动前后变化分析。

### 2.6 地区分组

```python
tables["region_2019_summary"] = (
    clean_data[(clean_data["year"] == 2019) & clean_data["region"].notna()]
    .groupby("region", as_index=False)
    .agg(
        avg_score=("score", "mean"),
        countries=("country", "nunique"),
        avg_gdp=("gdp", "mean"),
        avg_social_support=("social_support", "mean"),
        avg_life_expectancy=("life_expectancy", "mean"),
    )
)
```

分组均值必须同时看样本数，所以这里保留了 `countries`。

### 2.7 相关性分析

```python
corr = year_data[["score"] + METRICS].corr(numeric_only=True)["score"].drop("score")
```

相关性只能说明共同变化关系，不能解释因果。写结论时不能说“GDP 导致幸福分数提高”。

### 2.8 结果校验

```python
if clean_data.shape != (782, 11):
    raise AssertionError(...)
```

`validate_outputs()` 是简单的回归测试。它保证关键结果没有被后续改代码时破坏。

## 3. `analyse.sql`：SQL 分析口径

`analyse.sql` 保存了可以迁移到数据库中的分析查询，例如：

```sql
select
    year,
    count(distinct country) as countries,
    avg(score) as avg_score
from world_happiness
group by year
order by year;
```

它的作用是把分析口径显式写出来，方便以后迁移到 MySQL、Hive、PostgreSQL 或其他数据库环境。

## 4. `visualize.py`：数据可视化

`visualize.py` 只负责读分析结果表并画图，不重新做清洗逻辑。

### 4.1 读取分析表

```python
def read_table(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / f"{name}.csv")
```

图表层只依赖 `outputs/tables`，这样分工更清楚。

### 4.2 图表样式

```python
def style_axes(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", alpha=0.25)
```

这个函数统一图表标题、坐标轴和网格线。

### 4.3 四张图

`visualize.py` 生成 4 张图：

| 函数 | 图表 |
|---|---|
| `chart_2019_top_bottom()` | 2019 Top/Bottom 国家 |
| `chart_yearly_avg_trend()` | 2015-2019 年平均分趋势 |
| `chart_region_2019_avg()` | 2019 地区平均分 |
| `chart_2019_score_vs_key_indicators()` | 关键指标与幸福分数关系 |

每张图都对应一个业务问题，不是装饰性图表。

## 5. `run_all.py`：主入口

```python
from etl import main as run_etl
from analyse import main as run_analyse
from visualize import main as run_visualize

def main() -> None:
    run_etl()
    run_analyse()
    run_visualize()
```

这个文件只做流程编排：

```text
ETL -> analysis -> visualization
```

从仓库根目录运行：

```powershell
python projects/world-happiness-report/run_all.py
```

## 6. `src/analysis_world_happiness.py`：兼容旧入口

```python
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from run_all import main
```

这个文件保留是为了兼容之前 README 中的旧运行方式。实际逻辑已经迁移到项目根目录下的 `run_all.py`。

## 7. 这种结构对应的企业工作流

| 文件 | 企业分析中的角色 |
|---|---|
| `etl.py` | 数据抽取、清洗、标准化 |
| `analyse.py` | 指标计算、分组汇总、结果表生成 |
| `analyse.sql` | 可复用分析口径 |
| `visualize.py` | 图表和汇报素材生成 |
| `run_all.py` | 自动化执行入口 |

## 8. 你应该怎么复写

建议不要直接背完整代码，而是按顺序复写：

1. 先写 `etl.py`，只做到合并 CSV 和输出清洗表。
2. 再写 `analyse.py`，只做缺失值和 Top/Bottom。
3. 加入变化分析和地区分析。
4. 写 `analyse.sql`，把 pandas 里的分析口径翻译成 SQL。
5. 最后写 `visualize.py` 和 `run_all.py`。
