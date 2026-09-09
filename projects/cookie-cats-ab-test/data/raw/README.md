# 原始数据下载与校验

原始数据未随仓库发布。Kaggle 数据集标注为 `Other (specified in description)`，页面没有给出可确认的再分发条款，因此仓库仅提供复现说明。

1. 从 [Mobile Games A/B Testing - Cookie Cats](https://www.kaggle.com/datasets/mursideyarkin/mobile-games-ab-testing-cookie-cats) 下载数据。
2. 将文件命名为 `cookie_cats.csv`，放到本目录。
3. 确认文件字段为 `userid,version,sum_gamerounds,retention_1,retention_7`。
4. 本项目分析使用的本地文件 SHA-256 为：

   ```text
   5AB54D761FBDDCD50DE7B88E4EAF7837CBA4569474F50C043A4D17EE342C46BD
   ```

若下载文件校验值不同，请先确认数据版本和内容差异，再将其用于复现。
