# 数据分析项目集

这个仓库用于记录我的数据分析学习项目。当前项目以 World Happiness Report 为例，重点训练真实分析工作中常用的流程：数据清洗、字段口径统一、数据质量检查、分组对比、趋势分析、相关性分析、可视化表达和结论输出。

## 当前项目

### World Happiness Report 分析

项目路径：[projects/world-happiness-report](projects/world-happiness-report)

学习文档：

- [项目说明与结论](projects/world-happiness-report/README.md)
- [分析过程说明](projects/world-happiness-report/docs/analysis_process.md)
- [Python 代码逐段讲解](projects/world-happiness-report/docs/code_walkthrough.md)

业务场景：模拟咨询公司或国际业务部门的海外市场环境评估。分析目标不是做预测，而是回答：

- 哪些国家和地区幸福指数更高？
- 2015-2019 年哪些国家变化最明显？
- 地区之间是否存在明显差异？
- GDP、社会支持、健康预期寿命等指标与幸福分数的关系如何？
- 这些结果能为海外市场研究提供哪些参考？

## 核心图表

### 2019 年幸福指数 Top / Bottom

![2019 Happiness Score Top and Bottom](projects/world-happiness-report/outputs/figures/chart_2019_top_bottom.png)

### 2015-2019 年平均幸福指数趋势

![Average Happiness Score Trend](projects/world-happiness-report/outputs/figures/chart_yearly_avg_trend.png)

### 2019 年地区平均幸福指数

![2019 Region Average Score](projects/world-happiness-report/outputs/figures/chart_region_2019_avg.png)

### 关键指标与幸福分数关系

![Score vs Key Indicators](projects/world-happiness-report/outputs/figures/chart_2019_score_vs_key_indicators.png)

## 方法框架

| 环节 | 目的 | 本项目做法 |
|---|---|---|
| 数据读取 | 确认原始数据结构 | 读取 2015-2019 五个 CSV |
| 字段统一 | 保证跨年可比 | 将不同年份字段映射为统一字段 |
| 数据质量检查 | 避免错误结论 | 检查缺失值、重复国家年份、行列数 |
| 描述性分析 | 快速理解整体格局 | Top/Bottom、年度均值、地区均值 |
| 变化分析 | 识别变化明显国家 | 只比较 2015 和 2019 共同出现国家 |
| 相关性分析 | 初步判断指标关系 | 计算各指标与幸福分数的相关系数 |
| 可视化 | 支撑结论表达 | 输出 4 张分析图表 |

## 关键结论

- 2019 年幸福指数最高的是 Finland，最低的是 South Sudan。
- 2015-2019 年共同国家中，幸福分数上升最多的是 Benin，下降最多的是 Venezuela。
- 2019 年幸福分数与 GDP、健康预期寿命、社会支持的相关性较高。
- 地区之间差异明显，Western Europe、North America、Australia and New Zealand 整体表现较高，Sub-Saharan Africa 整体较低。

这些结论只能说明相关关系和分布差异，不能直接解释因果。数据是国家级聚合数据，样本量有限，并且部分解释变量本身就是幸福分数的组成维度，因此不适合直接作为严肃预测建模项目。

## 运行方式

```powershell
pip install -r requirements.txt
python projects/world-happiness-report/src/analysis_world_happiness.py
```

运行后会重新生成：

- 清洗后的长表
- 数据质量检查表
- Top / Bottom 国家表
- 分数变化表
- 地区汇总表
- 相关性结果表
- 4 张可视化图表

## 当前训练重点

这个项目对应数据分析基础能力，不是机器学习项目。重点能力包括：

- 多文件数据合并
- 跨年份字段口径统一
- 缺失值和重复值检查
- 排名分析
- 趋势分析
- 分组对比
- 相关性分析
- 图表支撑结论
- 分析结论边界说明
