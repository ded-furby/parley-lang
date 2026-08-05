# Log Summary

Turn a plain-text application or service log into a Markdown count of `ERROR`,
`WARN`, and `INFO` lines, followed by the exact error lines for triage.

```bash
parley workflow install log-summary
parley workflow test log-summary
parley workflow run log-summary \
  --input source=service.log \
  --output log-report.md
```
