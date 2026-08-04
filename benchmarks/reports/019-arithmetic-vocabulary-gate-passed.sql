-- Run from the parley-lang repository root:
-- sqlite3 ':memory:' < benchmarks/reports/019-arithmetic-vocabulary-gate-passed.sql

CREATE TEMP TABLE benchmark_document AS
SELECT json(readfile('benchmarks/results/agent_vocabulary_019_protocol_v1_v0.3.152.json')) AS body;

CREATE TEMP VIEW language_summary AS
SELECT
  CASE summary.key WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  json_extract(summary.value, '$.runs') AS runs,
  json_extract(summary.value, '$.hidden_successes') AS hidden_successes,
  json_extract(summary.value, '$.hidden_success_rate') AS hidden_success_rate,
  json_extract(summary.value, '$.first_public_check_successes') AS first_successes,
  json_extract(summary.value, '$.first_public_check_success_rate') AS first_success_rate,
  json_extract(summary.value, '$.command_protocol_compliance_rate') AS protocol_rate,
  json_extract(summary.value, '$.median_public_check_attempts') AS median_checks,
  json_extract(summary.value, '$.median_total_tokens') AS median_tokens,
  json_extract(summary.value, '$.median_elapsed_seconds') AS median_seconds
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.summary.by_language')) AS summary;

CREATE TEMP VIEW task_summary AS
SELECT
  json_extract(row.value, '$.task_id') AS task_id,
  replace(json_extract(row.value, '$.task_id'), '_', ' ') AS task,
  CASE json_extract(row.value, '$.language')
    WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  json_extract(row.value, '$.runs') AS runs,
  json_extract(row.value, '$.hidden_successes') AS hidden_successes,
  json_extract(row.value, '$.first_public_check_successes') AS first_successes,
  json_extract(row.value, '$.median_total_tokens') AS median_tokens
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.summary.per_task')) AS row;

CREATE TEMP VIEW parley_first_sources AS
SELECT
  json_extract(run.value, '$.task_id') AS task_id,
  replace(json_extract(run.value, '$.task_id'), '_', ' ') AS task,
  json_extract(run.value, '$.replicate') AS replicate,
  json_extract(run.value, '$.first_public_check_success') AS first_success,
  json_extract(run.value, '$.hidden_success') AS hidden_success,
  json_extract(run.value, '$.repair_turns') AS repair_turns,
  json_extract(run.value, '$.total_tokens') AS total_tokens,
  json_extract(run.value, '$.elapsed_seconds') AS elapsed_seconds,
  json_extract(run.value, '$.public_attempts[0].source') AS first_source,
  CASE
    WHEN instr(lower(json_extract(run.value, '$.public_attempts[0].source')), 'modulo') > 0
      THEN 'modulo'
    WHEN instr(lower(json_extract(run.value, '$.public_attempts[0].source')), 'remainder of') > 0
      THEN 'canonical remainder phrase'
    WHEN instr(lower(json_extract(run.value, '$.public_attempts[0].source')), 'remainder') > 0
      THEN 'malformed remainder phrase'
    ELSE 'no direct operator spelling'
  END AS spelling
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.results')) AS run
WHERE json_extract(run.value, '$.language') = 'parley';

CREATE TEMP VIEW spelling_summary AS
SELECT
  spelling,
  count(*) AS sessions,
  count(DISTINCT task_id) AS task_families,
  sum(first_success) AS first_successes,
  sum(hidden_success) AS hidden_successes,
  sum(repair_turns) AS repair_turns
FROM parley_first_sources
GROUP BY spelling;

CREATE TEMP VIEW parley_task_diagnostic AS
SELECT
  task_id,
  task,
  count(*) AS sessions,
  sum(first_success) AS first_successes,
  sum(hidden_success) AS hidden_successes,
  sum(repair_turns) AS repair_turns,
  round(avg(total_tokens), 1) AS mean_tokens,
  group_concat(spelling, '; ') AS first_spellings
FROM parley_first_sources
GROUP BY task_id, task;

CREATE TEMP VIEW headline AS
SELECT
  json_extract(body, '$.summary.runs') AS sessions,
  (SELECT hidden_successes FROM language_summary WHERE language = 'Parley') AS parley_hidden,
  (SELECT first_successes FROM language_summary WHERE language = 'Parley') AS parley_first,
  (SELECT sessions FROM spelling_summary WHERE spelling = 'modulo') AS modulo_sessions,
  (SELECT task_families FROM spelling_summary WHERE spelling = 'modulo') AS modulo_families,
  CASE WHEN (SELECT task_families FROM spelling_summary WHERE spelling = 'modulo') >= 2
       THEN 1 ELSE 0 END AS evidence_gate_passed,
  (SELECT sum(repair_turns) FROM parley_first_sources) AS parley_repairs
FROM benchmark_document;

SELECT 'language_summary' AS dataset, json_group_array(json_object(
  'language', language, 'runs', runs, 'hidden_successes', hidden_successes,
  'hidden_success_rate', hidden_success_rate, 'first_successes', first_successes,
  'first_success_rate', first_success_rate, 'protocol_rate', protocol_rate,
  'median_checks', median_checks, 'median_tokens', median_tokens,
  'median_seconds', median_seconds)) AS rows
FROM language_summary
UNION ALL
SELECT 'task_summary', json_group_array(json_object(
  'task_id', task_id, 'task', task, 'language', language, 'runs', runs,
  'hidden_successes', hidden_successes, 'first_successes', first_successes,
  'median_tokens', median_tokens))
FROM task_summary
UNION ALL
SELECT 'parley_first_sources', json_group_array(json_object(
  'task_id', task_id, 'task', task, 'replicate', replicate,
  'first_success', first_success, 'hidden_success', hidden_success,
  'repair_turns', repair_turns, 'total_tokens', total_tokens,
  'elapsed_seconds', elapsed_seconds, 'spelling', spelling))
FROM parley_first_sources
UNION ALL
SELECT 'spelling_summary', json_group_array(json_object(
  'spelling', spelling, 'sessions', sessions, 'task_families', task_families,
  'first_successes', first_successes, 'hidden_successes', hidden_successes,
  'repair_turns', repair_turns))
FROM spelling_summary
UNION ALL
SELECT 'parley_task_diagnostic', json_group_array(json_object(
  'task_id', task_id, 'task', task, 'sessions', sessions,
  'first_successes', first_successes, 'hidden_successes', hidden_successes,
  'repair_turns', repair_turns, 'mean_tokens', mean_tokens,
  'first_spellings', first_spellings))
FROM parley_task_diagnostic
UNION ALL
SELECT 'headline', json_group_array(json_object(
  'sessions', sessions, 'parley_hidden', parley_hidden,
  'parley_first', parley_first, 'modulo_sessions', modulo_sessions,
  'modulo_families', modulo_families,
  'evidence_gate_passed', evidence_gate_passed,
  'parley_repairs', parley_repairs))
FROM headline;
