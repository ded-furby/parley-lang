# Checklist Report

Convert a Markdown checklist into a compact status report and preserve the
still-open items for action.

```bash
parley workflow install checklist-report
parley workflow test checklist-report
parley workflow run checklist-report \
  --input source=release-checklist.md \
  --output checklist-status.md
```
