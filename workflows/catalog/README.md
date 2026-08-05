# First-party workflow catalog

This directory contains complete, fixture-tested workflow products. A catalog
entry owns its Parley source, schema-2 manifest, fixtures, documentation, and
version. Starter templates under `parley/workflows/templates/` are teaching
scaffolds; entries here are maintained automation products.

## Products

- [`release-steward`](../../parley/workflows/catalog/release-steward/) combines test results, release
  metadata, a checklist, and package information into one Markdown decision.
- [`log-summary`](../../parley/workflows/catalog/log-summary/) turns service
  logs into compact Markdown evidence for incident and release review.
- [`checklist-report`](../../parley/workflows/catalog/checklist-report/)
  summarizes checklist completion while preserving every open item.

Release Steward is dogfooded in its `dogfood/` directory. All three products
ship in the Python wheel and install with `parley workflow install NAME`.
`parley workflow verify` checks their whole-tree SHA-256 lock records.
