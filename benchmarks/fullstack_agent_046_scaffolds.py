"""Generate frozen language workspaces for full-stack agent study 046."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import textwrap
from typing import Any

try:
    from .fullstack_agent_046_logic import (
        parley_logic,
        python_browser,
        python_logic,
        rust_logic,
        typescript_logic,
    )
except ImportError:
    from fullstack_agent_046_logic import (
        parley_logic,
        python_browser,
        python_logic,
        rust_logic,
        typescript_logic,
    )


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS_PATH = BENCHMARKS / "fullstack_agent_046_tasks.json"
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
<title>Full-stack agent study 046</title>
<main>Full-stack agent study 046 browser target</main>
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
    "orbital_clearance_build": """
    let total be body's pressurized_pods plus body's vacuum_pods
    let effort be body's pressurized_pods times 8 plus body's vacuum_pods times 14
    if body's solar_flare:
        set effort to effort plus body's docking_arms times 5
    let allowance be body's docking_arms times 47
    let approved be effort
    if approved is more than allowance:
        set approved to allowance
    let spillover be effort minus allowance
    if spillover is less than 0:
        set spillover to 0
    let passes be number from ((total plus 3) divided by 4)
    let state be "cleared"
    if spillover is more than 0:
        set state to "routine_hold"
        if body's solar_flare:
            set state to "flare_hold"
    let result be a response_body with clearance_slug body's clearance_slug, payload_tally total, transfer_effort effort, berth_allowance allowance, approved_effort approved, spillover_effort spillover, orbit_passes passes, clearance_rating (orbital_clearance_rating with body's pressurized_pods, body's vacuum_pods, body's docking_arms, body's solar_flare), clearance_phase state
""",
    "estuary_assay_build": """
    let total be body's inlet_vials plus body's outlet_vials
    let effort be body's inlet_vials times 11 plus body's outlet_vials times 7 plus body's reagent_cartridges times 9
    if body's contamination_alert:
        set effort to effort plus body's reagent_cartridges times 4
    let allowance be body's assay_benches times 52
    let examined be effort
    if examined is more than allowance:
        set examined to allowance
    let pending be effort minus allowance
    if pending is less than 0:
        set pending to 0
    let cycles be number from ((effort plus 26) divided by 27)
    let state be "dispatched"
    if pending is more than 0:
        set state to "routine_queue"
        if body's contamination_alert:
            set state to "contamination_queue"
    let result be a response_body with assay_ref body's assay_ref, sample_tally total, assay_effort effort, bench_allowance allowance, examined_effort examined, pending_assay pending, assay_cycles cycles, assay_rating (estuary_assay_rating with body's inlet_vials, body's outlet_vials, body's reagent_cartridges, body's assay_benches, body's contamination_alert), assay_phase state
""",
    "archive_transfer_repair": """
    let total be body's folio_boxes plus body's atlas_tubes
    let effort be body's folio_boxes times 6 plus body's atlas_tubes times 17
    if body's humidity_warning:
        set effort to effort plus body's catalog_carts times 3
    let allowance be body's catalog_carts times 43
    let shelved be effort
    if shelved is more than allowance:
        set shelved to allowance
    let quarantine be effort minus allowance
    if quarantine is less than 0:
        set quarantine to 0
    let rounds be number from ((total plus 4) divided by 5)
    let state be "shelved"
    if quarantine is more than 0:
        set state to "routine_hold"
        if body's humidity_warning:
            set state to "humidity_hold"
    let result be a response_body with transfer_tag body's transfer_tag, volume_tally total, relocation_effort effort, cart_allowance allowance, shelved_effort shelved, quarantined_effort quarantine, transfer_rounds rounds, transfer_rating (archive_transfer_rating with body's folio_boxes, body's atlas_tubes, body's catalog_carts, body's humidity_warning), transfer_phase state
""",
    "beacon_enrollment_repair": """
    let total be body's analog_transponders plus body's digital_transponders
    let effort be body's analog_transponders times 9 plus body's digital_transponders times 16
    if body's whiteout_warning:
        set effort to effort plus body's calibration_frames times 7
    let allowance be body's calibration_frames times 50
    let commissioned be effort
    if commissioned is more than allowance:
        set commissioned to allowance
    let remainder be effort minus allowance
    if remainder is less than 0:
        set remainder to 0
    let rounds be number from ((total plus 5) divided by 6)
    let state be "enrolled"
    if remainder is more than 0:
        set state to "routine_hold"
        if body's whiteout_warning:
            set state to "whiteout_hold"
    let result be a response_body with enrollment_ref body's enrollment_ref, transponder_tally total, tuning_effort effort, frame_allowance allowance, commissioned_effort commissioned, uncommissioned_effort remainder, tuning_rounds rounds, enrollment_rating (beacon_enrollment_rating with body's analog_transponders, body's digital_transponders, body's calibration_frames, body's whiteout_warning), enrollment_phase state
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
        lines += [
            f'    let credential be (maybe item "{auth["header"]}" of request\'s headers) otherwise ""',
            f'    if credential is not "{auth["value"]}":',
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
        "orbital_clearance_build": ("docking_arms", "body's pressurized_pods plus body's vacuum_pods"),
        "estuary_assay_build": ("assay_benches", "body's inlet_vials plus body's outlet_vials"),
        "archive_transfer_repair": ("catalog_carts", "body's folio_boxes plus body's atlas_tubes"),
        "beacon_enrollment_repair": ("calibration_frames", "body's analog_transponders plus body's digital_transponders"),
    }[task["id"]]
    lines += [
        f"    if body's {zero_field} is 0:",
        f"        if {total_expr} is more than 0:",
        f'            set item "x-validation" of headers to "{zero_field}"',
        f'            give back a controlled_response with status 422, headers headers, body (empty_body with body\'s {key}, "invalid")',
    ]
    if task["id"] == "estuary_assay_build":
        lines += [
            "    if body's repeated_submission:",
            '        set item "x-conflict" of headers to "repeated_submission"',
            f'        give back a controlled_response with status 409, headers headers, body (empty_body with body\'s {key}, "duplicate")',
        ]
    lines.extend("    " + line for line in _clean(PARLEY_CALCULATE[task["id"]]).rstrip().splitlines())
    if task["kind"] == "implementation" and variant == "seed":
        lines.append("    give back a controlled_response with status 200, headers headers, body result")
    else:
        headers = {
            "orbital_clearance_build": [("location", f'/api/v10/orbital-clearances/{{body\'s {key}}}'), ("x-clearance-phase", "{state}")],
            "estuary_assay_build": [("location", f'/api/v10/estuary-assays/{{body\'s {key}}}'), ("retry-after", "5"), ("x-assay-phase", "{state}")],
            "archive_transfer_repair": [("location", f'/api/v10/archive-transfers/{{body\'s {key}}}'), ("x-transfer-phase", "{state}")],
            "beacon_enrollment_repair": [("location", f'/api/v10/beacon-enrollments/{{body\'s {key}}}'), ("retry-after", "4"), ("x-enrollment-phase", "{state}")],
        }[task["id"]]
        if task["id"] == "archive_transfer_repair" and variant == "seed":
            headers[1] = ("x-transfer-state", headers[1][1])
        for name, value in headers:
            lines.append(f'    set item "{name}" of headers to "{value}"')
        status = 201 if task["id"] == "beacon_enrollment_repair" and variant == "seed" else task["success_status"]
        lines.append(f"    give back a controlled_response with status {status}, headers headers, body result")
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
        "parley.web.json": ScaffoldFile(
            json.dumps(manifest, separators=(",", ":")) + "\n", True
        ),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _python_handler(task: dict[str, Any], variant: str) -> str:
    key, state = _names(task)
    zero = _zero_mapping(task, language="python", value=f"v.{key}", state="state")
    checks = []
    auth = task.get("authorization")
    if auth:
        headers = repr(auth["failure_headers"])
        checks.append(f"if request.headers.get('{auth['header']}','') != {auth['value']!r}: return outcome(zero(v,'authorization_required'),{auth['failure_status']},{headers})")
    numeric = [name for name, kind in task["request_fields"].items() if kind == "number"]
    checks.append(f"if any(item < 0 for item in ({','.join('v.' + name for name in numeric)},)): return outcome(zero(v,'invalid'),422,{{'x-validation':'nonnegative'}})")
    zero_field, positive = {
        "orbital_clearance_build": ("docking_arms", "v.pressurized_pods+v.vacuum_pods"),
        "estuary_assay_build": ("assay_benches", "v.inlet_vials+v.outlet_vials"),
        "archive_transfer_repair": ("catalog_carts", "v.folio_boxes+v.atlas_tubes"),
        "beacon_enrollment_repair": ("calibration_frames", "v.analog_transponders+v.digital_transponders"),
    }[task["id"]]
    checks.append(f"if v.{zero_field}==0 and {positive}>0: return outcome(zero(v,'invalid'),422,{{'x-validation':'{zero_field}'}})")
    if task["id"] == "estuary_assay_build":
        checks.append("if v.repeated_submission: return outcome(zero(v,'duplicate'),409,{'x-conflict':'repeated_submission'})")
    if task["kind"] == "implementation" and variant == "seed":
        success = "return outcome(calculate(v),200,{})"
    else:
        mapping = {
            "orbital_clearance_build": f"{{'location':f'/api/v10/orbital-clearances/{{v.{key}}}','x-clearance-phase':str(body['{state}'])}}",
            "estuary_assay_build": f"{{'location':f'/api/v10/estuary-assays/{{v.{key}}}','retry-after':'5','x-assay-phase':str(body['{state}'])}}",
            "archive_transfer_repair": f"{{'location':f'/api/v10/archive-transfers/{{v.{key}}}','x-transfer-phase':str(body['{state}'])}}",
            "beacon_enrollment_repair": f"{{'location':f'/api/v10/beacon-enrollments/{{v.{key}}}','retry-after':'4','x-enrollment-phase':str(body['{state}'])}}",
        }[task["id"]]
        if task["id"] == "archive_transfer_repair" and variant == "seed":
            mapping = mapping.replace("'x-transfer-phase'", "'x-transfer-state'", 1)
        status = 201 if task["id"] == "beacon_enrollment_repair" and variant == "seed" else task["success_status"]
        success = f"body=calculate(v); return outcome(body,{status},{mapping})"
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
        fail = json.dumps(auth["failure_headers"], separators=(",", ":"))
        lines.append(f"if((headers.get('{auth['header']}')??'')!=={json.dumps(auth['value'])})return response(zero(v,'authorization_required'),{auth['failure_status']},{fail});")
    numeric = [name for name, kind in task["request_fields"].items() if kind == "number"]
    lines.append(f"if([{','.join('v.' + name for name in numeric)}].some(item=>item<0))return response(zero(v,'invalid'),422,{{'x-validation':'nonnegative'}});")
    zero_field, positive = {
        "orbital_clearance_build": ("docking_arms", "v.pressurized_pods+v.vacuum_pods"),
        "estuary_assay_build": ("assay_benches", "v.inlet_vials+v.outlet_vials"),
        "archive_transfer_repair": ("catalog_carts", "v.folio_boxes+v.atlas_tubes"),
        "beacon_enrollment_repair": ("calibration_frames", "v.analog_transponders+v.digital_transponders"),
    }[task["id"]]
    lines.append(f"if(v.{zero_field}===0&&{positive}>0)return response(zero(v,'invalid'),422,{{'x-validation':'{zero_field}'}});")
    if task["id"] == "estuary_assay_build":
        lines.append("if(v.repeated_submission)return response(zero(v,'duplicate'),409,{'x-conflict':'repeated_submission'});")
    if task["kind"] == "implementation" and variant == "seed":
        lines.append("return response(calculate(v),200,{});")
    else:
        mapping = {
            "orbital_clearance_build": f"{{'location':`/api/v10/orbital-clearances/${{v.{key}}}`,'x-clearance-phase':String(body.{state})}}",
            "estuary_assay_build": f"{{'location':`/api/v10/estuary-assays/${{v.{key}}}`,'retry-after':'5','x-assay-phase':String(body.{state})}}",
            "archive_transfer_repair": f"{{'location':`/api/v10/archive-transfers/${{v.{key}}}`,'x-transfer-phase':String(body.{state})}}",
            "beacon_enrollment_repair": f"{{'location':`/api/v10/beacon-enrollments/${{v.{key}}}`,'retry-after':'4','x-enrollment-phase':String(body.{state})}}",
        }[task["id"]]
        if task["id"] == "archive_transfer_repair" and variant == "seed":
            mapping = mapping.replace("'x-transfer-phase'", "'x-transfer-state'", 1)
        status = 201 if task["id"] == "beacon_enrollment_repair" and variant == "seed" else task["success_status"]
        lines.append(f"const body=calculate(v);return response(body,{status},{mapping});")
    lines.append("};")
    return "".join(lines)


TS_SERVER = """import {serve} from '@hono/node-server';import {serveStatic} from '@hono/node-server/serve-static';import {Hono} from 'hono';import {z} from 'zod';import {calculate,type RequestInput} from './logic.js';
declare const process:{env:Record<string,string|undefined>};const maxBodyBytes=16_384;const schema=@@SCHEMA@@;
const response=(value:unknown,status=200,headers:Record<string,string>={})=>{if(Object.keys(headers).some(name=>['content-length','content-type','connection','transfer-encoding','x-content-type-options'].includes(name.toLowerCase())))return new Response(JSON.stringify({error:'invalid_response_headers',detail:'server-owned response header'}),{status:500,headers:{'content-type':'application/json'}});return new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json',...headers}})};const error=(code:string,status:number,detail:string)=>response({error:code,detail},status);@@DECIDE@@
const app=new Hono();app.get('@@STATUS@@',()=>response({service:'@@SERVICE@@',ready:true}));app.post('@@ROUTE@@',async context=>{const media=(context.req.header('content-type')??'').split(';',1)[0]!.trim().toLowerCase();if(media!=='application/json'&&!media.endsWith('+json'))return error('json_content_type_required',415,'expected application/json');const declared=context.req.header('content-length');if(declared&&(!/^\\d+$/.test(declared)||Number(declared)>maxBodyBytes))return error('body_too_large',413,'request body exceeds 16384 bytes');const raw=await context.req.arrayBuffer();if(raw.byteLength>maxBodyBytes)return error('body_too_large',413,'request body exceeds 16384 bytes');try{const parsed=schema.safeParse(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)));if(!parsed.success)return error('invalid_json',400,parsed.error.message);return decide(parsed.data,context.req.raw.headers)}catch(caught){return error('invalid_json',400,String(caught))}});app.all('/api/*',context=>error('not_found',404,`no API route ${context.req.path}`));app.get('/parley.js',serveStatic({path:process.env.FULLSTACK_046_BROWSER??'./dist/logic.js'}));app.get('/*',serveStatic({root:'./public'}));serve({fetch:app.fetch,hostname:'127.0.0.1',port:Number(process.env.PARLEY_WEB_PORT)});
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
    return f"const asI64=(v,n)=>{{if(typeof v==='bigint')return v;if(!Number.isSafeInteger(v))throw new TypeError(`${{n}} must be a safe whole number`);return BigInt(v)}};export async function loadParley(){{const r=await fetch(new URL('/fullstack_agent_046.wasm',import.meta.url));const m=(await WebAssembly.instantiateStreaming(r)).instance.exports;return {{{task['browser_export']}:({args})=>m.parley_browser_score({','.join(conversions)})}}}}"


def _rust_decisions(task: dict[str, Any], variant: str) -> str:
    key, state = _names(task)
    zero = _zero_mapping(task, language="rust", value=f"v.{key}", state="state")
    lines = [f"fn zero(v:&RequestInput,state:&str)->serde_json::Value{{json!({{{zero}}})}}", "fn decide(v:RequestInput,headers:&HeaderMap)->Response{"]
    auth = task.get("authorization")
    if auth:
        fail = "&[(\"%s\",\"%s\")]" % next(iter(auth["failure_headers"].items()))
        lines.append(f"if headers.get(\"{auth['header']}\").and_then(|x|x.to_str().ok()).unwrap_or(\"\")!=\"{auth['value']}\"{{return json_response(zero(&v,\"authorization_required\"),{auth['failure_status']},{fail})}}")
    numeric = [name for name, kind in task["request_fields"].items() if kind == "number"]
    lines.append(f"if [{','.join('v.' + name for name in numeric)}].iter().any(|x|*x<0){{return json_response(zero(&v,\"invalid\"),422,&[(\"x-validation\",\"nonnegative\")])}}")
    zero_field, positive = {
        "orbital_clearance_build": ("docking_arms", "v.pressurized_pods+v.vacuum_pods"),
        "estuary_assay_build": ("assay_benches", "v.inlet_vials+v.outlet_vials"),
        "archive_transfer_repair": ("catalog_carts", "v.folio_boxes+v.atlas_tubes"),
        "beacon_enrollment_repair": ("calibration_frames", "v.analog_transponders+v.digital_transponders"),
    }[task["id"]]
    lines.append(f"if v.{zero_field}==0&&{positive}>0{{return json_response(zero(&v,\"invalid\"),422,&[(\"x-validation\",\"{zero_field}\")])}}")
    if task["id"] == "estuary_assay_build":
        lines.append("if v.repeated_submission{return json_response(zero(&v,\"duplicate\"),409,&[(\"x-conflict\",\"repeated_submission\")])}")
    if task["kind"] == "implementation" and variant == "seed":
        lines.append("json_response(calculate(&v),200,&[])")
    else:
        mapping = {
            "orbital_clearance_build": f"vec![(\"location\",format!(\"/api/v10/orbital-clearances/{{}}\",v.{key})),(\"x-clearance-phase\",body.{state}.clone())]",
            "estuary_assay_build": f"vec![(\"location\",format!(\"/api/v10/estuary-assays/{{}}\",v.{key})),(\"retry-after\",\"5\".into()),(\"x-assay-phase\",body.{state}.clone())]",
            "archive_transfer_repair": f"vec![(\"location\",format!(\"/api/v10/archive-transfers/{{}}\",v.{key})),(\"x-transfer-phase\",body.{state}.clone())]",
            "beacon_enrollment_repair": f"vec![(\"location\",format!(\"/api/v10/beacon-enrollments/{{}}\",v.{key})),(\"retry-after\",\"4\".into()),(\"x-enrollment-phase\",body.{state}.clone())]",
        }[task["id"]]
        if task["id"] == "archive_transfer_repair" and variant == "seed":
            mapping = mapping.replace('(\"x-transfer-phase\"', '(\"x-transfer-state\"', 1)
        status = 201 if task["id"] == "beacon_enrollment_repair" and variant == "seed" else task["success_status"]
        lines.append(f"let body=calculate(&v);let owned={mapping};let refs:Vec<(&str,&str)>=owned.iter().map(|(a,b)|(*a,b.as_str())).collect();json_response(body,{status},&refs)")
    lines.append("}")
    return "".join(lines)


RUST_MAIN = """use std::env;use axum::{Router,body::{Body,to_bytes},extract::Request,http::{HeaderMap,StatusCode,header},response::{IntoResponse,Response},routing::{any,get,post}};use fullstack_agent_046::{RequestInput,calculate};use serde::Serialize;use serde_json::json;use tower_http::services::{ServeDir,ServeFile};const MAX_BODY_BYTES:usize=16_384;const BROWSER_MODULE:&str=r#"@@BROWSER@@"#;
fn json_response(value:impl Serialize,status:u16,headers:&[(&str,&str)])->Response{if headers.iter().any(|(n,_)|matches!(n.to_ascii_lowercase().as_str(),"content-length"|"content-type"|"connection"|"transfer-encoding"|"x-content-type-options")){return error("invalid_response_headers",500,"server-owned response header")}let status=StatusCode::from_u16(status).unwrap();let mut response=(status,serde_json::to_vec(&value).unwrap()).into_response();response.headers_mut().insert(header::CONTENT_TYPE,header::HeaderValue::from_static("application/json"));for(n,v)in headers{response.headers_mut().insert(header::HeaderName::from_bytes(n.as_bytes()).unwrap(),header::HeaderValue::from_str(v).unwrap());}response}fn error(code:&str,status:u16,detail:&str)->Response{let mut r=(StatusCode::from_u16(status).unwrap(),serde_json::to_vec(&json!({"error":code,"detail":detail})).unwrap()).into_response();r.headers_mut().insert(header::CONTENT_TYPE,header::HeaderValue::from_static("application/json"));r}@@DECIDE@@
async fn status()->Response{json_response(json!({"service":"@@SERVICE@@","ready":true}),200,&[])}async fn endpoint(request:Request)->Response{let headers=request.headers().clone();let media=headers.get(header::CONTENT_TYPE).and_then(|v|v.to_str().ok()).unwrap_or("").split(';').next().unwrap_or("").trim().to_ascii_lowercase();if media!="application/json"&&!media.ends_with("+json"){return error("json_content_type_required",415,"expected application/json")}if let Some(length)=headers.get(header::CONTENT_LENGTH){let declared=length.to_str().ok().and_then(|v|v.parse::<usize>().ok());if declared.is_none_or(|v|v>MAX_BODY_BYTES){return error("body_too_large",413,"request body exceeds 16384 bytes")}}let body=match to_bytes(request.into_body(),MAX_BODY_BYTES).await{Ok(body)=>body,Err(_)=>return error("body_too_large",413,"request body exceeds 16384 bytes")};match serde_json::from_slice::<RequestInput>(&body){Ok(v)=>decide(v,&headers),Err(reason)=>error("invalid_json",400,&reason.to_string())}}async fn missing(request:Request<Body>)->Response{error("not_found",404,&format!("no API route {}",request.uri().path()))}async fn browser()->Response{let mut r=BROWSER_MODULE.into_response();r.headers_mut().insert(header::CONTENT_TYPE,header::HeaderValue::from_static("text/javascript; charset=utf-8"));r}#[tokio::main]async fn main(){let wasm=env::var_os("FULLSTACK_046_WASM").map(std::path::PathBuf::from).unwrap();let app=Router::new().route("@@STATUS@@",get(status)).route("@@ROUTE@@",post(endpoint)).route("/api/{*rest}",any(missing)).route("/parley.js",get(browser)).route_service("/fullstack_agent_046.wasm",ServeFile::new(wasm)).fallback_service(ServeDir::new("public").append_index_html_on_directories(true));let port=env::var("PARLEY_WEB_PORT").unwrap().parse::<u16>().unwrap();let listener=tokio::net::TcpListener::bind(("127.0.0.1",port)).await.unwrap();axum::serve(listener,app).await.unwrap()}
"""


def _rust_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    main = RUST_MAIN.replace("@@BROWSER@@", _rust_browser(task)).replace("@@DECIDE@@", _rust_decisions(task, variant)).replace("@@STATUS@@", task["status_route"]).replace("@@SERVICE@@", task["service"]).replace("@@ROUTE@@", task["post_route"])
    return {
        "src/lib.rs": ScaffoldFile(_clean(rust_logic(task, variant)), True),
        "src/main.rs": ScaffoldFile(_clean(main), True),
        "Cargo.toml": ScaffoldFile((BENCHMARKS / "fullstack_046/rust/Cargo.toml").read_text(), False),
        "Cargo.lock": ScaffoldFile((BENCHMARKS / "fullstack_046/rust/Cargo.lock").read_text(), False),
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
