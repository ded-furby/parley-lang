# Release Steward

Release Steward accepts four small, inspectable evidence files and writes one
deterministic Markdown release-readiness report. It is Parley's flagship
multi-input workflow and is dogfooded on this repository.

```bash
parley workflow install release-steward
parley workflow test release-steward
parley workflow run release-steward \
  --input test_results=tests.txt \
  --input release_metadata=release.txt \
  --input checklist=checklist.md \
  --input package_info=package.txt \
  --output readiness.md
```

The three key-value files deliberately use `key=value` text rather than JSON:
the first product version needs only a small stable contract. JSON or CSV earns
its place only if multiple unrelated workflows need structured parsing.

The release is `READY` only when tests pass with zero failures, the checklist
has no open `- [ ]` items, and both wheel and registry evidence are ready.
