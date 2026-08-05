.mode list
.separator |
CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_data_033.json'));
CREATE TEMP VIEW tokenizer_summary AS
SELECT json_extract(item.value, '$.tokenizer') AS tokenizer,
       json_extract(item.value, '$.summary.compact_json_tokens') AS json_tokens,
       json_extract(item.value, '$.summary.adaptive_tokens') AS adaptive_tokens,
       json_extract(item.value, '$.summary.savings_tokens') AS saved_tokens,
       json_extract(item.value, '$.summary.savings_percent_vs_compact_json') AS savings_percent,
       json_extract(item.value, '$.summary.toon_supported') AS toon_supported,
       json_extract(item.value, '$.summary.toon_selected') AS toon_selected
FROM raw, json_each(json_extract(raw.document, '$.tokenizers')) AS item;
SELECT * FROM tokenizer_summary ORDER BY tokenizer;
