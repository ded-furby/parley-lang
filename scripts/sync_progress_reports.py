#!/usr/bin/env python3
"""Copy every benchmark HTML report into the durable progress archive."""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "benchmarks" / "reports"
PROGRESS = ROOT / "progress"
ARCHIVE = PROGRESS / "reports"


def report_title(path: Path) -> str:
    match = re.search(r"<title>(.*?)</title>", path.read_text(errors="replace"), re.I | re.S)
    if match:
        return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
    return path.stem.replace("-", " ").title()


def report_stage(number: int) -> str:
    if number <= 6:
        return "Foundations"
    if number <= 15:
        return "Reliability"
    if number <= 24:
        return "Broad validation"
    return "Repository scale"


def report_signal(name: str) -> str:
    if any(word in name for word in ("win", "passed", "restored")):
        return "positive"
    if any(word in name for word in ("failed", "regression", "gap", "not-met")):
        return "learning"
    return "evidence"


def report_label(path: Path) -> str:
    stem = re.sub(r"^\d{3}-", "", path.stem)
    return stem.replace("-", " ").title()


def collect_reports() -> list[dict]:
    reports = []
    for source in sorted(SOURCE.glob("*.html")):
        match = re.match(r"(\d{3})-", source.name)
        if not match:
            continue
        number = int(match.group(1))
        data = source.read_bytes()
        shutil.copy2(source, ARCHIVE / source.name)
        reports.append({
            "number": number,
            "file": source.name,
            "title": report_title(source),
            "label": report_label(source),
            "stage": report_stage(number),
            "signal": report_signal(source.stem),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source": f"benchmarks/reports/{source.name}",
            "archive": f"progress/reports/{source.name}",
        })
    return reports


INDEX_CSS = """
:root {
  color-scheme: light dark;
  --portable-canvas: #fff;
  --portable-surface: #fff;
  --portable-surface-subtle: #f7f7f7;
  --portable-ink: #0d0d0d;
  --portable-muted: #5d5d5d;
  --portable-tertiary: #8f8f8f;
  --portable-border: rgba(13,13,13,.08);
  --portable-accent: #0285ff;
  --portable-positive: #00692a;
  --portable-positive-bg: #edfaf2;
  --portable-negative: #ba2623;
  --portable-negative-bg: #fff0f0;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--portable-canvas);
  color: var(--portable-ink);
}
@media (prefers-color-scheme: dark) {
  :root {
    --portable-canvas: #181818;
    --portable-surface: #212121;
    --portable-surface-subtle: #2a2a2a;
    --portable-ink: #dfdfdf;
    --portable-muted: #cdcdcd;
    --portable-tertiary: #afafaf;
    --portable-border: rgba(255,255,255,.08);
    --portable-accent: #66b5ff;
    --portable-positive: #04b84c;
    --portable-positive-bg: rgba(4,184,76,.15);
    --portable-negative: #fa423e;
    --portable-negative-bg: rgba(250,66,62,.16);
  }
}
* { box-sizing: border-box; }
html, body { min-height: 100%; margin: 0; background: var(--portable-canvas); color: var(--portable-ink); }
html { scroll-behavior: smooth; }
body { font-size: 14px; line-height: 1.5; }
a { color: inherit; }
.report-bar {
  position: sticky;
  z-index: 10;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 48px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--portable-border);
  background: var(--portable-canvas);
  font-size: 14px;
  line-height: 22px;
}
.report-bar strong { font-weight: 500; }
.report-bar span { color: var(--portable-tertiary); font-weight: 500; }
.page { width: min(768px, 100%); margin: 0 auto; padding: 32px 0 56px; }
.intro h1 { margin: 0 0 10px; font-size: 28px; font-weight: 600; line-height: 1.2; letter-spacing: -.025em; }
.intro p { max-width: 720px; margin: 0; color: var(--portable-muted); }
.block { margin-top: 32px; }
.section-head { display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 16px; }
.section-head h2 { margin: 0; font-size: 20px; font-weight: 500; line-height: 26px; }
.section-head p { margin: 0; color: var(--portable-tertiary); font-size: 12px; line-height: 18px; text-align: right; }
.facts, .milestones { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr)); gap: 8px; }
.fact, .milestone { border: 1px solid var(--portable-border); border-radius: 16px; background: var(--portable-surface); }
.fact { min-height: 104px; padding: 20px; }
.fact span { display: block; color: var(--portable-muted); font-size: 14px; line-height: 20px; }
.fact strong { display: block; margin-top: 4px; font-size: 20px; font-weight: 500; line-height: 26px; }
.milestone { min-height: 150px; padding: 20px; text-decoration: none; transition: border-color .15s ease, background .15s ease; }
.milestone:hover { border-color: var(--portable-accent); background: var(--portable-surface-subtle); }
.milestone b { color: var(--portable-tertiary); font-size: 12px; font-weight: 600; line-height: 18px; }
.milestone h3 { margin: 24px 0 4px; font-size: 16px; font-weight: 500; line-height: 22px; }
.milestone p { margin: 0; color: var(--portable-muted); font-size: 12px; line-height: 18px; }
.timeline-wrap { padding: 20px; overflow-x: auto; border: 1px solid var(--portable-border); border-radius: 16px; background: var(--portable-surface); }
.timeline { position: relative; display: grid; grid-template-columns: repeat(31, 1fr); align-items: center; min-width: 720px; height: 68px; }
.timeline::before { position: absolute; top: 25px; right: 1.6%; left: 1.6%; height: 1px; background: var(--portable-border); content: ''; }
.tick { position: relative; display: grid; place-items: center; gap: 8px; color: var(--portable-tertiary); font-size: 10px; font-variant-numeric: tabular-nums; text-decoration: none; }
.dot { z-index: 1; width: 9px; height: 9px; border: 2px solid var(--portable-canvas); border-radius: 50%; background: var(--portable-accent); box-shadow: 0 0 0 1px var(--portable-border); }
.tick.positive .dot { background: var(--portable-positive); }
.tick.learning .dot { background: var(--portable-negative); }
.tick:hover { color: var(--portable-ink); }
.tick:hover .dot { transform: scale(1.35); }
.tools { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }
input, select {
  min-height: 36px;
  padding: 6px 12px;
  border: 1px solid var(--portable-border);
  border-radius: 999px;
  outline: 0;
  background: var(--portable-surface);
  color: var(--portable-ink);
  font: inherit;
}
input { flex: 1 1 320px; }
input:focus, select:focus { border-color: var(--portable-accent); box-shadow: 0 0 0 2px color-mix(in srgb, var(--portable-accent) 18%, transparent); }
.reports { margin-top: 12px; border-top: 1px solid var(--portable-border); }
.report { display: grid; grid-template-columns: 52px minmax(0, 1fr) auto; gap: 12px; align-items: center; min-height: 74px; padding: 12px 0; border-bottom: 1px solid var(--portable-border); text-decoration: none; }
.report:hover .copy strong { color: var(--portable-accent); }
.number { color: var(--portable-tertiary); font-size: 12px; font-weight: 600; font-variant-numeric: tabular-nums; }
.copy { min-width: 0; }
.copy strong { display: block; overflow: hidden; font-size: 14px; font-weight: 500; line-height: 20px; text-overflow: ellipsis; white-space: nowrap; }
.copy small { display: block; margin-top: 2px; color: var(--portable-tertiary); font-size: 12px; line-height: 18px; }
.signal { padding: 2px 8px; border-radius: 999px; background: var(--portable-surface-subtle); color: var(--portable-accent); font-size: 11px; font-weight: 500; line-height: 18px; }
.report.positive .signal { background: var(--portable-positive-bg); color: var(--portable-positive); }
.report.learning .signal { background: var(--portable-negative-bg); color: var(--portable-negative); }
.empty { display: none; padding: 32px 0; color: var(--portable-muted); text-align: center; }
footer { width: min(768px, 100%); margin: 0 auto; padding: 22px 0 40px; border-top: 1px solid var(--portable-border); color: var(--portable-tertiary); font-size: 12px; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
@media (max-width: 820px) {
  .page, footer { width: 100%; padding-right: 24px; padding-left: 24px; }
}
@media (max-width: 600px) {
  .report-bar { position: static; align-items: flex-start; flex-direction: column; gap: 0; padding: 20px 24px 0; border-bottom: 0; }
  .report-bar span { font-size: 11px; line-height: 16px; letter-spacing: .08em; text-transform: uppercase; }
  .page { padding-top: 20px; }
  .intro h1 { font-size: 24px; line-height: 30px; }
  .facts, .milestones { grid-template-columns: 1fr; }
  .section-head { align-items: flex-start; flex-direction: column; gap: 3px; }
  .section-head p { text-align: left; }
  .tools { flex-direction: column; }
  input, select { width: 100%; }
  .report { grid-template-columns: 40px minmax(0, 1fr); }
  .signal { display: none; }
}
@media print {
  :root { color-scheme: light; }
  .report-bar { position: static; }
  .tools { display: none; }
  .page, footer { width: 100%; padding-right: 0; padding-left: 0; }
}
"""


def render_index(reports: list[dict]) -> str:
    payload = json.dumps(reports, ensure_ascii=False).replace("</", "<\\/")
    total_bytes = sum(item["bytes"] for item in reports)
    latest = reports[-1] if reports else {"number": 0, "title": "No reports"}
    preserved_013 = any(item["number"] == 13 for item in reports)
    return f"""<!doctype html>
<html lang="en" data-parley-report-theme="portable-v1">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#181818" media="(prefers-color-scheme: dark)">
  <title>Parley Progress — Evidence archive</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22><rect width=%2264%22 height=%2264%22 rx=%2214%22 fill=%22%23fff%22/><path d=%22M18 48V16h17c9 0 15 5 15 13S44 42 35 42h-7v6H18zm10-15h7c3 0 5-1 5-4s-2-4-5-4h-7v8z%22 fill=%22%230285ff%22/></svg>">
  <style>{INDEX_CSS}</style>
</head>
<body>
  <header class="report-bar"><strong>Parley Progress</strong><span>{len(reports)} preserved reports</span></header>
  <main class="page">
    <section class="intro">
      <h1>Benchmark evidence archive</h1>
      <p>Every benchmark report remains available as a standalone HTML artifact. Wins, regressions, and failed hypotheses stay visible because the complete record matters more than a flattering summary.</p>
    </section>
    <section class="block">
      <div class="section-head"><h2>Archive summary</h2><p>Checksum-backed and locally browseable</p></div>
      <div class="facts">
        <div class="fact"><span>Reports preserved</span><strong>{len(reports)}</strong></div>
        <div class="fact"><span>Archived evidence</span><strong>{total_bytes / 1024 / 1024:.1f} MB</strong></div>
        <div class="fact"><span>Report 013 intact</span><strong>{'Yes' if preserved_013 else 'No'}</strong></div>
        <div class="fact"><span>Latest report</span><strong>{latest['number']:03d}</strong></div>
      </div>
    </section>
    <section class="block">
      <div class="section-head"><h2>Milestones</h2><p>Three turning points, not a victory lap.</p></div>
      <div class="milestones">
        <a class="milestone" href="reports/013-reliability-restored-context-gap.html"><b>013</b><h3>Reliability restored</h3><p>The report explicitly preserved before later experiments.</p></a>
        <a class="milestone" href="reports/030-ninety-session-scaling-mechanism.html"><b>030</b><h3>90-session mechanism</h3><p>The scale confirmation explaining where Parley saves agent work.</p></a>
        <a class="milestone" href="reports/031-deeper-project-efficiency-win.html"><b>031</b><h3>Deeper project win</h3><p>The strict efficiency result that justified building a real product next.</p></a>
      </div>
    </section>
    <section class="block">
      <div class="section-head"><h2>Evidence timeline</h2><p>Green: positive · red: gap or regression · blue: neutral evidence</p></div>
      <div class="timeline-wrap"><div class="timeline" id="timeline"></div></div>
    </section>
    <section class="block">
      <div class="section-head"><h2>All reports</h2><p>Open any report directly; no server required.</p></div>
      <div class="tools">
        <input id="search" type="search" placeholder="Search titles or report numbers" aria-label="Search reports">
        <select id="stage" aria-label="Filter by stage"><option value="">All stages</option></select>
      </div>
      <div class="reports" id="reports"></div>
      <div class="empty" id="empty">No reports match that filter.</div>
    </section>
  </main>
  <footer>Generated by <code>scripts/sync_progress_reports.py</code>. SHA-256 checksums live in <code>manifest.json</code>.</footer>
  <script id="report-data" type="application/json">{payload}</script>
  <script>
    const data = JSON.parse(document.querySelector('#report-data').textContent);
    const timeline = document.querySelector('#timeline');
    const reports = document.querySelector('#reports');
    const search = document.querySelector('#search');
    const stage = document.querySelector('#stage');
    const empty = document.querySelector('#empty');
    const escapeHTML = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
    const signalLabel = {{ positive: 'positive', learning: 'gap', evidence: 'evidence' }};
    const stages = [...new Set(data.map(item => item.stage))];
    stages.forEach(name => stage.insertAdjacentHTML('beforeend', `<option>${{name}}</option>`));
    timeline.innerHTML = data.map(item => `<a class="tick ${{item.signal}}" href="reports/${{item.file}}" title="${{escapeHTML(item.label)}}"><span class="dot"></span><span>${{String(item.number).padStart(3,'0')}}</span></a>`).join('');
    function render() {{
      const needle = search.value.trim().toLowerCase();
      const visible = data.filter(item => (!stage.value || item.stage === stage.value) && (!needle || `${{item.number}} ${{item.file}} ${{item.label}} ${{item.title}}`.toLowerCase().includes(needle)));
      reports.innerHTML = visible.map(item => `<a class="report ${{item.signal}}" href="reports/${{item.file}}"><span class="number">${{String(item.number).padStart(3,'0')}}</span><span class="copy"><strong>${{escapeHTML(item.label)}}</strong><small>${{escapeHTML(item.stage)}} · ${{(item.bytes / 1024).toFixed(0)}} KB</small></span><span class="signal">${{signalLabel[item.signal]}}</span></a>`).join('');
      empty.style.display = visible.length ? 'none' : 'block';
    }}
    search.addEventListener('input', render);
    stage.addEventListener('change', render);
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    reports = collect_reports()
    if not reports:
        raise SystemExit("No benchmark HTML reports found.")
    (PROGRESS / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "reports": reports}, indent=2) + "\n")
    (PROGRESS / "index.html").write_text(render_index(reports))
    print(f"Archived {len(reports)} HTML reports in {ARCHIVE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
