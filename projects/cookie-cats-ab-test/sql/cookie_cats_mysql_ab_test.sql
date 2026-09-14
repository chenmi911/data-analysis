CREATE DATABASE IF NOT EXISTS cookie_cats_ab_test DEFAULT CHARACTER SET utf8mb4;
USE cookie_cats_ab_test;

DROP VIEW IF EXISTS v_retention_ab_test;
DROP TABLE IF EXISTS cookie_cats;
DROP TABLE IF EXISTS cookie_cats_raw;

CREATE TABLE cookie_cats_raw (
    userid BIGINT,
    version VARCHAR(20),
    sum_gamerounds INT,
    retention_1_raw VARCHAR(10),
    retention_7_raw VARCHAR(10)
);

LOAD DATA LOCAL INFILE 'projects/cookie-cats-ab-test/data/raw/cookie_cats.csv'
INTO TABLE cookie_cats_raw
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(userid, version, sum_gamerounds, retention_1_raw, retention_7_raw);

CREATE TABLE cookie_cats AS
SELECT
    userid,
    version,
    sum_gamerounds,
    CASE LOWER(TRIM(BOTH '\r' FROM TRIM(retention_1_raw)))
        WHEN 'true' THEN 1
        WHEN 'false' THEN 0
        ELSE NULL
    END AS retention_1,
    CASE LOWER(TRIM(BOTH '\r' FROM TRIM(retention_7_raw)))
        WHEN 'true' THEN 1
        WHEN 'false' THEN 0
        ELSE NULL
    END AS retention_7
FROM cookie_cats_raw;

-- 0. 导入和数据质量检查
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT userid) AS unique_users,
    COUNT(*) - COUNT(DISTINCT userid) AS duplicate_userid_rows,
    SUM(userid IS NULL) AS missing_userid,
    SUM(version IS NULL) AS missing_version,
    SUM(sum_gamerounds IS NULL) AS missing_sum_gamerounds,
    SUM(retention_1 IS NULL) AS missing_retention_1,
    SUM(retention_7 IS NULL) AS missing_retention_7,
    MIN(sum_gamerounds) AS min_sum_gamerounds,
    MAX(sum_gamerounds) AS max_sum_gamerounds
FROM cookie_cats;

-- 1. 实验分组比例
SELECT
    version,
    COUNT(*) AS users,
    ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 6) AS user_share
FROM cookie_cats
GROUP BY version
ORDER BY version;

-- 2. 留存率
SELECT
    version,
    COUNT(*) AS users,
    ROUND(AVG(retention_1), 6) AS retention_1_rate,
    ROUND(AVG(retention_7), 6) AS retention_7_rate
FROM cookie_cats
GROUP BY version
ORDER BY version;

-- 3. A/B 留存比例检验

CREATE OR REPLACE VIEW v_retention_ab_test AS
WITH metric_long AS (
    SELECT 'retention_1' AS metric, version, retention_1 AS retained
    FROM cookie_cats
    UNION ALL
    SELECT 'retention_7' AS metric, version, retention_7 AS retained
    FROM cookie_cats
),
group_stats AS (
    SELECT
        metric,
        SUM(CASE WHEN version = 'gate_30' THEN retained ELSE 0 END) AS control_success,
        SUM(CASE WHEN version = 'gate_40' THEN retained ELSE 0 END) AS treatment_success,
        SUM(CASE WHEN version = 'gate_30' THEN 1 ELSE 0 END) AS control_n,
        SUM(CASE WHEN version = 'gate_40' THEN 1 ELSE 0 END) AS treatment_n
    FROM metric_long
    GROUP BY metric
),
rate_stats AS (
    SELECT
        metric,
        control_success,
        treatment_success,
        control_n,
        treatment_n,
        control_success / control_n AS control_rate,
        treatment_success / treatment_n AS treatment_rate
    FROM group_stats
),
test_stats AS (
    SELECT
        metric,
        control_success,
        treatment_success,
        control_n,
        treatment_n,
        control_rate,
        treatment_rate,
        treatment_rate - control_rate AS absolute_diff_treatment_minus_control,
        (treatment_rate - control_rate) / control_rate AS relative_diff_vs_control,
        (
            (treatment_success + control_success) / (treatment_n + control_n)
        ) AS pooled_rate,
        SQRT(
            control_rate * (1 - control_rate) / control_n
            + treatment_rate * (1 - treatment_rate) / treatment_n
        ) AS ci_se
    FROM rate_stats
),
z_stats AS (
    SELECT
        *,
        absolute_diff_treatment_minus_control / SQRT(
            pooled_rate * (1 - pooled_rate) * (1 / control_n + 1 / treatment_n)
        ) AS z_score
    FROM test_stats
),
normal_approx AS (
    SELECT
        *,
        ABS(z_score) AS abs_z,
        1 / (1 + 0.2316419 * ABS(z_score)) AS t_value,
        EXP(-POW(ABS(z_score), 2) / 2) / SQRT(2 * PI()) AS normal_density
    FROM z_stats
),
p_value_calc AS (
    SELECT
        *,
        2 * normal_density * (
            0.319381530 * t_value
            - 0.356563782 * POW(t_value, 2)
            + 1.781477937 * POW(t_value, 3)
            - 1.821255978 * POW(t_value, 4)
            + 1.330274429 * POW(t_value, 5)
        ) AS p_value
    FROM normal_approx
)
SELECT
    metric,
    control_n,
    treatment_n,
    control_success,
    treatment_success,
    ROUND(control_rate, 6) AS control_rate,
    ROUND(treatment_rate, 6) AS treatment_rate,
    ROUND(absolute_diff_treatment_minus_control, 6) AS absolute_diff_treatment_minus_control,
    ROUND(relative_diff_vs_control, 6) AS relative_diff_vs_control,
    ROUND(z_score, 6) AS z_score,
    ROUND(p_value, 6) AS p_value,
    ROUND(absolute_diff_treatment_minus_control - 1.96 * ci_se, 6) AS ci95_low,
    ROUND(absolute_diff_treatment_minus_control + 1.96 * ci_se, 6) AS ci95_high
FROM p_value_calc;

SELECT * FROM v_retention_ab_test ORDER BY metric;

-- 4. 游戏局数描述统计
WITH ordered AS (
    SELECT
        version,
        sum_gamerounds,
        ROW_NUMBER() OVER (PARTITION BY version ORDER BY sum_gamerounds) AS rn,
        COUNT(*) OVER (PARTITION BY version) AS n
    FROM cookie_cats
),
percentiles AS (
    SELECT
        version,
        MAX(CASE WHEN rn = CEIL(0.50 * n) THEN sum_gamerounds END) AS p50_gamerounds,
        MAX(CASE WHEN rn = CEIL(0.75 * n) THEN sum_gamerounds END) AS p75_gamerounds,
        MAX(CASE WHEN rn = CEIL(0.90 * n) THEN sum_gamerounds END) AS p90_gamerounds,
        MAX(CASE WHEN rn = CEIL(0.95 * n) THEN sum_gamerounds END) AS p95_gamerounds,
        MAX(CASE WHEN rn = CEIL(0.99 * n) THEN sum_gamerounds END) AS p99_gamerounds
    FROM ordered
    GROUP BY version
),
summary AS (
    SELECT
        version,
        COUNT(*) AS users,
        AVG(sum_gamerounds) AS mean_gamerounds,
        MIN(sum_gamerounds) AS min_gamerounds,
        MAX(sum_gamerounds) AS max_gamerounds
    FROM cookie_cats
    GROUP BY version
)
SELECT
    s.version,
    s.users,
    ROUND(s.mean_gamerounds, 4) AS mean_gamerounds,
    p.p50_gamerounds,
    p.p75_gamerounds,
    p.p90_gamerounds,
    p.p95_gamerounds,
    p.p99_gamerounds,
    s.min_gamerounds,
    s.max_gamerounds
FROM summary s
JOIN percentiles p
    ON s.version = p.version
ORDER BY s.version;

-- 5. 游戏局数均值差异
WITH group_mean AS (
    SELECT
        version,
        AVG(sum_gamerounds) AS mean_gamerounds
    FROM cookie_cats
    GROUP BY version
)
SELECT
    MAX(CASE WHEN version = 'gate_40' THEN mean_gamerounds END)
    - MAX(CASE WHEN version = 'gate_30' THEN mean_gamerounds END)
        AS treatment_minus_control_mean_gamerounds
FROM group_mean;

-- 6. 业务决策
SELECT
    metric,
    control_n,
    treatment_n,
    ROUND(control_rate * 100, 2)      AS control_pct,
    ROUND(treatment_rate * 100, 2)    AS treatment_pct,
    ROUND(absolute_diff_treatment_minus_control * 100, 2) AS diff_pp,  -- gate_40 - gate_30
    ROUND(relative_diff_vs_control * 100, 2)               AS rel_diff_pct,
    ROUND(z_score, 3)        AS z_score,
    ROUND(p_value, 5)        AS p_value,
    ROUND(ci95_low * 100, 2)  AS ci95_low_pp,
    ROUND(ci95_high * 100, 2) AS ci95_high_pp,
    -- 单指标门槛标记：仅回答"该指标是否构成显著负/正证据"，不下总体结论
    CASE
        WHEN p_value < 0.05 AND ci95_high < 0 THEN 'worse (sig)'
        WHEN p_value < 0.05 AND ci95_low  > 0 THEN 'better (sig)'
        ELSE 'no sig. difference'
    END AS per_metric_reading
FROM v_retention_ab_test
ORDER BY metric;

WITH ordered AS (
    SELECT
        version,
        sum_gamerounds,
        ROW_NUMBER() OVER (PARTITION BY version ORDER BY sum_gamerounds) AS rn,
        COUNT(*) OVER (PARTITION BY version) AS n
    FROM cookie_cats
),
grp AS (
    SELECT
        version,
        COUNT(*) AS users,
        AVG(sum_gamerounds) AS mean_rounds,
        MAX(CASE WHEN rn = CEIL(0.50 * n) THEN sum_gamerounds END) AS p50,
        MAX(CASE WHEN rn = CEIL(0.90 * n) THEN sum_gamerounds END) AS p90,
        MAX(CASE WHEN rn = CEIL(0.99 * n) THEN sum_gamerounds END) AS p99
    FROM ordered
    GROUP BY version
)
SELECT
    ROUND(MAX(CASE WHEN version = 'gate_40' THEN mean_rounds END)
        - MAX(CASE WHEN version = 'gate_30' THEN mean_rounds END), 2) AS mean_diff_rounds,
    MAX(CASE WHEN version = 'gate_40' THEN p50 END)
        - MAX(CASE WHEN version = 'gate_30' THEN p50 END) AS p50_diff_rounds,
    MAX(CASE WHEN version = 'gate_40' THEN p90 END)
        - MAX(CASE WHEN version = 'gate_30' THEN p90 END) AS p90_diff_rounds,
    MAX(CASE WHEN version = 'gate_40' THEN p99 END)
        - MAX(CASE WHEN version = 'gate_30' THEN p99 END) AS p99_diff_rounds
FROM grp;

SELECT
    version,
    COUNT(*) AS users,
    ROUND(SUM(CASE
        WHEN sum_gamerounds >= (CASE WHEN version = 'gate_30' THEN 30
                                     WHEN version = 'gate_40' THEN 40 END)
        THEN 1 ELSE 0 END) / COUNT(*), 4) AS share_reached_own_gate
FROM cookie_cats
GROUP BY version
ORDER BY version;
