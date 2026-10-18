-- Step 8: "why is there no data / no signal?" Replace {{table}}, {{date_col}}, {{value_col}}, {{cat_col}}.

-- D1. Date range and sentinels
SELECT MIN({{date_col}}) AS min_d, MAX({{date_col}}) AS max_d,
       SUM(CASE WHEN {{date_col}} < DATE '1971-01-01' OR {{date_col}} > DATE '2100-01-01' THEN 1 ELSE 0 END) AS sentinel_rows,
       SUM(CASE WHEN {{date_col}} > CURRENT_DATE THEN 1 ELSE 0 END) AS future_rows
FROM {{table}};

-- D2. Monthly volume + value coverage (gaps, cliffs, trend breaks)
SELECT DATE_TRUNC('month', {{date_col}}) AS month, COUNT(*) AS n,
       COUNT({{value_col}}) AS n_value, AVG({{value_col}}) AS avg_value
FROM {{table}} GROUP BY 1 ORDER BY 1;

-- D3. Percentiles (is the column degenerate? are outliers dominating?)
SELECT PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY {{value_col}}) AS p01,
       PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {{value_col}}) AS p25,
       PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {{value_col}}) AS p50,
       PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {{value_col}}) AS p75,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {{value_col}}) AS p95,
       PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY {{value_col}}) AS p99
FROM {{table}};

-- D4. Nulls and zeros
SELECT SUM(CASE WHEN {{value_col}} IS NULL THEN 1 ELSE 0 END) AS nulls,
       SUM(CASE WHEN {{value_col}} = 0 THEN 1 ELSE 0 END)     AS zeros,
       COUNT(*) AS n
FROM {{table}};

-- D5. Stray predicates: what does each value of the column you filter on actually look like?
SELECT {{cat_col}}, LOWER(TRIM({{cat_col}})) AS normalised, COUNT(*) AS n
FROM {{table}} GROUP BY 1, 2 ORDER BY n DESC;

-- D6. How many rows does your predicate really keep?
SELECT COUNT(*) AS total,
       SUM(CASE WHEN {{your_predicate}} THEN 1 ELSE 0 END) AS kept
FROM {{table}};
