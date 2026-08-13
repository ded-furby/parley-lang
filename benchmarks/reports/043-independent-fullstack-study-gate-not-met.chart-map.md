# Iteration 043 report chart map

The canonical artifact uses categorical bars only where a four-language
comparison makes a frozen gate or secondary magnitude materially easier to
read. Tables retain exact values, model strata, evidence integrity, and scratch
lifecycle details.

| View | Question | Dataset / encodings | Why this view |
|---|---|---|---|
| Hidden assignment success | Did every arm satisfy the withheld contract? | `languages`; x = language, y = hidden-success rate | A four-way categorical bar makes the perfect tie explicit. |
| First public check | Did Parley match the strongest first-pass arm? | `languages`; x = language, y = first-check rate | The direct comparison makes the four-way perfect tie explicit. |
| Complete session tokens | Did Parley match the cheapest baseline? | `languages`; x = language, y = median input-plus-output tokens, ascending | A sorted magnitude view shows the repeated complete-session token win. |
| Fresh-session elapsed | Was Parley fastest overall? | `languages`; x = language, y = median seconds, ascending | The language-level comparison shows the overall ordering without implying that every model stratum passed. |
| Model-stratified elapsed | Did Parley meet the elapsed threshold within both models? | `configuration_efficiency`; x = model and language, y = median seconds, ascending | Four focused Parley/Python bars expose the binding terra-medium miss hidden by the faster overall median. |
| Final editable source | Did representation compactness persist? | `languages`; x = language, y = median o200k source tokens, ascending | This secondary chart separates source size from complete-session cost. |

No pie, stacked, dual-axis, or time-series view is used: there is no
part-to-whole, composition, commensurate dual measure, or temporal sequence to
encode. Gate outcomes, model-stratified medians, evidence integrity, and
scratch integrity remain tables because exact mapping and auditability matter
more than shape. The model-stratified elapsed chart is intentionally limited to
Parley and the binding fastest baseline; the complete eight-row configuration
table retains TypeScript and Rust.
