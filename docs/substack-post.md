# Your first week at a new data job: build a SCHEMA.md before you write a single query

_Draft for Substack. Replace the bracketed bits with your own war stories; the repo link goes at the end._

---

The first time an AI wrote me a query against a warehouse I'd just joined, it was beautiful, confident and wrong.
One join, on a column that *looked* like the customer id, from a table that was a stale copy of the table I wanted.
The numbers were plausible. That's what made it dangerous.

The fix wasn't a better prompt. It was a better **grounding document**: a `SCHEMA.md` that says, for every table I care about,
what one row is, what identifies it, how it relates to its neighbours, which timestamp means what, and what's broken.

Here's the process I use whenever I join a company. It takes about a week to get a useful baseline, and every
query after that is faster and safer.

## 1. Find the architecture before the tables

Is there a customer data platform? Which layer is clean (raw → silver → gold)? Is there a semantic layer whose metric
definitions are the company's "official" numbers? Query from the **highest layer that still has the grain you need**.

## 2. Pick 5–6 domains from the business, not the catalog

How does the company make money? Walk the chain from first touch to revenue to churn. Group it into five or six
domains (customer, orders, billing, behaviour, support…) each with one entity and one unique id. Now you know which
tables to read first and which to ignore.

## 3. Profile each table for its grain

"What is one row?" is the most important question in analytics. Test it: `COUNT(*) = COUNT(DISTINCT key)`. Record the
primary key, the time columns (event time ≠ load time), the null profile, the JSON fields. When the grain is
**violated**, write that down. [Your story: the table that was "one row per order" and wasn't.]

## 4. Prove the relationships

Every foreign key gets five checks: is the parent key unique, what's the match rate, what do the orphans look like,
how many nulls, do the types agree. In my demo warehouse, 3% of events point at customers that don't exist. Without
that line in SCHEMA.md, an `INNER JOIN` silently drops them and nobody ever knows.

## 5. Grow the doc, one verified table at a time

Don't profile the warehouse; profile the questions you're asked. Machine-measured facts go in fenced regions, your
notes stay untouched, and a linter tells you when it's stale or contradicting itself.

## 6. Plan before SQL

Here's where the AI comes in, with rules. Before any SQL, it writes a plan: the business question, the business
parameters, the data parameters **per table** (which time column, which window, because they differ), the anchor
timestamp, the join order, the cardinality of every join, and the row count it expects at each step. *Then* it writes
a structured query with a `params` block, a spine, one pre-aggregated CTE per source.

## 7. Assert before you analyse

Grain unique. Row count equals the spine. No feature timestamp after the anchor. Sane null rates. My intentionally
sloppy demo query fails two of these: it fans out to 1.5 million rows and peeks 356,444 rows into the future. The
fixed one passes 6 of 6.

## 8. Is there signal? And if not, why not?

A null result is only a finding after you've ruled out a broken experiment. Check date ranges and gaps (my demo has a
missing August), percentiles (constant columns, one value holding half the mass), nulls and zero fills, stray
predicates (`'Open'` vs `'open '`, or a `WHERE` that quietly removes everything), trend breaks, duplicates, power.

---

All of it is open source: a CLI (`schemakit`) that does the measuring, plain-SQL equivalents of every check,
copy-paste prompts for each stage, an `AGENTS.md` so your AI follows the rules, and a demo warehouse with planted traps
so you can see each one get caught.

**Repo:** [link]

If you try it on your own warehouse, tell me what trap it found that I didn't plant.
