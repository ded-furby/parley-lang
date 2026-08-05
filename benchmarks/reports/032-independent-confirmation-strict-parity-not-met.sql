.mode list
.separator |
CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_deep_confirmation_032_protocol_v1_v0.3.158.json'));
CREATE TEMP VIEW runs AS
SELECT CAST(json_extract(run.value,'$.replicate') AS INTEGER) AS replicate,
       json_extract(run.value,'$.language') AS language,
       CAST(json_extract(run.value,'$.hidden_task_successes') AS INTEGER) AS hidden,
       CAST(json_extract(run.value,'$.first_public_task_successes') AS INTEGER) AS first_success,
       CAST(json_extract(run.value,'$.public_check_attempts') AS INTEGER) AS checks,
       CAST(json_extract(run.value,'$.repair_turns') AS INTEGER) AS repairs,
       CAST(json_extract(run.value,'$.total_tokens_per_task') AS REAL) AS tokens_task,
       CAST(json_extract(run.value,'$.elapsed_seconds_per_task') AS REAL) AS seconds_task,
       json_extract(run.value,'$.thread_id') AS thread_id
FROM raw, json_each(json_extract(raw.document,'$.results')) AS run;
CREATE TEMP VIEW language_summary AS
SELECT CASE json_extract(row.value,'$.language') WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
       json_extract(row.value,'$.hidden_task_successes') AS hidden,
       json_extract(row.value,'$.first_public_task_successes') AS first_success,
       json_extract(row.value,'$.repair_turns') AS repairs,
       json_extract(row.value,'$.median_total_tokens_per_task') AS median_tokens_task,
       json_extract(row.value,'$.weighted_total_tokens_per_task') AS weighted_tokens_task,
       json_extract(row.value,'$.median_elapsed_seconds_per_task') AS median_seconds_task
FROM raw, json_each(json_extract(raw.document,'$.summary.by_scale')) AS row;
SELECT 'headline', COUNT(*), SUM(hidden), SUM(first_success), SUM(repairs), COUNT(DISTINCT thread_id) FROM runs;
SELECT 'language_summary', * FROM language_summary ORDER BY language;
SELECT 'session_detail', replicate, language, hidden, first_success, checks, repairs, tokens_task, seconds_task, thread_id FROM runs ORDER BY replicate, language;
