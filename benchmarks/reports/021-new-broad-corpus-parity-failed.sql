.mode list
.separator |

CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_broad_021_protocol_v1_v0.3.154.json'));

CREATE TEMP VIEW runs AS
SELECT
  CAST(json_extract(run.value, '$.replicate') AS INTEGER) AS replicate,
  json_extract(run.value, '$.language') AS language,
  CAST(json_extract(run.value, '$.task_count') AS INTEGER) AS task_count,
  CAST(json_extract(run.value, '$.hidden_task_successes') AS INTEGER) AS hidden_successes,
  CAST(json_extract(run.value, '$.first_public_task_successes') AS INTEGER) AS first_successes,
  CAST(json_extract(run.value, '$.public_check_attempts') AS INTEGER) AS checks,
  CAST(json_extract(run.value, '$.repair_turns') AS INTEGER) AS repair_turns,
  CAST(json_extract(run.value, '$.total_tokens_per_task') AS REAL) AS tokens_task,
  CAST(json_extract(run.value, '$.elapsed_seconds_per_task') AS REAL) AS seconds_task,
  CAST(json_extract(run.value, '$.prompt_chars_per_task') AS REAL) AS prompt_chars_task,
  CAST(json_extract(run.value, '$.source_rough_tokens_per_task') AS REAL) AS source_tokens_task,
  CAST(json_extract(run.value, '$.check_integrity_ok') AS INTEGER) AS integrity_ok,
  CAST(json_extract(run.value, '$.command_protocol_compliant') AS INTEGER) AS protocol_ok,
  json_extract(run.value, '$.thread_id') AS thread_id,
  run.value AS run_json
FROM raw, json_each(json_extract(raw.document, '$.results')) AS run;

CREATE TEMP VIEW language_summary AS
SELECT
  CASE json_extract(row.value, '$.language')
    WHEN 'parley' THEN 'Parley'
    WHEN 'python' THEN 'Python'
    WHEN 'rust' THEN 'Rust'
  END AS language,
  CAST(json_extract(row.value, '$.sessions') AS INTEGER) AS sessions,
  CAST(json_extract(row.value, '$.assigned_tasks') AS INTEGER) AS assigned_tasks,
  CAST(json_extract(row.value, '$.hidden_task_successes') AS INTEGER) AS hidden_successes,
  CAST(json_extract(row.value, '$.hidden_task_success_rate') AS REAL) AS hidden_rate,
  CAST(json_extract(row.value, '$.first_public_task_successes') AS INTEGER) AS first_successes,
  CAST(json_extract(row.value, '$.first_public_task_success_rate') AS REAL) AS first_rate,
  CAST(json_extract(row.value, '$.repair_turns') AS INTEGER) AS repair_turns,
  CAST(json_extract(row.value, '$.median_total_tokens_per_task') AS REAL) AS median_tokens_task,
  CAST(json_extract(row.value, '$.weighted_total_tokens_per_task') AS REAL) AS weighted_tokens_task,
  CAST(json_extract(row.value, '$.median_elapsed_seconds_per_task') AS REAL) AS median_seconds_task,
  CAST(json_extract(row.value, '$.median_prompt_chars_per_task') AS REAL) AS prompt_chars_task,
  CAST(json_extract(row.value, '$.median_source_rough_tokens_per_task') AS REAL) AS source_tokens_task
FROM raw, json_each(json_extract(raw.document, '$.summary.by_scale')) AS row;

CREATE TEMP VIEW parley_task_reliability AS
WITH task_rows AS (
  SELECT
    task.key AS task_id,
    json_extract(task.value, '$.task_title') AS task,
    CAST(json_extract(task.value, '$.first_public_check_success') AS INTEGER) AS first_success,
    CAST(json_extract(task.value, '$.hidden_success') AS INTEGER) AS hidden_success
  FROM runs, json_each(json_extract(runs.run_json, '$.task_results')) AS task
  WHERE runs.language = 'parley'
)
SELECT
  task_id,
  task,
  COUNT(*) AS appearances,
  SUM(first_success) AS first_successes,
  COUNT(*) - SUM(first_success) AS first_failures,
  SUM(hidden_success) AS hidden_successes
FROM task_rows
GROUP BY task_id, task
ORDER BY first_failures DESC, task;

CREATE TEMP VIEW first_failures AS
WITH failed AS (
  SELECT
    runs.replicate,
    task.key AS task_id,
    json_extract(task.value, '$.compile_stderr') AS compile_stderr,
    json_extract(runs.run_json, '$.public_attempts[0].sources.' || task.key) AS source
  FROM runs, json_each(json_extract(runs.run_json, '$.public_attempts[0].tasks')) AS task
  WHERE runs.language = 'parley'
    AND CAST(json_extract(task.value, '$.ok') AS INTEGER) = 0
)
SELECT
  replicate,
  task_id,
  CASE
    WHEN compile_stderr LIKE '%"number" is part of Parley%' THEN 'Reserved ordinary identifier number'
    WHEN source LIKE '%repeat while%' THEN 'Unsupported repeat while phrasing'
    WHEN source LIKE '%numbers sorted%' THEN 'Postfix sorted form'
    WHEN source LIKE 'to locate needle%' OR source LIKE 'to absolute of%' THEN 'Multiword function declaration'
    WHEN task_id = 'polynomial_value' THEN 'Undefined local before declaration'
    WHEN source LIKE '%find_position with value of query_input and values%' THEN 'Unparenthesized call / and arguments'
    WHEN source LIKE '%insert incoming at position in values%' THEN 'Unsupported insert statement phrasing'
    ELSE 'Other'
  END AS signature,
  compile_stderr,
  source
FROM failed;

CREATE TEMP VIEW failure_signatures AS
SELECT
  signature,
  COUNT(*) AS events,
  COUNT(DISTINCT task_id) AS affected_tasks
FROM first_failures
GROUP BY signature
ORDER BY events DESC, signature;

CREATE TEMP VIEW headline AS
SELECT
  18 AS sessions,
  216 AS assigned_tasks,
  216 AS hidden_successes,
  1 AS gate_conditions_passed,
  51 AS parley_first,
  8 AS parley_repairs,
  10 AS number_failures,
  5 AS number_task_families,
  ROUND((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Python'), 2) AS python_token_multiple,
  ROUND(100.0 * ((SELECT source_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT source_tokens_task FROM language_summary WHERE language='Rust') - 1), 2) AS source_gap_vs_rust_percent;

SELECT 'language_summary', json_group_array(json_object(
  'language', language, 'sessions', sessions, 'assigned_tasks', assigned_tasks,
  'hidden_successes', hidden_successes, 'hidden_rate', hidden_rate,
  'first_successes', first_successes, 'first_rate', first_rate,
  'repair_turns', repair_turns, 'median_tokens_task', median_tokens_task,
  'weighted_tokens_task', weighted_tokens_task, 'median_seconds_task', median_seconds_task,
  'prompt_chars_task', prompt_chars_task, 'source_tokens_task', source_tokens_task
)) FROM language_summary;

SELECT 'session_detail', json_group_array(json_object(
  'replicate', replicate,
  'language', CASE language WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END,
  'hidden_successes', hidden_successes, 'first_successes', first_successes,
  'checks', checks, 'repair_turns', repair_turns, 'tokens_task', tokens_task,
  'seconds_task', seconds_task, 'prompt_chars_task', prompt_chars_task,
  'source_tokens_task', source_tokens_task, 'integrity_ok', integrity_ok,
  'protocol_ok', protocol_ok
)) FROM runs ORDER BY replicate, language;

SELECT 'parley_task_reliability', json_group_array(json_object(
  'task_id', task_id, 'task', task, 'appearances', appearances,
  'first_successes', first_successes, 'first_failures', first_failures,
  'hidden_successes', hidden_successes
)) FROM parley_task_reliability;

SELECT 'failure_signatures', json_group_array(json_object(
  'signature', signature, 'events', events, 'affected_tasks', affected_tasks
)) FROM failure_signatures;

SELECT 'first_failure_audit', json_group_array(json_object(
  'replicate', replicate, 'task_id', task_id, 'signature', signature,
  'compile_stderr', compile_stderr
)) FROM first_failures ORDER BY replicate, task_id;

SELECT 'headline', json_group_array(json_object(
  'sessions', sessions, 'assigned_tasks', assigned_tasks,
  'hidden_successes', hidden_successes, 'gate_conditions_passed', gate_conditions_passed,
  'parley_first', parley_first, 'parley_repairs', parley_repairs,
  'number_failures', number_failures, 'number_task_families', number_task_families,
  'python_token_multiple', python_token_multiple,
  'source_gap_vs_rust_percent', source_gap_vs_rust_percent
)) FROM headline;
