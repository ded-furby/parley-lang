-- Run from the parley-lang repository root:
-- sqlite3 ':memory:' < benchmarks/reports/009-progressive-disclosure-regression.sql

CREATE TEMP TABLE benchmark_document AS
SELECT json(readfile('benchmarks/results/agent_pilot_009_protocol_v2_v0.3.145.json')) AS body;

CREATE TEMP VIEW language_summary AS
SELECT
  CASE language.key
    WHEN 'parley' THEN 'Parley'
    WHEN 'python' THEN 'Python'
    WHEN 'rust' THEN 'Rust'
  END AS language,
  json_extract(language.value, '$.runs') AS runs,
  json_extract(language.value, '$.hidden_success_rate') AS hidden_success_rate,
  json_extract(language.value, '$.first_public_check_success_rate') AS first_public_check_success_rate,
  json_extract(language.value, '$.command_protocol_compliance_rate') AS command_protocol_compliance_rate,
  json_extract(language.value, '$.median_public_check_attempts') AS median_public_check_attempts,
  json_extract(language.value, '$.median_total_tokens') AS median_total_tokens,
  json_extract(language.value, '$.median_input_tokens') AS median_input_tokens,
  json_extract(language.value, '$.median_output_tokens') AS median_output_tokens,
  json_extract(language.value, '$.median_prompt_chars') AS median_prompt_chars,
  json_extract(language.value, '$.median_elapsed_seconds') AS median_elapsed_seconds,
  (
    SELECT sum(json_extract(run.value, '$.repair_turns'))
    FROM benchmark_document AS run_document,
         json_each(json_extract(run_document.body, '$.results')) AS run
    WHERE json_extract(run.value, '$.language') = language.key
  ) AS repair_turns
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.summary.by_language')) AS language;

CREATE TEMP VIEW task_tokens AS
SELECT
  CASE json_extract(task.value, '$.task_id')
    WHEN 'bracket_report' THEN 'Bracket report'
    WHEN 'compact_ranges' THEN 'Compact ranges'
    WHEN 'inventory_totals' THEN 'Inventory totals'
  END AS task,
  CASE json_extract(task.value, '$.language')
    WHEN 'parley' THEN 'Parley'
    WHEN 'python' THEN 'Python'
    WHEN 'rust' THEN 'Rust'
  END AS language,
  json_extract(task.value, '$.median_total_tokens') AS median_total_tokens
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.summary.per_task')) AS task;

CREATE TEMP VIEW headline AS
SELECT
  json_extract(benchmark_document.body, '$.summary.runs') AS sessions,
  (
    SELECT min(json_extract(language.value, '$.hidden_success_rate'))
    FROM json_each(json_extract(benchmark_document.body, '$.summary.by_language')) AS language
  ) AS hidden_success_rate,
  round(
    json_extract(benchmark_document.body, '$.summary.by_language.parley.median_total_tokens') /
    json_extract(benchmark_document.body, '$.summary.by_language.python.median_total_tokens'),
    2
  ) AS token_multiple,
  (
    SELECT sum(json_extract(run.value, '$.repair_turns'))
    FROM json_each(json_extract(benchmark_document.body, '$.results')) AS run
    WHERE json_extract(run.value, '$.language') = 'parley'
  ) AS parley_repairs,
  round(
    json_extract(benchmark_document.body, '$.summary.by_language.parley.median_total_tokens') /
    json_extract(benchmark_document.body, '$.summary.by_language.python.median_total_tokens') - 1.0,
    4
  ) AS python_token_gap,
  round(
    json_extract(benchmark_document.body, '$.summary.by_language.parley.median_elapsed_seconds') /
    json_extract(benchmark_document.body, '$.summary.by_language.python.median_elapsed_seconds') - 1.0,
    4
  ) AS python_elapsed_gap
FROM benchmark_document;

SELECT 'language_summary' AS dataset, json_group_array(json_object(
  'language', language,
  'runs', runs,
  'hidden_success_rate', hidden_success_rate,
  'first_public_check_success_rate', first_public_check_success_rate,
  'command_protocol_compliance_rate', command_protocol_compliance_rate,
  'median_public_check_attempts', median_public_check_attempts,
  'median_total_tokens', median_total_tokens,
  'median_input_tokens', median_input_tokens,
  'median_output_tokens', median_output_tokens,
  'median_prompt_chars', median_prompt_chars,
  'median_elapsed_seconds', median_elapsed_seconds,
  'repair_turns', repair_turns
)) AS rows
FROM language_summary
UNION ALL
SELECT 'task_tokens', json_group_array(json_object(
  'task', task,
  'language', language,
  'median_total_tokens', median_total_tokens
))
FROM task_tokens
UNION ALL
SELECT 'headline', json_group_array(json_object(
  'sessions', sessions,
  'hidden_success_rate', hidden_success_rate,
  'token_multiple', token_multiple,
  'parley_repairs', parley_repairs,
  'python_token_gap', python_token_gap,
  'python_elapsed_gap', python_elapsed_gap
))
FROM headline;
