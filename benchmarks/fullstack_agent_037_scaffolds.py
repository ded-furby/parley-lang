"""Generate frozen language workspaces for full-stack agent study 037."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .fullstack_agent_036_scaffolds import (
        PYTHON_APP_TEMPLATE as BASE_PYTHON_APP_TEMPLATE,
        RUST_MAIN_TEMPLATE as BASE_RUST_MAIN_TEMPLATE,
        TS_SERVER_TEMPLATE as BASE_TS_SERVER_TEMPLATE,
        ScaffoldFile,
        _clean,
        _replace,
    )
except ImportError:
    from fullstack_agent_036_scaffolds import (
        PYTHON_APP_TEMPLATE as BASE_PYTHON_APP_TEMPLATE,
        RUST_MAIN_TEMPLATE as BASE_RUST_MAIN_TEMPLATE,
        TS_SERVER_TEMPLATE as BASE_TS_SERVER_TEMPLATE,
        ScaffoldFile,
        _clean,
        _replace,
    )


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS_PATH = BENCHMARKS / "fullstack_agent_037_tasks.json"
LANGUAGES = ("parley", "python", "typescript", "rust")


def load_task_map() -> dict[str, dict[str, Any]]:
    payload = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    return {task["id"]: task for task in payload["tasks"]}


def _contract(task: dict[str, Any]) -> str:
    request = "\n".join(
        f"- `{name}`: {kind}" for name, kind in task["request_fields"].items()
    )
    response = "\n".join(
        f"- `{name}`: {kind}" for name, kind in task["response_fields"].items()
    )
    extra = (
        " `bucket_seconds` must be at least 1."
        if task["id"] == "timeline_bucket_repair"
        else ""
    )
    return _clean(
        f"""
        # {task['title']}

        {task['statement']}

        ## HTTP

        - `GET {task['status_route']}` returns `{{"service":"{task['service']}","ready":true}}`.
        - `POST {task['post_route']}` accepts strict JSON and returns strict JSON.
        - A number is a nonnegative JSON integer and never a boolean.{extra}
        - Unknown, missing, wrongly typed, or out-of-domain fields return
          status 400 with error `invalid_json`.
        - A non-JSON POST returns 415 with error `json_content_type_required`.
        - A body over 16384 bytes returns 413 with error `body_too_large`.

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
    <title>Full-stack agent study 037</title>
    <main>Full-stack agent study 037 browser target</main>
    """
).replace("    ", "")


PARLEY_LOGIC: dict[str, dict[str, str]] = {
    "rail_connection_build": {
        "seed": """
to transfer_buffer with platform_change as yesno giving number:
    give back 0

to connection_ready with arrival_minute as number, delay_minutes as number, platform_change as yesno giving number:
    give back 0

to connection_margin with arrival_minute as number, delay_minutes as number, departure_minute as number, platform_change as yesno giving number:
    give back 0
""",
        "reference": """
to transfer_buffer with platform_change as yesno giving number:
    if platform_change:
        give back 7
    give back 3

to connection_ready with arrival_minute as number, delay_minutes as number, platform_change as yesno giving number:
    give back arrival_minute plus delay_minutes plus (transfer_buffer with platform_change)

to connection_margin with arrival_minute as number, delay_minutes as number, departure_minute as number, platform_change as yesno giving number:
    give back departure_minute minus (connection_ready with arrival_minute, delay_minutes, platform_change)
""",
    },
    "orchard_irrigation_build": {
        "seed": """
to raw_irrigation with dryness_points as number, tree_rows as number giving number:
    give back 0

to rain_credit with tree_rows as number, rain_expected as yesno giving number:
    give back 0

to scheduled_irrigation with dryness_points as number, tree_rows as number, rain_expected as yesno giving number:
    give back 0

to irrigation_cycles with dryness_points as number, tree_rows as number, rain_expected as yesno giving number:
    give back 0
""",
        "reference": """
to raw_irrigation with dryness_points as number, tree_rows as number giving number:
    give back dryness_points times tree_rows times 2

to rain_credit with tree_rows as number, rain_expected as yesno giving number:
    if rain_expected:
        give back tree_rows times 5
    give back 0

to scheduled_irrigation with dryness_points as number, tree_rows as number, rain_expected as yesno giving number:
    let scheduled be (raw_irrigation with dryness_points, tree_rows) minus (rain_credit with tree_rows, rain_expected)
    if scheduled is less than 0:
        give back 0
    give back scheduled

to irrigation_cycles with dryness_points as number, tree_rows as number, rain_expected as yesno giving number:
    let scheduled be (scheduled_irrigation with dryness_points, tree_rows, rain_expected)
    give back number from ((scheduled plus 39) divided by 40)
""",
    },
    "tiered_meter_repair": {
        "seed": """
to standard_usage with consumed_units as number, included_units as number giving number:
    if consumed_units is less than included_units:
        give back consumed_units
    give back included_units

to excess_usage with consumed_units as number, included_units as number giving number:
    let excess be consumed_units minus included_units
    if excess is less than 0:
        give back 0
    give back excess

to meter_rate with peak_window as yesno giving number:
    if peak_window:
        give back 7
    give back 4

to usage_points with consumed_units as number, included_units as number, peak_window as yesno giving number:
    if consumed_units is more than included_units:
        give back consumed_units times (meter_rate with peak_window)
    give back consumed_units times 2
""",
        "reference": """
to standard_usage with consumed_units as number, included_units as number giving number:
    if consumed_units is less than included_units:
        give back consumed_units
    give back included_units

to excess_usage with consumed_units as number, included_units as number giving number:
    let excess be consumed_units minus included_units
    if excess is less than 0:
        give back 0
    give back excess

to meter_rate with peak_window as yesno giving number:
    if peak_window:
        give back 7
    give back 4

to usage_points with consumed_units as number, included_units as number, peak_window as yesno giving number:
    give back (standard_usage with consumed_units, included_units) times 2 plus (excess_usage with consumed_units, included_units) times (meter_rate with peak_window)
""",
    },
    "timeline_bucket_repair": {
        "seed": """
to timeline_offset with timestamp_second as number, origin_second as number giving number:
    let offset be timestamp_second minus origin_second
    if offset is less than 0:
        give back 0
    give back offset

to timeline_bucket_index with timestamp_second as number, origin_second as number, bucket_seconds as number giving number:
    let offset be (timeline_offset with timestamp_second, origin_second)
    let index be number from (offset divided by bucket_seconds)
    if offset minus index times bucket_seconds is 0:
        give back index plus 1
    give back index
""",
        "reference": """
to timeline_offset with timestamp_second as number, origin_second as number giving number:
    let offset be timestamp_second minus origin_second
    if offset is less than 0:
        give back 0
    give back offset

to timeline_bucket_index with timestamp_second as number, origin_second as number, bucket_seconds as number giving number:
    let offset be (timeline_offset with timestamp_second, origin_second)
    give back number from (offset divided by bucket_seconds)
""",
    },
}


PARLEY_MAIN = {
    "rail_connection_build": """
include "logic.par"

a connection_request has arrival_minute as number, delay_minutes as number, departure_minute as number, platform_change as yesno
a connection_response has ready_minute as number, margin_minutes as number, wait_minutes as number, outcome as text
a service_status has service as text, ready as yesno

to project_status giving service_status:
    give back a service_status with service "Rail Connection", ready yes

to handle_request with request as connection_request giving connection_response:
    let ready be (connection_ready with request's arrival_minute, request's delay_minutes, request's platform_change)
    let margin be (connection_margin with request's arrival_minute, request's delay_minutes, request's departure_minute, request's platform_change)
    let wait be margin
    let outcome be "make"
    if margin is less than 0:
        set wait to 0
        set outcome to "miss"
    give back a connection_response with ready_minute ready, margin_minutes margin, wait_minutes wait, outcome outcome
""",
    "orchard_irrigation_build": """
include "logic.par"

a irrigation_request has dryness_points as number, tree_rows as number, rain_expected as yesno
a irrigation_response has raw_liters as number, rain_credit_liters as number, scheduled_liters as number, pump_cycles as number, mode as text
a service_status has service as text, ready as yesno

to project_status giving service_status:
    give back a service_status with service "Orchard Irrigation", ready yes

to handle_request with request as irrigation_request giving irrigation_response:
    let raw be (raw_irrigation with request's dryness_points, request's tree_rows)
    let credit be (rain_credit with request's tree_rows, request's rain_expected)
    let scheduled be (scheduled_irrigation with request's dryness_points, request's tree_rows, request's rain_expected)
    let cycles be (irrigation_cycles with request's dryness_points, request's tree_rows, request's rain_expected)
    let mode be "active"
    if scheduled is 0:
        set mode to "idle"
    give back a irrigation_response with raw_liters raw, rain_credit_liters credit, scheduled_liters scheduled, pump_cycles cycles, mode mode
""",
    "tiered_meter_repair": """
include "logic.par"

a meter_request has consumed_units as number, included_units as number, peak_window as yesno
a meter_response has standard_units as number, excess_units as number, excess_rate as number, usage_points as number, band as text
a service_status has service as text, ready as yesno

to project_status giving service_status:
    give back a service_status with service "Tiered Meter", ready yes

to handle_request with request as meter_request giving meter_response:
    let standard be (standard_usage with request's consumed_units, request's included_units)
    let excess be (excess_usage with request's consumed_units, request's included_units)
    let rate be (meter_rate with request's peak_window)
    let points be (usage_points with request's consumed_units, request's included_units, request's peak_window)
    let band be "excess"
    if excess is 0:
        set band to "included"
    give back a meter_response with standard_units standard, excess_units excess, excess_rate rate, usage_points points, band band
""",
    "timeline_bucket_repair": """
include "logic.par"

a timeline_request has timestamp_second as number, origin_second as number, bucket_seconds as number
a timeline_response has offset_seconds as number, bucket_index as number, bucket_start_second as number, position_second as number, location as text
a service_status has service as text, ready as yesno

to project_status giving service_status:
    give back a service_status with service "Timeline Bucket", ready yes

to handle_request with request as timeline_request giving timeline_response:
    let offset be (timeline_offset with request's timestamp_second, request's origin_second)
    let index be (timeline_bucket_index with request's timestamp_second, request's origin_second, request's bucket_seconds)
    let start be request's origin_second plus index times request's bucket_seconds
    let position be offset minus index times request's bucket_seconds
    let location be "inside"
    if position is 0:
        set location to "boundary"
    give back a timeline_response with offset_seconds offset, bucket_index index, bucket_start_second start, position_second position, location location
""",
}


PYTHON_LOGIC: dict[str, dict[str, str]] = {
    "rail_connection_build": {
        "seed": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    arrival_minute: int = Field(ge=0)
    delay_minutes: int = Field(ge=0)
    departure_minute: int = Field(ge=0)
    platform_change: bool
def transfer_buffer(platform_change: bool) -> int: return 0
def connection_ready(arrival_minute: int, delay_minutes: int, platform_change: bool) -> int: return 0
def connection_margin(arrival_minute: int, delay_minutes: int, departure_minute: int, platform_change: bool) -> int: return 0
def handle(value: RequestInput) -> dict[str, object]:
    ready = connection_ready(value.arrival_minute, value.delay_minutes, value.platform_change)
    margin = connection_margin(value.arrival_minute, value.delay_minutes, value.departure_minute, value.platform_change)
    return {"ready_minute": ready, "margin_minutes": margin, "wait_minutes": max(margin, 0), "outcome": "make" if margin >= 0 else "miss"}
""",
        "reference": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    arrival_minute: int = Field(ge=0)
    delay_minutes: int = Field(ge=0)
    departure_minute: int = Field(ge=0)
    platform_change: bool
def transfer_buffer(platform_change: bool) -> int: return 7 if platform_change else 3
def connection_ready(arrival_minute: int, delay_minutes: int, platform_change: bool) -> int: return arrival_minute + delay_minutes + transfer_buffer(platform_change)
def connection_margin(arrival_minute: int, delay_minutes: int, departure_minute: int, platform_change: bool) -> int: return departure_minute - connection_ready(arrival_minute, delay_minutes, platform_change)
def handle(value: RequestInput) -> dict[str, object]:
    ready = connection_ready(value.arrival_minute, value.delay_minutes, value.platform_change)
    margin = connection_margin(value.arrival_minute, value.delay_minutes, value.departure_minute, value.platform_change)
    return {"ready_minute": ready, "margin_minutes": margin, "wait_minutes": max(margin, 0), "outcome": "make" if margin >= 0 else "miss"}
""",
    },
    "orchard_irrigation_build": {
        "seed": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    dryness_points: int = Field(ge=0)
    tree_rows: int = Field(ge=0)
    rain_expected: bool
def raw_irrigation(dryness_points: int, tree_rows: int) -> int: return 0
def rain_credit(tree_rows: int, rain_expected: bool) -> int: return 0
def scheduled_irrigation(dryness_points: int, tree_rows: int, rain_expected: bool) -> int: return 0
def irrigation_cycles(dryness_points: int, tree_rows: int, rain_expected: bool) -> int: return 0
def handle(value: RequestInput) -> dict[str, object]:
    raw = raw_irrigation(value.dryness_points, value.tree_rows)
    credit = rain_credit(value.tree_rows, value.rain_expected)
    scheduled = scheduled_irrigation(value.dryness_points, value.tree_rows, value.rain_expected)
    return {"raw_liters": raw, "rain_credit_liters": credit, "scheduled_liters": scheduled, "pump_cycles": irrigation_cycles(value.dryness_points, value.tree_rows, value.rain_expected), "mode": "idle" if scheduled == 0 else "active"}
""",
        "reference": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    dryness_points: int = Field(ge=0)
    tree_rows: int = Field(ge=0)
    rain_expected: bool
def raw_irrigation(dryness_points: int, tree_rows: int) -> int: return dryness_points * tree_rows * 2
def rain_credit(tree_rows: int, rain_expected: bool) -> int: return tree_rows * 5 if rain_expected else 0
def scheduled_irrigation(dryness_points: int, tree_rows: int, rain_expected: bool) -> int: return max(raw_irrigation(dryness_points, tree_rows) - rain_credit(tree_rows, rain_expected), 0)
def irrigation_cycles(dryness_points: int, tree_rows: int, rain_expected: bool) -> int: return (scheduled_irrigation(dryness_points, tree_rows, rain_expected) + 39) // 40
def handle(value: RequestInput) -> dict[str, object]:
    raw = raw_irrigation(value.dryness_points, value.tree_rows)
    credit = rain_credit(value.tree_rows, value.rain_expected)
    scheduled = scheduled_irrigation(value.dryness_points, value.tree_rows, value.rain_expected)
    return {"raw_liters": raw, "rain_credit_liters": credit, "scheduled_liters": scheduled, "pump_cycles": irrigation_cycles(value.dryness_points, value.tree_rows, value.rain_expected), "mode": "idle" if scheduled == 0 else "active"}
""",
    },
    "tiered_meter_repair": {
        "seed": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    consumed_units: int = Field(ge=0)
    included_units: int = Field(ge=0)
    peak_window: bool
def standard_usage(consumed_units: int, included_units: int) -> int: return min(consumed_units, included_units)
def excess_usage(consumed_units: int, included_units: int) -> int: return max(consumed_units - included_units, 0)
def meter_rate(peak_window: bool) -> int: return 7 if peak_window else 4
def usage_points(consumed_units: int, included_units: int, peak_window: bool) -> int: return consumed_units * meter_rate(peak_window) if consumed_units > included_units else consumed_units * 2
def handle(value: RequestInput) -> dict[str, object]:
    standard = standard_usage(value.consumed_units, value.included_units)
    excess = excess_usage(value.consumed_units, value.included_units)
    return {"standard_units": standard, "excess_units": excess, "excess_rate": meter_rate(value.peak_window), "usage_points": usage_points(value.consumed_units, value.included_units, value.peak_window), "band": "included" if excess == 0 else "excess"}
""",
        "reference": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    consumed_units: int = Field(ge=0)
    included_units: int = Field(ge=0)
    peak_window: bool
def standard_usage(consumed_units: int, included_units: int) -> int: return min(consumed_units, included_units)
def excess_usage(consumed_units: int, included_units: int) -> int: return max(consumed_units - included_units, 0)
def meter_rate(peak_window: bool) -> int: return 7 if peak_window else 4
def usage_points(consumed_units: int, included_units: int, peak_window: bool) -> int: return standard_usage(consumed_units, included_units) * 2 + excess_usage(consumed_units, included_units) * meter_rate(peak_window)
def handle(value: RequestInput) -> dict[str, object]:
    standard = standard_usage(value.consumed_units, value.included_units)
    excess = excess_usage(value.consumed_units, value.included_units)
    return {"standard_units": standard, "excess_units": excess, "excess_rate": meter_rate(value.peak_window), "usage_points": usage_points(value.consumed_units, value.included_units, value.peak_window), "band": "included" if excess == 0 else "excess"}
""",
    },
    "timeline_bucket_repair": {
        "seed": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    timestamp_second: int = Field(ge=0)
    origin_second: int = Field(ge=0)
    bucket_seconds: int = Field(gt=0)
def timeline_offset(timestamp_second: int, origin_second: int) -> int: return max(timestamp_second - origin_second, 0)
def timeline_bucket_index(timestamp_second: int, origin_second: int, bucket_seconds: int) -> int:
    offset = timeline_offset(timestamp_second, origin_second)
    index = offset // bucket_seconds
    return index + 1 if offset - index * bucket_seconds == 0 else index
def handle(value: RequestInput) -> dict[str, object]:
    offset = timeline_offset(value.timestamp_second, value.origin_second)
    index = timeline_bucket_index(value.timestamp_second, value.origin_second, value.bucket_seconds)
    start = value.origin_second + index * value.bucket_seconds
    position = offset - index * value.bucket_seconds
    return {"offset_seconds": offset, "bucket_index": index, "bucket_start_second": start, "position_second": position, "location": "boundary" if position == 0 else "inside"}
""",
        "reference": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    timestamp_second: int = Field(ge=0)
    origin_second: int = Field(ge=0)
    bucket_seconds: int = Field(gt=0)
def timeline_offset(timestamp_second: int, origin_second: int) -> int: return max(timestamp_second - origin_second, 0)
def timeline_bucket_index(timestamp_second: int, origin_second: int, bucket_seconds: int) -> int: return timeline_offset(timestamp_second, origin_second) // bucket_seconds
def handle(value: RequestInput) -> dict[str, object]:
    offset = timeline_offset(value.timestamp_second, value.origin_second)
    index = timeline_bucket_index(value.timestamp_second, value.origin_second, value.bucket_seconds)
    start = value.origin_second + index * value.bucket_seconds
    position = offset - index * value.bucket_seconds
    return {"offset_seconds": offset, "bucket_index": index, "bucket_start_second": start, "position_second": position, "location": "boundary" if position == 0 else "inside"}
""",
    },
}


PYTHON_BROWSER = {
    "rail_connection_build": {
        "seed": "const connectionMargin = () => 0n;",
        "reference": "const connectionMargin = (arrival, delay, departure, platformChange) => BigInt(departure - (arrival + delay + (platformChange ? 7 : 3)));",
    },
    "orchard_irrigation_build": {
        "seed": "const irrigationCycles = () => 0n;",
        "reference": "const irrigationCycles = (dryness, rows, rainExpected) => { const scheduled = Math.max(dryness * rows * 2 - (rainExpected ? rows * 5 : 0), 0); return BigInt(Math.trunc((scheduled + 39) / 40)); };",
    },
    "tiered_meter_repair": {
        "seed": "const usagePoints = (consumed, included, peak) => BigInt(consumed > included ? consumed * (peak ? 7 : 4) : consumed * 2);",
        "reference": "const usagePoints = (consumed, included, peak) => BigInt(Math.min(consumed, included) * 2 + Math.max(consumed - included, 0) * (peak ? 7 : 4));",
    },
    "timeline_bucket_repair": {
        "seed": "const timelineBucketIndex = (timestamp, origin, width) => { const offset = Math.max(timestamp - origin, 0); const index = Math.trunc(offset / width); return BigInt(offset - index * width === 0 ? index + 1 : index); };",
        "reference": "const timelineBucketIndex = (timestamp, origin, width) => BigInt(Math.trunc(Math.max(timestamp - origin, 0) / width));",
    },
}


PYTHON_BROWSER_EXPORT = {
    "rail_connection_build": ("connection_margin", "connectionMargin"),
    "orchard_irrigation_build": ("irrigation_cycles", "irrigationCycles"),
    "tiered_meter_repair": ("usage_points", "usagePoints"),
    "timeline_bucket_repair": ("timeline_bucket_index", "timelineBucketIndex"),
}


PYTHON_APP_TEMPLATE = BASE_PYTHON_APP_TEMPLATE.replace(
    '@app.get("/api/status")', '@app.get("@@STATUS_ROUTE@@")'
)


TYPESCRIPT_LOGIC: dict[str, dict[str, str]] = {
    "rail_connection_build": {
        "seed": """
export type RequestInput = { arrival_minute: number; delay_minutes: number; departure_minute: number; platform_change: boolean };
export const transferBuffer = (_platformChange: boolean) => 0;
export const connectionReady = (_arrival: number, _delay: number, _platformChange: boolean) => 0;
export const connectionMargin = (_arrival: number, _delay: number, _departure: number, _platformChange: boolean) => 0;
export const handle = (value: RequestInput) => { const ready = connectionReady(value.arrival_minute, value.delay_minutes, value.platform_change); const margin = connectionMargin(value.arrival_minute, value.delay_minutes, value.departure_minute, value.platform_change); return { ready_minute: ready, margin_minutes: margin, wait_minutes: Math.max(margin, 0), outcome: margin >= 0 ? "make" : "miss" }; };
export async function loadParley() { return { connection_margin: (arrival: number, delay: number, departure: number, platformChange: boolean) => BigInt(connectionMargin(arrival, delay, departure, platformChange)) }; }
""",
        "reference": """
export type RequestInput = { arrival_minute: number; delay_minutes: number; departure_minute: number; platform_change: boolean };
export const transferBuffer = (platformChange: boolean) => platformChange ? 7 : 3;
export const connectionReady = (arrival: number, delay: number, platformChange: boolean) => arrival + delay + transferBuffer(platformChange);
export const connectionMargin = (arrival: number, delay: number, departure: number, platformChange: boolean) => departure - connectionReady(arrival, delay, platformChange);
export const handle = (value: RequestInput) => { const ready = connectionReady(value.arrival_minute, value.delay_minutes, value.platform_change); const margin = connectionMargin(value.arrival_minute, value.delay_minutes, value.departure_minute, value.platform_change); return { ready_minute: ready, margin_minutes: margin, wait_minutes: Math.max(margin, 0), outcome: margin >= 0 ? "make" : "miss" }; };
export async function loadParley() { return { connection_margin: (arrival: number, delay: number, departure: number, platformChange: boolean) => BigInt(connectionMargin(arrival, delay, departure, platformChange)) }; }
""",
    },
    "orchard_irrigation_build": {
        "seed": """
export type RequestInput = { dryness_points: number; tree_rows: number; rain_expected: boolean };
export const rawIrrigation = (_dryness: number, _rows: number) => 0;
export const rainCredit = (_rows: number, _rainExpected: boolean) => 0;
export const scheduledIrrigation = (_dryness: number, _rows: number, _rainExpected: boolean) => 0;
export const irrigationCycles = (_dryness: number, _rows: number, _rainExpected: boolean) => 0;
export const handle = (value: RequestInput) => { const raw_liters = rawIrrigation(value.dryness_points, value.tree_rows); const rain_credit_liters = rainCredit(value.tree_rows, value.rain_expected); const scheduled_liters = scheduledIrrigation(value.dryness_points, value.tree_rows, value.rain_expected); return { raw_liters, rain_credit_liters, scheduled_liters, pump_cycles: irrigationCycles(value.dryness_points, value.tree_rows, value.rain_expected), mode: scheduled_liters === 0 ? "idle" : "active" }; };
export async function loadParley() { return { irrigation_cycles: (dryness: number, rows: number, rainExpected: boolean) => BigInt(irrigationCycles(dryness, rows, rainExpected)) }; }
""",
        "reference": """
export type RequestInput = { dryness_points: number; tree_rows: number; rain_expected: boolean };
export const rawIrrigation = (dryness: number, rows: number) => dryness * rows * 2;
export const rainCredit = (rows: number, rainExpected: boolean) => rainExpected ? rows * 5 : 0;
export const scheduledIrrigation = (dryness: number, rows: number, rainExpected: boolean) => Math.max(rawIrrigation(dryness, rows) - rainCredit(rows, rainExpected), 0);
export const irrigationCycles = (dryness: number, rows: number, rainExpected: boolean) => Math.trunc((scheduledIrrigation(dryness, rows, rainExpected) + 39) / 40);
export const handle = (value: RequestInput) => { const raw_liters = rawIrrigation(value.dryness_points, value.tree_rows); const rain_credit_liters = rainCredit(value.tree_rows, value.rain_expected); const scheduled_liters = scheduledIrrigation(value.dryness_points, value.tree_rows, value.rain_expected); return { raw_liters, rain_credit_liters, scheduled_liters, pump_cycles: irrigationCycles(value.dryness_points, value.tree_rows, value.rain_expected), mode: scheduled_liters === 0 ? "idle" : "active" }; };
export async function loadParley() { return { irrigation_cycles: (dryness: number, rows: number, rainExpected: boolean) => BigInt(irrigationCycles(dryness, rows, rainExpected)) }; }
""",
    },
    "tiered_meter_repair": {
        "seed": """
export type RequestInput = { consumed_units: number; included_units: number; peak_window: boolean };
export const standardUsage = (consumed: number, included: number) => Math.min(consumed, included);
export const excessUsage = (consumed: number, included: number) => Math.max(consumed - included, 0);
export const meterRate = (peak: boolean) => peak ? 7 : 4;
export const usagePoints = (consumed: number, included: number, peak: boolean) => consumed > included ? consumed * meterRate(peak) : consumed * 2;
export const handle = (value: RequestInput) => { const standard_units = standardUsage(value.consumed_units, value.included_units); const excess_units = excessUsage(value.consumed_units, value.included_units); return { standard_units, excess_units, excess_rate: meterRate(value.peak_window), usage_points: usagePoints(value.consumed_units, value.included_units, value.peak_window), band: excess_units === 0 ? "included" : "excess" }; };
export async function loadParley() { return { usage_points: (consumed: number, included: number, peak: boolean) => BigInt(usagePoints(consumed, included, peak)) }; }
""",
        "reference": """
export type RequestInput = { consumed_units: number; included_units: number; peak_window: boolean };
export const standardUsage = (consumed: number, included: number) => Math.min(consumed, included);
export const excessUsage = (consumed: number, included: number) => Math.max(consumed - included, 0);
export const meterRate = (peak: boolean) => peak ? 7 : 4;
export const usagePoints = (consumed: number, included: number, peak: boolean) => standardUsage(consumed, included) * 2 + excessUsage(consumed, included) * meterRate(peak);
export const handle = (value: RequestInput) => { const standard_units = standardUsage(value.consumed_units, value.included_units); const excess_units = excessUsage(value.consumed_units, value.included_units); return { standard_units, excess_units, excess_rate: meterRate(value.peak_window), usage_points: usagePoints(value.consumed_units, value.included_units, value.peak_window), band: excess_units === 0 ? "included" : "excess" }; };
export async function loadParley() { return { usage_points: (consumed: number, included: number, peak: boolean) => BigInt(usagePoints(consumed, included, peak)) }; }
""",
    },
    "timeline_bucket_repair": {
        "seed": """
export type RequestInput = { timestamp_second: number; origin_second: number; bucket_seconds: number };
export const timelineOffset = (timestamp: number, origin: number) => Math.max(timestamp - origin, 0);
export const timelineBucketIndex = (timestamp: number, origin: number, width: number) => { const offset = timelineOffset(timestamp, origin); const index = Math.trunc(offset / width); return offset - index * width === 0 ? index + 1 : index; };
export const handle = (value: RequestInput) => { const offset_seconds = timelineOffset(value.timestamp_second, value.origin_second); const bucket_index = timelineBucketIndex(value.timestamp_second, value.origin_second, value.bucket_seconds); const bucket_start_second = value.origin_second + bucket_index * value.bucket_seconds; const position_second = offset_seconds - bucket_index * value.bucket_seconds; return { offset_seconds, bucket_index, bucket_start_second, position_second, location: position_second === 0 ? "boundary" : "inside" }; };
export async function loadParley() { return { timeline_bucket_index: (timestamp: number, origin: number, width: number) => BigInt(timelineBucketIndex(timestamp, origin, width)) }; }
""",
        "reference": """
export type RequestInput = { timestamp_second: number; origin_second: number; bucket_seconds: number };
export const timelineOffset = (timestamp: number, origin: number) => Math.max(timestamp - origin, 0);
export const timelineBucketIndex = (timestamp: number, origin: number, width: number) => Math.trunc(timelineOffset(timestamp, origin) / width);
export const handle = (value: RequestInput) => { const offset_seconds = timelineOffset(value.timestamp_second, value.origin_second); const bucket_index = timelineBucketIndex(value.timestamp_second, value.origin_second, value.bucket_seconds); const bucket_start_second = value.origin_second + bucket_index * value.bucket_seconds; const position_second = offset_seconds - bucket_index * value.bucket_seconds; return { offset_seconds, bucket_index, bucket_start_second, position_second, location: position_second === 0 ? "boundary" : "inside" }; };
export async function loadParley() { return { timeline_bucket_index: (timestamp: number, origin: number, width: number) => BigInt(timelineBucketIndex(timestamp, origin, width)) }; }
""",
    },
}


TS_SCHEMA = {
    "rail_connection_build": "z.object({ arrival_minute: z.number().int().nonnegative(), delay_minutes: z.number().int().nonnegative(), departure_minute: z.number().int().nonnegative(), platform_change: z.boolean() }).strict()",
    "orchard_irrigation_build": "z.object({ dryness_points: z.number().int().nonnegative(), tree_rows: z.number().int().nonnegative(), rain_expected: z.boolean() }).strict()",
    "tiered_meter_repair": "z.object({ consumed_units: z.number().int().nonnegative(), included_units: z.number().int().nonnegative(), peak_window: z.boolean() }).strict()",
    "timeline_bucket_repair": "z.object({ timestamp_second: z.number().int().nonnegative(), origin_second: z.number().int().nonnegative(), bucket_seconds: z.number().int().positive() }).strict()",
}


TS_SERVER_TEMPLATE = BASE_TS_SERVER_TEMPLATE.replace(
    'app.get("/api/status"', 'app.get("@@STATUS_ROUTE@@"'
).replace("FULLSTACK_036", "FULLSTACK_037")


RUST_LIB: dict[str, dict[str, str]] = {
    "rail_connection_build": {
        "seed": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub arrival_minute: i64, pub delay_minutes: i64, pub departure_minute: i64, pub platform_change: bool }
impl RequestInput { pub fn valid(&self) -> bool { self.arrival_minute >= 0 && self.delay_minutes >= 0 && self.departure_minute >= 0 } }
#[derive(Serialize)] pub struct ResponseOutput { pub ready_minute: i64, pub margin_minutes: i64, pub wait_minutes: i64, pub outcome: String }
pub fn transfer_buffer(_platform_change: bool) -> i64 { 0 }
pub fn connection_ready(_arrival: i64, _delay: i64, _platform_change: bool) -> i64 { 0 }
pub fn connection_margin(_arrival: i64, _delay: i64, _departure: i64, _platform_change: bool) -> i64 { 0 }
pub fn handle(value: RequestInput) -> ResponseOutput { let ready = connection_ready(value.arrival_minute, value.delay_minutes, value.platform_change); let margin = connection_margin(value.arrival_minute, value.delay_minutes, value.departure_minute, value.platform_change); ResponseOutput { ready_minute: ready, margin_minutes: margin, wait_minutes: margin.max(0), outcome: if margin >= 0 { "make".into() } else { "miss".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_connection_margin(arrival: i64, delay: i64, departure: i64, platform_change: i32) -> i64 { connection_margin(arrival, delay, departure, platform_change != 0) }
""",
        "reference": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub arrival_minute: i64, pub delay_minutes: i64, pub departure_minute: i64, pub platform_change: bool }
impl RequestInput { pub fn valid(&self) -> bool { self.arrival_minute >= 0 && self.delay_minutes >= 0 && self.departure_minute >= 0 } }
#[derive(Serialize)] pub struct ResponseOutput { pub ready_minute: i64, pub margin_minutes: i64, pub wait_minutes: i64, pub outcome: String }
pub fn transfer_buffer(platform_change: bool) -> i64 { if platform_change { 7 } else { 3 } }
pub fn connection_ready(arrival: i64, delay: i64, platform_change: bool) -> i64 { arrival + delay + transfer_buffer(platform_change) }
pub fn connection_margin(arrival: i64, delay: i64, departure: i64, platform_change: bool) -> i64 { departure - connection_ready(arrival, delay, platform_change) }
pub fn handle(value: RequestInput) -> ResponseOutput { let ready = connection_ready(value.arrival_minute, value.delay_minutes, value.platform_change); let margin = connection_margin(value.arrival_minute, value.delay_minutes, value.departure_minute, value.platform_change); ResponseOutput { ready_minute: ready, margin_minutes: margin, wait_minutes: margin.max(0), outcome: if margin >= 0 { "make".into() } else { "miss".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_connection_margin(arrival: i64, delay: i64, departure: i64, platform_change: i32) -> i64 { connection_margin(arrival, delay, departure, platform_change != 0) }
""",
    },
    "orchard_irrigation_build": {
        "seed": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub dryness_points: i64, pub tree_rows: i64, pub rain_expected: bool }
impl RequestInput { pub fn valid(&self) -> bool { self.dryness_points >= 0 && self.tree_rows >= 0 } }
#[derive(Serialize)] pub struct ResponseOutput { pub raw_liters: i64, pub rain_credit_liters: i64, pub scheduled_liters: i64, pub pump_cycles: i64, pub mode: String }
pub fn raw_irrigation(_dryness: i64, _rows: i64) -> i64 { 0 }
pub fn rain_credit(_rows: i64, _rain_expected: bool) -> i64 { 0 }
pub fn scheduled_irrigation(_dryness: i64, _rows: i64, _rain_expected: bool) -> i64 { 0 }
pub fn irrigation_cycles(_dryness: i64, _rows: i64, _rain_expected: bool) -> i64 { 0 }
pub fn handle(value: RequestInput) -> ResponseOutput { let raw_liters = raw_irrigation(value.dryness_points, value.tree_rows); let rain_credit_liters = rain_credit(value.tree_rows, value.rain_expected); let scheduled_liters = scheduled_irrigation(value.dryness_points, value.tree_rows, value.rain_expected); ResponseOutput { raw_liters, rain_credit_liters, scheduled_liters, pump_cycles: irrigation_cycles(value.dryness_points, value.tree_rows, value.rain_expected), mode: if scheduled_liters == 0 { "idle".into() } else { "active".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_irrigation_cycles(dryness: i64, rows: i64, rain_expected: i32) -> i64 { irrigation_cycles(dryness, rows, rain_expected != 0) }
""",
        "reference": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub dryness_points: i64, pub tree_rows: i64, pub rain_expected: bool }
impl RequestInput { pub fn valid(&self) -> bool { self.dryness_points >= 0 && self.tree_rows >= 0 } }
#[derive(Serialize)] pub struct ResponseOutput { pub raw_liters: i64, pub rain_credit_liters: i64, pub scheduled_liters: i64, pub pump_cycles: i64, pub mode: String }
pub fn raw_irrigation(dryness: i64, rows: i64) -> i64 { dryness * rows * 2 }
pub fn rain_credit(rows: i64, rain_expected: bool) -> i64 { if rain_expected { rows * 5 } else { 0 } }
pub fn scheduled_irrigation(dryness: i64, rows: i64, rain_expected: bool) -> i64 { (raw_irrigation(dryness, rows) - rain_credit(rows, rain_expected)).max(0) }
pub fn irrigation_cycles(dryness: i64, rows: i64, rain_expected: bool) -> i64 { (scheduled_irrigation(dryness, rows, rain_expected) + 39) / 40 }
pub fn handle(value: RequestInput) -> ResponseOutput { let raw_liters = raw_irrigation(value.dryness_points, value.tree_rows); let rain_credit_liters = rain_credit(value.tree_rows, value.rain_expected); let scheduled_liters = scheduled_irrigation(value.dryness_points, value.tree_rows, value.rain_expected); ResponseOutput { raw_liters, rain_credit_liters, scheduled_liters, pump_cycles: irrigation_cycles(value.dryness_points, value.tree_rows, value.rain_expected), mode: if scheduled_liters == 0 { "idle".into() } else { "active".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_irrigation_cycles(dryness: i64, rows: i64, rain_expected: i32) -> i64 { irrigation_cycles(dryness, rows, rain_expected != 0) }
""",
    },
    "tiered_meter_repair": {
        "seed": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub consumed_units: i64, pub included_units: i64, pub peak_window: bool }
impl RequestInput { pub fn valid(&self) -> bool { self.consumed_units >= 0 && self.included_units >= 0 } }
#[derive(Serialize)] pub struct ResponseOutput { pub standard_units: i64, pub excess_units: i64, pub excess_rate: i64, pub usage_points: i64, pub band: String }
pub fn standard_usage(consumed: i64, included: i64) -> i64 { consumed.min(included) }
pub fn excess_usage(consumed: i64, included: i64) -> i64 { (consumed - included).max(0) }
pub fn meter_rate(peak: bool) -> i64 { if peak { 7 } else { 4 } }
pub fn usage_points(consumed: i64, included: i64, peak: bool) -> i64 { if consumed > included { consumed * meter_rate(peak) } else { consumed * 2 } }
pub fn handle(value: RequestInput) -> ResponseOutput { let standard_units = standard_usage(value.consumed_units, value.included_units); let excess_units = excess_usage(value.consumed_units, value.included_units); ResponseOutput { standard_units, excess_units, excess_rate: meter_rate(value.peak_window), usage_points: usage_points(value.consumed_units, value.included_units, value.peak_window), band: if excess_units == 0 { "included".into() } else { "excess".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_usage_points(consumed: i64, included: i64, peak: i32) -> i64 { usage_points(consumed, included, peak != 0) }
""",
        "reference": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub consumed_units: i64, pub included_units: i64, pub peak_window: bool }
impl RequestInput { pub fn valid(&self) -> bool { self.consumed_units >= 0 && self.included_units >= 0 } }
#[derive(Serialize)] pub struct ResponseOutput { pub standard_units: i64, pub excess_units: i64, pub excess_rate: i64, pub usage_points: i64, pub band: String }
pub fn standard_usage(consumed: i64, included: i64) -> i64 { consumed.min(included) }
pub fn excess_usage(consumed: i64, included: i64) -> i64 { (consumed - included).max(0) }
pub fn meter_rate(peak: bool) -> i64 { if peak { 7 } else { 4 } }
pub fn usage_points(consumed: i64, included: i64, peak: bool) -> i64 { standard_usage(consumed, included) * 2 + excess_usage(consumed, included) * meter_rate(peak) }
pub fn handle(value: RequestInput) -> ResponseOutput { let standard_units = standard_usage(value.consumed_units, value.included_units); let excess_units = excess_usage(value.consumed_units, value.included_units); ResponseOutput { standard_units, excess_units, excess_rate: meter_rate(value.peak_window), usage_points: usage_points(value.consumed_units, value.included_units, value.peak_window), band: if excess_units == 0 { "included".into() } else { "excess".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_usage_points(consumed: i64, included: i64, peak: i32) -> i64 { usage_points(consumed, included, peak != 0) }
""",
    },
    "timeline_bucket_repair": {
        "seed": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub timestamp_second: i64, pub origin_second: i64, pub bucket_seconds: i64 }
impl RequestInput { pub fn valid(&self) -> bool { self.timestamp_second >= 0 && self.origin_second >= 0 && self.bucket_seconds > 0 } }
#[derive(Serialize)] pub struct ResponseOutput { pub offset_seconds: i64, pub bucket_index: i64, pub bucket_start_second: i64, pub position_second: i64, pub location: String }
pub fn timeline_offset(timestamp: i64, origin: i64) -> i64 { (timestamp - origin).max(0) }
pub fn timeline_bucket_index(timestamp: i64, origin: i64, width: i64) -> i64 { let offset = timeline_offset(timestamp, origin); let index = offset / width; if offset - index * width == 0 { index + 1 } else { index } }
pub fn handle(value: RequestInput) -> ResponseOutput { let offset_seconds = timeline_offset(value.timestamp_second, value.origin_second); let bucket_index = timeline_bucket_index(value.timestamp_second, value.origin_second, value.bucket_seconds); let bucket_start_second = value.origin_second + bucket_index * value.bucket_seconds; let position_second = offset_seconds - bucket_index * value.bucket_seconds; ResponseOutput { offset_seconds, bucket_index, bucket_start_second, position_second, location: if position_second == 0 { "boundary".into() } else { "inside".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_timeline_bucket_index(timestamp: i64, origin: i64, width: i64) -> i64 { timeline_bucket_index(timestamp, origin, width) }
""",
        "reference": """
use serde::{Deserialize, Serialize};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput { pub timestamp_second: i64, pub origin_second: i64, pub bucket_seconds: i64 }
impl RequestInput { pub fn valid(&self) -> bool { self.timestamp_second >= 0 && self.origin_second >= 0 && self.bucket_seconds > 0 } }
#[derive(Serialize)] pub struct ResponseOutput { pub offset_seconds: i64, pub bucket_index: i64, pub bucket_start_second: i64, pub position_second: i64, pub location: String }
pub fn timeline_offset(timestamp: i64, origin: i64) -> i64 { (timestamp - origin).max(0) }
pub fn timeline_bucket_index(timestamp: i64, origin: i64, width: i64) -> i64 { timeline_offset(timestamp, origin) / width }
pub fn handle(value: RequestInput) -> ResponseOutput { let offset_seconds = timeline_offset(value.timestamp_second, value.origin_second); let bucket_index = timeline_bucket_index(value.timestamp_second, value.origin_second, value.bucket_seconds); let bucket_start_second = value.origin_second + bucket_index * value.bucket_seconds; let position_second = offset_seconds - bucket_index * value.bucket_seconds; ResponseOutput { offset_seconds, bucket_index, bucket_start_second, position_second, location: if position_second == 0 { "boundary".into() } else { "inside".into() } } }
#[unsafe(no_mangle)] pub extern "C" fn parley_timeline_bucket_index(timestamp: i64, origin: i64, width: i64) -> i64 { timeline_bucket_index(timestamp, origin, width) }
""",
    },
}


RUST_WASM = {
    "rail_connection_build": ("parley_connection_margin", ["a", "b", "c", "d ? 1 : 0"]),
    "orchard_irrigation_build": ("parley_irrigation_cycles", ["a", "b", "c ? 1 : 0"]),
    "tiered_meter_repair": ("parley_usage_points", ["a", "b", "c ? 1 : 0"]),
    "timeline_bucket_repair": ("parley_timeline_bucket_index", ["a", "b", "c"]),
}


RUST_MAIN_TEMPLATE = BASE_RUST_MAIN_TEMPLATE.replace(
    "fullstack_agent_036", "fullstack_agent_037"
).replace("FULLSTACK_036", "FULLSTACK_037").replace(
    'route("/api/status"', 'route("@@STATUS_ROUTE@@"'
).replace(
    "Ok(value) => json_response(handle(value), StatusCode::OK)",
    'Ok(value) if value.valid() => json_response(handle(value), StatusCode::OK), Ok(_) => error("invalid_json", StatusCode::BAD_REQUEST, "numeric value outside contract")',
)


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
        status_route=task["status_route"],
    )
    return {
        "logic.py": ScaffoldFile(_clean(PYTHON_LOGIC[task["id"]][variant]), True),
        "browser.js": ScaffoldFile(browser, True),
        "app.py": ScaffoldFile(app, True),
        "requirements.txt": ScaffoldFile((BENCHMARKS / "fullstack_035/python/requirements.txt").read_text(), False),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _typescript_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    server = _replace(
        TS_SERVER_TEMPLATE,
        schema=TS_SCHEMA[task["id"]],
        service=task["service"],
        route=task["post_route"],
        status_route=task["status_route"],
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
    converted = ", ".join(
        f"asI64({value}, '{names[index]}')" if "?" not in value else value
        for index, value in enumerate(args)
    )
    return _clean(
        f"""
const asI64 = (value, name) => {{ if (typeof value === "bigint") return value; if (!Number.isSafeInteger(value)) throw new TypeError(`${{name}} must be a safe whole number`); return BigInt(value); }};
export async function loadParley() {{
  const response = await fetch(new URL("/fullstack_agent_037.wasm", import.meta.url));
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
        status_route=task["status_route"],
    )
    return {
        "src/lib.rs": ScaffoldFile(_clean(RUST_LIB[task["id"]][variant]), True),
        "src/main.rs": ScaffoldFile(main, True),
        "Cargo.toml": ScaffoldFile((BENCHMARKS / "fullstack_037/rust/Cargo.toml").read_text(), False),
        "Cargo.lock": ScaffoldFile((BENCHMARKS / "fullstack_037/rust/Cargo.lock").read_text(), False),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def scaffold_files(
    task: dict[str, Any], language: str, variant: str = "seed"
) -> dict[str, ScaffoldFile]:
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
