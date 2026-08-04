-- Run from the parley-lang repository root:
-- sqlite3 ':memory:' < benchmarks/reports/017-workload-scale-parity-failed.sql

CREATE TEMP TABLE benchmark_document AS
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
  json_extract(row.value, '$.median_input_tokens_per_task') AS median_input_tokens_task,
  json_extract(row.value, '$.median_output_tokens_per_task') AS median_output_tokens_task,
  json_extract(row.value, '$.median_elapsed_seconds_per_task') AS median_seconds_task,
  json_extract(row.value, '$.median_prompt_chars_per_task') AS median_prompt_chars_task,
  json_extract(row.value, '$.median_source_rough_tokens_per_task') AS median_source_tokens_task
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.summary.by_scale')) AS row;

CREATE TEMP VIEW parley_task_reliability AS
SELECT
  task.key AS task_id,
  replace(task.key, '_', ' ') AS task,
  count(*) AS appearances,
  sum(CASE WHEN json_extract(task.value, '$.first_public_check_success') THEN 1 ELSE 0 END) AS first_successes,
  count(*) - sum(CASE WHEN json_extract(task.value, '$.first_public_check_success') THEN 1 ELSE 0 END) AS first_failures,
  sum(CASE WHEN json_extract(task.value, '$.hidden_success') THEN 1 ELSE 0 END) AS hidden_successes
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.results')) AS run,
     json_each(json_extract(run.value, '$.task_results')) AS task
WHERE json_extract(run.value, '$.language') = 'parley'
GROUP BY task.key;

CREATE TEMP VIEW first_failure_events AS
SELECT
  task.key AS task_id,
  json_extract(task.value, '$.compile_stderr') AS compile_stderr
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.results')) AS run,
     json_each(json_extract(run.value, '$.public_attempts[0].tasks')) AS task
WHERE json_extract(run.value, '$.language') = 'parley'
  AND NOT json_extract(task.value, '$.ok');

CREATE TEMP VIEW failure_signatures AS
SELECT
  CASE
    WHEN instr(compile_stderr, '''position'' is reserved') > 0 THEN 'Reserved position identifier'
    WHEN instr(compile_stderr, '''modulo''') > 0 THEN 'Unsupported modulo spelling'
    ELSE 'Other P101 parse failure'
  END AS signature,
  count(*) AS failure_events,
  count(DISTINCT task_id) AS affected_tasks
FROM first_failure_events
GROUP BY signature;

CREATE TEMP VIEW headline AS
SELECT
  json_extract(body, '$.summary.sessions') AS sessions,
  json_extract(body, '$.summary.assigned_tasks') AS assigned_tasks,
  1.0 * (SELECT sum(json_extract(run.value, '$.hidden_task_successes'))
         FROM json_each(json_extract(body, '$.results')) AS run) /
        json_extract(body, '$.summary.assigned_tasks') AS hidden_success_rate,
  (SELECT min(json_extract(run.value, '$.command_protocol_compliant'))
   FROM json_each(json_extract(body, '$.results')) AS run) AS protocol_rate,
  (SELECT sum(CASE WHEN value THEN 1 ELSE 0 END)
   FROM json_each(json_extract(body, '$.summary.strict_gate.conditions'))) AS gate_conditions_passed,
  (SELECT sum(json_extract(run.value, '$.repair_turns'))
   FROM json_each(json_extract(body, '$.results')) AS run
   WHERE json_extract(run.value, '$.language') = 'parley') AS parley_repairs,
  round(
    json_extract(body, '$.summary.by_scale[9].median_total_tokens_per_task') /
    json_extract(body, '$.summary.by_scale[10].median_total_tokens_per_task'), 2
  ) AS size8_token_multiple
FROM benchmark_document;

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
  'median_input_tokens_task', median_input_tokens_task,
  'median_output_tokens_task', median_output_tokens_task,
  'median_seconds_task', median_seconds_task,
  'median_prompt_chars_task', median_prompt_chars_task,
  'median_source_tokens_task', median_source_tokens_task)) AS rows
FROM scale_summary
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
SELECT 'headline', json_group_array(json_object(
  'sessions', sessions, 'assigned_tasks', assigned_tasks,
  'hidden_success_rate', hidden_success_rate, 'protocol_rate', protocol_rate,
  'gate_conditions_passed', gate_conditions_passed,
  'parley_repairs', parley_repairs, 'size8_token_multiple', size8_token_multiple))
FROM headline;
