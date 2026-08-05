import { loadParley } from "/parley.js";

const $ = (selector) => document.querySelector(selector);
const form = $("#release-form");
const button = $("#assess-button");
let parley;

const inputValue = () => ({
  version: $("#version").value.trim(),
  tests_passed: Number($("#tests-passed").value),
  tests_total: Number($("#tests-total").value),
  checklist_done: Number($("#checklist-done").value),
  checklist_total: Number($("#checklist-total").value),
  package_ready: $("#package-ready").checked,
});

const setSystemState = (label, state = "") => {
  const node = $(".system-state");
  node.className = `system-state ${state}`.trim();
  $("#system-label").textContent = label;
};

const updateGate = (selector, pass) => {
  const node = $(selector);
  node.textContent = pass ? "pass" : "blocked";
  node.className = `gate-state ${pass ? "pass" : "fail"}`;
};

const updateLocalScore = () => {
  if (!parley) return;
  const value = inputValue();
  const score = parley.readiness_score(
    value.tests_passed,
    value.tests_total,
    value.checklist_done,
    value.checklist_total,
    value.package_ready,
  );
  $("#local-score").textContent = Number(score);
};

const renderAssessment = (assessment, input) => {
  $("#confirmed-score").textContent = assessment.score;
  const fill = $("#score-fill");
  fill.style.width = `${Math.max(0, Math.min(100, assessment.score))}%`;
  fill.style.background = assessment.ready ? "var(--green)" : "var(--red)";

  updateGate("#tests-state", input.tests_total > 0 && input.tests_passed === input.tests_total);
  updateGate("#checklist-state", input.checklist_total > 0 && input.checklist_done === input.checklist_total);
  updateGate("#package-state", input.package_ready);

  const verdict = $("#verdict");
  verdict.textContent = `${assessment.version}: ${assessment.verdict}`;
  verdict.className = `verdict ${assessment.ready ? "ready" : "blocked"}`;
  $("#blockers").replaceChildren(...assessment.blockers.map((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    return item;
  }));
};

form.addEventListener("input", updateLocalScore);
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = inputValue();
  button.disabled = true;
  button.firstChild.textContent = "Checking typed route… ";
  try {
    const response = await fetch("/api/assess", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(input),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || body.error || "Assessment failed");
    renderAssessment(body, input);
  } catch (error) {
    const verdict = $("#verdict");
    verdict.textContent = error.message;
    verdict.className = "verdict blocked";
  } finally {
    button.disabled = false;
    button.firstChild.textContent = "Confirm with typed backend ";
  }
});

try {
  const [wasm, response] = await Promise.all([
    loadParley(),
    fetch("/api/status"),
  ]);
  if (!response.ok) throw new Error(`API status ${response.status}`);
  const status = await response.json();
  parley = wasm;
  updateLocalScore();
  setSystemState(`${status.typed_routes} typed routes · ${status.browser_exports} WASM export`, "ready");
  $("#runtime-proof").textContent = "WASM ready · native API ready";
} catch (error) {
  setSystemState(error.message, "failed");
  $("#runtime-proof").textContent = "Runtime check failed";
}
