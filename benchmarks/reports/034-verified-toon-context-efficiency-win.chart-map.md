# Iteration 034 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does exact-round-trip TOON preserve task accuracy while
  lowering complete agent-session tokens versus compact JSON?
- Decision-useful answer: yes on this frozen record-heavy corpus and two model
  IDs; 90/90 exact, 45/45 paired token wins, and the gate passes 5/5.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Configurations | Is the reduction consistent across agent configurations? | Comparison / grouped bar | agent_config, representation, total_tokens | All three configurations preserve exact accuracy and lower total TOON tokens | Hard two-root cap for the meaningful representation grouping |
| Tasks | Which task contexts create the largest full-session saving? | Comparison / bar | task, saved_percent | Every task saves; rollback and rename planning save most | Single-root preferred; task identity is already on the axis |

Both visuals use bars because both questions are discrete category comparisons;
one needs a representation grouping and the other is a single paired effect.
Exact gates, configurations, tasks, and all 45 pairs remain in audit tables.
