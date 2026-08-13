# Full-stack agent study 047 corpus freeze

The semantics-only study-047 corpus is frozen after product/evidence commit
`f1959a5247db7444c161340110ec1782faa3d2b7` and before any scaffold, reference
application, protocol threshold, prompt, or model output.

It contains four tasks and 40 cases: two new path-routing implementations and
two route-handler repairs. Each task has five public and five hidden cases.
The cases cover exact-route priority, successful and invalid parameterized
lookups, case-insensitive request headers, once-decoded percent escapes,
generated malformed/invalid UTF-8 and encoded-separator rejection, dynamic
response envelopes, and three real-browser score checks.

Every task ID, route, browser export, path/response field, and case ID is
mechanically disjoint from iterations 036–046. The new domains are tundra
probes, magma cores, aviary bands, and canal gates under `/api/v11/*` routes.
Study 046's corpus is not reused.

The maintenance defects are predeclared and publicly observable: one reads a
substituted path-parameter key; the other converts the raw request path instead
of its decoded capture. Both defects are confined to the route-handler owner.

Frozen SHA-256 digests:

- `fullstack_agent_047_tasks.json`:
  `c7cc0680ad62b0e78ce4fb1fda306f3f48ae5018f18ffdf19ad6e6a9df418348`
- `fullstack_agent_047_cases.json`:
  `11f08afbede6825f455d630ca0507c7e6661fccb0110c95aab2df2a2f8d4a5c9`

This checkpoint freezes evaluation semantics only. It provides no performance
or language-superiority evidence.
