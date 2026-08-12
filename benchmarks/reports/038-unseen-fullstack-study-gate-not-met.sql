-- Canonical language-level extraction for iteration 038.
-- Run from the repository root with SQLite JSON1 available.
WITH raw AS (
    SELECT json(readfile('benchmarks/results/fullstack_agent_038_raw.json')) AS body
),
languages(language) AS (
    VALUES ('parley'), ('python'), ('typescript'), ('rust')
)
SELECT
    language,
    json_extract(body, '$.summary.by_language.' || language || '.sessions') AS sessions,
    json_extract(body, '$.summary.by_language.' || language || '.hidden_successes') AS hidden_successes,
    json_extract(body, '$.summary.by_language.' || language || '.hidden_success_rate') AS hidden_success_rate,
    json_extract(body, '$.summary.by_language.' || language || '.first_check_successes') AS first_check_successes,
    json_extract(body, '$.summary.by_language.' || language || '.first_check_success_rate') AS first_check_success_rate,
    json_extract(body, '$.summary.by_language.' || language || '.median_total_tokens') AS median_total_tokens,
    json_extract(body, '$.summary.by_language.' || language || '.median_elapsed_seconds') AS median_elapsed_seconds,
    json_extract(body, '$.summary.by_language.' || language || '.hidden_correct_maintenance_rows') AS hidden_correct_maintenance_rows,
    json_extract(body, '$.summary.by_language.' || language || '.exact_root_successes') AS exact_root_successes,
    json_extract(body, '$.summary.by_language.' || language || '.exact_root_rate') AS exact_root_rate
FROM raw
CROSS JOIN languages
ORDER BY hidden_success_rate DESC, first_check_success_rate DESC,
         median_total_tokens ASC;
