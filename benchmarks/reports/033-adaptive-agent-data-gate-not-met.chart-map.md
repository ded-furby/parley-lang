# Iteration 033 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does verified adaptive TOON save at least 5% under both
  frozen primary tokenizers without changing the JSON model?
- Decision-useful answer: integrity and adaptive coverage pass, but primary
  savings are about 4.57%; the frozen Stage A gate finishes 4/5 and fails.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate tokens | Does adaptive selection reduce identical corpus tokens? | Comparison / grouped bar | tokenizer, representation, tokens | Savings are large under rough counting but narrowly below 5% under both primary tokenizers | Hard two-root cap; representation is the meaningful grouping |

Exact gate values and all 12 case decisions remain in audit tables. One grouped
chart is sufficient because every quantitative section compares the same two
representations; additional charts would repeat the relationship rather than
answer a new question.
