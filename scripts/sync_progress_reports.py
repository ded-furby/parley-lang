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
            "stage": report_stage(number),
            "signal": report_signal(source.stem),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source": f"benchmarks/reports/{source.name}",
            "archive": f"progress/reports/{source.name}",
        })
    return reports


def render_index(reports: list[dict]) -> str:
    payload = json.dumps(reports, ensure_ascii=False).replace("</", "<\\/")
    total_bytes = sum(item["bytes"] for item in reports)
    latest = reports[-1] if reports else {"number": 0, "title": "No reports"}
    preserved_013 = any(item["number"] == 13 for item in reports)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Parley Progress — Evidence archive</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22><rect width=%2264%22 height=%2264%22 rx=%2214%22 fill=%22%230c0d0e%22/><path d=%22M18 48V16h17c9 0 15 5 15 13S44 42 35 42h-7v6H18zm10-15h7c3 0 5-1 5-4s-2-4-5-4h-7v8z%22 fill=%22%2378e7ae%22/></svg>">
  <style>
    :root {{
      color-scheme: dark;
      --ink: #f3efe5;
      --muted: #9d9b94;
      --panel: rgba(255,255,255,.045);
      --line: rgba(255,255,255,.11);
      --green: #78e7ae;
      --amber: #ffc36a;
      --blue: #80bfff;
      --bg: #0c0d0e;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 88% 5%, rgba(40,126,91,.2), transparent 30rem),
        radial-gradient(circle at 0% 58%, rgba(45,91,133,.13), transparent 34rem),
        var(--bg);
      color: var(--ink);
      font: 15px/1.55 Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    }}
    a {{ color: inherit; }}
    .shell {{ width: min(1180px, calc(100% - 36px)); margin: auto; }}
    header {{ padding: 78px 0 44px; border-bottom: 1px solid var(--line); }}
    .eyebrow {{ color: var(--green); font: 700 12px/1.2 ui-monospace, monospace; letter-spacing: .16em; text-transform: uppercase; }}
    h1 {{ max-width: 920px; margin: 16px 0 18px; font-size: clamp(44px, 8vw, 94px); line-height: .94; letter-spacing: -.065em; }}
    .intro {{ max-width: 720px; color: #c8c5bc; font-size: clamp(17px, 2vw, 21px); }}
    .facts {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; margin-top: 42px; background: var(--line); border: 1px solid var(--line); border-radius: 16px; overflow: hidden; }}
    .fact {{ padding: 22px; background: #111314; }}
    .fact strong {{ display: block; font-size: 27px; letter-spacing: -.04em; }}
    .fact span {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .1em; }}
    main {{ padding: 42px 0 80px; }}
    .section-head {{ display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 20px; }}
    h2 {{ margin: 0; font-size: 27px; letter-spacing: -.035em; }}
    .section-head p {{ margin: 0; color: var(--muted); }}
    .milestones {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 54px; }}
    .milestone {{ min-height: 180px; padding: 24px; border: 1px solid var(--line); border-radius: 16px; background: var(--panel); text-decoration: none; transition: .2s ease; }}
    .milestone:hover {{ transform: translateY(-3px); border-color: rgba(120,231,174,.45); background: rgba(120,231,174,.06); }}
    .milestone b {{ color: var(--green); font: 700 13px ui-monospace, monospace; }}
    .milestone h3 {{ margin: 28px 0 8px; font-size: 20px; }}
    .milestone p {{ margin: 0; color: var(--muted); }}
    .timeline-wrap {{ margin-bottom: 50px; padding: 25px; border: 1px solid var(--line); border-radius: 16px; background: var(--panel); overflow-x: auto; }}
    .timeline {{ min-width: 860px; display: grid; grid-template-columns: repeat(31, 1fr); align-items: center; position: relative; height: 88px; }}
    .timeline::before {{ content: ''; position: absolute; left: 1.6%; right: 1.6%; top: 31px; height: 1px; background: var(--line); }}
    .tick {{ position: relative; display: grid; place-items: center; gap: 10px; color: var(--muted); font: 10px ui-monospace, monospace; text-decoration: none; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; background: var(--blue); box-shadow: 0 0 0 5px var(--bg); z-index: 1; }}
    .tick.positive .dot {{ background: var(--green); }}
    .tick.learning .dot {{ background: var(--amber); }}
    .tick:hover {{ color: var(--ink); }}
    .tick:hover .dot {{ transform: scale(1.5); }}
    .tools {{ display: flex; gap: 10px; margin-bottom: 16px; }}
    input, select {{ border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; background: #111314; color: var(--ink); font: inherit; }}
    input {{ min-width: min(390px, 65vw); }}
    .reports {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
    .report {{ display: grid; grid-template-columns: 52px 1fr auto; gap: 14px; align-items: center; min-height: 92px; padding: 16px; border: 1px solid var(--line); border-radius: 13px; background: rgba(255,255,255,.025); text-decoration: none; }}
    .report:hover {{ border-color: rgba(255,255,255,.3); background: rgba(255,255,255,.055); }}
    .number {{ color: var(--muted); font: 700 15px ui-monospace, monospace; }}
    .copy strong {{ display: block; margin-bottom: 3px; }}
    .copy small {{ color: var(--muted); }}
    .signal {{ width: 8px; height: 8px; border-radius: 50%; background: var(--blue); }}
    .report.positive .signal {{ background: var(--green); }}
    .report.learning .signal {{ background: var(--amber); }}
    .empty {{ display: none; padding: 40px; color: var(--muted); text-align: center; border: 1px dashed var(--line); border-radius: 14px; }}
    footer {{ padding: 26px 0 44px; border-top: 1px solid var(--line); color: var(--muted); }}
    code {{ font-family: ui-monospace, monospace; color: #d9d5ca; }}
    @media (max-width: 760px) {{
      header {{ padding-top: 48px; }}
      .facts {{ grid-template-columns: repeat(2, 1fr); }}
      .milestones, .reports {{ grid-template-columns: 1fr; }}
      .section-head {{ align-items: start; flex-direction: column; }}
      .tools {{ align-items: stretch; flex-direction: column; }}
      input {{ min-width: 0; width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="shell">
      <div class="eyebrow">Parley / evidence trail</div>
      <h1>Progress you can inspect.</h1>
      <p class="intro">Every benchmark page is preserved here as a standalone HTML artifact. Wins, regressions, and failed hypotheses stay visible because the history matters more than a flattering chart.</p>
      <div class="facts">
        <div class="fact"><strong>{len(reports)}</strong><span>reports preserved</span></div>
        <div class="fact"><strong>{total_bytes / 1024 / 1024:.1f} MB</strong><span>archived evidence</span></div>
        <div class="fact"><strong>{'Yes' if preserved_013 else 'No'}</strong><span>report 013 intact</span></div>
        <div class="fact"><strong>{latest['number']:03d}</strong><span>latest report</span></div>
      </div>
    </div>
  </header>
  <main class="shell">
    <section>
      <div class="section-head"><h2>Milestones</h2><p>Three turning points, not a victory lap.</p></div>
      <div class="milestones">
        <a class="milestone" href="reports/013-reliability-restored-context-gap.html"><b>013</b><h3>Reliability restored</h3><p>The report explicitly preserved before later experiments.</p></a>
        <a class="milestone" href="reports/030-ninety-session-scaling-mechanism.html"><b>030</b><h3>90-session mechanism</h3><p>The scale confirmation explaining where Parley saves agent work.</p></a>
        <a class="milestone" href="reports/031-deeper-project-efficiency-win.html"><b>031</b><h3>Deeper project win</h3><p>The strict efficiency result that justified building a real product next.</p></a>
      </div>
    </section>
    <section>
      <div class="section-head"><h2>Evidence timeline</h2><p>Green: positive · amber: gap or regression · blue: neutral evidence</p></div>
      <div class="timeline-wrap"><div class="timeline" id="timeline"></div></div>
    </section>
    <section>
      <div class="section-head"><h2>All reports</h2><p>Open any report directly; no server required.</p></div>
      <div class="tools">
        <input id="search" type="search" placeholder="Search titles or report numbers" aria-label="Search reports">
        <select id="stage" aria-label="Filter by stage"><option value="">All stages</option></select>
      </div>
      <div class="reports" id="reports"></div>
      <div class="empty" id="empty">No reports match that filter.</div>
    </section>
  </main>
  <footer><div class="shell">Generated by <code>scripts/sync_progress_reports.py</code>. SHA-256 checksums live in <code>manifest.json</code>.</div></footer>
  <script id="report-data" type="application/json">{payload}</script>
  <script>
    const data = JSON.parse(document.querySelector('#report-data').textContent);
    const timeline = document.querySelector('#timeline');
    const reports = document.querySelector('#reports');
    const search = document.querySelector('#search');
    const stage = document.querySelector('#stage');
    const empty = document.querySelector('#empty');
    const stages = [...new Set(data.map(item => item.stage))];
    stages.forEach(name => stage.insertAdjacentHTML('beforeend', `<option>${{name}}</option>`));
    timeline.innerHTML = data.map(item => `<a class="tick ${{item.signal}}" href="reports/${{item.file}}" title="${{item.title.replaceAll('&', '&amp;').replaceAll('"', '&quot;')}}"><span class="dot"></span><span>${{String(item.number).padStart(3,'0')}}</span></a>`).join('');
    function render() {{
      const needle = search.value.trim().toLowerCase();
      const visible = data.filter(item => (!stage.value || item.stage === stage.value) && (!needle || `${{item.number}} ${{item.file}} ${{item.title}}`.toLowerCase().includes(needle)));
      reports.innerHTML = visible.map(item => `<a class="report ${{item.signal}}" href="reports/${{item.file}}"><span class="number">${{String(item.number).padStart(3,'0')}}</span><span class="copy"><strong>${{item.title}}</strong><small>${{item.stage}} · ${{(item.bytes / 1024).toFixed(0)}} KB</small></span><span class="signal"></span></a>`).join('');
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
