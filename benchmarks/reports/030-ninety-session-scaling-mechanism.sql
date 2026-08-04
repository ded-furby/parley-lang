.mode list
.separator |

CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_scaling_030_protocol_v1_v0.3.155.json'));

CREATE TEMP VIEW runs AS
SELECT
  CAST(json_extract(run.value, '$.bundle_size') AS INTEGER) AS bundle_size,
  json_extract(run.value, '$.bundle_id') AS bundle_id,
  CAST(json_extract(run.value, '$.replicate') AS INTEGER) AS replicate,
  json_extract(run.value, '$.language') AS language,
  CAST(json_extract(run.value, '$.task_count') AS INTEGER) AS task_count,
  CAST(json_extract(run.value, '$.hidden_task_successes') AS INTEGER) AS hidden_successes,
  CAST(json_extract(run.value, '$.first_public_task_successes') AS INTEGER) AS first_successes,
  CAST(json_extract(run.value, '$.public_check_attempts') AS INTEGER) AS checks,
  CAST(json_extract(run.value, '$.repair_turns') AS INTEGER) AS repairs,
  CAST(json_extract(run.value, '$.total_tokens_per_task') AS REAL) AS tokens_task,
  CAST(json_extract(run.value, '$.elapsed_seconds_per_task') AS REAL) AS seconds_task,
  CAST(json_extract(run.value, '$.check_integrity_ok') AS INTEGER) AS integrity_ok,
  CAST(json_extract(run.value, '$.command_protocol_compliant') AS INTEGER) AS protocol_ok,
  json_extract(run.value, '$.thread_id') AS thread_id,
  run.value AS run_json
FROM raw, json_each(json_extract(raw.document, '$.results')) AS run;

CREATE TEMP VIEW scale_summary AS
SELECT
  CAST(json_extract(row.value, '$.bundle_size') AS INTEGER) AS bundle_size,
  CASE json_extract(row.value, '$.language') WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  CAST(json_extract(row.value, '$.sessions') AS INTEGER) AS sessions,
  CAST(json_extract(row.value, '$.assigned_tasks') AS INTEGER) AS assignments,
  CAST(json_extract(row.value, '$.hidden_task_successes') AS INTEGER) AS hidden_successes,
  CAST(json_extract(row.value, '$.first_public_task_successes') AS INTEGER) AS first_successes,
  CAST(json_extract(row.value, '$.repair_turns') AS INTEGER) AS repairs,
  CAST(json_extract(row.value, '$.median_total_tokens_per_task') AS REAL) AS median_tokens_task,
  CAST(json_extract(row.value, '$.median_elapsed_seconds_per_task') AS REAL) AS median_seconds_task
FROM raw, json_each(json_extract(raw.document, '$.summary.by_scale')) AS row;

CREATE TEMP VIEW fit_summary AS
WITH points AS (
  SELECT language, 1.0 / bundle_size AS x, median_tokens_task AS y FROM scale_summary
), moments AS (
  SELECT language, AVG(x) AS mx, AVG(y) AS my, AVG(x*y) AS mxy, AVG(x*x) AS mxx FROM points GROUP BY language
), coefficients AS (
  SELECT language, (mxy-mx*my)/(mxx-mx*mx) AS fixed_session_tokens,
         my-((mxy-mx*my)/(mxx-mx*mx))*mx AS residual_task_tokens
  FROM moments
)
SELECT * FROM coefficients;

SELECT 'headline', COUNT(*), SUM(task_count), COUNT(DISTINCT thread_id),
       SUM(first_successes), SUM(hidden_successes), SUM(repairs)
FROM runs;
SELECT 'scale_summary', * FROM scale_summary ORDER BY bundle_size, language;
SELECT 'fit_summary', * FROM fit_summary ORDER BY language;
SELECT 'session_detail', bundle_size, bundle_id, replicate, language, task_count,
       first_successes, hidden_successes, checks, repairs, tokens_task, seconds_task,
       integrity_ok, protocol_ok, thread_id
FROM runs ORDER BY bundle_size, language, replicate, bundle_id;
