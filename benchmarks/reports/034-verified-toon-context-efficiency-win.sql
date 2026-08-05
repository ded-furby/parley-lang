.mode list
.separator |
CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_data_confirmation_034.json'));
CREATE TEMP VIEW representation_summary AS
SELECT json_extract(item.value, '$.representation') AS representation,
       json_extract(item.value, '$.sessions') AS sessions,
       json_extract(item.value, '$.exact_successes') AS exact_successes,
       json_extract(item.value, '$.parse_successes') AS parse_successes,
       json_extract(item.value, '$.input_tokens') AS input_tokens,
       json_extract(item.value, '$.output_tokens') AS output_tokens,
       json_extract(item.value, '$.total_tokens') AS total_tokens,
       json_extract(item.value, '$.median_total_tokens') AS median_total_tokens,
       json_extract(item.value, '$.median_elapsed_seconds') AS median_elapsed_seconds
FROM raw, json_each(json_extract(raw.document, '$.summary.by_representation')) AS item;
SELECT * FROM representation_summary ORDER BY representation;
SELECT 'gate', json_extract(document, '$.summary.gate.passed'), json_extract(document, '$.summary.gate.conditions_passed') FROM raw;
