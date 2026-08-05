#!/usr/bin/env python3
"""Execute the frozen Release Radar browser case with system Playwright."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright


url = sys.argv[1]
screenshot = Path(sys.argv[2]) if len(sys.argv) > 2 else None
console_errors: list[str] = []

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    try:
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.goto(url, wait_until="networkidle", timeout=30_000)
        page.locator("#version").fill("0.4.0")
        page.locator("#tests-passed").fill("394")
        page.locator("#tests-total").fill("394")
        page.locator("#checklist-done").fill("12")
        page.locator("#checklist-total").fill("12")
        page.locator("#package-ready").check()
        page.wait_for_function(
            'document.querySelector("#local-score")?.textContent === "100"'
        )
        page.locator("#assess-button").click()
        page.wait_for_function(
            'document.querySelector("#confirmed-score")?.textContent === "100"'
        )
        result = page.evaluate(
            """() => ({
              local_score: document.querySelector("#local-score")?.textContent ?? "",
              confirmed_score: document.querySelector("#confirmed-score")?.textContent ?? "",
              verdict: document.querySelector("#verdict")?.textContent ?? "",
              gate_states: Array.from(document.querySelectorAll(".gate-state"))
                .map((node) => node.textContent ?? ""),
              runtime_proof: document.querySelector("#runtime-proof")?.textContent ?? "",
            })"""
        )
        result["console_errors"] = console_errors
        result["pass"] = (
            result["local_score"] == "100"
            and result["confirmed_score"] == "100"
            and "Ready" in result["verdict"]
            and result["gate_states"] == ["pass", "pass", "pass"]
            and not console_errors
        )
        if screenshot:
            page.screenshot(path=str(screenshot), full_page=True)
        print(json.dumps(result, ensure_ascii=False))
    finally:
        browser.close()
