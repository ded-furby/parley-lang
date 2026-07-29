-- Run from the parley-lang repository root:
-- sqlite3 ':memory:' < benchmarks/reports/016-broad-corpus-diagnostic.sql

CREATE TEMP TABLE benchmark_document AS
SELECT json(readfile('benchmarks/results/agent_broad_016_protocol_v2_v0.3.151.json')) AS body;

CREATE TEMP TABLE manifest_document AS
SELECT json(readfile('benchmarks/agent_tasks_broad.json')) AS body;

CREATE TEMP VIEW task_catalog AS
SELECT
  CAST(task.key AS INTEGER) AS sort_order,
  json_extract(task.value, '$.id') AS task_id,
  json_extract(task.value, '$.title') AS task,
  json_extract(task.value, '$.category') AS category
FROM manifest_document,
     json_each(json_extract(manifest_document.body, '$.tasks')) AS task;

CREATE TEMP VIEW language_summary AS
SELECT
  CASE language.key WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' WHEN 'rust' THEN 'Rust' END AS language,
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
  (SELECT sum(json_extract(run.value, '$.repair_turns'))
   FROM benchmark_document AS run_document,
        json_each(json_extract(run_document.body, '$.results')) AS run
   WHERE json_extract(run.value, '$.language') = language.key) AS repair_turns
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.summary.by_language')) AS language;

CREATE TEMP VIEW task_cell AS
SELECT
  catalog.sort_order,
  catalog.task_id,
  catalog.task,
  catalog.category,
  CASE json_extract(cell.value, '$.language') WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' WHEN 'rust' THEN 'Rust' END AS language,
  json_extract(cell.value, '$.runs') AS runs,
  json_extract(cell.value, '$.hidden_successes') AS hidden_successes,
  json_extract(cell.value, '$.first_public_check_successes') AS first_successes,
  json_extract(cell.value, '$.median_total_tokens') AS median_total_tokens,
  (SELECT sum(json_extract(run.value, '$.repair_turns'))
   FROM benchmark_document AS run_document,
        json_each(json_extract(run_document.body, '$.results')) AS run
   WHERE json_extract(run.value, '$.task_id') = catalog.task_id
     AND json_extract(run.value, '$.language') = json_extract(cell.value, '$.language')) AS repair_turns
FROM benchmark_document,
     json_each(json_extract(benchmark_document.body, '$.summary.per_task')) AS cell
JOIN task_catalog AS catalog
  ON catalog.task_id = json_extract(cell.value, '$.task_id');

CREATE TEMP VIEW task_wide AS
SELECT
  sort_order,
  task,
  category,
  max(CASE WHEN language = 'Parley' THEN first_successes END) AS parley_first,
  max(CASE WHEN language = 'Python' THEN first_successes END) AS python_first,
  max(CASE WHEN language = 'Rust' THEN first_successes END) AS rust_first,
  max(CASE WHEN language = 'Parley' THEN median_total_tokens END) AS parley_tokens,
  max(CASE WHEN language = 'Python' THEN median_total_tokens END) AS python_tokens,
  max(CASE WHEN language = 'Rust' THEN median_total_tokens END) AS rust_tokens,
  max(CASE WHEN language = 'Parley' THEN repair_turns END) AS parley_repairs,
  max(CASE WHEN language = 'Python' THEN repair_turns END) AS python_repairs,
  max(CASE WHEN language = 'Rust' THEN repair_turns END) AS rust_repairs,
  round(
    max(CASE WHEN language = 'Parley' THEN median_total_tokens END) /
    min(
      max(CASE WHEN language = 'Python' THEN median_total_tokens END),
      max(CASE WHEN language = 'Rust' THEN median_total_tokens END)
    ) - 1.0,
    4
  ) AS parley_vs_best_gap
FROM task_cell
GROUP BY sort_order, task, category;

CREATE TEMP VIEW headline AS
SELECT
  json_extract(benchmark_document.body, '$.summary.runs') AS sessions,
  (SELECT min(json_extract(language.value, '$.hidden_success_rate'))
   FROM json_each(json_extract(benchmark_document.body, '$.summary.by_language')) AS language) AS hidden_success_rate,
  (SELECT min(json_extract(language.value, '$.command_protocol_compliance_rate'))
   FROM json_each(json_extract(benchmark_document.body, '$.summary.by_language')) AS language) AS protocol_rate,
  round(json_extract(benchmark_document.body, '$.summary.by_language.parley.median_total_tokens') /
        json_extract(benchmark_document.body, '$.summary.by_language.python.median_total_tokens') - 1.0, 4) AS python_token_gap,
  json_extract(benchmark_document.body, '$.summary.by_language.parley.first_public_check_success_rate') AS parley_first_pass_rate,
  (SELECT sum(json_extract(run.value, '$.repair_turns'))
   FROM json_each(json_extract(benchmark_document.body, '$.results')) AS run
   WHERE json_extract(run.value, '$.language') = 'parley') AS parley_repairs
FROM benchmark_document;

SELECT 'language_summary' AS dataset, json_group_array(json_object(
  'language', language, 'runs', runs, 'hidden_success_rate', hidden_success_rate,
  'first_public_check_success_rate', first_public_check_success_rate,
  'command_protocol_compliance_rate', command_protocol_compliance_rate,
  'median_public_check_attempts', median_public_check_attempts,
  'median_total_tokens', median_total_tokens, 'median_input_tokens', median_input_tokens,
  'median_output_tokens', median_output_tokens, 'median_prompt_chars', median_prompt_chars,
  'median_elapsed_seconds', median_elapsed_seconds, 'repair_turns', repair_turns)) AS rows
FROM language_summary
UNION ALL
SELECT 'task_wide', json_group_array(json_object(
  'task', task, 'category', category,
  'parley_first', parley_first, 'python_first', python_first, 'rust_first', rust_first,
  'parley_tokens', parley_tokens, 'python_tokens', python_tokens, 'rust_tokens', rust_tokens,
  'parley_repairs', parley_repairs, 'python_repairs', python_repairs, 'rust_repairs', rust_repairs,
  'parley_vs_best_gap', parley_vs_best_gap))
FROM (SELECT * FROM task_wide ORDER BY sort_order)
UNION ALL
SELECT 'headline', json_group_array(json_object(
  'sessions', sessions, 'hidden_success_rate', hidden_success_rate,
  'protocol_rate', protocol_rate, 'python_token_gap', python_token_gap,
  'parley_first_pass_rate', parley_first_pass_rate, 'parley_repairs', parley_repairs))
FROM headline;
