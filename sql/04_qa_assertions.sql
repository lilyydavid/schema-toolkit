-- Step 7: assertions on your assembled dataset. Wrap your final SELECT as `result` (CTE or view).
-- Every assertion below should return 0 rows / 0. Non-zero = do not trust the dataset.
-- Replace {{key}}, {{anchor_ts}}, {{feature_ts}}, {{expected_n}}.

-- A1. Grain unique
SELECT {{key}}, COUNT(*) AS n FROM result GROUP BY {{key}} HAVING COUNT(*) > 1 LIMIT 20;

-- A2. Population preserved (compare with an independently written spine count)
SELECT (SELECT COUNT(*) FROM result) - {{expected_n}} AS row_diff;

-- A3. No leakage: features must be knowable at the anchor
SELECT COUNT(*) AS leaked_rows FROM result WHERE {{feature_ts}} > {{anchor_ts}};

-- A4. Null rate per column (repeat per column, or generate from information_schema)
SELECT 100.0 * (COUNT(*) - COUNT({{col}})) / COUNT(*) AS null_pct FROM result;

-- A5. Label window does not overlap feature window
SELECT COUNT(*) AS overlap_rows FROM result WHERE {{label_start_ts}} <= {{feature_end_ts}};

-- A6. Negative control: a column that must be uninformative should show no relationship.
-- Compare label mean across deciles of a hash of the key; large spread => leakage or a bug.
SELECT MOD(ABS(HASH({{key}})), 10) AS bucket, AVG({{label}}) AS label_mean, COUNT(*) AS n
FROM result GROUP BY 1 ORDER BY 1;
