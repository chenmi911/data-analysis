# Python 代码逐段讲解

对应代码文件：`src/analysis_world_happiness.py`

这份脚本不是为了炫技，而是把一次完整 EDA 项目拆成可复现的流水线：

```text
读取原始 CSV
→ 统一字段
→ 合并成长表
→ 生成分析表
→ 生成图表
→ 做结果校验
→ 打印关键结果
```

## 1. 导入库和设置路径

代码位置：第 1-11 行

```python
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data" / "raw"
TABLE_DIR = PROJECT_DIR / "outputs" / "tables"
FIGURE_DIR = PROJECT_DIR / "outputs" / "figures"
```

这里用了 3 个核心库：

| 库 | 用途 |
|---|---|
| pandas | 读取 CSV、清洗数据、分组汇总、相关性分析 |
| numpy | 处理缺失值、生成回归线坐标 |
| matplotlib | 画图并保存 PNG |

`Path(__file__).resolve().parents[1]` 的作用是定位当前项目目录。这样脚本不依赖本机的绝对路径，别人 clone 仓库后也能运行。

## 2. 定义标准字段

代码位置：第 13-25 行

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

这是清洗后的目标表结构。后面所有年份的数据都要被整理成这 11 个字段。

为什么要先定义标准字段：

- 保证 2015-2019 可以纵向合并。
- 避免同一个含义出现多个字段名。
- 让后续分析函数只面对一套统一口径。

## 3. 建立字段映射表

代码位置：第 27-85 行

`RENAME_MAPS` 是整个清洗流程的关键。不同年份字段名不同，例如：

| 年份 | 原字段 | 标准字段 |
|---|---|---|
| 2015/2016 | Happiness Score | score |
| 2017 | Happiness.Score | score |
| 2018/2019 | Score | score |
| 2015/2016 | Family | social_support |
| 2018/2019 | Social support | social_support |

代码用字典显式写出每个年份的字段映射：

```python
"2019.csv": {
    "Overall rank": "rank",
    "Country or region": "country",
    "Score": "score",
    ...
}
```

真实工作里，不建议靠模糊匹配自动猜字段。字段口径是分析结论的基础，应该显式维护。

## 4. `load_and_standardize()`：读取并标准化数据

代码位置：第 88-137 行

这个函数做 5 件事。

### 4.1 遍历全部 CSV

```python
for file in sorted(DATA_DIR.glob("*.csv")):
    raw = pd.read_csv(file)
    year = int(file.stem)
    rename_map = RENAME_MAPS[file.name]
```

`DATA_DIR.glob("*.csv")` 找到 `data/raw/` 下所有 CSV。`file.stem` 是不带扩展名的文件名，例如 `2019.csv` 的 stem 是 `2019`。

### 4.2 记录原始文件信息

```python
raw_summary_rows.append(
    {
        "year": year,
        "file": file.name,
        "rows": len(raw),
        "cols": len(raw.columns),
        "raw_columns": " | ".join(raw.columns),
    }
)
```

这一步不是分析结论，而是数据审计。它能回答：

- 每年多少行？
- 每年多少列？
- 原始字段是什么？

企业里做多文件合并时，这一步很重要。否则字段变了、文件少了、行数异常了，后面可能完全不知道。

### 4.3 保存字段映射记录

```python
for raw_col, standard_col in rename_map.items():
    column_map_rows.append(...)
```

这个输出会生成 `standardized_column_map.csv`。它记录了每个原字段被改成了什么标准字段。

这样做的好处是：别人可以复查你的字段口径，不需要只相信你的代码。

### 4.4 重命名并补年份

```python
df = raw.rename(columns=rename_map)
df["year"] = year
```

`rename()` 把不同年份字段统一成标准字段。新增 `year` 是为了合并后仍然知道每条记录来自哪一年。

### 4.5 建立国家-地区映射

```python
if "region" in df.columns:
    current_region = df.dropna(subset=["region"]).set_index("country")["region"]
    region_map.update(current_region.to_dict())
```

2015 和 2016 有 `region`，后面年份没有完整地区字段。这里从有地区信息的数据中提取：

```text
country -> region
```

后面用它给 2017-2019 补地区。

### 4.6 补齐缺失字段并选择标准列

```python
for col in STANDARD_COLUMNS:
    if col not in df.columns:
        df[col] = np.nan

frames.append(df[STANDARD_COLUMNS])
```

如果某一年没有某个标准字段，就补成 `NaN`。这样所有年份的 DataFrame 列结构一致，可以安全合并。

### 4.7 合并成长表并补地区

```python
clean = pd.concat(frames, ignore_index=True)
clean["region"] = clean["region"].fillna(clean["country"].map(region_map))
```

`pd.concat()` 把 5 年数据纵向拼接。`ignore_index=True` 让新表重新生成连续索引。

`country.map(region_map)` 用国家名查地区。查不到的仍然保持缺失，这就是后面看到的 8 条 `region` 缺失。

## 5. `build_tables()`：生成分析结果表

代码位置：第 140-230 行

这个函数不画图，只负责产出分析表。这样表格逻辑和图表逻辑分开，方便检查。

### 5.1 缺失值检查

```python
tables["missing_summary"] = (
    clean.isna().sum().reset_index().rename(columns={"index": "field", 0: "missing_count"})
)
```

`clean.isna().sum()` 会统计每列缺失值数量。

这一步对应数据质量检查。结论里说 `region` 缺失 8 条、`corruption` 缺失 1 条，就是从这里来的。

### 5.2 找出地区缺失的国家

```python
tables["region_missing_countries"] = clean.loc[
    clean["region"].isna(), ["year", "country"]
].sort_values(["country", "year"])
```

这不是只说“缺失 8 条”，而是把缺失的具体国家列出来。真实分析中，只报缺失数量不够，还要能定位是哪几条。

### 5.3 数据质量总览

```python
tables["quality_summary"] = pd.DataFrame(
    [
        {
            "total_rows": len(clean),
            "total_columns": len(clean.columns),
            "unique_countries": clean["country"].nunique(),
            "duplicate_country_year_rows": clean.duplicated(["year", "country"]).sum(),
            "min_year": clean["year"].min(),
            "max_year": clean["year"].max(),
        }
    ]
)
```

这里检查：

- 总行数
- 总列数
- 国家数量
- 同一年同一国家是否重复
- 年份范围

如果 `duplicate_country_year_rows` 不为 0，说明同一年同一国家出现多次，后续排名、分组均值都可能有问题。

### 5.4 2019 Top 10 / Bottom 10

```python
sub2019 = clean[clean["year"] == 2019].copy()
tables["2019_top10"] = sub2019.nlargest(10, "score")[table_cols]
tables["2019_bottom10"] = sub2019.nsmallest(10, "score")[table_cols]
```

`nlargest(10, "score")` 取幸福分数最高的 10 个国家。`nsmallest()` 取最低的 10 个。

这类排名分析在企业里很常见，例如：

- 销售额 Top 门店
- 利润率最低商品
- 转化率最高渠道
- 投诉最多地区

### 5.5 2015-2019 变化分析

代码位置：第 178-187 行

```python
countries_2015 = set(clean.loc[clean["year"] == 2015, "country"])
countries_2019 = set(clean.loc[clean["year"] == 2019, "country"])
common_countries = sorted(countries_2015 & countries_2019)
```

先取 2015 和 2019 都出现的国家。这样做是为了保证比较对象一致。

```python
delta = clean[
    clean["country"].isin(common_countries) & clean["year"].isin([2015, 2019])
].pivot(index="country", columns="year", values="score")
```

`pivot()` 把长表变成宽表：

```text
country | 2015 | 2019
```

然后计算变化量：

```python
delta["delta_2019_vs_2015"] = delta[2019] - delta[2015]
```

这一步对应企业分析里的同比、环比、活动前后对比。

### 5.6 年度趋势

```python
tables["yearly_avg_score"] = clean.groupby("year", as_index=False).agg(
    avg_score=("score", "mean"),
    countries=("country", "nunique"),
)
```

按年份分组，计算每年的平均幸福分数和国家数量。

注意这里同时保留 `countries`。分组均值必须看样本数，否则均值可能误导。

### 5.7 地区汇总

```python
tables["region_2019_summary"] = (
    clean[(clean["year"] == 2019) & clean["region"].notna()]
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

这里按地区统计：

- 平均幸福分数
- 国家数
- 平均 GDP 指标
- 平均社会支持
- 平均健康预期寿命

这一步用于回答“不同地区整体表现有什么差异”。

### 5.8 相关性分析

```python
corr = year_df[["score"] + metrics].corr(numeric_only=True)["score"].drop("score")
```

这行计算每个指标和 `score` 的相关系数。

解释时必须谨慎：

- 可以说 “GDP 与幸福分数高度正相关”。
- 不能说 “GDP 导致幸福分数提高”。

原因是这个数据不是实验数据，也没有控制其他变量。

## 6. `save_tables()`：保存输出表格

代码位置：第 233-240 行

```python
TABLE_DIR.mkdir(parents=True, exist_ok=True)
clean.to_csv(TABLE_DIR / "world_happiness_clean_2015_2019.csv", index=False, encoding="utf-8-sig")
```

`mkdir(parents=True, exist_ok=True)` 保证输出目录存在。

`encoding="utf-8-sig"` 是为了让 CSV 在 Excel 中打开时更稳定，尤其是包含中文列名或中文内容时。

## 7. `style_axes()`：统一图表样式

代码位置：第 243-249 行

```python
def style_axes(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
```

这是一个小工具函数，用来统一标题、坐标轴、网格线和边框风格。

它不是为了过度抽象，而是因为 4 张图都需要相同的基础样式，集中处理能减少重复代码。

## 8. `build_charts()`：生成 4 张图

代码位置：第 252-310 行

### 8.1 Top / Bottom 横向柱状图

```python
rank_df = pd.concat([top10.assign(group="Top 10"), bottom10.assign(group="Bottom 10")])
rank_df = rank_df.sort_values("score")
```

先把 Top 10 和 Bottom 10 合在一起，再按分数排序。

```python
colors = ["#b84545" if group == "Bottom 10" else "#286a8f" for group in rank_df["group"]]
```

颜色用于区分高分组和低分组。蓝色表示 Top，红色表示 Bottom。

### 8.2 年度趋势折线图

```python
ax.plot(trend["year"], trend["avg_score"], marker="o", color="#286a8f", linewidth=2.4)
```

折线图适合展示时间趋势。这里展示 2015-2019 平均幸福分数的变化。

### 8.3 地区平均分图

```python
region_2019 = tables["region_2019_summary"].sort_values("avg_score")
ax.barh(region_2019["region"], region_2019["avg_score"], color="#4f8f6b")
```

横向柱状图适合地区名称较长的场景。图上额外标注 `n=国家数`，防止只看均值忽略样本量。

### 8.4 散点图和趋势线

```python
ax.scatter(sub2019[metric], sub2019["score"], alpha=0.72, color="#286a8f", s=30)
coef = np.polyfit(valid[metric], valid["score"], 1)
xs = np.linspace(valid[metric].min(), valid[metric].max(), 100)
ax.plot(xs, coef[0] * xs + coef[1], color="#b84545", linewidth=1.8)
```

散点图展示两个变量之间的关系。红线是线性趋势线，用来辅助观察整体方向。

```python
corr = valid[metric].corr(valid["score"])
style_axes(ax, f"{label}\nr = {corr:.3f}", label, "Score")
```

图标题里加入相关系数 `r`，让读者不用回到表格也能看到关系强度。

## 9. `validate_outputs()`：结果校验

代码位置：第 313-334 行

这个函数是为了防止脚本静默生成错误结果。

```python
if clean.shape != (782, 11):
    raise AssertionError(...)
```

如果合并后的数据不是 782 行、11 列，脚本直接报错。

```python
if top_2019 != "Finland":
    raise AssertionError(...)
if bottom_2019 != "South Sudan":
    raise AssertionError(...)
```

这些断言不是业务分析本身，而是回归测试。以后如果有人改了字段映射或数据处理逻辑，导致关键结果变了，脚本会立刻提醒。

## 10. `main()`：组织完整流程

代码位置：第 337-364 行

```python
clean, raw_summary, column_map = load_and_standardize()
tables = build_tables(clean)
validate_outputs(clean, tables)
save_tables(clean, raw_summary, column_map, tables)
build_charts(clean, tables)
```

这就是完整执行顺序：

1. 读数据并清洗。
2. 生成分析结果表。
3. 校验关键结果。
4. 保存 CSV。
5. 保存图表。

最后的 `print()` 用于在命令行展示关键结果，方便运行后快速确认。

## 11. 这份代码对应的数据分析能力

| 代码模块 | 训练能力 |
|---|---|
| `RENAME_MAPS` | 字段口径管理 |
| `load_and_standardize()` | 多文件读取、清洗、合并 |
| `missing_summary` | 数据质量检查 |
| `2019_top10` / `2019_bottom10` | 排名分析 |
| `score_delta_2019_vs_2015` | 变化分析 |
| `region_2019_summary` | 分组对比 |
| `correlation_by_year` | 相关性分析 |
| `build_charts()` | 可视化表达 |
| `validate_outputs()` | 结果校验和可复现性 |

## 12. 初学者容易错的地方

1. 直接合并 5 个 CSV，不先统一字段名。
2. 直接比较 2015 和 2019 全量国家，不取共同国家。
3. 只看地区均值，不看国家数。
4. 把相关性写成因果关系。
5. 只画图，不说明图表支撑哪个业务问题。
6. 不写校验，导致数据处理错了也不知道。

## 13. 建议你自己复写的顺序

不要一开始照抄完整脚本。建议拆成 6 次练习：

1. 只读取 5 个 CSV，打印行数和字段名。
2. 写 `RENAME_MAPS`，把 5 年数据统一字段。
3. 合并成长表，检查缺失值和重复值。
4. 做 Top/Bottom、趋势、地区汇总。
5. 做相关性和变化分析。
6. 最后再加图表和 `validate_outputs()`。
