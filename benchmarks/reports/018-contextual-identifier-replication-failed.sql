-- Run from the parley-lang repository root:
-- sqlite3 ':memory:' < benchmarks/reports/018-contextual-identifier-replication-failed.sql

CREATE TEMP TABLE current_document AS
SELECT json(readfile('benchmarks/results/agent_bundle_018_protocol_v1_v0.3.152.json')) AS body;

CREATE TEMP TABLE prior_document AS
SELECT json(readfile('benchmarks/results/agent_bundle_017_protocol_v1_v0.3.151.json')) AS body;

CREATE TEMP VIEW scale_summary AS
SELECT
  json_extract(row.value, '$.bundle_size') AS bundle_size,
  'Size ' || json_extract(row.value, '$.bundle_size') AS bundle_label,
  CASE json_extract(row.value, '$.language')
    WHEN 'parley' THEN 'Parley'
    WHEN 'python' THEN 'Python'
    WHEN 'rust' THEN 'Rust'
  END AS language,
  json_extract(row.value, '$.sessions') AS sessions,
  json_extract(row.value, '$.assigned_tasks') AS assigned_tasks,
  json_extract(row.value, '$.hidden_task_success_rate') AS hidden_task_success_rate,
  json_extract(row.value, '$.first_public_task_success_rate') AS first_public_task_success_rate,
  json_extract(row.value, '$.first_bundle_check_success_rate') AS first_bundle_check_success_rate,
  json_extract(row.value, '$.command_protocol_compliance_rate') AS protocol_rate,
  json_extract(row.value, '$.repair_turns') AS repair_turns,
  json_extract(row.value, '$.median_total_tokens_per_session') AS median_tokens_session,
  json_extract(row.value, '$.median_total_tokens_per_task') AS median_tokens_task,
  json_extract(row.value, '$.weighted_total_tokens_per_task') AS weighted_tokens_task,
  json_extract(row.value, '$.median_elapsed_seconds_per_task') AS median_seconds_task,
  json_extract(row.value, '$.median_prompt_chars_per_task') AS median_prompt_chars_task
FROM current_document,
     json_each(json_extract(current_document.body, '$.summary.by_scale')) AS row;

CREATE TEMP VIEW parley_iteration_compare AS
SELECT
  json_extract(row.value, '$.bundle_size') AS bundle_size,
  'Size ' || json_extract(row.value, '$.bundle_size') AS bundle_label,
  '017 / v0.3.151' AS iteration,
  json_extract(row.value, '$.median_total_tokens_per_task') AS median_tokens_task,
  json_extract(row.value, '$.first_public_task_success_rate') AS first_task_rate,
  json_extract(row.value, '$.repair_turns') AS repair_turns
FROM prior_document,
     json_each(json_extract(prior_document.body, '$.summary.by_scale')) AS row
WHERE json_extract(row.value, '$.language') = 'parley'
UNION ALL
SELECT
  json_extract(row.value, '$.bundle_size'),
  'Size ' || json_extract(row.value, '$.bundle_size'),
  '018 / v0.3.152',
  json_extract(row.value, '$.median_total_tokens_per_task'),
  json_extract(row.value, '$.first_public_task_success_rate'),
  json_extract(row.value, '$.repair_turns')
FROM current_document,
     json_each(json_extract(current_document.body, '$.summary.by_scale')) AS row
WHERE json_extract(row.value, '$.language') = 'parley';

CREATE TEMP VIEW parley_task_reliability AS
SELECT
  task.key AS task_id,
  replace(task.key, '_', ' ') AS task,
  count(*) AS appearances,
  sum(CASE WHEN json_extract(task.value, '$.first_public_check_success') THEN 1 ELSE 0 END) AS first_successes,
  count(*) - sum(CASE WHEN json_extract(task.value, '$.first_public_check_success') THEN 1 ELSE 0 END) AS first_failures,
  sum(CASE WHEN json_extract(task.value, '$.hidden_success') THEN 1 ELSE 0 END) AS hidden_successes
FROM current_document,
     json_each(json_extract(current_document.body, '$.results')) AS run,
     json_each(json_extract(run.value, '$.task_results')) AS task
WHERE json_extract(run.value, '$.language') = 'parley'
GROUP BY task.key;

CREATE TEMP VIEW first_failure_events AS
SELECT
  task.key AS task_id,
  json_extract(task.value, '$.compile_stderr') AS compile_stderr
FROM current_document,
     json_each(json_extract(current_document.body, '$.results')) AS run,
     json_each(json_extract(run.value, '$.public_attempts[0].tasks')) AS task
WHERE json_extract(run.value, '$.language') = 'parley'
  AND NOT json_extract(task.value, '$.ok');

CREATE TEMP VIEW failure_signatures AS
SELECT
  CASE
    WHEN instr(compile_stderr, '''modulo''') > 0 THEN 'Unsupported modulo spelling'
    WHEN instr(compile_stderr, '''does''') > 0 THEN 'Unsupported does phrasing'
    ELSE 'Other first-check failure'
  END AS signature,
  count(*) AS failure_events,
  count(DISTINCT task_id) AS affected_tasks
FROM first_failure_events
GROUP BY signature;

CREATE TEMP VIEW clean_ranked AS
SELECT
  json_extract(run.value, '$.bundle_size') AS bundle_size,
  CASE json_extract(run.value, '$.language')
    WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  json_extract(run.value, '$.total_tokens_per_task') AS tokens_task,
  json_extract(run.value, '$.elapsed_seconds_per_task') AS seconds_task,
  row_number() OVER (
    PARTITION BY json_extract(run.value, '$.bundle_size'), json_extract(run.value, '$.language')
    ORDER BY json_extract(run.value, '$.total_tokens_per_task')
  ) AS token_rank,
  row_number() OVER (
    PARTITION BY json_extract(run.value, '$.bundle_size'), json_extract(run.value, '$.language')
    ORDER BY json_extract(run.value, '$.elapsed_seconds_per_task')
  ) AS second_rank,
  count(*) OVER (
    PARTITION BY json_extract(run.value, '$.bundle_size'), json_extract(run.value, '$.language')
  ) AS clean_sessions
FROM current_document,
     json_each(json_extract(current_document.body, '$.results')) AS run
WHERE json_extract(run.value, '$.repair_turns') = 0;

CREATE TEMP VIEW clean_sensitivity AS
SELECT
  bundle_size,
  language,
  clean_sessions,
  round(avg(CASE WHEN token_rank IN ((clean_sessions + 1) / 2, (clean_sessions + 2) / 2)
                 THEN tokens_task END), 4) AS median_tokens_task,
  round(avg(CASE WHEN second_rank IN ((clean_sessions + 1) / 2, (clean_sessions + 2) / 2)
                 THEN seconds_task END), 4) AS median_seconds_task
FROM clean_ranked
GROUP BY bundle_size, language, clean_sessions;

CREATE TEMP VIEW headline AS
SELECT
  json_extract(body, '$.summary.sessions') AS sessions,
  json_extract(body, '$.summary.assigned_tasks') AS assigned_tasks,
  1.0 * (SELECT sum(json_extract(run.value, '$.hidden_task_successes'))
         FROM json_each(json_extract(body, '$.results')) AS run) /
        json_extract(body, '$.summary.assigned_tasks') AS hidden_success_rate,
  (SELECT sum(CASE WHEN value THEN 1 ELSE 0 END)
   FROM json_each(json_extract(body, '$.summary.strict_gate.conditions'))) AS gate_conditions_passed,
  (SELECT sum(json_extract(run.value, '$.repair_turns'))
   FROM json_each(json_extract(body, '$.results')) AS run
   WHERE json_extract(run.value, '$.language') = 'parley') AS parley_repairs,
  round(
    (SELECT median_tokens_task FROM scale_summary WHERE bundle_size = 8 AND language = 'Parley') /
    (SELECT median_tokens_task FROM scale_summary WHERE bundle_size = 8 AND language = 'Python'), 2
  ) AS size8_token_multiple,
  round(100.0 * (
    (SELECT median_tokens_task FROM parley_iteration_compare WHERE bundle_size = 8 AND iteration LIKE '018%') /
    (SELECT median_tokens_task FROM parley_iteration_compare WHERE bundle_size = 8 AND iteration LIKE '017%') - 1
  ), 2) AS size8_change_percent
FROM current_document;

SELECT 'scale_summary' AS dataset, json_group_array(json_object(
  'bundle_size', bundle_size, 'bundle_label', bundle_label, 'language', language,
  'sessions', sessions, 'assigned_tasks', assigned_tasks,
  'hidden_task_success_rate', hidden_task_success_rate,
  'first_public_task_success_rate', first_public_task_success_rate,
  'first_bundle_check_success_rate', first_bundle_check_success_rate,
  'protocol_rate', protocol_rate, 'repair_turns', repair_turns,
  'median_tokens_session', median_tokens_session,
  'median_tokens_task', median_tokens_task,
  'weighted_tokens_task', weighted_tokens_task,
  'median_seconds_task', median_seconds_task,
  'median_prompt_chars_task', median_prompt_chars_task)) AS rows
FROM scale_summary
UNION ALL
SELECT 'parley_iteration_compare', json_group_array(json_object(
  'bundle_size', bundle_size, 'bundle_label', bundle_label, 'iteration', iteration,
  'median_tokens_task', median_tokens_task, 'first_task_rate', first_task_rate,
  'repair_turns', repair_turns))
FROM parley_iteration_compare
UNION ALL
SELECT 'parley_task_reliability', json_group_array(json_object(
  'task_id', task_id, 'task', task, 'appearances', appearances,
  'first_successes', first_successes, 'first_failures', first_failures,
  'hidden_successes', hidden_successes))
FROM (SELECT * FROM parley_task_reliability ORDER BY first_failures DESC, task)
UNION ALL
SELECT 'failure_signatures', json_group_array(json_object(
  'signature', signature, 'failure_events', failure_events,
  'affected_tasks', affected_tasks))
FROM failure_signatures
UNION ALL
SELECT 'clean_sensitivity', json_group_array(json_object(
  'bundle_size', bundle_size, 'language', language, 'clean_sessions', clean_sessions,
  'median_tokens_task', median_tokens_task, 'median_seconds_task', median_seconds_task))
FROM (SELECT * FROM clean_sensitivity ORDER BY bundle_size, language)
UNION ALL
SELECT 'headline', json_group_array(json_object(
  'sessions', sessions, 'assigned_tasks', assigned_tasks,
  'hidden_success_rate', hidden_success_rate,
  'gate_conditions_passed', gate_conditions_passed,
  'parley_repairs', parley_repairs, 'size8_token_multiple', size8_token_multiple,
  'size8_change_percent', size8_change_percent))
FROM headline;
