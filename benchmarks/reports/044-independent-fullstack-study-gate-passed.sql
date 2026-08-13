-- SQLite JSON1 audit queries for the canonical iteration-044 raw artifact.
-- Bind readfile('benchmarks/fullstack_agent_044_raw.json') as :raw_json.

WITH raw AS (SELECT json(:raw_json) AS document),
rows AS (
  SELECT value AS row
  FROM raw, json_each(raw.document, '$.results')
)
SELECT
  json_extract(row, '$.language') AS language,
  count(*) AS sessions,
  sum(json_extract(row, '$.hidden_success')) AS hidden_successes,
  sum(json_extract(row, '$.first_public_check_success')) AS first_check_successes,
  sum(json_extract(row, '$.repair_turns')) AS repair_turns
FROM rows
GROUP BY language
ORDER BY language;

WITH raw AS (SELECT json(:raw_json) AS document),
rows AS (
  SELECT value AS row
  FROM raw, json_each(raw.document, '$.results')
),
ordered AS (
  SELECT
    json_extract(row, '$.language') AS language,
    json_extract(row, '$.total_tokens') AS tokens,
    json_extract(row, '$.elapsed_seconds') AS seconds,
    row_number() OVER (
      PARTITION BY json_extract(row, '$.language')
      ORDER BY json_extract(row, '$.total_tokens')
    ) AS token_rank,
    row_number() OVER (
      PARTITION BY json_extract(row, '$.language')
      ORDER BY json_extract(row, '$.elapsed_seconds')
    ) AS elapsed_rank
  FROM rows
)
SELECT
  language,
  avg(tokens) FILTER (WHERE token_rank IN (12, 13)) AS median_tokens,
  avg(seconds) FILTER (WHERE elapsed_rank IN (12, 13)) AS median_seconds
FROM ordered
GROUP BY language
ORDER BY language;

WITH raw AS (SELECT json(:raw_json) AS document),
attempts AS (
  SELECT attempt.value AS attempt
  FROM raw,
       json_each(raw.document, '$.results') AS result,
       json_each(result.value, '$.public_attempts') AS attempt
),
public_cases AS (
  SELECT case_row.value AS case_row
  FROM attempts, json_each(attempts.attempt, '$.cases') AS case_row
),
hidden_cases AS (
  SELECT case_row.value AS case_row
  FROM raw,
       json_each(raw.document, '$.results') AS result,
       json_each(result.value, '$.hidden_judgment.cases') AS case_row
)
SELECT
  (SELECT count(*) FROM attempts) AS public_attempts,
  (SELECT count(*) FROM public_cases) AS public_cases,
  (SELECT sum(json_extract(case_row, '$.pass')) FROM public_cases) AS public_case_passes,
  (SELECT count(*) FROM hidden_cases) AS hidden_cases,
  (SELECT sum(json_extract(case_row, '$.pass')) FROM hidden_cases) AS hidden_case_passes;

WITH raw AS (SELECT json(:raw_json) AS document),
journal AS (
  SELECT value AS entry
  FROM raw, json_each(raw.document, '$.journal')
),
capacity AS (
  SELECT value AS check_row
  FROM raw, json_each(raw.document, '$.scratch_capacity_checks')
)
SELECT
  count(*) AS cleanup_records,
  sum(json_extract(entry, '$.cleanup.status') = 'removed') AS removed,
  max(json_extract(entry, '$.cleanup.workspace_bytes')) AS peak_workspace_bytes,
  (SELECT count(*) FROM capacity) AS capacity_checks,
  (SELECT min(json_extract(check_row, '$.filesystem_free_bytes')) FROM capacity)
    AS minimum_free_bytes
FROM journal;

WITH raw AS (SELECT json(:raw_json) AS document),
conditions AS (
  SELECT key AS condition, value AS passed
  FROM raw, json_each(raw.document, '$.summary.primary_gate.conditions')
)
SELECT condition, passed
FROM conditions
ORDER BY condition;
