# Python 代码逐段讲解

这个项目现在只保留 Python 顺序脚本，不使用数据库查询，也不写自定义函数。这样更适合当前学习阶段：你可以从上到下逐行运行、逐行理解，每一步输入什么、输出什么都比较直接。完整代码: world-happiness-report/analyse.py

项目代码结构：

```text
etl.py
analyse.py
visualize.py
run_all.py
src/analysis_world_happiness.py
```

整体流程：

```text
原始 CSV
→ etl.py：字段统一、合并、补齐地区、保存清洗表
→ analyse.py：读取清洗表，生成分析结果表
→ visualize.py：读取结果表，生成图表
→ run_all.py：按顺序执行完整流程
```

## 1. `etl.py`：清洗和标准化

`etl.py` 的目标是把 2015-2019 年 5 个原始 CSV 变成一张统一口径的长表。

### 1.1 路径配置

```python
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
```

这里使用脚本所在目录定位数据，不写 `D:\...` 这类本机绝对路径。别人 clone 仓库后，只要目录结构不变，也能运行。

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

后续所有分析都围绕这 11 个字段。真实业务里，多期报表字段名经常不一致，第一步必须先把字段口径统一。

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

这段是清洗规则，不是装饰代码。它明确说明每个原始字段对应哪个标准字段，例如：

| 标准字段 | 2015/2016 | 2017 | 2018/2019 |
|---|---|---|---|
| score | Happiness Score | Happiness.Score | Score |
| gdp | Economy (GDP per Capita) | Economy..GDP.per.Capita. | GDP per capita |
| social_support | Family | Family | Social support |

### 1.4 逐个读取 CSV

```python
for path in sorted(DATA_DIR.glob("*.csv")):
    raw = pd.read_csv(path)
    year = int(path.stem)
    rename_map = RENAME_MAPS[path.name]
```

`DATA_DIR.glob("*.csv")` 找到所有原始 CSV。`path.stem` 会把 `2019.csv` 变成 `2019`，用来生成年份字段。

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

这一步用于数据审计，回答三个问题：

1. 每个文件是否都读到了。
2. 每个文件有多少行、多少列。
3. 每个文件原始字段是什么。

企业分析里，先做审计比直接画图更重要，因为后续结论都依赖这些基础数据是否可靠。

### 1.6 字段改名和补年份

```python
data = raw.rename(columns=rename_map)
data["year"] = year
```

`rename` 把原始字段改成统一字段。`year` 是后面做趋势分析和 2015-2019 对比的基础。

### 1.7 用已有年份补地区

```python
if "region" in data.columns:
    current_region = data.dropna(subset=["region"]).set_index("country")["region"]
    region_map.update(current_region.to_dict())
```

2015、2016 有 `region` 字段，2017-2019 不完整。这里先建立：

```text
country -> region
```

后面用国家名称去补地区。补不到的仍然保留缺失，不手工硬改。

### 1.8 补齐缺失列并合并

```python
for col in STANDARD_COLUMNS:
    if col not in data.columns:
        data[col] = np.nan

data_list.append(data[STANDARD_COLUMNS])
```

不同年份缺的列用空值补齐，然后按同样的列顺序追加到 `data_list`。

```python
clean_data = pd.concat(data_list, ignore_index=True)
clean_data["region"] = clean_data["region"].fillna(clean_data["country"].map(region_map))
```

`pd.concat` 是纵向合并，把 5 年数据合成一张长表。

### 1.9 输出清洗结果

```python
clean_data.to_csv(
    TABLE_DIR / "world_happiness_clean_2015_2019.csv",
    index=False,
    encoding="utf-8-sig",
)
raw_summary.to_csv(TABLE_DIR / "raw_file_summary.csv", index=False, encoding="utf-8-sig")
column_map.to_csv(TABLE_DIR / "standardized_column_map.csv", index=False, encoding="utf-8-sig")
```

这里输出三类表：

| 输出表 | 作用 |
|---|---|
| `world_happiness_clean_2015_2019.csv` | 后续分析主表 |
| `raw_file_summary.csv` | 原始文件审计 |
| `standardized_column_map.csv` | 字段映射记录 |

## 2. `analyse.py`：分析结果表

`analyse.py` 不再读取原始 CSV，而是读取 `etl.py` 生成的清洗表。

### 2.1 读取清洗表

```python
CLEAN_DATA_PATH = TABLE_DIR / "world_happiness_clean_2015_2019.csv"
clean_data = pd.read_csv(CLEAN_DATA_PATH)
```

这一步让清洗和分析分开：清洗负责造一张标准表，分析只基于标准表做指标。

### 2.2 缺失值检查

```python
missing_summary = (
    clean_data.isna().sum().reset_index().rename(columns={"index": "field", 0: "missing_count"})
)
```

输出每个字段缺失多少条。本项目关键结果：

* `region` 缺失 8 条。
* `corruption` 缺失 1 条。

### 2.3 数据质量总览

```python
quality_summary = pd.DataFrame(
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

这一步确认数据规模、年份范围、国家数量和是否存在同一年同一国家重复。

### 2.4 2019 Top / Bottom

```python
data_2019 = clean_data[clean_data["year"] == 2019].copy()
top10_2019 = data_2019.nlargest(10, "score")[output_cols]
bottom10_2019 = data_2019.nsmallest(10, "score")[output_cols]
```

这是最常见的排名分析。企业场景里可以对应 Top 门店、Bottom 商品、Top 渠道、低表现地区等问题。

### 2.5 2015-2019 变化分析

```python
countries_2015 = set(clean_data.loc[clean_data["year"] == 2015, "country"])
countries_2019 = set(clean_data.loc[clean_data["year"] == 2019, "country"])
common_countries = sorted(countries_2015 & countries_2019)
```

先取共同国家，避免新增国家或缺失国家影响变化判断。

```python
score_delta_2019_vs_2015 = clean_data[
    clean_data["country"].isin(common_countries) & clean_data["year"].isin([2015, 2019])
].pivot(index="country", columns="year", values="score")
score_delta_2019_vs_2015["delta_2019_vs_2015"] = (
    score_delta_2019_vs_2015[2019] - score_delta_2019_vs_2015[2015]
)
```

这类逻辑对应业务里的同比、环比、活动前后对比。

### 2.6 年度趋势

```python
yearly_avg_score = clean_data.groupby("year", as_index=False).agg(
    avg_score=("score", "mean"),
    countries=("country", "nunique"),
)
```

年度平均值用于观察整体趋势，同时保留每年国家数量，避免只看均值忽略样本变化。

### 2.7 地区分组

```python
region_2019_summary = (
    clean_data[(clean_data["year"] == 2019) & clean_data["region"].notna()]
    .groupby("region", as_index=False)
    .agg(
        avg_score=("score", "mean"),
        countries=("country", "nunique"),
        avg_gdp=("gdp", "mean"),
        avg_social_support=("social_support", "mean"),
        avg_life_expectancy=("life_expectancy", "mean"),
    )
    .sort_values("avg_score", ascending=False)
)
```

地区均值必须同时看 `countries`，因为不同地区样本数不同。

### 2.8 相关性分析

```python
for year, year_data in clean_data.groupby("year"):
    corr = year_data[["score"] + METRICS].corr(numeric_only=True)["score"].drop("score")
    for metric, value in corr.items():
        corr_rows.append({"year": year, "metric": metric, "corr_with_score": value})
```

这一步计算每年各指标和幸福分数的相关系数。相关性只能说明共同变化关系，不能直接写成因果关系。

### 2.9 关键结果校验

```python
if clean_data.shape != (782, 11):
    raise AssertionError(f"Expected clean shape (782, 11), got {clean_data.shape}")
```

后面还校验：

* `region` 缺失是否为 8。
* `corruption` 缺失是否为 1。
* 2019 最高是否为 Finland。
* 2019 最低是否为 South Sudan。
* 2015-2019 上升最多是否为 Benin。
* 2015-2019 下降最多是否为 Venezuela。

这些校验的作用是防止以后改代码时把关键结果改坏。

### 2.10 保存分析结果

```python
top10_2019.to_csv(TABLE_DIR / "2019_top10.csv", index=False, encoding="utf-8-sig")
bottom10_2019.to_csv(TABLE_DIR / "2019_bottom10.csv", index=False, encoding="utf-8-sig")
score_delta_2019_vs_2015.to_csv(
    TABLE_DIR / "score_delta_2019_vs_2015.csv", index=False, encoding="utf-8-sig"
)
```

分析脚本把每个主题输出为一张结果表，方便检查，也方便后续图表脚本复用。

## 3. `visualize.py`：图表生成

`visualize.py` 只读取 `outputs/tables/` 里的结果表，不重复清洗逻辑。

### 3.1 读取 Top / Bottom 表

```python
top10 = pd.read_csv(TABLE_DIR / "2019_top10.csv")
bottom10 = pd.read_csv(TABLE_DIR / "2019_bottom10.csv")
rank_data = pd.concat([top10.assign(group="Top 10"), bottom10.assign(group="Bottom 10")])
rank_data = rank_data.sort_values("score")
```

这里把 Top 10 和 Bottom 10 合在一张图里，便于对比高低差距。

### 3.2 绘制横向柱状图

```python
fig, ax = plt.subplots(figsize=(11, 7))
colors = ["#b84545" if group == "Bottom 10" else "#286a8f" for group in rank_data["group"]]
ax.barh(rank_data["country"], rank_data["score"], color=colors)
```

横向柱状图适合国家名称较长的场景，标签比竖向柱状图更容易阅读。

### 3.3 年度趋势图

```python
trend = pd.read_csv(TABLE_DIR / "yearly_avg_score.csv")
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(trend["year"], trend["avg_score"], marker="o", color="#286a8f", linewidth=2.4)
```

折线图用于展示 2015-2019 年平均幸福分数变化。

### 3.4 地区对比图

```python
region_2019 = pd.read_csv(TABLE_DIR / "region_2019_summary.csv").sort_values("avg_score")
fig, ax = plt.subplots(figsize=(11, 6.5))
ax.barh(region_2019["region"], region_2019["avg_score"], color="#4f8f6b")
```

地区对比图回答“哪些地区整体更高、哪些地区整体更低”。

### 3.5 关键指标散点图

```python
chart_specs = [
    ("gdp", "GDP per capita"),
    ("social_support", "Social support"),
    ("life_expectancy", "Healthy life expectancy"),
]
```

这里选择 GDP、社会支持、健康预期寿命三个指标，是因为它们和幸福分数相关性较高，也更容易向业务方解释。

```python
for ax, (metric, label) in zip(axes, chart_specs):
    ax.scatter(data_2019[metric], data_2019["score"], alpha=0.72, color="#286a8f", s=30)
    valid = data_2019[[metric, "score"]].dropna()
    coef = np.polyfit(valid[metric], valid["score"], 1)
```

散点图展示单个国家的分布，趋势线只辅助观察方向，不代表因果。

## 4. `run_all.py`：主入口

```python
PROJECT_DIR = Path(__file__).resolve().parent

runpy.run_path(str(PROJECT_DIR / "etl.py"), run_name="__main__")
runpy.run_path(str(PROJECT_DIR / "analyse.py"), run_name="__main__")
runpy.run_path(str(PROJECT_DIR / "visualize.py"), run_name="__main__")
```

`run_all.py` 只负责按顺序执行三个脚本：

```text
ETL -> analysis -> visualization
```

从仓库根目录运行：

```powershell
python projects/world-happiness-report/run_all.py
```

## 5. `src/analysis_world_happiness.py`：兼容入口

```python
PROJECT_DIR = Path(__file__).resolve().parents[1]
runpy.run_path(str(PROJECT_DIR / "run_all.py"), run_name="__main__")
```

这个文件保留是为了兼容之前的运行方式。真正的主入口是项目根目录下的 `run_all.py`。

## 6. 这种结构对应的企业工作流

| 文件 | 企业分析中的角色 |
|---|---|
| `etl.py` | 数据抽取、字段标准化、清洗表生成 |
| `analyse.py` | 指标计算、分组汇总、结果表生成 |
| `visualize.py` | 图表和汇报素材生成 |
| `run_all.py` | 自动化执行入口 |

## 7. 你应该怎么复写

建议按顺序复写，不要一上来写完整项目：

1. 先写 `etl.py`，只做到合并 CSV 和输出清洗表。
2. 再写 `analyse.py`，只做缺失值检查和 2019 Top/Bottom。
3. 加入 2015-2019 变化分析和地区分析。
4. 加入相关性分析和关键结果校验。
5. 最后写 `visualize.py` 和 `run_all.py`。
