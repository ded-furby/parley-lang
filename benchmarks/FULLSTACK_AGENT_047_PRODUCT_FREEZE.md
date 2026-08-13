# Full-stack agent study 047 product freeze

Iteration 047 freezes Parley 0.5.7, its 176-token path-response card, and the
JSON-native evidence mechanism before selecting any task semantics.

The product is the accepted path-parameter implementation at commit
`c9e8c9bea770c9243ac244663c28209bb18264df`. Its gate passed 21 dedicated tests
and all 727 repository tests; the release wheel SHA-256 is recorded in the
machine-readable freeze. Product, protocol, result, documentation, and test
inputs are read from immutable Git blobs.

The context boundary is commit
`0791f128b90437b4970cf5c414e8674a6f508889`. At that commit no study-047 task,
case, protocol, scaffold, semantic oracle, output, raw result, or audit file
existed. The compact card is 760 bytes and 176 `o200k_base` tokens.

The evidence boundary retains JSON-native header-pair comparison and requires
the future live and persisted evidence to agree on route paths and captured
path parameters. Study 046 remains immutable, valid, and unsuccessful on its
strict elapsed-time gate; none of its task corpus may be reused.

The next permitted step is to select and hash a disjoint path-routing corpus.
This checkpoint proves reproducibility only. It does not establish agent
efficiency, broad framework parity, or universal superiority.
