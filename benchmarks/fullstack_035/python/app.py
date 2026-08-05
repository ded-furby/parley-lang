from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, ValidationError


MAX_BODY_BYTES = 16_384
ROOT = Path(__file__).resolve().parents[3]
PUBLIC = Path(os.environ.get("RELEASE_RADAR_PUBLIC", ROOT / "examples/release-radar/public"))


class ReleaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    version: str
    tests_passed: int
    tests_total: int
    checklist_done: int
    checklist_total: int
    package_ready: bool


class ReleaseAssessment(BaseModel):
    version: str
    ready: bool
    score: int
    verdict: str
    blockers: list[str]


def readiness_score(release: ReleaseInput) -> int:
    score = 0
    if release.tests_total > 0 and release.tests_passed == release.tests_total:
        score += 60
    if release.checklist_total > 0 and release.checklist_done == release.checklist_total:
        score += 30
    if release.package_ready:
        score += 10
    return score


def assess_release(release: ReleaseInput) -> ReleaseAssessment:
    blockers: list[str] = []
    if release.tests_total <= 0:
        blockers.append("No test run was supplied.")
    elif release.tests_passed != release.tests_total:
        blockers.append("The test suite is not fully passing.")
    if release.checklist_total <= 0:
        blockers.append("No release checklist was supplied.")
    elif release.checklist_done != release.checklist_total:
        blockers.append("The release checklist is incomplete.")
    if not release.package_ready:
        blockers.append("The package artifact is not ready.")
    score = readiness_score(release)
    ready = score == 100
    verdict = (
        "Ready — every declared release gate passed."
        if ready
        else "Blocked — resolve the remaining release evidence."
    )
    return ReleaseAssessment(
        version=release.version,
        ready=ready,
        score=score,
        verdict=verdict,
        blockers=blockers,
    )


def error(code: str, status: int, detail: str) -> JSONResponse:
    return JSONResponse({"error": code, "detail": detail}, status_code=status)


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/api/status")
async def status() -> dict[str, Any]:
    return {
        "service": "Release Radar",
        "milestone": "typed-http-json-plus-browser-wasm",
        "typed_routes": 2,
        "browser_exports": 1,
        "ready": True,
    }


@app.post("/api/assess")
async def assess(request: Request) -> JSONResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json" and not content_type.endswith("+json"):
        return error("json_content_type_required", 415, "expected application/json")
    declared = request.headers.get("content-length")
    if declared and (not declared.isdigit() or int(declared) > MAX_BODY_BYTES):
        return error("body_too_large", 413, "request body exceeds 16384 bytes")
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        return error("body_too_large", 413, "request body exceeds 16384 bytes")
    try:
        value = json.loads(body)
        release = ReleaseInput.model_validate(value, strict=True)
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as exc:
        return error("invalid_json", 400, str(exc))
    return JSONResponse(assess_release(release).model_dump())


@app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def missing_api(rest: str) -> JSONResponse:
    return error("not_found", 404, f"no API route /api/{rest}")


@app.get("/parley.js")
async def browser_module() -> FileResponse:
    return FileResponse(Path(__file__).with_name("browser.js"), media_type="text/javascript")


app.mount("/", StaticFiles(directory=PUBLIC, html=True), name="public")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("PARLEY_WEB_PORT", "8787")),
        log_level="warning",
    )
