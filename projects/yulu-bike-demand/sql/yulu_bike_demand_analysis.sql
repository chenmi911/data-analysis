-- Yulu case study: load the hourly bike-sharing file and produce summary tables.
-- Welch tests and the chi-square test are calculated in the Python script.

CREATE DATABASE IF NOT EXISTS practice DEFAULT CHARACTER SET utf8mb4;
USE practice;

DROP TABLE IF EXISTS yulu_bike_hourly;

CREATE TABLE yulu_bike_hourly (
    datetime DATETIME,
    season TINYINT,
    holiday TINYINT,
    workingday TINYINT,
    weather TINYINT,
    temp DECIMAL(6, 3),
    atemp DECIMAL(6, 3),
    humidity TINYINT,
    windspeed DECIMAL(7, 4),
    casual INT,
    registered INT,
    `count` INT
);

LOAD DATA LOCAL INFILE 'projects/yulu-bike-demand/data/raw/yulu_bike_sharing_dataset.csv'
INTO TABLE yulu_bike_hourly
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(datetime, season, holiday, workingday, weather, temp, atemp, humidity,
 windspeed, casual, registered, `count`);

-- Confirm period, row count, and reconciliation of rental totals.
SELECT
    COUNT(*) AS hourly_rows,
    MIN(datetime) AS first_hour,
    MAX(datetime) AS last_hour,
    SUM(`count` <> casual + registered) AS count_mismatch_rows
FROM yulu_bike_hourly;

-- Daily totals for the workingday comparison in Python.
WITH daily AS (
    SELECT
        DATE(datetime) AS ride_date,
        MIN(workingday) AS workingday,
        SUM(`count`) AS daily_rentals
    FROM yulu_bike_hourly
    GROUP BY DATE(datetime)
)
SELECT
    workingday,
    COUNT(*) AS days,
    ROUND(AVG(daily_rentals), 1) AS mean_daily_rentals,
    ROUND(STDDEV_SAMP(daily_rentals), 1) AS sd_daily_rentals
FROM daily
GROUP BY workingday
ORDER BY workingday;

-- Season-level summaries; the Python Welch ANOVA tests the means.
SELECT
    season,
    COUNT(*) AS hours,
    ROUND(AVG(`count`), 2) AS mean_hourly_rentals,
    ROUND(STDDEV_SAMP(`count`), 2) AS sd_hourly_rentals
FROM yulu_bike_hourly
GROUP BY season
ORDER BY season;

-- Weather category 4 has one observation; Python inference covers categories 1-3.
SELECT
    weather,
    COUNT(*) AS hours,
    ROUND(AVG(`count`), 2) AS mean_hourly_rentals,
    ROUND(STDDEV_SAMP(`count`), 2) AS sd_hourly_rentals
FROM yulu_bike_hourly
GROUP BY weather
ORDER BY weather;

-- Season/weather counts for the chi-square test; weather 4 is excluded.
SELECT season, weather, COUNT(*) AS hours
FROM yulu_bike_hourly
WHERE weather IN (1, 2, 3)
GROUP BY season, weather
ORDER BY season, weather;
