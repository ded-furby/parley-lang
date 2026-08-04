.mode list
.separator |

CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_repositories_025_protocol_v1_v0.3.155.json'));

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
  CAST(json_extract(run.value, '$.input_tokens_per_task') AS REAL) AS input_tokens_task,
  CAST(json_extract(run.value, '$.output_tokens_per_task') AS REAL) AS output_tokens_task,
  CAST(json_extract(run.value, '$.elapsed_seconds_per_task') AS REAL) AS seconds_task,
  CAST(json_extract(run.value, '$.prompt_chars_per_task') AS REAL) AS prompt_chars_task,
  CAST(json_extract(run.value, '$.seed_source_rough_tokens_per_task') AS REAL) AS seed_tokens_task,
  CAST(json_extract(run.value, '$.source_rough_tokens_per_task') AS REAL) AS source_tokens_task,
  CAST(json_extract(run.value, '$.source_edit_rough_tokens_per_task') AS REAL) AS edit_tokens_task,
  CAST(json_extract(run.value, '$.changed_files_per_task') AS REAL) AS changed_files_task,
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
  CAST(json_extract(row.value, '$.median_input_tokens_per_task') AS REAL) AS median_input_tokens_task,
  CAST(json_extract(row.value, '$.median_output_tokens_per_task') AS REAL) AS median_output_tokens_task,
  CAST(json_extract(row.value, '$.median_elapsed_seconds_per_task') AS REAL) AS median_seconds_task,
  CAST(json_extract(row.value, '$.median_prompt_chars_per_task') AS REAL) AS prompt_chars_task,
  CAST(json_extract(row.value, '$.median_seed_source_rough_tokens_per_task') AS REAL) AS seed_tokens_task,
  CAST(json_extract(row.value, '$.median_source_rough_tokens_per_task') AS REAL) AS source_tokens_task,
  CAST(json_extract(row.value, '$.median_source_edit_rough_tokens_per_task') AS REAL) AS edit_tokens_task,
  CAST(json_extract(row.value, '$.median_changed_files_per_task') AS REAL) AS changed_files_task
FROM raw, json_each(json_extract(raw.document, '$.summary.by_scale')) AS row;

CREATE TEMP VIEW repository_detail AS
WITH task_rows AS (
  SELECT
    CASE runs.language WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
    task.key AS repository_id,
    json_extract(task.value, '$.task_title') AS repository,
    CAST(json_extract(task.value, '$.first_public_check_success') AS INTEGER) AS first_success,
    CAST(json_extract(task.value, '$.hidden_success') AS INTEGER) AS hidden_success,
    CAST(json_extract(task.value, '$.seed_source_rough_tokens') AS REAL) AS seed_tokens,
    CAST(json_extract(task.value, '$.source_rough_tokens') AS REAL) AS final_tokens,
    CAST(json_extract(task.value, '$.source_edit_rough_tokens') AS REAL) AS edit_tokens,
    json_array_length(json_extract(task.value, '$.changed_files')) AS changed_files
  FROM runs, json_each(json_extract(runs.run_json, '$.task_results')) AS task
)
SELECT language, repository_id, repository, COUNT(*) AS appearances,
  SUM(first_success) AS first_successes, SUM(hidden_success) AS hidden_successes,
  ROUND(AVG(seed_tokens), 2) AS seed_tokens,
  ROUND(AVG(final_tokens), 2) AS final_tokens,
  ROUND(AVG(edit_tokens), 2) AS edit_tokens,
  ROUND(AVG(changed_files), 2) AS changed_files
FROM task_rows
GROUP BY language, repository_id, repository
ORDER BY repository, language;

CREATE TEMP VIEW command_audit AS
SELECT
  CASE language WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  COUNT(*) AS sessions,
  SUM(CASE WHEN json_extract(run_json, '$.command_events[0].command') LIKE '%./sources%' THEN 1 ELSE 0 END) AS sources_first,
  SUM(CASE WHEN (SELECT COUNT(*) FROM json_each(json_extract(run_json, '$.command_events')) AS e
                 WHERE json_extract(e.value, '$.command') LIKE '%./sources%') = 1 THEN 1 ELSE 0 END) AS one_sources,
  SUM(protocol_ok) AS protocol_ok,
  SUM(integrity_ok) AS integrity_ok
FROM runs GROUP BY language;

CREATE TEMP VIEW file_judgment AS
SELECT
  CASE runs.language WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  COUNT(*) AS sessions,
  SUM(CAST(json_extract(runs.run_json, '$.task_results.filtered_report_repo.first_public_check_success') AS INTEGER)) AS first_successes,
  SUM(CAST(json_extract(runs.run_json, '$.task_results.filtered_report_repo.hidden_success') AS INTEGER)) AS hidden_successes,
  SUM((SELECT COUNT(*) FROM json_each(json_extract(runs.run_json, '$.task_results.filtered_report_repo.hidden_judgment.cases')) AS c
       WHERE CAST(json_extract(c.value, '$.ok') AS INTEGER)=1)) AS exact_hidden_cases
FROM runs GROUP BY runs.language;

CREATE TEMP VIEW source_stage AS
SELECT language, 'Seed' AS stage, seed_tokens_task AS rough_tokens_task FROM language_summary
UNION ALL
SELECT language, 'Final' AS stage, source_tokens_task AS rough_tokens_task FROM language_summary;

CREATE TEMP VIEW headline AS
SELECT 18 AS sessions, 72 AS assignments, 72 AS hidden_successes, 72 AS first_successes,
  0 AS repairs, 2 AS gate_conditions_passed, 2 AS changed_files_task, 72 AS exact_file_cases,
  ROUND(100.0 * ((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Python') - 1), 2) AS token_gap_python_percent,
  ROUND(100.0 * ((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Rust') - 1), 2) AS token_gap_rust_percent,
  ROUND(100.0 * ((SELECT median_seconds_task FROM language_summary WHERE language='Parley') /
        (SELECT median_seconds_task FROM language_summary WHERE language='Rust') - 1), 2) AS elapsed_gap_rust_percent,
  ROUND(100.0 * ((SELECT source_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT source_tokens_task FROM language_summary WHERE language='Rust') - 1), 2) AS source_gap_rust_percent;

SELECT 'language_summary', json_group_array(json_object(
  'language',language,'sessions',sessions,'assigned_tasks',assigned_tasks,
  'hidden_successes',hidden_successes,'hidden_rate',hidden_rate,'first_successes',first_successes,
  'first_rate',first_rate,'repair_turns',repair_turns,'median_tokens_task',median_tokens_task,
  'weighted_tokens_task',weighted_tokens_task,'median_input_tokens_task',median_input_tokens_task,
  'median_output_tokens_task',median_output_tokens_task,'median_seconds_task',median_seconds_task,
  'prompt_chars_task',prompt_chars_task,'seed_tokens_task',seed_tokens_task,
  'source_tokens_task',source_tokens_task,'edit_tokens_task',edit_tokens_task,
  'changed_files_task',changed_files_task)) FROM language_summary;

SELECT 'session_detail', json_group_array(json_object(
  'replicate',replicate,'language',CASE language WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END,
  'hidden_successes',hidden_successes,'first_successes',first_successes,'checks',checks,
  'repair_turns',repair_turns,'tokens_task',tokens_task,'input_tokens_task',input_tokens_task,
  'output_tokens_task',output_tokens_task,'seconds_task',seconds_task,
  'prompt_chars_task',prompt_chars_task,'seed_tokens_task',seed_tokens_task,
  'source_tokens_task',source_tokens_task,'edit_tokens_task',edit_tokens_task,
  'changed_files_task',changed_files_task,'integrity_ok',integrity_ok,'protocol_ok',protocol_ok))
FROM runs ORDER BY replicate, language;

SELECT 'repository_detail', json_group_array(json_object(
  'language',language,'repository_id',repository_id,'repository',repository,
  'appearances',appearances,'first_successes',first_successes,'hidden_successes',hidden_successes,
  'seed_tokens',seed_tokens,'final_tokens',final_tokens,'edit_tokens',edit_tokens,
  'changed_files',changed_files)) FROM repository_detail;

SELECT 'command_audit', json_group_array(json_object(
  'language',language,'sessions',sessions,'sources_first',sources_first,
  'one_sources',one_sources,'protocol_ok',protocol_ok,'integrity_ok',integrity_ok)) FROM command_audit;

SELECT 'file_judgment', json_group_array(json_object(
  'language',language,'sessions',sessions,'first_successes',first_successes,
  'hidden_successes',hidden_successes,'exact_hidden_cases',exact_hidden_cases)) FROM file_judgment;

SELECT 'source_stage', json_group_array(json_object(
  'language',language,'stage',stage,'rough_tokens_task',rough_tokens_task)) FROM source_stage;

SELECT 'headline', json_group_array(json_object(
  'sessions',sessions,'assignments',assignments,'hidden_successes',hidden_successes,
  'first_successes',first_successes,'repairs',repairs,'gate_conditions_passed',gate_conditions_passed,
  'changed_files_task',changed_files_task,'exact_file_cases',exact_file_cases,
  'token_gap_python_percent',token_gap_python_percent,'token_gap_rust_percent',token_gap_rust_percent,
  'elapsed_gap_rust_percent',elapsed_gap_rust_percent,'source_gap_rust_percent',source_gap_rust_percent))
FROM headline;
