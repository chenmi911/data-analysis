-- Superstore MySQL 练习 SQL
-- 先运行 Python:
-- python projects/superstore-business-analysis/src/analysis_superstore.py
--
-- 再用 MySQL 客户端运行本文件:
-- mysql --local-infile=1 -uroot -p --execute="source projects/superstore-business-analysis/sql/superstore_mysql_analysis.sql"

CREATE DATABASE IF NOT EXISTS practice DEFAULT CHARACTER SET utf8mb4;
USE practice;

DROP TABLE IF EXISTS superstore_orders_clean;

CREATE TABLE superstore_orders_clean (
    row_id INT,
    order_id VARCHAR(30),
    order_date DATE,
    ship_date DATE,
    ship_mode VARCHAR(50),
    customer_id VARCHAR(30),
    customer_name VARCHAR(100),
    segment VARCHAR(50),
    country VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    region VARCHAR(50),
    product_id VARCHAR(50),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    product_name VARCHAR(255),
    sales DECIMAL(12, 4),
    quantity INT,
    discount DECIMAL(6, 4),
    profit DECIMAL(12, 4),
    ship_days INT,
    profit_margin DECIMAL(12, 6)
);

LOAD DATA LOCAL INFILE 'projects/superstore-business-analysis/data/superstore_orders_clean.csv'
INTO TABLE superstore_orders_clean
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(row_id, order_id, order_date, ship_date, ship_mode, customer_id, customer_name,
 segment, country, city, state, postal_code, region, product_id, category,
 sub_category, product_name, sales, quantity, discount, profit, ship_days,
 profit_margin);

-- 0. 导入检查
SELECT
    COUNT(*) AS row_count,
    MIN(order_date) AS min_order_date,
    MAX(order_date) AS max_order_date,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit
FROM superstore_orders_clean;

-- 1. 年度经营总览
SELECT
    YEAR(order_date) AS order_year,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / SUM(sales), 4) AS profit_margin,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM superstore_orders_clean
GROUP BY YEAR(order_date)
ORDER BY order_year;

-- 2. 月度销售额、利润和环比
WITH monthly AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS order_month,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        SUM(profit) / SUM(sales) AS profit_margin
    FROM superstore_orders_clean
    GROUP BY DATE_FORMAT(order_date, '%Y-%m')
),
monthly_with_lag AS (
    SELECT
        order_month,
        total_sales,
        total_profit,
        profit_margin,
        LAG(total_sales) OVER (ORDER BY order_month) AS last_month_sales,
        LAG(total_profit) OVER (ORDER BY order_month) AS last_month_profit
    FROM monthly
)
SELECT
    order_month,
    ROUND(total_sales, 2) AS total_sales,
    ROUND(total_profit, 2) AS total_profit,
    ROUND(profit_margin, 4) AS profit_margin,
    ROUND((total_sales - last_month_sales) / NULLIF(last_month_sales, 0), 4) AS sales_mom_growth,
    ROUND((total_profit - last_month_profit) / NULLIF(last_month_profit, 0), 4) AS profit_mom_growth
FROM monthly_with_lag
ORDER BY order_month;

-- 3. 区域利润表现
SELECT
    region,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / SUM(sales), 4) AS profit_margin
FROM superstore_orders_clean
GROUP BY region
ORDER BY total_profit;

-- 4. 子品类利润表现
SELECT
    sub_category,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / SUM(sales), 4) AS profit_margin
FROM superstore_orders_clean
GROUP BY sub_category
ORDER BY total_profit;

-- 5. 每个区域销售额 Top 3 子品类
SELECT *
FROM (
    SELECT
        region,
        sub_category,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        RANK() OVER (
            PARTITION BY region
            ORDER BY SUM(sales) DESC
        ) AS sales_rank
    FROM superstore_orders_clean
    GROUP BY region, sub_category
) t
WHERE sales_rank <= 3
ORDER BY region, sales_rank;

-- 6. 折扣区间利润表现
SELECT
    CASE
        WHEN discount = 0 THEN '0'
        WHEN discount <= 0.1 THEN '0-10%'
        WHEN discount <= 0.2 THEN '10%-20%'
        WHEN discount <= 0.3 THEN '20%-30%'
        ELSE '>30%'
    END AS discount_band,
    COUNT(*) AS row_count,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / SUM(sales), 4) AS profit_margin,
    ROUND(SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS loss_rate
FROM superstore_orders_clean
GROUP BY discount_band
ORDER BY
    CASE discount_band
        WHEN '0' THEN 1
        WHEN '0-10%' THEN 2
        WHEN '10%-20%' THEN 3
        WHEN '20%-30%' THEN 4
        ELSE 5
    END;

-- 7. 高折扣亏损子品类
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / SUM(sales), 4) AS profit_margin
FROM superstore_orders_clean
WHERE discount > 0.3
GROUP BY category, sub_category
ORDER BY total_profit;

-- 8. 客户利润贡献 Top 20
SELECT
    customer_id,
    customer_name,
    segment,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / SUM(sales), 4) AS profit_margin,
    ROUND(AVG(discount), 4) AS avg_discount,
    RANK() OVER (ORDER BY SUM(profit) DESC) AS profit_rank
FROM superstore_orders_clean
GROUP BY customer_id, customer_name, segment
ORDER BY total_profit DESC
LIMIT 20;

-- 9. 高销售但亏损客户
SELECT
    customer_id,
    customer_name,
    segment,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / SUM(sales), 4) AS profit_margin,
    ROUND(AVG(discount), 4) AS avg_discount
FROM superstore_orders_clean
GROUP BY customer_id, customer_name, segment
HAVING total_sales >= 3000
   AND total_profit < 0
ORDER BY total_sales DESC;

-- 10. RFM 客户分层明细
WITH customer_rfm AS (
    SELECT
        customer_id,
        customer_name,
        segment,
        DATEDIFF((SELECT MAX(order_date) FROM superstore_orders_clean), MAX(order_date)) AS recency_days,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(sales) AS monetary,
        SUM(profit) AS total_profit,
        AVG(discount) AS avg_discount
    FROM superstore_orders_clean
    GROUP BY customer_id, customer_name, segment
),
rfm_scores AS (
    SELECT
        customer_rfm.*,
        6 - NTILE(5) OVER (ORDER BY recency_days) AS r_score,
        NTILE(5) OVER (ORDER BY frequency) AS f_score,
        NTILE(5) OVER (ORDER BY monetary) AS m_score
    FROM customer_rfm
),
rfm_segments AS (
    SELECT
        *,
        CONCAT(r_score, f_score, m_score) AS rfm_score,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN '高价值客户'
            WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 THEN '重点发展客户'
            WHEN r_score >= 4 AND f_score <= 2 THEN '新近低频客户'
            WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN '流失风险客户'
            WHEN m_score >= 4 AND total_profit < 0 THEN '高消费低利润客户'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN '低价值沉默客户'
            ELSE '普通客户'
        END AS customer_type
    FROM rfm_scores
)
SELECT
    customer_id,
    customer_name,
    segment,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary,
    ROUND(total_profit, 2) AS total_profit,
    ROUND(avg_discount, 4) AS avg_discount,
    r_score,
    f_score,
    m_score,
    rfm_score,
    customer_type
FROM rfm_segments
ORDER BY monetary DESC
LIMIT 50;

-- 11. RFM 客户分层汇总
WITH customer_rfm AS (
    SELECT
        customer_id,
        customer_name,
        segment,
        DATEDIFF((SELECT MAX(order_date) FROM superstore_orders_clean), MAX(order_date)) AS recency_days,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(sales) AS monetary,
        SUM(profit) AS total_profit,
        AVG(discount) AS avg_discount
    FROM superstore_orders_clean
    GROUP BY customer_id, customer_name, segment
),
rfm_scores AS (
    SELECT
        customer_rfm.*,
        6 - NTILE(5) OVER (ORDER BY recency_days) AS r_score,
        NTILE(5) OVER (ORDER BY frequency) AS f_score,
        NTILE(5) OVER (ORDER BY monetary) AS m_score
    FROM customer_rfm
),
rfm_segments AS (
    SELECT
        *,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN '高价值客户'
            WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 THEN '重点发展客户'
            WHEN r_score >= 4 AND f_score <= 2 THEN '新近低频客户'
            WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN '流失风险客户'
            WHEN m_score >= 4 AND total_profit < 0 THEN '高消费低利润客户'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN '低价值沉默客户'
            ELSE '普通客户'
        END AS customer_type
    FROM rfm_scores
)
SELECT
    customer_type,
    COUNT(*) AS customer_count,
    ROUND(SUM(monetary), 2) AS total_sales,
    ROUND(SUM(total_profit), 2) AS total_profit,
    ROUND(SUM(total_profit) / SUM(monetary), 4) AS profit_margin,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(frequency), 1) AS avg_frequency,
    ROUND(AVG(avg_discount), 4) AS avg_discount
FROM rfm_segments
GROUP BY customer_type
ORDER BY total_sales DESC;
