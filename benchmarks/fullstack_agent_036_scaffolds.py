"""Generate the frozen language workspaces for full-stack agent study 036."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS_PATH = BENCHMARKS / "fullstack_agent_036_tasks.json"
LANGUAGES = ("parley", "python", "typescript", "rust")


@dataclass(frozen=True)
class ScaffoldFile:
    text: str
    editable: bool


def load_task_map() -> dict[str, dict[str, Any]]:
    payload = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    return {task["id"]: task for task in payload["tasks"]}


def _clean(text: str) -> str:
    return text.strip("\n") + "\n"


def _contract(task: dict[str, Any]) -> str:
    request = "\n".join(
        f"- `{name}`: {kind}" for name, kind in task["request_fields"].items()
    )
    response = "\n".join(
        f"- `{name}`: {kind}" for name, kind in task["response_fields"].items()
    )
    return _clean(
        f"""
        # {task['title']}

        {task['statement']}

        ## HTTP

        - `GET {task['status_route']}` returns `{{"service":"{task['service']}","ready":true}}`.
        - `POST {task['post_route']}` accepts strict JSON and returns strict JSON.
        - Unknown, missing, or wrongly typed fields are invalid JSON.

        Request fields:

        {request}

        Response fields:

        {response}

        ## Browser

        Export `{task['browser_export']}` with request fields in the order listed
        above. It returns the same value as response field
        `{task['shared_result_field']}` for equivalent inputs.
        """
    ).replace("        ", "")


PUBLIC_INDEX = _clean(
    """
    <!doctype html>
    <meta charset="utf-8">
    <title>Full-stack agent study 036</title>
    <main>Full-stack agent study 036 browser target</main>
    """
).replace("    ", "")


PARLEY_LOGIC: dict[str, dict[str, str]] = {
    "shipping_quote_build": {
        "seed": """
to quote_subtotal with weight_units as number, zone as number giving number:
    give back 0

to quote_surcharge with fragile as yesno giving number:
    give back 0

to quote_total with weight_units as number, zone as number, fragile as yesno giving number:
    give back 0
""",
        "reference": """
to quote_subtotal with weight_units as number, zone as number giving number:
    give back 500 plus weight_units times 120 plus zone times 80

to quote_surcharge with fragile as yesno giving number:
    if fragile:
        give back 250
    give back 0

to quote_total with weight_units as number, zone as number, fragile as yesno giving number:
    give back (quote_subtotal with weight_units, zone) plus (quote_surcharge with fragile)
""",
    },
    "capacity_planner_build": {
        "seed": """
to usable_slots with slots as number, reserved as number giving number:
    give back 0

to demand_jobs with requested as number, priority as yesno giving number:
    give back 0

to accepted_jobs with slots as number, reserved as number, requested as number, priority as yesno giving number:
    give back 0

to overflow_jobs with slots as number, reserved as number, requested as number, priority as yesno giving number:
    give back 0
""",
        "reference": """
to usable_slots with slots as number, reserved as number giving number:
    let usable be slots minus reserved
    if usable is less than 0:
        give back 0
    give back usable

to demand_jobs with requested as number, priority as yesno giving number:
    if priority:
        give back requested plus 2
    give back requested

to accepted_jobs with slots as number, reserved as number, requested as number, priority as yesno giving number:
    let usable be (usable_slots with slots, reserved)
    let demand be (demand_jobs with requested, priority)
    if demand is less than usable:
        give back demand
    give back usable

to overflow_jobs with slots as number, reserved as number, requested as number, priority as yesno giving number:
    let overflow be (demand_jobs with requested, priority) minus (usable_slots with slots, reserved)
    if overflow is less than 0:
        give back 0
    give back overflow
""",
    },
    "quota_carryover_repair": {
        "seed": """
to effective_limit with limit as number, carryover as number giving number:
    give back limit plus carryover

to remaining_units with used as number, limit as number, carryover as number giving number:
    let remaining be (effective_limit with limit, carryover) minus used
    if remaining is less than 0:
        give back 0
    give back remaining

to remaining_percent with used as number, limit as number, carryover as number giving number:
    let remaining be (remaining_units with used, limit, carryover)
    if limit is 0:
        give back 0
    give back number from ((remaining times 100) divided by limit)
""",
        "reference": """
to effective_limit with limit as number, carryover as number giving number:
    give back limit plus carryover

to remaining_units with used as number, limit as number, carryover as number giving number:
    let remaining be (effective_limit with limit, carryover) minus used
    if remaining is less than 0:
        give back 0
    give back remaining

to remaining_percent with used as number, limit as number, carryover as number giving number:
    let effective be (effective_limit with limit, carryover)
    if effective is 0:
        give back 0
    let remaining be (remaining_units with used, limit, carryover)
    give back number from ((remaining times 100) divided by effective)
""",
    },
    "tenant_cache_repair": {
        "seed": """
to cache_token with tenant_id as number, resource_id as number, generation as number giving number:
    give back resource_id times 1000 plus generation
""",
        "reference": """
to cache_token with tenant_id as number, resource_id as number, generation as number giving number:
    give back tenant_id times 1000000 plus resource_id times 1000 plus generation
""",
    },
}


PARLEY_MAIN: dict[str, str] = {
    "shipping_quote_build": """
include "logic.par"

a quote_request has weight_units as number, zone as number, fragile as yesno
a quote_response has subtotal_cents as number, surcharge_cents as number, total_cents as number, service as text
a service_status has service as text, ready as yesno

to project_status giving service_status:
    give back a service_status with service "Shipping Quote", ready yes

to handle_request with request as quote_request giving quote_response:
    let subtotal be (quote_subtotal with request's weight_units, request's zone)
    let surcharge be (quote_surcharge with request's fragile)
    let total be (quote_total with request's weight_units, request's zone, request's fragile)
    let service be "economy"
    if total is at least 1500:
        set service to "tracked"
    give back a quote_response with subtotal_cents subtotal, surcharge_cents surcharge, total_cents total, service service
""",
    "capacity_planner_build": """
include "logic.par"

a plan_request has slots as number, reserved as number, requested as number, priority as yesno
a plan_response has usable as number, demand as number, accepted as number, overflow as number, state as text
a service_status has service as text, ready as yesno

to project_status giving service_status:
    give back a service_status with service "Capacity Planner", ready yes

to handle_request with request as plan_request giving plan_response:
    let usable be (usable_slots with request's slots, request's reserved)
    let demand be (demand_jobs with request's requested, request's priority)
    let accepted be (accepted_jobs with request's slots, request's reserved, request's requested, request's priority)
    let overflow be (overflow_jobs with request's slots, request's reserved, request's requested, request's priority)
    let state be "clear"
    if overflow is more than 0:
        set state to "overloaded"
    give back a plan_response with usable usable, demand demand, accepted accepted, overflow overflow, state state
""",
    "quota_carryover_repair": """
include "logic.par"

a quota_request has used as number, limit as number, carryover as number
a quota_response has effective_limit as number, remaining as number, remaining_percent as number, state as text
a service_status has service as text, ready as yesno

to project_status giving service_status:
    give back a service_status with service "Quota Surface", ready yes

to handle_request with request as quota_request giving quota_response:
    let effective be (effective_limit with request's limit, request's carryover)
    let remaining be (remaining_units with request's used, request's limit, request's carryover)
    let percent be (remaining_percent with request's used, request's limit, request's carryover)
    let state be "available"
    if remaining is 0:
        set state to "exhausted"
    give back a quota_response with effective_limit effective, remaining remaining, remaining_percent percent, state state
""",
    "tenant_cache_repair": """
include "logic.par"

a cache_request has tenant_id as number, resource_id as number, generation as number
a cache_response has token as number, state as text
a service_status has service as text, ready as yesno

to project_status giving service_status:
    give back a service_status with service "Tenant Cache", ready yes

to handle_request with request as cache_request giving cache_response:
    let token be (cache_token with request's tenant_id, request's resource_id, request's generation)
    give back a cache_response with token token, state "isolated"
""",
}


PYTHON_LOGIC: dict[str, dict[str, str]] = {
    "shipping_quote_build": {
        "seed": """
from pydantic import BaseModel, ConfigDict

class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    weight_units: int
    zone: int
    fragile: bool

def quote_subtotal(weight_units: int, zone: int) -> int:
    return 0

def quote_surcharge(fragile: bool) -> int:
    return 0

def quote_total(weight_units: int, zone: int, fragile: bool) -> int:
    return 0

def handle(value: RequestInput) -> dict[str, object]:
    total = quote_total(value.weight_units, value.zone, value.fragile)
    return {"subtotal_cents": quote_subtotal(value.weight_units, value.zone), "surcharge_cents": quote_surcharge(value.fragile), "total_cents": total, "service": "tracked" if total >= 1500 else "economy"}
""",
        "reference": """
from pydantic import BaseModel, ConfigDict

class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    weight_units: int
    zone: int
    fragile: bool

def quote_subtotal(weight_units: int, zone: int) -> int:
    return 500 + weight_units * 120 + zone * 80

def quote_surcharge(fragile: bool) -> int:
    return 250 if fragile else 0

def quote_total(weight_units: int, zone: int, fragile: bool) -> int:
    return quote_subtotal(weight_units, zone) + quote_surcharge(fragile)

def handle(value: RequestInput) -> dict[str, object]:
    total = quote_total(value.weight_units, value.zone, value.fragile)
    return {"subtotal_cents": quote_subtotal(value.weight_units, value.zone), "surcharge_cents": quote_surcharge(value.fragile), "total_cents": total, "service": "tracked" if total >= 1500 else "economy"}
""",
    },
    "capacity_planner_build": {
        "seed": """
from pydantic import BaseModel, ConfigDict

class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    slots: int
    reserved: int
    requested: int
    priority: bool

def usable_slots(slots: int, reserved: int) -> int: return 0
def demand_jobs(requested: int, priority: bool) -> int: return 0
def accepted_jobs(slots: int, reserved: int, requested: int, priority: bool) -> int: return 0
def overflow_jobs(slots: int, reserved: int, requested: int, priority: bool) -> int: return 0

def handle(value: RequestInput) -> dict[str, object]:
    usable = usable_slots(value.slots, value.reserved)
    demand = demand_jobs(value.requested, value.priority)
    accepted = accepted_jobs(value.slots, value.reserved, value.requested, value.priority)
    overflow = overflow_jobs(value.slots, value.reserved, value.requested, value.priority)
    return {"usable": usable, "demand": demand, "accepted": accepted, "overflow": overflow, "state": "overloaded" if overflow > 0 else "clear"}
""",
        "reference": """
from pydantic import BaseModel, ConfigDict

class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    slots: int
    reserved: int
    requested: int
    priority: bool

def usable_slots(slots: int, reserved: int) -> int: return max(slots - reserved, 0)
def demand_jobs(requested: int, priority: bool) -> int: return requested + (2 if priority else 0)
def accepted_jobs(slots: int, reserved: int, requested: int, priority: bool) -> int: return min(usable_slots(slots, reserved), demand_jobs(requested, priority))
def overflow_jobs(slots: int, reserved: int, requested: int, priority: bool) -> int: return max(demand_jobs(requested, priority) - usable_slots(slots, reserved), 0)

def handle(value: RequestInput) -> dict[str, object]:
    usable = usable_slots(value.slots, value.reserved)
    demand = demand_jobs(value.requested, value.priority)
    accepted = accepted_jobs(value.slots, value.reserved, value.requested, value.priority)
    overflow = overflow_jobs(value.slots, value.reserved, value.requested, value.priority)
    return {"usable": usable, "demand": demand, "accepted": accepted, "overflow": overflow, "state": "overloaded" if overflow > 0 else "clear"}
""",
    },
    "quota_carryover_repair": {
        "seed": """
from pydantic import BaseModel, ConfigDict

class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    used: int
    limit: int
    carryover: int

def effective_limit(limit: int, carryover: int) -> int: return limit + carryover
def remaining_units(used: int, limit: int, carryover: int) -> int: return max(effective_limit(limit, carryover) - used, 0)
def remaining_percent(used: int, limit: int, carryover: int) -> int:
    return 0 if limit == 0 else remaining_units(used, limit, carryover) * 100 // limit

def handle(value: RequestInput) -> dict[str, object]:
    effective = effective_limit(value.limit, value.carryover)
    remaining = remaining_units(value.used, value.limit, value.carryover)
    return {"effective_limit": effective, "remaining": remaining, "remaining_percent": remaining_percent(value.used, value.limit, value.carryover), "state": "exhausted" if remaining == 0 else "available"}
""",
        "reference": """
from pydantic import BaseModel, ConfigDict

class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    used: int
    limit: int
    carryover: int

def effective_limit(limit: int, carryover: int) -> int: return limit + carryover
def remaining_units(used: int, limit: int, carryover: int) -> int: return max(effective_limit(limit, carryover) - used, 0)
def remaining_percent(used: int, limit: int, carryover: int) -> int:
    effective = effective_limit(limit, carryover)
    return 0 if effective == 0 else remaining_units(used, limit, carryover) * 100 // effective

def handle(value: RequestInput) -> dict[str, object]:
    effective = effective_limit(value.limit, value.carryover)
    remaining = remaining_units(value.used, value.limit, value.carryover)
    return {"effective_limit": effective, "remaining": remaining, "remaining_percent": remaining_percent(value.used, value.limit, value.carryover), "state": "exhausted" if remaining == 0 else "available"}
""",
    },
    "tenant_cache_repair": {
        "seed": """
from pydantic import BaseModel, ConfigDict

class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tenant_id: int
    resource_id: int
    generation: int

def cache_token(tenant_id: int, resource_id: int, generation: int) -> int:
    return resource_id * 1000 + generation

def handle(value: RequestInput) -> dict[str, object]:
    return {"token": cache_token(value.tenant_id, value.resource_id, value.generation), "state": "isolated"}
""",
        "reference": """
from pydantic import BaseModel, ConfigDict

class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tenant_id: int
    resource_id: int
    generation: int

def cache_token(tenant_id: int, resource_id: int, generation: int) -> int:
    return tenant_id * 1000000 + resource_id * 1000 + generation

def handle(value: RequestInput) -> dict[str, object]:
    return {"token": cache_token(value.tenant_id, value.resource_id, value.generation), "state": "isolated"}
""",
    },
}


PYTHON_BROWSER: dict[str, dict[str, str]] = {
    "shipping_quote_build": {
        "seed": "const quoteTotal = () => 0n;",
        "reference": "const quoteTotal = (weight, zone, fragile) => BigInt(500 + weight * 120 + zone * 80 + (fragile ? 250 : 0));",
    },
    "capacity_planner_build": {
        "seed": "const acceptedJobs = () => 0n;",
        "reference": "const acceptedJobs = (slots, reserved, requested, priority) => BigInt(Math.min(Math.max(slots - reserved, 0), requested + (priority ? 2 : 0)));",
    },
    "quota_carryover_repair": {
        "seed": "const remainingPercent = (used, limit, carryover) => BigInt(limit === 0 ? 0 : Math.trunc(Math.max(limit + carryover - used, 0) * 100 / limit));",
        "reference": "const remainingPercent = (used, limit, carryover) => { const effective = limit + carryover; return BigInt(effective === 0 ? 0 : Math.trunc(Math.max(effective - used, 0) * 100 / effective)); };",
    },
    "tenant_cache_repair": {
        "seed": "const cacheToken = (tenant, resource, generation) => BigInt(resource * 1000 + generation);",
        "reference": "const cacheToken = (tenant, resource, generation) => BigInt(tenant * 1000000 + resource * 1000 + generation);",
    },
}


PYTHON_BROWSER_EXPORT = {
    "shipping_quote_build": ("quote_total", "quoteTotal"),
    "capacity_planner_build": ("accepted_jobs", "acceptedJobs"),
    "quota_carryover_repair": ("remaining_percent", "remainingPercent"),
    "tenant_cache_repair": ("cache_token", "cacheToken"),
}


PYTHON_APP_TEMPLATE = r'''
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from logic import RequestInput, handle

MAX_BODY_BYTES = 16_384
PUBLIC = Path(__file__).with_name("public")

def error(code: str, status: int, detail: str) -> JSONResponse:
    return JSONResponse({"error": code, "detail": detail}, status_code=status)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.get("/api/status")
async def status() -> dict[str, object]:
    return {"service": "@@SERVICE@@", "ready": True}

@app.post("@@ROUTE@@")
async def endpoint(request: Request) -> JSONResponse:
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
        parsed = RequestInput.model_validate(value, strict=True)
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as exc:
        return error("invalid_json", 400, str(exc))
    return JSONResponse(handle(parsed))

@app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def missing_api(rest: str) -> JSONResponse:
    return error("not_found", 404, f"no API route /api/{rest}")

@app.get("/parley.js")
async def browser_module() -> FileResponse:
    return FileResponse(Path(__file__).with_name("browser.js"), media_type="text/javascript")

app.mount("/", StaticFiles(directory=PUBLIC, html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ["PARLEY_WEB_PORT"]), log_level="warning")
'''


TYPESCRIPT_LOGIC: dict[str, dict[str, str]] = {
    "shipping_quote_build": {
        "seed": """
export type RequestInput = { weight_units: number; zone: number; fragile: boolean };
export const quoteSubtotal = (_weight: number, _zone: number) => 0;
export const quoteSurcharge = (_fragile: boolean) => 0;
export const quoteTotal = (_weight: number, _zone: number, _fragile: boolean) => 0;
export const handle = (value: RequestInput) => { const total = quoteTotal(value.weight_units, value.zone, value.fragile); return { subtotal_cents: quoteSubtotal(value.weight_units, value.zone), surcharge_cents: quoteSurcharge(value.fragile), total_cents: total, service: total >= 1500 ? "tracked" : "economy" }; };
export async function loadParley() { return { quote_total: (weight: number, zone: number, fragile: boolean) => BigInt(quoteTotal(weight, zone, fragile)) }; }
""",
        "reference": """
export type RequestInput = { weight_units: number; zone: number; fragile: boolean };
export const quoteSubtotal = (weight: number, zone: number) => 500 + weight * 120 + zone * 80;
export const quoteSurcharge = (fragile: boolean) => fragile ? 250 : 0;
export const quoteTotal = (weight: number, zone: number, fragile: boolean) => quoteSubtotal(weight, zone) + quoteSurcharge(fragile);
export const handle = (value: RequestInput) => { const total = quoteTotal(value.weight_units, value.zone, value.fragile); return { subtotal_cents: quoteSubtotal(value.weight_units, value.zone), surcharge_cents: quoteSurcharge(value.fragile), total_cents: total, service: total >= 1500 ? "tracked" : "economy" }; };
export async function loadParley() { return { quote_total: (weight: number, zone: number, fragile: boolean) => BigInt(quoteTotal(weight, zone, fragile)) }; }
""",
    },
    "capacity_planner_build": {
        "seed": """
export type RequestInput = { slots: number; reserved: number; requested: number; priority: boolean };
export const usableSlots = (_slots: number, _reserved: number) => 0;
export const demandJobs = (_requested: number, _priority: boolean) => 0;
export const acceptedJobs = (_slots: number, _reserved: number, _requested: number, _priority: boolean) => 0;
export const overflowJobs = (_slots: number, _reserved: number, _requested: number, _priority: boolean) => 0;
export const handle = (value: RequestInput) => { const usable = usableSlots(value.slots, value.reserved); const demand = demandJobs(value.requested, value.priority); const accepted = acceptedJobs(value.slots, value.reserved, value.requested, value.priority); const overflow = overflowJobs(value.slots, value.reserved, value.requested, value.priority); return { usable, demand, accepted, overflow, state: overflow > 0 ? "overloaded" : "clear" }; };
export async function loadParley() { return { accepted_jobs: (slots: number, reserved: number, requested: number, priority: boolean) => BigInt(acceptedJobs(slots, reserved, requested, priority)) }; }
""",
        "reference": """
export type RequestInput = { slots: number; reserved: number; requested: number; priority: boolean };
export const usableSlots = (slots: number, reserved: number) => Math.max(slots - reserved, 0);
export const demandJobs = (requested: number, priority: boolean) => requested + (priority ? 2 : 0);
export const acceptedJobs = (slots: number, reserved: number, requested: number, priority: boolean) => Math.min(usableSlots(slots, reserved), demandJobs(requested, priority));
export const overflowJobs = (slots: number, reserved: number, requested: number, priority: boolean) => Math.max(demandJobs(requested, priority) - usableSlots(slots, reserved), 0);
export const handle = (value: RequestInput) => { const usable = usableSlots(value.slots, value.reserved); const demand = demandJobs(value.requested, value.priority); const accepted = acceptedJobs(value.slots, value.reserved, value.requested, value.priority); const overflow = overflowJobs(value.slots, value.reserved, value.requested, value.priority); return { usable, demand, accepted, overflow, state: overflow > 0 ? "overloaded" : "clear" }; };
export async function loadParley() { return { accepted_jobs: (slots: number, reserved: number, requested: number, priority: boolean) => BigInt(acceptedJobs(slots, reserved, requested, priority)) }; }
""",
    },
    "quota_carryover_repair": {
        "seed": """
export type RequestInput = { used: number; limit: number; carryover: number };
export const effectiveLimit = (limit: number, carryover: number) => limit + carryover;
export const remainingUnits = (used: number, limit: number, carryover: number) => Math.max(effectiveLimit(limit, carryover) - used, 0);
export const remainingPercent = (used: number, limit: number, carryover: number) => limit === 0 ? 0 : Math.trunc(remainingUnits(used, limit, carryover) * 100 / limit);
export const handle = (value: RequestInput) => { const effective_limit = effectiveLimit(value.limit, value.carryover); const remaining = remainingUnits(value.used, value.limit, value.carryover); return { effective_limit, remaining, remaining_percent: remainingPercent(value.used, value.limit, value.carryover), state: remaining === 0 ? "exhausted" : "available" }; };
export async function loadParley() { return { remaining_percent: (used: number, limit: number, carryover: number) => BigInt(remainingPercent(used, limit, carryover)) }; }
""",
        "reference": """
export type RequestInput = { used: number; limit: number; carryover: number };
export const effectiveLimit = (limit: number, carryover: number) => limit + carryover;
export const remainingUnits = (used: number, limit: number, carryover: number) => Math.max(effectiveLimit(limit, carryover) - used, 0);
export const remainingPercent = (used: number, limit: number, carryover: number) => { const effective = effectiveLimit(limit, carryover); return effective === 0 ? 0 : Math.trunc(remainingUnits(used, limit, carryover) * 100 / effective); };
export const handle = (value: RequestInput) => { const effective_limit = effectiveLimit(value.limit, value.carryover); const remaining = remainingUnits(value.used, value.limit, value.carryover); return { effective_limit, remaining, remaining_percent: remainingPercent(value.used, value.limit, value.carryover), state: remaining === 0 ? "exhausted" : "available" }; };
export async function loadParley() { return { remaining_percent: (used: number, limit: number, carryover: number) => BigInt(remainingPercent(used, limit, carryover)) }; }
""",
    },
    "tenant_cache_repair": {
        "seed": """
export type RequestInput = { tenant_id: number; resource_id: number; generation: number };
export const cacheToken = (_tenant: number, resource: number, generation: number) => resource * 1000 + generation;
export const handle = (value: RequestInput) => ({ token: cacheToken(value.tenant_id, value.resource_id, value.generation), state: "isolated" });
export async function loadParley() { return { cache_token: (tenant: number, resource: number, generation: number) => BigInt(cacheToken(tenant, resource, generation)) }; }
""",
        "reference": """
export type RequestInput = { tenant_id: number; resource_id: number; generation: number };
export const cacheToken = (tenant: number, resource: number, generation: number) => tenant * 1000000 + resource * 1000 + generation;
export const handle = (value: RequestInput) => ({ token: cacheToken(value.tenant_id, value.resource_id, value.generation), state: "isolated" });
export async function loadParley() { return { cache_token: (tenant: number, resource: number, generation: number) => BigInt(cacheToken(tenant, resource, generation)) }; }
""",
    },
}


TS_SCHEMA = {
    "shipping_quote_build": "z.object({ weight_units: z.number().int(), zone: z.number().int(), fragile: z.boolean() }).strict()",
    "capacity_planner_build": "z.object({ slots: z.number().int(), reserved: z.number().int(), requested: z.number().int(), priority: z.boolean() }).strict()",
    "quota_carryover_repair": "z.object({ used: z.number().int(), limit: z.number().int(), carryover: z.number().int() }).strict()",
    "tenant_cache_repair": "z.object({ tenant_id: z.number().int(), resource_id: z.number().int(), generation: z.number().int() }).strict()",
}


TS_SERVER_TEMPLATE = r'''
import { serve } from "@hono/node-server";
import { serveStatic } from "@hono/node-server/serve-static";
import { Hono } from "hono";
import { z } from "zod";
import { handle } from "./logic.js";

declare const process: { env: Record<string, string | undefined> };
const maxBodyBytes = 16_384;
const schema = @@SCHEMA@@;
const response = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
const error = (code: string, status: number, detail: string) => response({ error: code, detail }, status);
const app = new Hono();

app.get("/api/status", () => response({ service: "@@SERVICE@@", ready: true }));
app.post("@@ROUTE@@", async (context) => {
  const mediaType = (context.req.header("content-type") ?? "").split(";", 1)[0]!.trim().toLowerCase();
  if (mediaType !== "application/json" && !mediaType.endsWith("+json")) return error("json_content_type_required", 415, "expected application/json");
  const declared = context.req.header("content-length");
  if (declared && (!/^\d+$/.test(declared) || Number(declared) > maxBodyBytes)) return error("body_too_large", 413, "request body exceeds 16384 bytes");
  const raw = await context.req.arrayBuffer();
  if (raw.byteLength > maxBodyBytes) return error("body_too_large", 413, "request body exceeds 16384 bytes");
  try {
    const value: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(raw));
    const parsed = schema.safeParse(value);
    if (!parsed.success) return error("invalid_json", 400, parsed.error.message);
    return response(handle(parsed.data));
  } catch (caught) { return error("invalid_json", 400, String(caught)); }
});
app.all("/api/*", (context) => error("not_found", 404, `no API route ${context.req.path}`));
app.get("/parley.js", serveStatic({ path: process.env.FULLSTACK_036_BROWSER ?? "./dist/logic.js" }));
app.get("/*", serveStatic({ root: "./public" }));
serve({ fetch: app.fetch, hostname: "127.0.0.1", port: Number(process.env.PARLEY_WEB_PORT) });
'''


RUST_LIB: dict[str, dict[str, str]] = {
    "shipping_quote_build": {
        "seed": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub weight_units: i64, pub zone: i64, pub fragile: bool }
#[derive(Serialize)] pub struct ResponseOutput { pub subtotal_cents: i64, pub surcharge_cents: i64, pub total_cents: i64, pub service: String }
pub fn quote_subtotal(_weight: i64, _zone: i64) -> i64 { 0 }
pub fn quote_surcharge(_fragile: bool) -> i64 { 0 }
pub fn quote_total(_weight: i64, _zone: i64, _fragile: bool) -> i64 { 0 }
pub fn handle(value: RequestInput) -> ResponseOutput { let total = quote_total(value.weight_units, value.zone, value.fragile); ResponseOutput { subtotal_cents: quote_subtotal(value.weight_units, value.zone), surcharge_cents: quote_surcharge(value.fragile), total_cents: total, service: if total >= 1500 { "tracked".into() } else { "economy".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_quote_total(weight: i64, zone: i64, fragile: i32) -> i64 { quote_total(weight, zone, fragile != 0) }
""",
        "reference": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub weight_units: i64, pub zone: i64, pub fragile: bool }
#[derive(Serialize)] pub struct ResponseOutput { pub subtotal_cents: i64, pub surcharge_cents: i64, pub total_cents: i64, pub service: String }
pub fn quote_subtotal(weight: i64, zone: i64) -> i64 { 500 + weight * 120 + zone * 80 }
pub fn quote_surcharge(fragile: bool) -> i64 { if fragile { 250 } else { 0 } }
pub fn quote_total(weight: i64, zone: i64, fragile: bool) -> i64 { quote_subtotal(weight, zone) + quote_surcharge(fragile) }
pub fn handle(value: RequestInput) -> ResponseOutput { let total = quote_total(value.weight_units, value.zone, value.fragile); ResponseOutput { subtotal_cents: quote_subtotal(value.weight_units, value.zone), surcharge_cents: quote_surcharge(value.fragile), total_cents: total, service: if total >= 1500 { "tracked".into() } else { "economy".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_quote_total(weight: i64, zone: i64, fragile: i32) -> i64 { quote_total(weight, zone, fragile != 0) }
""",
    },
    "capacity_planner_build": {
        "seed": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub slots: i64, pub reserved: i64, pub requested: i64, pub priority: bool }
#[derive(Serialize)] pub struct ResponseOutput { pub usable: i64, pub demand: i64, pub accepted: i64, pub overflow: i64, pub state: String }
pub fn usable_slots(_slots: i64, _reserved: i64) -> i64 { 0 }
pub fn demand_jobs(_requested: i64, _priority: bool) -> i64 { 0 }
pub fn accepted_jobs(_slots: i64, _reserved: i64, _requested: i64, _priority: bool) -> i64 { 0 }
pub fn overflow_jobs(_slots: i64, _reserved: i64, _requested: i64, _priority: bool) -> i64 { 0 }
pub fn handle(value: RequestInput) -> ResponseOutput { let usable = usable_slots(value.slots, value.reserved); let demand = demand_jobs(value.requested, value.priority); let accepted = accepted_jobs(value.slots, value.reserved, value.requested, value.priority); let overflow = overflow_jobs(value.slots, value.reserved, value.requested, value.priority); ResponseOutput { usable, demand, accepted, overflow, state: if overflow > 0 { "overloaded".into() } else { "clear".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_accepted_jobs(slots: i64, reserved: i64, requested: i64, priority: i32) -> i64 { accepted_jobs(slots, reserved, requested, priority != 0) }
""",
        "reference": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub slots: i64, pub reserved: i64, pub requested: i64, pub priority: bool }
#[derive(Serialize)] pub struct ResponseOutput { pub usable: i64, pub demand: i64, pub accepted: i64, pub overflow: i64, pub state: String }
pub fn usable_slots(slots: i64, reserved: i64) -> i64 { (slots - reserved).max(0) }
pub fn demand_jobs(requested: i64, priority: bool) -> i64 { requested + if priority { 2 } else { 0 } }
pub fn accepted_jobs(slots: i64, reserved: i64, requested: i64, priority: bool) -> i64 { usable_slots(slots, reserved).min(demand_jobs(requested, priority)) }
pub fn overflow_jobs(slots: i64, reserved: i64, requested: i64, priority: bool) -> i64 { (demand_jobs(requested, priority) - usable_slots(slots, reserved)).max(0) }
pub fn handle(value: RequestInput) -> ResponseOutput { let usable = usable_slots(value.slots, value.reserved); let demand = demand_jobs(value.requested, value.priority); let accepted = accepted_jobs(value.slots, value.reserved, value.requested, value.priority); let overflow = overflow_jobs(value.slots, value.reserved, value.requested, value.priority); ResponseOutput { usable, demand, accepted, overflow, state: if overflow > 0 { "overloaded".into() } else { "clear".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_accepted_jobs(slots: i64, reserved: i64, requested: i64, priority: i32) -> i64 { accepted_jobs(slots, reserved, requested, priority != 0) }
""",
    },
    "quota_carryover_repair": {
        "seed": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub used: i64, pub limit: i64, pub carryover: i64 }
#[derive(Serialize)] pub struct ResponseOutput { pub effective_limit: i64, pub remaining: i64, pub remaining_percent: i64, pub state: String }
pub fn effective_limit(limit: i64, carryover: i64) -> i64 { limit + carryover }
pub fn remaining_units(used: i64, limit: i64, carryover: i64) -> i64 { (effective_limit(limit, carryover) - used).max(0) }
pub fn remaining_percent(used: i64, limit: i64, carryover: i64) -> i64 { if limit == 0 { 0 } else { remaining_units(used, limit, carryover) * 100 / limit } }
pub fn handle(value: RequestInput) -> ResponseOutput { let effective_limit = effective_limit(value.limit, value.carryover); let remaining = remaining_units(value.used, value.limit, value.carryover); ResponseOutput { effective_limit, remaining, remaining_percent: remaining_percent(value.used, value.limit, value.carryover), state: if remaining == 0 { "exhausted".into() } else { "available".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_remaining_percent(used: i64, limit: i64, carryover: i64) -> i64 { remaining_percent(used, limit, carryover) }
""",
        "reference": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub used: i64, pub limit: i64, pub carryover: i64 }
#[derive(Serialize)] pub struct ResponseOutput { pub effective_limit: i64, pub remaining: i64, pub remaining_percent: i64, pub state: String }
pub fn effective_limit(limit: i64, carryover: i64) -> i64 { limit + carryover }
pub fn remaining_units(used: i64, limit: i64, carryover: i64) -> i64 { (effective_limit(limit, carryover) - used).max(0) }
pub fn remaining_percent(used: i64, limit: i64, carryover: i64) -> i64 { let effective = effective_limit(limit, carryover); if effective == 0 { 0 } else { remaining_units(used, limit, carryover) * 100 / effective } }
pub fn handle(value: RequestInput) -> ResponseOutput { let effective_limit = effective_limit(value.limit, value.carryover); let remaining = remaining_units(value.used, value.limit, value.carryover); ResponseOutput { effective_limit, remaining, remaining_percent: remaining_percent(value.used, value.limit, value.carryover), state: if remaining == 0 { "exhausted".into() } else { "available".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_remaining_percent(used: i64, limit: i64, carryover: i64) -> i64 { remaining_percent(used, limit, carryover) }
""",
    },
    "tenant_cache_repair": {
        "seed": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub tenant_id: i64, pub resource_id: i64, pub generation: i64 }
#[derive(Serialize)] pub struct ResponseOutput { pub token: i64, pub state: String }
pub fn cache_token(_tenant: i64, resource: i64, generation: i64) -> i64 { resource * 1000 + generation }
pub fn handle(value: RequestInput) -> ResponseOutput { ResponseOutput { token: cache_token(value.tenant_id, value.resource_id, value.generation), state: "isolated".into() } }
#[unsafe(no_mangle)] pub extern "C" fn parley_cache_token(tenant: i64, resource: i64, generation: i64) -> i64 { cache_token(tenant, resource, generation) }
""",
        "reference": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub tenant_id: i64, pub resource_id: i64, pub generation: i64 }
#[derive(Serialize)] pub struct ResponseOutput { pub token: i64, pub state: String }
pub fn cache_token(tenant: i64, resource: i64, generation: i64) -> i64 { tenant * 1000000 + resource * 1000 + generation }
pub fn handle(value: RequestInput) -> ResponseOutput { ResponseOutput { token: cache_token(value.tenant_id, value.resource_id, value.generation), state: "isolated".into() } }
#[unsafe(no_mangle)] pub extern "C" fn parley_cache_token(tenant: i64, resource: i64, generation: i64) -> i64 { cache_token(tenant, resource, generation) }
""",
    },
}


RUST_WASM = {
    "shipping_quote_build": ("parley_quote_total", ["a", "b", "c ? 1 : 0"]),
    "capacity_planner_build": ("parley_accepted_jobs", ["a", "b", "c", "d ? 1 : 0"]),
    "quota_carryover_repair": ("parley_remaining_percent", ["a", "b", "c"]),
    "tenant_cache_repair": ("parley_cache_token", ["a", "b", "c"]),
}


RUST_MAIN_TEMPLATE = r'''
use std::env;
use axum::{Router, body::{Body, to_bytes}, extract::Request, http::{StatusCode, header}, response::{IntoResponse, Response}, routing::{any, get, post}};
use fullstack_agent_036::{RequestInput, handle};
use serde::Serialize;
use serde_json::json;
use tower_http::services::{ServeDir, ServeFile};

const MAX_BODY_BYTES: usize = 16_384;
const BROWSER_MODULE: &str = r#"@@BROWSER@@"#;
fn json_response(value: impl Serialize, status: StatusCode) -> Response { let mut response = (status, serde_json::to_vec(&value).unwrap()).into_response(); response.headers_mut().insert(header::CONTENT_TYPE, header::HeaderValue::from_static("application/json")); response }
fn error(code: &str, status: StatusCode, detail: impl Into<String>) -> Response { json_response(json!({"error": code, "detail": detail.into()}), status) }
async fn status() -> Response { json_response(json!({"service": "@@SERVICE@@", "ready": true}), StatusCode::OK) }
async fn endpoint(request: Request) -> Response {
    let media_type = request.headers().get(header::CONTENT_TYPE).and_then(|value| value.to_str().ok()).unwrap_or("").split(';').next().unwrap_or("").trim().to_ascii_lowercase();
    if media_type != "application/json" && !media_type.ends_with("+json") { return error("json_content_type_required", StatusCode::UNSUPPORTED_MEDIA_TYPE, "expected application/json"); }
    if let Some(length) = request.headers().get(header::CONTENT_LENGTH) { let declared = length.to_str().ok().and_then(|value| value.parse::<usize>().ok()); if declared.is_none_or(|value| value > MAX_BODY_BYTES) { return error("body_too_large", StatusCode::PAYLOAD_TOO_LARGE, "request body exceeds 16384 bytes"); } }
    let body = match to_bytes(request.into_body(), MAX_BODY_BYTES).await { Ok(body) => body, Err(_) => return error("body_too_large", StatusCode::PAYLOAD_TOO_LARGE, "request body exceeds 16384 bytes") };
    match serde_json::from_slice::<RequestInput>(&body) { Ok(value) => json_response(handle(value), StatusCode::OK), Err(reason) => error("invalid_json", StatusCode::BAD_REQUEST, reason.to_string()) }
}
async fn missing_api(request: Request<Body>) -> Response { error("not_found", StatusCode::NOT_FOUND, format!("no API route {}", request.uri().path())) }
async fn browser_module() -> Response { let mut response = BROWSER_MODULE.into_response(); response.headers_mut().insert(header::CONTENT_TYPE, header::HeaderValue::from_static("text/javascript; charset=utf-8")); response }
#[tokio::main] async fn main() {
    let wasm = env::var_os("FULLSTACK_036_WASM").map(std::path::PathBuf::from).unwrap();
    let app = Router::new().route("/api/status", get(status)).route("@@ROUTE@@", post(endpoint)).route("/api/{*rest}", any(missing_api)).route("/parley.js", get(browser_module)).route_service("/fullstack_agent_036.wasm", ServeFile::new(wasm)).fallback_service(ServeDir::new("public").append_index_html_on_directories(true));
    let port = env::var("PARLEY_WEB_PORT").unwrap().parse::<u16>().unwrap();
    let listener = tokio::net::TcpListener::bind(("127.0.0.1", port)).await.unwrap(); axum::serve(listener, app).await.unwrap();
}
'''


def _replace(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace(f"@@{key.upper()}@@", value)
    return _clean(template)


def _parley_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    manifest = {
        "schema_version": 1,
        "name": task["id"],
        "entrypoint": "main.par",
        "static_dir": "public",
        "routes": [
            {"method": "GET", "path": task["status_route"], "handler": "project_status"},
            {"method": "POST", "path": task["post_route"], "handler": "handle_request"},
        ],
        "browser": {"entrypoint": "main.par", "exports": [{"name": task["browser_export"]}]},
        "server": {"host": "127.0.0.1", "port": 8787, "max_body_bytes": 16384},
    }
    return {
        "logic.par": ScaffoldFile(_clean(PARLEY_LOGIC[task["id"]][variant]), True),
        "main.par": ScaffoldFile(_clean(PARLEY_MAIN[task["id"]]), True),
        "parley.web.json": ScaffoldFile(json.dumps(manifest, indent=2) + "\n", True),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _python_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    export_name, js_name = PYTHON_BROWSER_EXPORT[task["id"]]
    browser = _clean(
        PYTHON_BROWSER[task["id"]][variant]
        + f"\nexport async function loadParley() {{ return {{ {export_name}: {js_name} }}; }}"
    )
    app = _replace(
        PYTHON_APP_TEMPLATE,
        service=task["service"],
        route=task["post_route"],
    )
    requirements = (BENCHMARKS / "fullstack_035/python/requirements.txt").read_text()
    return {
        "logic.py": ScaffoldFile(_clean(PYTHON_LOGIC[task["id"]][variant]), True),
        "browser.js": ScaffoldFile(browser, True),
        "app.py": ScaffoldFile(app, True),
        "requirements.txt": ScaffoldFile(requirements, False),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _typescript_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    server = _replace(
        TS_SERVER_TEMPLATE,
        schema=TS_SCHEMA[task["id"]],
        service=task["service"],
        route=task["post_route"],
    )
    return {
        "src/logic.ts": ScaffoldFile(_clean(TYPESCRIPT_LOGIC[task["id"]][variant]), True),
        "src/server.ts": ScaffoldFile(server, True),
        "package.json": ScaffoldFile((BENCHMARKS / "fullstack_035/typescript/package.json").read_text(), False),
        "package-lock.json": ScaffoldFile((BENCHMARKS / "fullstack_035/typescript/package-lock.json").read_text(), False),
        "tsconfig.json": ScaffoldFile((BENCHMARKS / "fullstack_035/typescript/tsconfig.json").read_text(), False),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _rust_browser(task: dict[str, Any]) -> str:
    symbol, args = RUST_WASM[task["id"]]
    names = [chr(ord("a") + index) for index in range(len(args))]
    converted = ", ".join(f"asI64({value}, '{names[index]}')" if "?" not in value else value for index, value in enumerate(args))
    return _clean(
        f"""
const asI64 = (value, name) => {{ if (typeof value === "bigint") return value; if (!Number.isSafeInteger(value)) throw new TypeError(`${{name}} must be a safe whole number`); return BigInt(value); }};
export async function loadParley() {{
  const response = await fetch(new URL("/fullstack_agent_036.wasm", import.meta.url));
  const result = await WebAssembly.instantiateStreaming(response);
  const wasm = result.instance.exports;
  return {{ {task['browser_export']}: ({', '.join(names)}) => wasm.{symbol}({converted}) }};
}}
"""
    )


def _rust_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    main = _replace(
        RUST_MAIN_TEMPLATE,
        browser=_rust_browser(task).rstrip("\n"),
        service=task["service"],
        route=task["post_route"],
    )
    cargo = _clean(
        """
[package]
name = "fullstack-agent-036"
version = "0.1.0"
edition = "2024"

[lib]
crate-type = ["rlib", "cdylib"]

[dependencies]
serde = { version = "=1.0.229", features = ["derive"] }
serde_json = "=1.0.151"

[target.'cfg(not(target_arch = "wasm32"))'.dependencies]
axum = "=0.8.9"
tokio = { version = "=1.53.1", features = ["macros", "rt-multi-thread", "net"] }
tower-http = { version = "=0.7.0", features = ["fs"] }
"""
    )
    return {
        "src/lib.rs": ScaffoldFile(_clean(RUST_LIB[task["id"]][variant]), True),
        "src/main.rs": ScaffoldFile(main, True),
        "Cargo.toml": ScaffoldFile(cargo, False),
        "Cargo.lock": ScaffoldFile((BENCHMARKS / "fullstack_035/rust/Cargo.lock").read_text(), False),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def scaffold_files(task: dict[str, Any], language: str, variant: str = "seed") -> dict[str, ScaffoldFile]:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    if variant not in {"seed", "reference"}:
        raise ValueError(f"unsupported scaffold variant: {variant}")
    builders = {
        "parley": _parley_files,
        "python": _python_files,
        "typescript": _typescript_files,
        "rust": _rust_files,
    }
    files = builders[language](task, variant)
    files["CONTRACT.md"] = ScaffoldFile(_contract(task), False)
    return files


ROOT_FILES: dict[str, tuple[str, ...]] = {
    "parley": ("logic.par",),
    "python": ("browser.js", "logic.py"),
    "typescript": ("src/logic.ts",),
    "rust": ("src/lib.rs",),
}
