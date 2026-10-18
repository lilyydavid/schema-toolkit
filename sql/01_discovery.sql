-- Step 1: discovery with plain SQL (ANSI information_schema; works on Snowflake, Postgres, Redshift,
-- BigQuery (use `region-xx`.INFORMATION_SCHEMA or dataset.INFORMATION_SCHEMA), Databricks, DuckDB, MySQL).
-- Replace {{schema}} with your schema (or drop the filter to see everything).

-- 1a. Tables and views by schema (spot raw/silver/gold layering)
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY table_schema, table_name;

-- 1b. Columns of a candidate set of tables
SELECT table_schema, table_name, column_name, data_type, ordinal_position
FROM information_schema.columns
WHERE table_schema = '{{schema}}'
ORDER BY table_name, ordinal_position;

-- 1c. Join-key candidates: id/key columns that appear in 2+ tables
SELECT column_name, COUNT(DISTINCT table_schema || '.' || table_name) AS n_tables,
       MIN(data_type) AS min_type, MAX(data_type) AS max_type   -- differing types = cast needed
FROM information_schema.columns
WHERE (LOWER(column_name) LIKE '%\_id' ESCAPE '\' OR LOWER(column_name) LIKE '%\_key' ESCAPE '\')
  AND table_schema = '{{schema}}'
GROUP BY column_name
HAVING COUNT(DISTINCT table_schema || '.' || table_name) > 1
ORDER BY n_tables DESC;

-- 1d. Declared constraints (often missing in warehouses; don't rely on them)
SELECT tc.table_name, tc.constraint_type, kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
WHERE tc.table_schema = '{{schema}}' AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY');
