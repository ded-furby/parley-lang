# Parley progress archive

This folder is the committed, browseable history of Parley's benchmark work.
Open [`index.html`](index.html) locally for the visual timeline.

- `reports/` contains copies of every standalone HTML report from
  `benchmarks/reports/`, including preserved report 013.
- `manifest.json` records each file's source path, byte length, and SHA-256.
- `index.html` is a self-contained searchable dashboard with no external
  dependencies. Its light/dark typography, spacing, cards, borders, and status
  colors deliberately match the established portable design of the numbered
  benchmark reports.

After adding a benchmark HTML report, refresh this archive with:

```bash
python3 scripts/sync_progress_reports.py
```

The benchmark directory remains the source of truth. The progress copy exists
so the complete visual history is obvious, durable, and easy to browse.
