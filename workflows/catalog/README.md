# First-party workflow catalog

This directory contains complete, fixture-tested workflow products. A catalog
entry owns its Parley source, schema-2 manifest, fixtures, documentation, and
version. Starter templates under `parley/workflows/templates/` are teaching
scaffolds; entries here are maintained automation products.

## Products

- [`release-steward`](release-steward/) combines test results, release
  metadata, a checklist, and package information into one Markdown decision.

Release Steward is currently dogfooded in its `dogfood/` directory. Installation
and checksum verification are the next platform checkpoint; no entry should be
called installable until that path is tested end to end.
