-- World Happiness Report 数据分析 SQL
-- 数据表：world_happiness

-- 1. 整体数据规模
select
    count(1) as total_rows,
    count(distinct country) as countries,
    min(year) as min_year,
    max(year) as max_year,
    avg(score) as avg_score
from world_happiness;

-- 2. 2019 年幸福指数 Top 10
select
    rank,
    country,
    region,
    score,
    gdp,
    social_support,
    life_expectancy,
    freedom,
    generosity,
    corruption
from world_happiness
where year = 2019
order by score desc
limit 10;

-- 3. 2019 年幸福指数 Bottom 10
select
    rank,
    country,
    region,
    score,
    gdp,
    social_support,
    life_expectancy,
    freedom,
    generosity,
    corruption
from world_happiness
where year = 2019
order by score asc
limit 10;

-- 4. 年度平均幸福分数趋势
select
    year,
    count(distinct country) as countries,
    avg(score) as avg_score
from world_happiness
group by year
order by year;

-- 5. 2019 年地区表现
select
    region,
    count(distinct country) as countries,
    avg(score) as avg_score,
    avg(gdp) as avg_gdp,
    avg(social_support) as avg_social_support,
    avg(life_expectancy) as avg_life_expectancy
from world_happiness
where year = 2019
  and region is not null
group by region
order by avg_score desc;

-- 6. 2015-2019 共同国家分数变化
select
    a.country,
    a.score as score_2015,
    b.score as score_2019,
    b.score - a.score as delta_2019_vs_2015
from world_happiness a
join world_happiness b
  on a.country = b.country
where a.year = 2015
  and b.year = 2019
order by delta_2019_vs_2015 desc;

-- 7. 缺少地区信息的记录
select
    year,
    country
from world_happiness
where region is null
order by country, year;
