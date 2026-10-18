-- Step 3: profile one table by hand. Replace {{table}}, {{col}}, {{key_cols}}, {{time_col}}.

-- 3a. Size
SELECT COUNT(*) AS n_rows FROM {{table}};

-- 3b. Is {{key_cols}} the grain? (n_rows = n_distinct and n_null = 0  =>  yes)
SELECT COUNT(*)                                    AS n_rows,
       COUNT(DISTINCT {{key_cols}})                AS n_distinct,   -- for composite keys use a subquery on SELECT DISTINCT a, b
       COUNT(*) - COUNT({{key_cols}})              AS n_null
FROM {{table}};

-- 3c. Which keys are duplicated, and by how much
SELECT {{key_cols}}, COUNT(*) AS n
FROM {{table}}
GROUP BY {{key_cols}}
HAVING COUNT(*) > 1
ORDER BY n DESC
LIMIT 20;

-- 3d. One column: nulls, distincts, range
SELECT COUNT(*) - COUNT({{col}}) AS n_null,
       COUNT(DISTINCT {{col}})   AS n_distinct,
       MIN({{col}}) AS min_v, MAX({{col}}) AS max_v
FROM {{table}};

-- 3e. Time coverage by month (look for gaps and cliffs)
SELECT DATE_TRUNC('month', {{time_col}}) AS month, COUNT(*) AS n
FROM {{table}}
GROUP BY 1
ORDER BY 1;

-- 3f. Freshness: event time vs load time
SELECT MAX({{time_col}}) AS latest_event, MAX(loaded_at) AS latest_load FROM {{table}};

-- 3g. Top values of a categorical column (placeholders, case variants)
SELECT {{col}}, COUNT(*) AS n FROM {{table}} GROUP BY 1 ORDER BY n DESC LIMIT 25;
