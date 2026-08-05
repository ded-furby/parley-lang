-- Reproducible SQLite audit over the preserved iteration 035 result.
.headers on
.mode column

WITH raw AS (
  SELECT json(readfile('benchmarks/results/fullstack_035_v0.4.0.json')) AS body
), languages(language, label) AS (
  VALUES ('parley', 'Parley'), ('python', 'Python'),
         ('typescript', 'TypeScript'), ('rust', 'Rust')
)
SELECT
  label AS language,
  json_extract(body, '$.correctness.' || language || '.passed') AS passed,
  json_extract(body, '$.source.' || language || '.totals.o200k_base') AS o200k_tokens,
  json_extract(body, '$.source.' || language || '.totals.cl100k_base') AS cl100k_tokens,
  json_extract(body, '$.build.' || language || '.median') AS build_median_seconds,
  json_extract(body, '$.startup.' || language || '.median') * 1000.0 AS startup_median_ms,
  json_extract(body, '$.load.' || language || '.median_requests_per_second') AS requests_per_second,
  json_extract(body, '$.artifacts.' || language || '.deploy_closure_bytes') AS deploy_closure_bytes
FROM raw, languages
ORDER BY o200k_tokens;

WITH raw AS (
  SELECT json(readfile('benchmarks/results/fullstack_035_v0.4.0.json')) AS body
)
SELECT
  json_extract(body, '$.gates.all_languages_correct') AS correctness_gate,
  json_extract(body, '$.gates.parley_primary_compactness') AS compactness_gate,
  json_extract(body, '$.gates.parley_cross_target_reuse') AS reuse_gate,
  json_extract(body, '$.gates.overall_fullstack_compactness_proof') AS overall_gate
FROM raw;
