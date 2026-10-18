-- Step 4: validate child.fk -> parent.pk. Replace {{child}}, {{fk}}, {{parent}}, {{pk}}.

-- 4a. Is the parent key unique? (must be, or joins fan out)
SELECT COUNT(*) AS parent_rows, COUNT(DISTINCT {{pk}}) AS parent_distinct FROM {{parent}};

-- 4b. Match rate and orphans
SELECT COUNT(*)                                             AS child_rows,
       COUNT(c.{{fk}})                                      AS child_non_null,
       COUNT(p.{{pk}})                                      AS matched,
       COUNT(c.{{fk}}) - COUNT(p.{{pk}})                    AS orphans,
       100.0 * COUNT(p.{{pk}}) / NULLIF(COUNT(c.{{fk}}), 0) AS match_pct
FROM {{child}} c
LEFT JOIN {{parent}} p ON p.{{pk}} = c.{{fk}};

-- 4c. What do the orphans look like?
SELECT c.{{fk}}, COUNT(*) AS n
FROM {{child}} c
LEFT JOIN {{parent}} p ON p.{{pk}} = c.{{fk}}
WHERE c.{{fk}} IS NOT NULL AND p.{{pk}} IS NULL
GROUP BY 1 ORDER BY n DESC LIMIT 20;

-- 4d. Parents never referenced (dead dimension rows, or a missing child feed)
SELECT COUNT(*) AS unreferenced_parents
FROM {{parent}} p
WHERE NOT EXISTS (SELECT 1 FROM {{child}} c WHERE c.{{fk}} = p.{{pk}});

-- 4e. Fan-out test: rows before vs after the join (must be equal for a many:1 join)
SELECT (SELECT COUNT(*) FROM {{child}}) AS before_join,
       (SELECT COUNT(*) FROM {{child}} c LEFT JOIN {{parent}} p ON p.{{pk}} = c.{{fk}}) AS after_join;
