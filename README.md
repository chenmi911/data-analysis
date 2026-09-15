# data-analysis

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Cleaning%20%26%20EDA-150458?logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557C)
![MySQL](https://img.shields.io/badge/MySQL-Analysis%20Practice-4479A1?logo=mysql&logoColor=white)
![A/B Testing](https://img.shields.io/badge/A%2FB%20Testing-Z--test%20%26%20CI%20%26%20ITT-2B7CD3)
![Business Analytics](https://img.shields.io/badge/Business%20Analytics-Portfolio-FF8C00)
![Beginner Friendly](https://img.shields.io/badge/Beginner--Friendly-Code%20Walkthrough-6A5ACD)
[![CodeTriage](https://img.shields.io/badge/CodeTriage-open%20source%20helpers-2ea44f)](https://www.codetriage.com/chenmi911/data-analysis)


- **Cookie Cats 手游 A/B 测试（最新）**：围绕真实业务决策——"是否把首个等待门槛从第 30 关后移到第 40 关"，用 90,189 名玩家的随机分流数据做因果判断。
- **Superstore 零售经营分析**：原始订单数据到清洗表、SQL 经营分析、图表和结论的完整常规业务分析工作流，覆盖指标口径、分组对比、折扣影响、客户分层。

## list

| 主题 | 处理方式 | 技术栈 | 项目入口 | 数据 |
|---|---|---|---|---|
| Cookie Cats 手游 A/B 测试 | SQL 双比例 Z 检验 + 95% CI + 留存多指标 + ITT 口径稳健性 + 实际意义换算 | MySQL 8 + SQL 窗口函数 + Python/pandas 复核 + A/B Test | [项目说明](projects/cookie-cats-ab-test/README.md) / [业务分析报告](projects/cookie-cats-ab-test/docs/analysis_report.md) / [SQL 分析](projects/cookie-cats-ab-test/sql/cookie_cats_mysql_ab_test.sql) / [Python 脚本](projects/cookie-cats-ab-test/python/cookie_cats_ab_test_python_commented.py) / [简历表述](projects/cookie-cats-ab-test/docs/resume_project_summary.md) | [下载与校验说明](projects/cookie-cats-ab-test/data/raw/README.md)（CSV 不随仓库分发） |
| Superstore 零售经营分析 | pandas 清洗订单明细 + MySQL 经营分析 + RFM 客户分层 + 结论输出 | Python + pandas + MySQL + SQL 窗口函数 | [项目说明](projects/superstore-business-analysis/README.md) / [过程说明](projects/superstore-business-analysis/docs/analysis_process.md) / [代码讲解](projects/superstore-business-analysis/docs/code_walkthrough.md) / [SQL 分析](projects/superstore-business-analysis/sql/superstore_mysql_analysis.sql) / [结论文档](projects/superstore-business-analysis/docs/conclusions.md) | [clean csv](projects/superstore-business-analysis/data/superstore_orders_clean.csv) |

## projects

### Cookie Cats 手游关卡门槛调整的 A/B 测试（最新）

业务场景：免费消除手游 Cookie Cats 用"等待门槛"（能量/时间墙）控制节奏。产品团队想知道把首个门槛从第 30 关**后移到第 40 关**能否让玩家先养成习惯再撞墙——但也可能只是白白折损留存。两种假设都成立，只能靠随机实验区分因果效应与人群体质差异。

核心分析判断：

* 主指标 **7 日留存** 用双比例 Z 检验 + 95% CI 判断（样本 9 万人，但 1pp 量级差异仍在随机波动内，不能用点估计拍板）。
* 辅助指标 **1 日留存** 与 **前 14 天游戏局数**（长尾分布，以 P50–P99 分位数看）做一致性参照，防"留存没变但玩得更少"被漏掉。
* 识别**选择偏差陷阱**：62.7% / 69.6% 玩家从未触达各自门槛；若只看"到达者"，结论会反转成后移更好，这是后处理变量导致的假象，故以**全体样本（ITT）**为主口径。

结论：`gate_40` 的 7 日留存较 `gate_30` 显著下降 **0.82 个百分点**（约 -4.3%，p≈0.0016，95% CI [-1.33, -0.31] 个百分点），折算本批实验组约少 370 名第 7 天留存用户；辅助指标方向同负或无差异。按既定决策规则**建议不推广第 40 关方案**，并给出补充商业化数据后的下一步实验设计。

学习文档：

* [项目说明（Why / STAR / 复现）](projects/cookie-cats-ab-test/README.md)
* [业务分析报告（含决策论证与下一步实验）](projects/cookie-cats-ab-test/docs/analysis_report.md)
* [MySQL 分析 SQL](projects/cookie-cats-ab-test/sql/cookie_cats_mysql_ab_test.sql)
* [Python 复核脚本（分步注释版）](projects/cookie-cats-ab-test/python/cookie_cats_ab_test_python_commented.py)
* [简历项目表述](projects/cookie-cats-ab-test/docs/resume_project_summary.md)

### Superstore 零售经营分析

业务场景：模拟零售电商经营分析，基于订单明细回答销售、利润、折扣、区域、品类和客户价值问题。

分析目标：

* 公司整体销售额、利润和利润率表现如何？
* 利润问题主要集中在哪些区域、品类和子品类？
* 高折扣是否导致亏损，哪些品类风险最高？
* 哪些客户贡献利润，哪些客户高消费但低利润？
* 如何用 RFM 将客户分为高价值、重点发展、流失风险等类型？

学习文档：

* [项目说明](projects/superstore-business-analysis/README.md)
* [分析过程说明](projects/superstore-business-analysis/docs/analysis_process.md)
* [Python 与 SQL 代码逐段讲解](projects/superstore-business-analysis/docs/code_walkthrough.md)
* [MySQL 分析 SQL](projects/superstore-business-analysis/sql/superstore_mysql_analysis.sql)
* [经营分析结论](projects/superstore-business-analysis/docs/conclusions.md)

## stats

![GitHub Stats](https://github-readme-stats.vercel.app/api?username=chenmi911&show_icons=true)

## refer

> 1. [pandas documentation](https://pandas.pydata.org/docs/)
> 2. [MySQL documentation](https://dev.mysql.com/doc/)
> 3. [GitHub repository style reference: TurboWay/bigdata_analyse](https://github.com/TurboWay/bigdata_analyse)

## license

Code and documents in this repository are released under the MIT License. Raw datasets keep their original data source licenses and terms.
