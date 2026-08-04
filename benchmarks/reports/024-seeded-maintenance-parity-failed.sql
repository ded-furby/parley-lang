.mode list
.separator |

CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_maintenance_024_protocol_v1_v0.3.155.json'));

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
  CAST(json_extract(run.value, '$.seed_source_rough_tokens_per_task') AS REAL) AS seed_tokens_task,
  CAST(json_extract(run.value, '$.source_rough_tokens_per_task') AS REAL) AS source_tokens_task,
  CAST(json_extract(run.value, '$.source_edit_rough_tokens_per_task') AS REAL) AS edit_tokens_task,
  CAST(json_extract(run.value, '$.check_integrity_ok') AS INTEGER) AS integrity_ok,
  CAST(json_extract(run.value, '$.command_protocol_compliant') AS INTEGER) AS protocol_ok,
  json_extract(run.value, '$.thread_id') AS thread_id,
  run.value AS run_json
FROM raw, json_each(json_extract(raw.document, '$.results')) AS run;

CREATE TEMP VIEW language_summary AS
SELECT
  CASE json_extract(row.value, '$.language')
    WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
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
  CAST(json_extract(row.value, '$.median_seed_source_rough_tokens_per_task') AS REAL) AS seed_tokens_task,
  CAST(json_extract(row.value, '$.median_source_rough_tokens_per_task') AS REAL) AS source_tokens_task,
  CAST(json_extract(row.value, '$.median_source_edit_rough_tokens_per_task') AS REAL) AS edit_tokens_task
FROM raw, json_each(json_extract(raw.document, '$.summary.by_scale')) AS row;

CREATE TEMP VIEW parley_task_reliability AS
WITH task_rows AS (
  SELECT task.key AS task_id, json_extract(task.value, '$.task_title') AS task,
    CAST(json_extract(task.value, '$.first_public_check_success') AS INTEGER) AS first_success,
    CAST(json_extract(task.value, '$.hidden_success') AS INTEGER) AS hidden_success
  FROM runs, json_each(json_extract(runs.run_json, '$.task_results')) AS task
  WHERE runs.language = 'parley'
)
SELECT task_id, task, COUNT(*) AS appearances, SUM(first_success) AS first_successes,
  COUNT(*) - SUM(first_success) AS first_failures, SUM(hidden_success) AS hidden_successes
FROM task_rows GROUP BY task_id, task ORDER BY first_failures DESC, task;

CREATE TEMP VIEW first_failures AS
WITH failed AS (
  SELECT runs.replicate, task.key AS task_id,
    CAST(json_extract(task.value, '$.compile_ok') AS INTEGER) AS compile_ok,
    COALESCE(json_extract(task.value, '$.compile_stderr'), '') AS compile_stderr
  FROM runs, json_each(json_extract(runs.run_json, '$.public_attempts[0].tasks')) AS task
  WHERE runs.language='parley' AND CAST(json_extract(task.value, '$.ok') AS INTEGER)=0
)
SELECT replicate, task_id,
  CASE
    WHEN task_id='invoice_net_extension' THEN 'Whole-number division produced decimal'
    ELSE 'Unwrapped read-file maybe'
  END AS signature,
  compile_ok, compile_stderr
FROM failed;

CREATE TEMP VIEW failure_signatures AS
SELECT signature, COUNT(*) AS events, COUNT(DISTINCT task_id) AS affected_tasks,
  COUNT(DISTINCT replicate) AS independent_sessions
FROM first_failures GROUP BY signature ORDER BY events DESC, signature;

CREATE TEMP VIEW file_judgment AS
SELECT
  CASE runs.language WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  COUNT(*) AS sessions,
  SUM(CAST(json_extract(runs.run_json, '$.task_results.notes_index_extension.first_public_check_success') AS INTEGER)) AS first_successes,
  SUM(CAST(json_extract(runs.run_json, '$.task_results.notes_index_extension.hidden_success') AS INTEGER)) AS hidden_successes,
  SUM((SELECT COUNT(*) FROM json_each(json_extract(runs.run_json, '$.task_results.notes_index_extension.hidden_judgment.cases')) AS c
       WHERE CAST(json_extract(c.value, '$.ok') AS INTEGER)=1)) AS exact_hidden_cases
FROM runs GROUP BY runs.language;

CREATE TEMP VIEW source_stage AS
SELECT language, 'Seed' AS stage, seed_tokens_task AS rough_tokens_task FROM language_summary
UNION ALL
SELECT language, 'Final' AS stage, source_tokens_task AS rough_tokens_task FROM language_summary;

CREATE TEMP VIEW headline AS
SELECT 18 AS sessions, 72 AS assigned_tasks, 72 AS hidden_successes,
  1 AS gate_conditions_passed, 17 AS parley_first, 6 AS parley_repairs,
  0 AS parley_clean_sessions, 72 AS exact_file_cases,
  ROUND((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Python'), 2) AS python_token_multiple,
  ROUND((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Rust'), 2) AS rust_token_multiple,
  ROUND(100.0 * ((SELECT source_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT source_tokens_task FROM language_summary WHERE language='Rust') - 1), 2) AS source_gap_vs_rust_percent,
  ROUND(100.0 * ((SELECT edit_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT edit_tokens_task FROM language_summary WHERE language='Rust') - 1), 2) AS edit_gap_vs_rust_percent;

SELECT 'language_summary', json_group_array(json_object(
  'language',language,'sessions',sessions,'assigned_tasks',assigned_tasks,
  'hidden_successes',hidden_successes,'hidden_rate',hidden_rate,'first_successes',first_successes,
  'first_rate',first_rate,'repair_turns',repair_turns,'median_tokens_task',median_tokens_task,
  'weighted_tokens_task',weighted_tokens_task,'median_seconds_task',median_seconds_task,
  'prompt_chars_task',prompt_chars_task,'seed_tokens_task',seed_tokens_task,
  'source_tokens_task',source_tokens_task,'edit_tokens_task',edit_tokens_task)) FROM language_summary;

SELECT 'session_detail', json_group_array(json_object(
  'replicate',replicate,'language',CASE language WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END,
  'hidden_successes',hidden_successes,'first_successes',first_successes,'checks',checks,
  'repair_turns',repair_turns,'tokens_task',tokens_task,'seconds_task',seconds_task,
  'prompt_chars_task',prompt_chars_task,'seed_tokens_task',seed_tokens_task,
  'source_tokens_task',source_tokens_task,'edit_tokens_task',edit_tokens_task,
  'integrity_ok',integrity_ok,'protocol_ok',protocol_ok)) FROM runs ORDER BY replicate, language;

SELECT 'parley_task_reliability', json_group_array(json_object(
  'task_id',task_id,'task',task,'appearances',appearances,'first_successes',first_successes,
  'first_failures',first_failures,'hidden_successes',hidden_successes)) FROM parley_task_reliability;

SELECT 'failure_signatures', json_group_array(json_object(
  'signature',signature,'events',events,'affected_tasks',affected_tasks,
  'independent_sessions',independent_sessions)) FROM failure_signatures;

SELECT 'first_failure_audit', json_group_array(json_object(
  'replicate',replicate,'task_id',task_id,'signature',signature,'compile_ok',compile_ok,
  'compile_stderr',compile_stderr)) FROM first_failures ORDER BY replicate, task_id;

SELECT 'file_judgment', json_group_array(json_object(
  'language',language,'sessions',sessions,'first_successes',first_successes,
  'hidden_successes',hidden_successes,'exact_hidden_cases',exact_hidden_cases)) FROM file_judgment;

SELECT 'source_stage', json_group_array(json_object(
  'language',language,'stage',stage,'rough_tokens_task',rough_tokens_task)) FROM source_stage;

SELECT 'headline', json_group_array(json_object(
  'sessions',sessions,'assigned_tasks',assigned_tasks,'hidden_successes',hidden_successes,
  'gate_conditions_passed',gate_conditions_passed,'parley_first',parley_first,
  'parley_repairs',parley_repairs,'parley_clean_sessions',parley_clean_sessions,
  'exact_file_cases',exact_file_cases,'python_token_multiple',python_token_multiple,
  'rust_token_multiple',rust_token_multiple,'source_gap_vs_rust_percent',source_gap_vs_rust_percent,
  'edit_gap_vs_rust_percent',edit_gap_vs_rust_percent)) FROM headline;
