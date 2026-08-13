"""Generate frozen language workspaces for full-stack agent study 045."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import textwrap
from typing import Any

try:
    from .fullstack_agent_045_logic import (
        parley_logic,
        python_browser,
        python_logic,
        rust_logic,
        typescript_logic,
    )
except ImportError:
    from fullstack_agent_045_logic import (
        parley_logic,
        python_browser,
        python_logic,
        rust_logic,
        typescript_logic,
    )


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS_PATH = BENCHMARKS / "fullstack_agent_045_tasks.json"
LANGUAGES = ("parley", "python", "typescript", "rust")


@dataclass(frozen=True)
class ScaffoldFile:
    text: str
    editable: bool


def _clean(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


def load_task_map() -> dict[str, dict[str, Any]]:
    payload = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    return {task["id"]: task for task in payload["tasks"]}


def _contract(task: dict[str, Any]) -> str:
    request = "\n".join(f"- `{name}`: {kind}" for name, kind in task["request_fields"].items())
    response = "\n".join(f"- `{name}`: {kind}" for name, kind in task["response_fields"].items())
    return _clean(f"""
    # {task['title']}

    {task['statement']}

    ## HTTP

    - `GET {task['status_route']}` returns `{{"service":"{task['service']}","ready":true}}`.
    - `POST {task['post_route']}` uses strict JSON, then the application decides authorization,
      domain validation, status, response headers, and body.
    - Missing, unknown, or wrongly typed JSON fields return 400 `invalid_json` before the handler.
    - Negative integers are well-typed and must reach the handler's 422 decision.
    - Non-JSON POSTs return 415; bodies above 16384 bytes return 413.

    Request fields:

    {request}

    Response fields:

    {response}

    ## Browser

    Export `{task['browser_export']}` with arguments in this order:
    `{', '.join(task['browser_fields'])}`. It returns `{task['shared_result_field']}`.
    """)


PUBLIC_INDEX = _clean("""
<!doctype html>
<meta charset="utf-8">
<title>Full-stack agent study 045</title>
<main>Full-stack agent study 045 browser target</main>
""")


def _names(task: dict[str, Any]) -> tuple[str, str]:
    key = next(iter(task["request_fields"]))
    state = next(name for name, kind in reversed(task["response_fields"].items()) if kind == "text")
    return key, state


def _zero_mapping(task: dict[str, Any], *, language: str, value: str, state: str) -> str:
    key, state_field = _names(task)
    parts = []
    for name, kind in task["response_fields"].items():
        if name == key:
            rendered = value
        elif name == state_field:
            rendered = state
        elif kind == "number":
            rendered = "0"
        else:
            raise ValueError(f"unexpected response field {name}")
        if language == "parley":
            parts.append(f"{name} {rendered}")
        elif language == "python":
            parts.append(f"'{name}':{rendered}")
        elif language == "typescript":
            parts.append(f"{name}:{rendered}")
        else:
            parts.append(f"\"{name}\":{rendered}")
    separator = ", " if language == "parley" else ","
    return separator.join(parts)


PARLEY_CALCULATE = {
    "artifact_accession_build": """
    let total be body's stable_units plus body's fragile_units
    let packing be body's stable_units times 6 plus body's fragile_units times 11
    if body's expedited:
        set packing to packing plus body's packing_stations times 4
    let capacity be body's packing_stations times 40
    let overflow be packing minus capacity
    if overflow is less than 0:
        set overflow to 0
    let rounds be number from (total divided by 5)
    let state be "accepted"
    if overflow is more than 0:
        set state to "queued"
    let result be a response_body with accession_key body's accession_key, artifact_total total, packing_units packing, capacity_units capacity, overflow_units overflow, inspection_rounds rounds, priority_score (artifact_priority_score with body's stable_units, body's fragile_units, body's packing_stations, body's expedited), accession_state state
""",
    "microgrid_bid_build": """
    let generation be body's solar_arrays times 9 plus body's wind_turbines times 13
    let buffer be body's storage_banks times 3
    if body's emergency_mode:
        set buffer to body's storage_banks times 7
    let required be generation plus buffer
    let capacity be body's interconnects times 55
    let delivered be required
    if delivered is more than capacity:
        set delivered to capacity
    let shortfall be required minus capacity
    if shortfall is less than 0:
        set shortfall to 0
    let windows be number from (required divided by 31)
    let state be "accepted"
    if shortfall is more than 0:
        set state to "routine_shortfall"
        if body's emergency_mode:
            set state to "emergency_shortfall"
    let result be a response_body with bid_key body's bid_key, generation_units generation, battery_buffer_units buffer, grid_required_units required, grid_capacity_units capacity, delivered_units delivered, shortfall_units shortfall, dispatch_windows windows, bid_score (microgrid_bid_score with body's solar_arrays, body's wind_turbines, body's storage_banks, body's interconnects, body's emergency_mode), bid_state state
""",
    "trail_permit_repair": """
    let total be body's day_hikers plus body's overnight_hikers
    let required be body's day_hikers times 5 plus body's overnight_hikers times 12
    if body's storm_alert:
        set required to required plus body's trail_guides times 6
    let capacity be body's trail_guides times 38
    let admitted be required
    if admitted is more than capacity:
        set admitted to capacity
    let waiting be required minus capacity
    if waiting is less than 0:
        set waiting to 0
    let state be "issued"
    if waiting is more than 0:
        set state to "routine_queue"
        if body's storm_alert:
            set state to "storm_queue"
    let result be a response_body with permit_code body's permit_code, visitor_total total, trail_units required, guide_capacity_units capacity, admitted_units admitted, waiting_units waiting, permit_score (trail_permit_score with body's day_hikers, body's overnight_hikers, body's trail_guides, body's storm_alert), permit_state state
""",
    "cold_chain_booking_repair": """
    let total be body's chilled_crates plus body's frozen_crates
    let cooling be body's chilled_crates times 7 plus body's frozen_crates times 15
    if body's rush_load:
        set cooling to cooling plus body's loading_docks times 5
    let capacity be body's loading_docks times 44
    let loaded be cooling
    if loaded is more than capacity:
        set loaded to capacity
    let deferred be cooling minus capacity
    if deferred is less than 0:
        set deferred to 0
    let rounds be number from (total divided by 6)
    let state be "booked"
    if deferred is more than 0:
        set state to "routine_queue"
        if body's rush_load:
            set state to "rush_queue"
    let result be a response_body with booking_code body's booking_code, shipment_total total, cooling_units cooling, dock_capacity_units capacity, loaded_units loaded, deferred_units deferred, loading_rounds rounds, booking_score (cold_chain_booking_score with body's chilled_crates, body's frozen_crates, body's loading_docks, body's rush_load), booking_state state
""",
}


def _parley_main(task: dict[str, Any], variant: str) -> str:
    request_fields = ", ".join(f"{name} as {'number' if kind == 'number' else 'yesno' if kind == 'yesno' else 'text'}" for name, kind in task["request_fields"].items())
    response_fields = ", ".join(f"{name} as {'number' if kind == 'number' else 'text'}" for name, kind in task["response_fields"].items())
    key, state = _names(task)
    zero = _zero_mapping(task, language="parley", value="key", state="state")
    lines = [
        'include "logic.par"',
        "a web_request has method as text, path as text, query as text, headers as map from text to text, body as text",
        f"a request_input has {request_fields}",
        f"a response_body has {response_fields}",
        "a controlled_response has status as number, headers as map from text to text, body as response_body",
        "a service_status has service as text, ready as yesno",
        f'to project_status giving service_status:\n    give back a service_status with service "{task["service"]}", ready yes',
        f"to empty_body with key as text, state as text giving response_body:\n    give back a response_body with {zero}",
        "to handle_request with request as web_request, body as request_input giving controlled_response:",
        "    let headers be a map from text to text",
    ]
    auth = task.get("authorization")
    if auth:
        operator = "is not" if not (task["id"] == "trail_permit_repair" and variant == "seed") else "is"
        lines += [
            f'    let credential be (maybe item "{auth["header"]}" of request\'s headers) otherwise ""',
            f'    if credential {operator} "{auth["value"]}":',
            f'        set item "{next(iter(auth["failure_headers"]))}" of headers to "{next(iter(auth["failure_headers"].values()))}"',
            f'        give back a controlled_response with status {auth["failure_status"]}, headers headers, body (empty_body with body\'s {key}, "authorization_required")',
        ]
    for name, kind in task["request_fields"].items():
        if kind == "number":
            lines += [
                f"    if body's {name} is less than 0:",
                '        set item "x-validation" of headers to "nonnegative"',
                f'        give back a controlled_response with status 422, headers headers, body (empty_body with body\'s {key}, "invalid")',
            ]
    zero_field, total_expr = {
        "artifact_accession_build": ("packing_stations", "body's stable_units plus body's fragile_units"),
        "microgrid_bid_build": ("interconnects", "body's solar_arrays times 9 plus body's wind_turbines times 13"),
        "trail_permit_repair": ("trail_guides", "body's day_hikers plus body's overnight_hikers"),
        "cold_chain_booking_repair": ("loading_docks", "body's chilled_crates plus body's frozen_crates"),
    }[task["id"]]
    lines += [
        f"    if body's {zero_field} is 0:",
        f"        if {total_expr} is more than 0:",
        f'            set item "x-validation" of headers to "{zero_field}"',
        f'            give back a controlled_response with status 422, headers headers, body (empty_body with body\'s {key}, "invalid")',
    ]
    if task["id"] == "microgrid_bid_build":
        lines += [
            "    if body's duplicate_bid:",
            '        set item "x-conflict" of headers to "duplicate_bid"',
            f'        give back a controlled_response with status 409, headers headers, body (empty_body with body\'s {key}, "duplicate")',
        ]
    lines.extend("    " + line for line in _clean(PARLEY_CALCULATE[task["id"]]).rstrip().splitlines())
    if task["kind"] == "implementation" and variant == "seed":
        lines.append("    give back a controlled_response with status 200, headers headers, body result")
    else:
        headers = {
            "artifact_accession_build": [("location", f'/api/v9/artifact-accessions/{{body\'s {key}}}'), ("x-accession-state", "{state}")],
            "microgrid_bid_build": [("location", f'/api/v9/microgrid-bids/{{body\'s {key}}}'), ("retry-after", "3"), ("x-bid-state", "{state}")],
            "trail_permit_repair": [("x-permit-state", "{state}")],
            "cold_chain_booking_repair": [("location", f'/api/v9/cold-chain-bookings/{{body\'s {key}}}'), ("x-booking-state", "{state}")],
        }[task["id"]]
        if task["id"] == "cold_chain_booking_repair" and variant == "seed":
            headers[0] = ("content-length", headers[0][1])
        for name, value in headers:
            lines.append(f'    set item "{name}" of headers to "{value}"')
        lines.append(f"    give back a controlled_response with status {task['success_status']}, headers headers, body result")
    return "\n".join(lines) + "\n"


def _parley_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    manifest = {
        "schema_version": 1,
        "name": task["id"],
        "entrypoint": "main.par",
        "static_dir": "public",
        "routes": [
            {"method": "GET", "path": task["status_route"], "handler": "project_status"},
            {"method": "POST", "path": task["post_route"], "handler": "handle_request", "response": {"status_field": "status", "headers_field": "headers", "body_field": "body"}},
        ],
        "browser": {"entrypoint": "main.par", "exports": [{"name": task["browser_export"]}]},
        "server": {"host": "127.0.0.1", "port": 8787, "max_body_bytes": 16384},
    }
    return {
        "logic.par": ScaffoldFile(_clean(parley_logic(task, variant)), True),
        "main.par": ScaffoldFile(_parley_main(task, variant), True),
        "parley.web.json": ScaffoldFile(json.dumps(manifest, indent=2) + "\n", True),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _python_handler(task: dict[str, Any], variant: str) -> str:
    key, state = _names(task)
    zero = _zero_mapping(task, language="python", value=f"v.{key}", state="state")
    checks = []
    auth = task.get("authorization")
    if auth:
        operator = "!=" if not (task["id"] == "trail_permit_repair" and variant == "seed") else "=="
        headers = repr(auth["failure_headers"])
        checks.append(f"if request.headers.get('{auth['header']}','') {operator} {auth['value']!r}: return outcome(zero(v,'authorization_required'),{auth['failure_status']},{headers})")
    numeric = [name for name, kind in task["request_fields"].items() if kind == "number"]
    checks.append(f"if any(item < 0 for item in ({','.join('v.' + name for name in numeric)},)): return outcome(zero(v,'invalid'),422,{{'x-validation':'nonnegative'}})")
    zero_field, positive = {
        "artifact_accession_build": ("packing_stations", "v.stable_units+v.fragile_units"),
        "microgrid_bid_build": ("interconnects", "v.solar_arrays*9+v.wind_turbines*13"),
        "trail_permit_repair": ("trail_guides", "v.day_hikers+v.overnight_hikers"),
        "cold_chain_booking_repair": ("loading_docks", "v.chilled_crates+v.frozen_crates"),
    }[task["id"]]
    checks.append(f"if v.{zero_field}==0 and {positive}>0: return outcome(zero(v,'invalid'),422,{{'x-validation':'{zero_field}'}})")
    if task["id"] == "microgrid_bid_build":
        checks.append("if v.duplicate_bid: return outcome(zero(v,'duplicate'),409,{'x-conflict':'duplicate_bid'})")
    if task["kind"] == "implementation" and variant == "seed":
        success = "return outcome(calculate(v),200,{})"
    else:
        mapping = {
            "artifact_accession_build": f"{{'location':f'/api/v9/artifact-accessions/{{v.{key}}}','x-accession-state':str(body['{state}'])}}",
            "microgrid_bid_build": f"{{'location':f'/api/v9/microgrid-bids/{{v.{key}}}','retry-after':'3','x-bid-state':str(body['{state}'])}}",
            "trail_permit_repair": f"{{'x-permit-state':str(body['{state}'])}}",
            "cold_chain_booking_repair": f"{{'location':f'/api/v9/cold-chain-bookings/{{v.{key}}}','x-booking-state':str(body['{state}'])}}",
        }[task["id"]]
        if task["id"] == "cold_chain_booking_repair" and variant == "seed":
            mapping = mapping.replace("'location'", "'content-length'", 1)
        success = f"body=calculate(v); return outcome(body,{task['success_status']},{mapping})"
    body = "\n    ".join(checks + [success])
    return f"def zero(v:RequestInput,state:str)->dict[str,object]: return {{{zero}}}\ndef decide(v:RequestInput,request:Request)->JSONResponse:\n    {body}\n"


PYTHON_APP = """from __future__ import annotations
import json,os
from pathlib import Path
from fastapi import FastAPI,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from logic import RequestInput,calculate
MAX_BODY_BYTES=16_384
PUBLIC=Path(__file__).with_name('public')
def error(code:str,status:int,detail:str)->JSONResponse: return JSONResponse({'error':code,'detail':detail},status_code=status)
def outcome(body:dict[str,object],status:int,headers:dict[str,str])->JSONResponse:
    if any(name.lower() in {'content-length','content-type','connection','transfer-encoding','x-content-type-options'} for name in headers): return error('invalid_response_headers',500,'server-owned response header')
    return JSONResponse(body,status_code=status,headers=headers)
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
@app.get('@@STATUS@@')
async def status(): return {'service':'@@SERVICE@@','ready':True}
@app.post('@@ROUTE@@')
async def endpoint(request:Request):
    media=request.headers.get('content-type','').split(';',1)[0].strip().lower()
    if media!='application/json' and not media.endswith('+json'): return error('json_content_type_required',415,'expected application/json')
    declared=request.headers.get('content-length')
    if declared and (not declared.isdigit() or int(declared)>MAX_BODY_BYTES): return error('body_too_large',413,'request body exceeds 16384 bytes')
    raw=await request.body()
    if len(raw)>MAX_BODY_BYTES: return error('body_too_large',413,'request body exceeds 16384 bytes')
    try: parsed=RequestInput.model_validate(json.loads(raw),strict=True)
    except (json.JSONDecodeError,UnicodeDecodeError,ValidationError) as exc: return error('invalid_json',400,str(exc))
    return decide(parsed,request)
@app.api_route('/api/{rest:path}',methods=['GET','POST','PUT','PATCH','DELETE'])
async def missing(rest:str): return error('not_found',404,f'no API route /api/{rest}')
@app.get('/parley.js')
async def browser(): return FileResponse(Path(__file__).with_name('browser.js'),media_type='text/javascript')
app.mount('/',StaticFiles(directory=PUBLIC,html=True),name='public')
if __name__=='__main__':
 import uvicorn; uvicorn.run(app,host='127.0.0.1',port=int(os.environ['PARLEY_WEB_PORT']),log_level='warning')
"""


def _python_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    app = PYTHON_APP.replace("@@STATUS@@", task["status_route"]).replace("@@SERVICE@@", task["service"]).replace("@@ROUTE@@", task["post_route"])
    app = app.replace("MAX_BODY_BYTES=16_384", _python_handler(task, variant) + "\nMAX_BODY_BYTES=16_384")
    return {
        "logic.py": ScaffoldFile(_clean(python_logic(task, variant)), True),
        "browser.js": ScaffoldFile(_clean(python_browser(task, variant)), True),
        "app.py": ScaffoldFile(_clean(app), True),
        "requirements.txt": ScaffoldFile((BENCHMARKS / "fullstack_035/python/requirements.txt").read_text(), False),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _ts_schema(task: dict[str, Any]) -> str:
    fields = ",".join(f"{name}:z.{('number().int()' if kind == 'number' else 'boolean()' if kind == 'yesno' else 'string()')}" for name, kind in task["request_fields"].items())
    return f"z.object({{{fields}}}).strict()"


def _typescript_decide(task: dict[str, Any], variant: str) -> str:
    key, state = _names(task)
    zero = _zero_mapping(task, language="typescript", value=f"v.{key}", state="state")
    lines = [f"const zero=(v:RequestInput,state:string)=>({{{zero}}});", "const decide=(v:RequestInput,headers:Headers)=>{"]
    auth = task.get("authorization")
    if auth:
        operator = "!==" if not (task["id"] == "trail_permit_repair" and variant == "seed") else "==="
        fail = json.dumps(auth["failure_headers"], separators=(",", ":"))
        lines.append(f"if((headers.get('{auth['header']}')??''){operator}{json.dumps(auth['value'])})return response(zero(v,'authorization_required'),{auth['failure_status']},{fail});")
    numeric = [name for name, kind in task["request_fields"].items() if kind == "number"]
    lines.append(f"if([{','.join('v.' + name for name in numeric)}].some(item=>item<0))return response(zero(v,'invalid'),422,{{'x-validation':'nonnegative'}});")
    zero_field, positive = {
        "artifact_accession_build": ("packing_stations", "v.stable_units+v.fragile_units"),
        "microgrid_bid_build": ("interconnects", "v.solar_arrays*9+v.wind_turbines*13"),
        "trail_permit_repair": ("trail_guides", "v.day_hikers+v.overnight_hikers"),
        "cold_chain_booking_repair": ("loading_docks", "v.chilled_crates+v.frozen_crates"),
    }[task["id"]]
    lines.append(f"if(v.{zero_field}===0&&{positive}>0)return response(zero(v,'invalid'),422,{{'x-validation':'{zero_field}'}});")
    if task["id"] == "microgrid_bid_build":
        lines.append("if(v.duplicate_bid)return response(zero(v,'duplicate'),409,{'x-conflict':'duplicate_bid'});")
    if task["kind"] == "implementation" and variant == "seed":
        lines.append("return response(calculate(v),200,{});")
    else:
        mapping = {
            "artifact_accession_build": f"{{'location':`/api/v9/artifact-accessions/${{v.{key}}}`,'x-accession-state':String(body.{state})}}",
            "microgrid_bid_build": f"{{'location':`/api/v9/microgrid-bids/${{v.{key}}}`,'retry-after':'3','x-bid-state':String(body.{state})}}",
            "trail_permit_repair": f"{{'x-permit-state':String(body.{state})}}",
            "cold_chain_booking_repair": f"{{'location':`/api/v9/cold-chain-bookings/${{v.{key}}}`,'x-booking-state':String(body.{state})}}",
        }[task["id"]]
        if task["id"] == "cold_chain_booking_repair" and variant == "seed":
            mapping = mapping.replace("'location'", "'content-length'", 1)
        lines.append(f"const body=calculate(v);return response(body,{task['success_status']},{mapping});")
    lines.append("};")
    return "".join(lines)


TS_SERVER = """import {serve} from '@hono/node-server';import {serveStatic} from '@hono/node-server/serve-static';import {Hono} from 'hono';import {z} from 'zod';import {calculate,type RequestInput} from './logic.js';
declare const process:{env:Record<string,string|undefined>};const maxBodyBytes=16_384;const schema=@@SCHEMA@@;
const response=(value:unknown,status=200,headers:Record<string,string>={})=>{if(Object.keys(headers).some(name=>['content-length','content-type','connection','transfer-encoding','x-content-type-options'].includes(name.toLowerCase())))return new Response(JSON.stringify({error:'invalid_response_headers',detail:'server-owned response header'}),{status:500,headers:{'content-type':'application/json'}});return new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json',...headers}})};const error=(code:string,status:number,detail:string)=>response({error:code,detail},status);@@DECIDE@@
const app=new Hono();app.get('@@STATUS@@',()=>response({service:'@@SERVICE@@',ready:true}));app.post('@@ROUTE@@',async context=>{const media=(context.req.header('content-type')??'').split(';',1)[0]!.trim().toLowerCase();if(media!=='application/json'&&!media.endsWith('+json'))return error('json_content_type_required',415,'expected application/json');const declared=context.req.header('content-length');if(declared&&(!/^\\d+$/.test(declared)||Number(declared)>maxBodyBytes))return error('body_too_large',413,'request body exceeds 16384 bytes');const raw=await context.req.arrayBuffer();if(raw.byteLength>maxBodyBytes)return error('body_too_large',413,'request body exceeds 16384 bytes');try{const parsed=schema.safeParse(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)));if(!parsed.success)return error('invalid_json',400,parsed.error.message);return decide(parsed.data,context.req.raw.headers)}catch(caught){return error('invalid_json',400,String(caught))}});app.all('/api/*',context=>error('not_found',404,`no API route ${context.req.path}`));app.get('/parley.js',serveStatic({path:process.env.FULLSTACK_045_BROWSER??'./dist/logic.js'}));app.get('/*',serveStatic({root:'./public'}));serve({fetch:app.fetch,hostname:'127.0.0.1',port:Number(process.env.PARLEY_WEB_PORT)});
"""


def _typescript_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    server = TS_SERVER.replace("@@SCHEMA@@", _ts_schema(task)).replace("@@DECIDE@@", _typescript_decide(task, variant)).replace("@@STATUS@@", task["status_route"]).replace("@@SERVICE@@", task["service"]).replace("@@ROUTE@@", task["post_route"])
    return {
        "src/logic.ts": ScaffoldFile(_clean(typescript_logic(task, variant)), True),
        "src/server.ts": ScaffoldFile(_clean(server), True),
        "package.json": ScaffoldFile((BENCHMARKS / "fullstack_035/typescript/package.json").read_text(), False),
        "package-lock.json": ScaffoldFile((BENCHMARKS / "fullstack_035/typescript/package-lock.json").read_text(), False),
        "tsconfig.json": ScaffoldFile((BENCHMARKS / "fullstack_035/typescript/tsconfig.json").read_text(), False),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _rust_browser(task: dict[str, Any]) -> str:
    conversions = []
    for index, name in enumerate(task["browser_fields"]):
        conversions.append(f"a{index}?1:0" if task["request_fields"][name] == "yesno" else f"asI64(a{index},'a{index}')")
    args = ",".join(f"a{i}" for i in range(len(task["browser_fields"])))
    return f"const asI64=(v,n)=>{{if(typeof v==='bigint')return v;if(!Number.isSafeInteger(v))throw new TypeError(`${{n}} must be a safe whole number`);return BigInt(v)}};export async function loadParley(){{const r=await fetch(new URL('/fullstack_agent_045.wasm',import.meta.url));const m=(await WebAssembly.instantiateStreaming(r)).instance.exports;return {{{task['browser_export']}:({args})=>m.parley_browser_score({','.join(conversions)})}}}}"


def _rust_decisions(task: dict[str, Any], variant: str) -> str:
    key, state = _names(task)
    zero = _zero_mapping(task, language="rust", value=f"v.{key}", state="state")
    lines = [f"fn zero(v:&RequestInput,state:&str)->serde_json::Value{{json!({{{zero}}})}}", "fn decide(v:RequestInput,headers:&HeaderMap)->Response{"]
    auth = task.get("authorization")
    if auth:
        operator = "!=" if not (task["id"] == "trail_permit_repair" and variant == "seed") else "=="
        fail = "&[(\"%s\",\"%s\")]" % next(iter(auth["failure_headers"].items()))
        lines.append(f"if headers.get(\"{auth['header']}\").and_then(|x|x.to_str().ok()).unwrap_or(\"\"){operator}\"{auth['value']}\"{{return json_response(zero(&v,\"authorization_required\"),{auth['failure_status']},{fail})}}")
    numeric = [name for name, kind in task["request_fields"].items() if kind == "number"]
    lines.append(f"if [{','.join('v.' + name for name in numeric)}].iter().any(|x|*x<0){{return json_response(zero(&v,\"invalid\"),422,&[(\"x-validation\",\"nonnegative\")])}}")
    zero_field, positive = {
        "artifact_accession_build": ("packing_stations", "v.stable_units+v.fragile_units"),
        "microgrid_bid_build": ("interconnects", "v.solar_arrays*9+v.wind_turbines*13"),
        "trail_permit_repair": ("trail_guides", "v.day_hikers+v.overnight_hikers"),
        "cold_chain_booking_repair": ("loading_docks", "v.chilled_crates+v.frozen_crates"),
    }[task["id"]]
    lines.append(f"if v.{zero_field}==0&&{positive}>0{{return json_response(zero(&v,\"invalid\"),422,&[(\"x-validation\",\"{zero_field}\")])}}")
    if task["id"] == "microgrid_bid_build":
        lines.append("if v.duplicate_bid{return json_response(zero(&v,\"duplicate\"),409,&[(\"x-conflict\",\"duplicate_bid\")])}")
    if task["kind"] == "implementation" and variant == "seed":
        lines.append("json_response(calculate(&v),200,&[])")
    else:
        mapping = {
            "artifact_accession_build": f"vec![(\"location\",format!(\"/api/v9/artifact-accessions/{{}}\",v.{key})),(\"x-accession-state\",body.{state}.clone())]",
            "microgrid_bid_build": f"vec![(\"location\",format!(\"/api/v9/microgrid-bids/{{}}\",v.{key})),(\"retry-after\",\"3\".into()),(\"x-bid-state\",body.{state}.clone())]",
            "trail_permit_repair": f"vec![(\"x-permit-state\",body.{state}.clone())]",
            "cold_chain_booking_repair": f"vec![(\"location\",format!(\"/api/v9/cold-chain-bookings/{{}}\",v.{key})),(\"x-booking-state\",body.{state}.clone())]",
        }[task["id"]]
        if task["id"] == "cold_chain_booking_repair" and variant == "seed":
            mapping = mapping.replace('(\"location\"', '(\"content-length\"', 1)
        lines.append(f"let body=calculate(&v);let owned={mapping};let refs:Vec<(&str,&str)>=owned.iter().map(|(a,b)|(*a,b.as_str())).collect();json_response(body,{task['success_status']},&refs)")
    lines.append("}")
    return "".join(lines)


RUST_MAIN = """use std::env;use axum::{Router,body::{Body,to_bytes},extract::Request,http::{HeaderMap,StatusCode,header},response::{IntoResponse,Response},routing::{any,get,post}};use fullstack_agent_045::{RequestInput,calculate};use serde::Serialize;use serde_json::json;use tower_http::services::{ServeDir,ServeFile};const MAX_BODY_BYTES:usize=16_384;const BROWSER_MODULE:&str=r#"@@BROWSER@@"#;
fn json_response(value:impl Serialize,status:u16,headers:&[(&str,&str)])->Response{if headers.iter().any(|(n,_)|matches!(n.to_ascii_lowercase().as_str(),"content-length"|"content-type"|"connection"|"transfer-encoding"|"x-content-type-options")){return error("invalid_response_headers",500,"server-owned response header")}let status=StatusCode::from_u16(status).unwrap();let mut response=(status,serde_json::to_vec(&value).unwrap()).into_response();response.headers_mut().insert(header::CONTENT_TYPE,header::HeaderValue::from_static("application/json"));for(n,v)in headers{response.headers_mut().insert(header::HeaderName::from_bytes(n.as_bytes()).unwrap(),header::HeaderValue::from_str(v).unwrap());}response}fn error(code:&str,status:u16,detail:&str)->Response{let mut r=(StatusCode::from_u16(status).unwrap(),serde_json::to_vec(&json!({"error":code,"detail":detail})).unwrap()).into_response();r.headers_mut().insert(header::CONTENT_TYPE,header::HeaderValue::from_static("application/json"));r}@@DECIDE@@
async fn status()->Response{json_response(json!({"service":"@@SERVICE@@","ready":true}),200,&[])}async fn endpoint(request:Request)->Response{let headers=request.headers().clone();let media=headers.get(header::CONTENT_TYPE).and_then(|v|v.to_str().ok()).unwrap_or("").split(';').next().unwrap_or("").trim().to_ascii_lowercase();if media!="application/json"&&!media.ends_with("+json"){return error("json_content_type_required",415,"expected application/json")}if let Some(length)=headers.get(header::CONTENT_LENGTH){let declared=length.to_str().ok().and_then(|v|v.parse::<usize>().ok());if declared.is_none_or(|v|v>MAX_BODY_BYTES){return error("body_too_large",413,"request body exceeds 16384 bytes")}}let body=match to_bytes(request.into_body(),MAX_BODY_BYTES).await{Ok(body)=>body,Err(_)=>return error("body_too_large",413,"request body exceeds 16384 bytes")};match serde_json::from_slice::<RequestInput>(&body){Ok(v)=>decide(v,&headers),Err(reason)=>error("invalid_json",400,&reason.to_string())}}async fn missing(request:Request<Body>)->Response{error("not_found",404,&format!("no API route {}",request.uri().path()))}async fn browser()->Response{let mut r=BROWSER_MODULE.into_response();r.headers_mut().insert(header::CONTENT_TYPE,header::HeaderValue::from_static("text/javascript; charset=utf-8"));r}#[tokio::main]async fn main(){let wasm=env::var_os("FULLSTACK_045_WASM").map(std::path::PathBuf::from).unwrap();let app=Router::new().route("@@STATUS@@",get(status)).route("@@ROUTE@@",post(endpoint)).route("/api/{*rest}",any(missing)).route("/parley.js",get(browser)).route_service("/fullstack_agent_045.wasm",ServeFile::new(wasm)).fallback_service(ServeDir::new("public").append_index_html_on_directories(true));let port=env::var("PARLEY_WEB_PORT").unwrap().parse::<u16>().unwrap();let listener=tokio::net::TcpListener::bind(("127.0.0.1",port)).await.unwrap();axum::serve(listener,app).await.unwrap()}
"""


def _rust_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    main = RUST_MAIN.replace("@@BROWSER@@", _rust_browser(task)).replace("@@DECIDE@@", _rust_decisions(task, variant)).replace("@@STATUS@@", task["status_route"]).replace("@@SERVICE@@", task["service"]).replace("@@ROUTE@@", task["post_route"])
    return {
        "src/lib.rs": ScaffoldFile(_clean(rust_logic(task, variant)), True),
        "src/main.rs": ScaffoldFile(_clean(main), True),
        "Cargo.toml": ScaffoldFile((BENCHMARKS / "fullstack_045/rust/Cargo.toml").read_text(), False),
        "Cargo.lock": ScaffoldFile((BENCHMARKS / "fullstack_045/rust/Cargo.lock").read_text(), False),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def scaffold_files(task: dict[str, Any], language: str, variant: str = "seed") -> dict[str, ScaffoldFile]:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    if variant not in {"seed", "reference"}:
        raise ValueError(f"unsupported scaffold variant: {variant}")
    files = {"parley": _parley_files, "python": _python_files, "typescript": _typescript_files, "rust": _rust_files}[language](task, variant)
    files["CONTRACT.md"] = ScaffoldFile(_contract(task), False)
    return files


ROOT_FILES: dict[str, tuple[str, ...]] = {
    "parley": ("main.par",),
    "python": ("app.py",),
    "typescript": ("src/server.ts",),
    "rust": ("src/main.rs",),
}
