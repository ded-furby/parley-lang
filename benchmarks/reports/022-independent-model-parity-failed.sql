.mode list
.separator |

CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_model_split_022_protocol_v1_v0.3.155.json'));

CREATE TEMP TABLE prior_raw(document TEXT NOT NULL);
INSERT INTO prior_raw VALUES (readfile('benchmarks/results/agent_broad_021_protocol_v1_v0.3.154.json'));

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
    CAST(json_extract(task.value, '$.compile_ok') AS INTEGER) AS compile_ok,
    COALESCE(json_extract(task.value, '$.compile_stderr'), '') AS compile_stderr,
    json_extract(runs.run_json, '$.public_attempts[0].sources.' || task.key) AS source
  FROM runs, json_each(json_extract(runs.run_json, '$.public_attempts[0].tasks')) AS task
  WHERE runs.language = 'parley'
    AND CAST(json_extract(task.value, '$.ok') AS INTEGER) = 0
)
SELECT
  replicate,
  task_id,
  CASE
    WHEN source LIKE '% contains key %' THEN 'Unsupported map-key membership phrase'
    WHEN replicate = 1 AND compile_stderr LIKE '%maybe number%' THEN 'Unwrapped numeric input'
    WHEN replicate = 3 AND task_id IN ('matrix_diagonal_difference', 'nearest_pair_gap') THEN 'Unparenthesized prefix/value phrase'
    WHEN task_id = 'nearest_pair_gap' AND source LIKE '%let best be nothing%' THEN 'Bare nothing accumulator'
    WHEN source LIKE '%repeat while%' THEN 'Unsupported repeat while phrasing'
    WHEN task_id = 'binary_search_queries' THEN 'Decimal midpoint used as list position'
    WHEN task_id = 'polynomial_value' AND compile_ok = 1 THEN 'Incorrect polynomial computation'
    ELSE 'Other'
  END AS signature,
  compile_ok,
  compile_stderr,
  source
FROM failed;

CREATE TEMP VIEW failure_signatures AS
SELECT
  signature,
  COUNT(*) AS events,
  COUNT(DISTINCT task_id) AS affected_tasks,
  COUNT(DISTINCT replicate) AS independent_sessions
FROM first_failures
GROUP BY signature
ORDER BY events DESC, signature;

CREATE TEMP VIEW model_comparison AS
SELECT
  '021 sol / Parley 0.3.154' AS experiment,
  CASE json_extract(row.value, '$.language')
    WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  CAST(json_extract(row.value, '$.first_public_task_successes') AS INTEGER) AS first_successes,
  CAST(json_extract(row.value, '$.repair_turns') AS INTEGER) AS repair_turns,
  CAST(json_extract(row.value, '$.median_total_tokens_per_task') AS REAL) AS median_tokens_task,
  CAST(json_extract(row.value, '$.median_elapsed_seconds_per_task') AS REAL) AS median_seconds_task
FROM prior_raw, json_each(json_extract(prior_raw.document, '$.summary.by_scale')) AS row
UNION ALL
SELECT
  '022 terra / Parley 0.3.155' AS experiment,
  language,
  first_successes,
  repair_turns,
  median_tokens_task,
  median_seconds_task
FROM language_summary;

CREATE TEMP VIEW headline AS
SELECT
  18 AS sessions,
  216 AS assigned_tasks,
  216 AS hidden_successes,
  1 AS gate_conditions_passed,
  39 AS parley_first,
  15 AS parley_repairs,
  (SELECT events FROM failure_signatures WHERE signature='Unsupported map-key membership phrase') AS membership_failures,
  (SELECT affected_tasks FROM failure_signatures WHERE signature='Unsupported map-key membership phrase') AS membership_task_families,
  (SELECT COUNT(*) FROM first_failures WHERE compile_stderr LIKE '%"number" is part of Parley%') AS number_failures,
  ROUND((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Python'), 2) AS python_token_multiple,
  ROUND((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Rust'), 2) AS rust_token_multiple,
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
  'signature', signature, 'events', events, 'affected_tasks', affected_tasks,
  'independent_sessions', independent_sessions
)) FROM failure_signatures;

SELECT 'first_failure_audit', json_group_array(json_object(
  'replicate', replicate, 'task_id', task_id, 'signature', signature,
  'compile_ok', compile_ok, 'compile_stderr', compile_stderr
)) FROM first_failures ORDER BY replicate, task_id;

SELECT 'model_comparison', json_group_array(json_object(
  'experiment', experiment, 'language', language, 'first_successes', first_successes,
  'repair_turns', repair_turns, 'median_tokens_task', median_tokens_task,
  'median_seconds_task', median_seconds_task
)) FROM model_comparison;

SELECT 'headline', json_group_array(json_object(
  'sessions', sessions, 'assigned_tasks', assigned_tasks,
  'hidden_successes', hidden_successes, 'gate_conditions_passed', gate_conditions_passed,
  'parley_first', parley_first, 'parley_repairs', parley_repairs,
  'membership_failures', membership_failures,
  'membership_task_families', membership_task_families,
  'number_failures', number_failures,
  'python_token_multiple', python_token_multiple,
  'rust_token_multiple', rust_token_multiple,
  'source_gap_vs_rust_percent', source_gap_vs_rust_percent
)) FROM headline;
