-- Run from the parley-lang repository root:
-- sqlite3 ':memory:' < benchmarks/reports/020-size-eight-confirmation-failed.sql

CREATE TEMP TABLE benchmark_document AS
SELECT json(readfile('benchmarks/results/agent_bundle_020_protocol_v1_v0.3.153.json')) AS body;

CREATE TEMP VIEW language_summary AS
SELECT
  CASE json_extract(row.value, '$.language')
    WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  json_extract(row.value, '$.sessions') AS sessions,
  json_extract(row.value, '$.assigned_tasks') AS assigned_tasks,
  json_extract(row.value, '$.hidden_task_successes') AS hidden_successes,
  json_extract(row.value, '$.hidden_task_success_rate') AS hidden_rate,
  json_extract(row.value, '$.first_public_task_successes') AS first_successes,
  json_extract(row.value, '$.first_public_task_success_rate') AS first_rate,
  json_extract(row.value, '$.first_bundle_check_successes') AS first_bundle_successes,
  json_extract(row.value, '$.repair_turns') AS repair_turns,
  json_extract(row.value, '$.median_total_tokens_per_session') AS median_session_tokens,
  json_extract(row.value, '$.median_total_tokens_per_task') AS median_tokens_task,
  json_extract(row.value, '$.weighted_total_tokens_per_task') AS weighted_tokens_task,
  json_extract(row.value, '$.median_elapsed_seconds_per_task') AS median_seconds_task,
  json_extract(row.value, '$.median_prompt_chars_per_task') AS prompt_chars_task
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.summary.by_scale')) AS row;

CREATE TEMP VIEW session_detail AS
SELECT
  json_extract(run.value, '$.replicate') AS replicate,
  CASE json_extract(run.value, '$.language')
    WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  json_extract(run.value, '$.hidden_task_successes') AS hidden_successes,
  json_extract(run.value, '$.first_public_task_successes') AS first_successes,
  json_extract(run.value, '$.public_check_attempts') AS checks,
  json_extract(run.value, '$.repair_turns') AS repair_turns,
  json_extract(run.value, '$.total_tokens') AS session_tokens,
  json_extract(run.value, '$.total_tokens_per_task') AS tokens_task,
  json_extract(run.value, '$.elapsed_seconds_per_task') AS seconds_task,
  json_extract(run.value, '$.command_protocol_compliant') AS protocol_ok
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.results')) AS run;

CREATE TEMP VIEW parley_task_reliability AS
SELECT
  task.key AS task_id,
  replace(task.key, '_', ' ') AS task,
  count(*) AS appearances,
  sum(json_extract(task.value, '$.first_public_check_success')) AS first_successes,
  count(*) - sum(json_extract(task.value, '$.first_public_check_success')) AS first_failures,
  sum(json_extract(task.value, '$.hidden_success')) AS hidden_successes
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.results')) AS run,
     json_each(json_extract(run.value, '$.task_results')) AS task
WHERE json_extract(run.value, '$.language') = 'parley'
GROUP BY task.key;

CREATE TEMP VIEW first_failure_events AS
SELECT
  task.key AS task_id,
  json_extract(task.value, '$.compile_stderr') AS compile_stderr,
  json_extract(run.value, '$.public_attempts[0].sources.' || task.key) AS source
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.results')) AS run,
     json_each(json_extract(run.value, '$.public_attempts[0].tasks')) AS task
WHERE json_extract(run.value, '$.language') = 'parley'
  AND NOT json_extract(task.value, '$.ok');

CREATE TEMP VIEW failure_signatures AS
SELECT
  CASE
    WHEN instr(compile_stderr, 'P901') > 0 THEN 'P901 mutable loop-variable backend bug'
    WHEN instr(lower(source), 'repeat while') > 0 THEN 'Unsupported repeat while phrasing'
    WHEN instr(lower(source), 'does not contain') > 0 THEN 'Unsupported does-not-contain phrasing'
    WHEN instr(lower(source), 'contains word is no') > 0 THEN 'Unsupported contains-is-no phrasing'
    ELSE 'Other first-check failure'
  END AS signature,
  count(*) AS events,
  count(DISTINCT task_id) AS affected_tasks
FROM first_failure_events
GROUP BY signature;

CREATE TEMP VIEW clean_ranked AS
SELECT
  language,
  tokens_task,
  seconds_task,
  hidden_successes,
  first_successes,
  row_number() OVER (PARTITION BY language ORDER BY tokens_task) AS token_rank,
  row_number() OVER (PARTITION BY language ORDER BY seconds_task) AS second_rank,
  count(*) OVER (PARTITION BY language) AS clean_sessions
FROM session_detail
WHERE repair_turns = 0;

CREATE TEMP VIEW clean_sensitivity AS
SELECT
  language,
  clean_sessions,
  round(avg(CASE WHEN token_rank IN ((clean_sessions + 1) / 2, (clean_sessions + 2) / 2)
                 THEN tokens_task END), 4) AS median_tokens_task,
  round(avg(CASE WHEN second_rank IN ((clean_sessions + 1) / 2, (clean_sessions + 2) / 2)
                 THEN seconds_task END), 4) AS median_seconds_task,
  sum(hidden_successes) AS hidden_successes,
  sum(first_successes) AS first_successes
FROM clean_ranked
GROUP BY language, clean_sessions;

CREATE TEMP VIEW headline AS
SELECT
  json_extract(body, '$.summary.sessions') AS sessions,
  json_extract(body, '$.summary.assigned_tasks') AS assigned_tasks,
  (SELECT sum(CASE WHEN value THEN 1 ELSE 0 END)
   FROM json_each(json_extract(body, '$.summary.strict_gate.conditions'))) AS gate_conditions_passed,
  (SELECT hidden_successes FROM language_summary WHERE language = 'Parley') AS parley_hidden,
  (SELECT first_successes FROM language_summary WHERE language = 'Parley') AS parley_first,
  (SELECT clean_sessions FROM clean_sensitivity WHERE language = 'Parley') AS parley_clean_sessions,
  (SELECT repair_turns FROM language_summary WHERE language = 'Parley') AS parley_repairs,
  round((SELECT median_tokens_task FROM language_summary WHERE language = 'Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language = 'Python'), 2) AS overall_python_multiple,
  round(100.0 * ((SELECT median_tokens_task FROM clean_sensitivity WHERE language = 'Parley') /
                 (SELECT median_tokens_task FROM clean_sensitivity WHERE language = 'Python') - 1), 2) AS clean_python_gap_percent,
  round(100.0 * ((SELECT median_tokens_task FROM clean_sensitivity WHERE language = 'Parley') /
                 (SELECT median_tokens_task FROM clean_sensitivity WHERE language = 'Rust') - 1), 2) AS clean_rust_gap_percent
FROM benchmark_document;

SELECT 'language_summary' AS dataset, json_group_array(json_object(
  'language', language, 'sessions', sessions, 'assigned_tasks', assigned_tasks,
  'hidden_successes', hidden_successes, 'hidden_rate', hidden_rate,
  'first_successes', first_successes, 'first_rate', first_rate,
  'first_bundle_successes', first_bundle_successes, 'repair_turns', repair_turns,
  'median_session_tokens', median_session_tokens,
  'median_tokens_task', median_tokens_task, 'weighted_tokens_task', weighted_tokens_task,
  'median_seconds_task', median_seconds_task, 'prompt_chars_task', prompt_chars_task)) AS rows
FROM language_summary
UNION ALL
SELECT 'session_detail', json_group_array(json_object(
  'replicate', replicate, 'language', language, 'hidden_successes', hidden_successes,
  'first_successes', first_successes, 'checks', checks, 'repair_turns', repair_turns,
  'session_tokens', session_tokens, 'tokens_task', tokens_task,
  'seconds_task', seconds_task, 'protocol_ok', protocol_ok))
FROM session_detail
UNION ALL
SELECT 'parley_task_reliability', json_group_array(json_object(
  'task_id', task_id, 'task', task, 'appearances', appearances,
  'first_successes', first_successes, 'first_failures', first_failures,
  'hidden_successes', hidden_successes))
FROM (SELECT * FROM parley_task_reliability ORDER BY first_failures DESC, task)
UNION ALL
SELECT 'failure_signatures', json_group_array(json_object(
  'signature', signature, 'events', events, 'affected_tasks', affected_tasks))
FROM failure_signatures
UNION ALL
SELECT 'clean_sensitivity', json_group_array(json_object(
  'language', language, 'clean_sessions', clean_sessions,
  'median_tokens_task', median_tokens_task, 'median_seconds_task', median_seconds_task,
  'hidden_successes', hidden_successes, 'first_successes', first_successes))
FROM clean_sensitivity
UNION ALL
SELECT 'headline', json_group_array(json_object(
  'sessions', sessions, 'assigned_tasks', assigned_tasks,
  'gate_conditions_passed', gate_conditions_passed,
  'parley_hidden', parley_hidden, 'parley_first', parley_first,
  'parley_clean_sessions', parley_clean_sessions, 'parley_repairs', parley_repairs,
  'overall_python_multiple', overall_python_multiple,
  'clean_python_gap_percent', clean_python_gap_percent,
  'clean_rust_gap_percent', clean_rust_gap_percent))
FROM headline;
