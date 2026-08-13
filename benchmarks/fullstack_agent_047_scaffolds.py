"""Generate frozen language workspaces for full-stack agent study 047."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import textwrap
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS_PATH = BENCHMARKS / "fullstack_agent_047_tasks.json"
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
    response = "\n".join(
        f"- `{name}`: {kind}" for name, kind in task["response_fields"].items()
    )
    return _clean(f"""
    # {task['title']}

    {task['statement']}

    ## HTTP

    - `GET {task['status_route']}` returns
      `{{"service":"{task['service']}","ready":true}}`.
    - `GET {task['exact_route']}` is exact and wins over the template.
    - `GET {task['parameter_route']}` receives one decoded path parameter.
    - Invalid path encoding or a decoded separator/control returns 400
      `invalid_path_parameter` before handler logic.

    Response fields:

    {response}

    ## Browser

    Export `{task['browser_export']}(sequence, mode)` and return the same score as
    a successful parameterized HTTP lookup.
    """)


PUBLIC_INDEX = _clean("""
<!doctype html>
<meta charset="utf-8">
<title>Full-stack agent study 047</title>
<main>Full-stack agent study 047 browser target</main>
""")


def _implementation_seed(task: dict[str, Any], variant: str) -> bool:
    return task["kind"] == "implementation" and variant == "seed"


def _score_expression(task: dict[str, Any], sequence: str, active: str, language: str) -> str:
    factor, boost = task["factor"], task["boost"]
    if language == "parley":
        return f"{sequence} times {factor} plus ({boost} if {active} else 0)"
    if language in {"python", "typescript"}:
        return f"{sequence}*{factor}+({boost} if {active} else 0)" if language == "python" else f"{sequence}*{factor}+({active}?{boost}:0)"
    return f"{sequence}*{factor}+if {active}{{{boost}}}else{{0}}"


def _parley_logic(task: dict[str, Any], variant: str) -> str:
    name = task["browser_export"]
    if _implementation_seed(task, variant):
        return _clean(f"""
        to {name} with sequence as number, mode as yesno giving number:
            give back 0
        """)
    return _clean(f"""
    to {name} with sequence as number, mode as yesno giving number:
        let result be sequence times {task['factor']}
        if mode:
            set result to result plus {task['boost']}
        give back result
    """)


def _parley_main(task: dict[str, Any], variant: str) -> str:
    capture_key = task["path_parameter"]
    capture_value = f'(maybe item "{capture_key}" of request\'s path_parameters) otherwise ""'
    if task["id"] == "aviary_band_lookup_repair" and variant == "seed":
        capture_value = '(maybe item "band_code" of request\'s path_parameters) otherwise ""'
    if task["id"] == "canal_gate_lookup_repair" and variant == "seed":
        capture_value = "request's path"
    response_fields = ", ".join(
        f"{name} as {'text' if kind == 'text' else 'number'}"
        for name, kind in task["response_fields"].items()
    )
    lines = [
        'include "logic.par"',
        "",
        "a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text",
        f"a response_body has {response_fields}",
        "a controlled_response has status as number, headers as map from text to text, body as response_body",
        "a service_status has service as text, ready as yesno",
        "",
        "to project_status giving service_status:",
        f'    give back a service_status with service "{task["service"]}", ready yes',
        "",
        "to empty_body with capture as text, state as text giving response_body:",
        f"    give back a response_body with {task['path_parameter']} capture, {task['sequence_field']} 0, {task['score_field']} 0, {task['state_field']} state",
        "",
        "to exact_item giving controlled_response:",
        "    let headers be a map from text to text",
        f'    set item "{task["state_header"]}" of headers to "{task["exact_segment"]}"',
        f"    let exact_body be a response_body with {task['path_parameter']} \"{task['exact_segment']}\", {task['sequence_field']} {task['exact_sequence']}, {task['score_field']} {task['exact_sequence'] * task['factor']}, {task['state_field']} \"{task['exact_segment']}\"",
        "    give back a controlled_response with status 200, headers headers, body exact_body",
        "",
        "to lookup_item with request as web_request giving controlled_response:",
        f"    let capture be {capture_value}",
        "    let headers be a map from text to text",
    ]
    if auth := task.get("authorization"):
        header_name, header_value = next(iter(auth["failure_headers"].items()))
        lines.extend([
            f'    let credential be (maybe item "{auth["header"]}" of request\'s headers) otherwise ""',
            f'    if credential is not "{auth["value"]}":',
            f'        set item "{header_name}" of headers to "{header_value}"',
            f'        give back a controlled_response with status {auth["failure_status"]}, headers headers, body (empty_body with capture, "authorization_required")',
        ])
    lines.extend([
        "    let sequence be (number from capture) otherwise 0",
        "    if sequence is at most 0:",
        f'        set item "x-validation" of headers to "{task["path_parameter"]}"',
        '        give back a controlled_response with status 422, headers headers, body (empty_body with capture, "invalid")',
        f'    let mode_value be (maybe item "{task["mode_header"]}" of request\'s headers) otherwise ""',
        "    let mode be no",
        f'    if mode_value is "{task["mode_value"]}":',
        "        set mode to yes",
        f"    let result be a response_body with {task['path_parameter']} capture, {task['sequence_field']} sequence, {task['score_field']} ({task['browser_export']} with sequence, mode), {task['state_field']} \"{task['success_state']}\"",
        f'    set item "{task["state_header"]}" of headers to "{task["success_state"]}"',
        "    give back a controlled_response with status 200, headers headers, body result",
    ])
    return "\n".join(lines) + "\n"


def _parley_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    response = {
        "status_field": "status", "headers_field": "headers", "body_field": "body"
    }
    manifest = {
        "schema_version": 1,
        "name": task["id"],
        "entrypoint": "main.par",
        "static_dir": "public",
        "routes": [
            {
                "method": "GET", "path": task["parameter_route"],
                "handler": "lookup_item", "response": response,
            },
            {
                "method": "GET", "path": task["exact_route"],
                "handler": "exact_item", "response": response,
            },
            {"method": "GET", "path": task["status_route"], "handler": "project_status"},
        ],
        "browser": {
            "entrypoint": "logic.par", "exports": [{"name": task["browser_export"]}]
        },
        "server": {"host": "127.0.0.1", "port": 8787, "max_body_bytes": 16384},
    }
    return {
        "logic.par": ScaffoldFile(_parley_logic(task, variant), True),
        "main.par": ScaffoldFile(_parley_main(task, variant), True),
        "parley.web.json": ScaffoldFile(
            json.dumps(manifest, separators=(",", ":")) + "\n", True
        ),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _python_logic(task: dict[str, Any], variant: str) -> str:
    calculation = "return 0" if _implementation_seed(task, variant) else (
        f"return sequence*{task['factor']}+({task['boost']} if mode else 0)"
    )
    return _clean(f"""
    def score(sequence: int, mode: bool) -> int:
        {calculation}
    """)


PYTHON_APP = r'''from __future__ import annotations
import os
from pathlib import Path
from urllib.parse import unquote_to_bytes
from fastapi import FastAPI,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from logic import score
PUBLIC=Path(__file__).with_name('public');PREFIX='@@PREFIX@@';EXACT='@@EXACT@@';PARAM='@@PARAM@@'
def error(code:str,status:int,detail:str)->JSONResponse:return JSONResponse({'error':code,'detail':detail},status_code=status)
def response(body:dict[str,object],status:int=200,headers:dict[str,str]|None=None)->JSONResponse:return JSONResponse(body,status_code=status,headers=headers or {})
def raw_capture(request:Request)->str:
    raw=request.scope.get('raw_path',b'').split(b'?',1)[0]; prefix=PREFIX.encode()
    if not raw.startswith(prefix):raise ValueError('path prefix')
    segment=raw[len(prefix):]
    if not segment or b'/' in segment:raise ValueError('separator')
    index=0
    while index<len(segment):
        if segment[index]==37:
            if index+2>=len(segment) or any(chr(v) not in '0123456789abcdefABCDEF' for v in segment[index+1:index+3]):raise ValueError('escape')
            index+=3
        else:index+=1
    value=unquote_to_bytes(segment).decode('utf-8','strict')
    if any(ord(ch)<32 or ord(ch)==127 or ch in '/\\' for ch in value):raise ValueError('unsafe')
    return value
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
@app.middleware('http')
async def path_guard(request:Request,call_next):
    raw=request.scope.get('raw_path',b'').split(b'?',1)[0]
    if raw.startswith(PREFIX.encode()) and raw!=EXACT.encode():
        try:request.state.capture=raw_capture(request)
        except (ValueError,UnicodeDecodeError):return error('invalid_path_parameter',400,'invalid path parameter')
    return await call_next(request)
@app.get('@@STATUS@@')
async def status():return {'service':'@@SERVICE@@','ready':True}
@app.get('@@EXACT@@')
async def exact():return response(@@EXACT_BODY@@,200,{'@@STATE_HEADER@@':'@@EXACT_SEGMENT@@'})
def empty(capture:str,state:str)->dict[str,object]:return {@@EMPTY_BODY@@}
def decide(params:dict[str,str],request:Request)->JSONResponse:
    capture=@@CAPTURE@@; headers:dict[str,str]={}
@@AUTH@@
    try:sequence=int(capture) if capture.isascii() and capture.isdecimal() else 0
    except ValueError:sequence=0
    if sequence<=0:return response(empty(capture,'invalid'),422,{'x-validation':'@@PARAM@@'})
    mode=request.headers.get('@@MODE_HEADER@@','')=='@@MODE_VALUE@@'
    return response({@@SUCCESS_BODY@@},200,{'@@STATE_HEADER@@':'@@SUCCESS_STATE@@'})
@app.get('@@DYNAMIC@@')
async def dynamic(request:Request,_capture:str):
    capture=request.state.capture; params={PARAM:capture}; return decide(params,request)
@app.get('/parley.js')
async def browser():return FileResponse(Path(__file__).with_name('browser.js'),media_type='text/javascript')
app.mount('/',StaticFiles(directory=PUBLIC,html=True),name='public')
if __name__=='__main__':
 import uvicorn;uvicorn.run(app,host='127.0.0.1',port=int(os.environ['PARLEY_WEB_PORT']),log_level='warning')
'''


def _python_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    capture = f"params.get('{task['path_parameter']}','')"
    if task["id"] == "aviary_band_lookup_repair" and variant == "seed":
        capture = "params.get('band_code','')"
    if task["id"] == "canal_gate_lookup_repair" and variant == "seed":
        capture = "request.url.path"
    auth = ""
    if spec := task.get("authorization"):
        header, value = next(iter(spec["failure_headers"].items()))
        auth = (
            f"    if request.headers.get('{spec['header']}','')!={spec['value']!r}:"
            f"return response(empty(capture,'authorization_required'),{spec['failure_status']},"
            f"{{'{header}':{value!r}}})"
        )
    exact_body = {
        task["path_parameter"]: task["exact_segment"],
        task["sequence_field"]: task["exact_sequence"],
        task["score_field"]: task["exact_sequence"] * task["factor"],
        task["state_field"]: task["exact_segment"],
    }
    empty = (
        f"'{task['path_parameter']}':capture,'{task['sequence_field']}':0,"
        f"'{task['score_field']}':0,'{task['state_field']}':state"
    )
    success = (
        f"'{task['path_parameter']}':capture,'{task['sequence_field']}':sequence,"
        f"'{task['score_field']}':score(sequence,mode),"
        f"'{task['state_field']}':'{task['success_state']}'"
    )
    prefix = task["parameter_route"].split("{")[0]
    app = PYTHON_APP
    replacements = {
        "@@PREFIX@@": prefix, "@@EXACT@@": task["exact_route"],
        "@@PARAM@@": task["path_parameter"], "@@STATUS@@": task["status_route"],
        "@@SERVICE@@": task["service"], "@@EXACT_BODY@@": repr(exact_body),
        "@@STATE_HEADER@@": task["state_header"],
        "@@EXACT_SEGMENT@@": task["exact_segment"], "@@EMPTY_BODY@@": empty,
        "@@CAPTURE@@": capture, "@@AUTH@@": auth,
        "@@MODE_HEADER@@": task["mode_header"], "@@MODE_VALUE@@": task["mode_value"],
        "@@SUCCESS_BODY@@": success, "@@SUCCESS_STATE@@": task["success_state"],
        "@@DYNAMIC@@": prefix + "{_capture}",
    }
    for old, new in replacements.items():
        app = app.replace(old, new)
    browser_score = "0" if _implementation_seed(task, variant) else (
        f"sequence*{task['factor']}+(mode?{task['boost']}:0)"
    )
    browser = (
        f"const score=(sequence,mode)=>{browser_score};\n"
        f"export async function loadParley(){{return {{{task['browser_export']}:score}}}}\n"
    )
    return {
        "logic.py": ScaffoldFile(_python_logic(task, variant), True),
        "browser.js": ScaffoldFile(browser, True),
        "app.py": ScaffoldFile(_clean(app), True),
        "requirements.txt": ScaffoldFile(
            (BENCHMARKS / "fullstack_035/python/requirements.txt").read_text(), False
        ),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


TS_SERVER = r'''import {serve} from '@hono/node-server';import {serveStatic} from '@hono/node-server/serve-static';import {Hono} from 'hono';import {score} from './logic.js';
declare const process:{env:Record<string,string|undefined>};const prefix='@@PREFIX@@',exactPath='@@EXACT@@',param='@@PARAM@@';
const response=(body:unknown,status=200,headers:Record<string,string>={})=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json',...headers}});const error=(code:string,status:number)=>response({error:code,detail:'invalid path parameter'},status);
const decodeCapture=(url:string)=>{const path=new URL(url).pathname;if(!path.startsWith(prefix))throw Error('prefix');const raw=path.slice(prefix.length);if(!raw||raw.includes('/'))throw Error('separator');for(let i=0;i<raw.length;i++)if(raw[i]==='%'){if(i+2>=raw.length||!/^[0-9a-f]{2}$/i.test(raw.slice(i+1,i+3)))throw Error('escape');i+=2}const value=decodeURIComponent(raw);if([...value].some(ch=>{const n=ch.charCodeAt(0);return n<32||n===127||ch==='/'||ch==='\\'}))throw Error('unsafe');return value};
const empty=(capture:string,state:string)=>({@@EMPTY_BODY@@});const decide=(params:Record<string,string>,headers:Headers,rawPath:string)=>{const capture=@@CAPTURE@@;@@AUTH@@const sequence=/^[0-9]+$/.test(capture)?Number(capture):0;if(!Number.isSafeInteger(sequence)||sequence<=0)return response(empty(capture,'invalid'),422,{'x-validation':param});const mode=(headers.get('@@MODE_HEADER@@')??'')==='@@MODE_VALUE@@';return response({@@SUCCESS_BODY@@},200,{'@@STATE_HEADER@@':'@@SUCCESS_STATE@@'})};
const app=new Hono();app.get('@@STATUS@@',()=>response({service:'@@SERVICE@@',ready:true}));app.get(exactPath,()=>response(@@EXACT_BODY@@,200,{'@@STATE_HEADER@@':'@@EXACT_SEGMENT@@'}));app.get('@@DYNAMIC@@',context=>{try{const capture=decodeCapture(context.req.url);return decide({[param]:capture},context.req.raw.headers,new URL(context.req.url).pathname)}catch{return error('invalid_path_parameter',400)}});app.get('/parley.js',serveStatic({path:process.env.FULLSTACK_047_BROWSER??'./dist/logic.js'}));app.get('/*',serveStatic({root:'./public'}));serve({fetch:app.fetch,hostname:'127.0.0.1',port:Number(process.env.PARLEY_WEB_PORT)});
'''


def _typescript_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    score_body = "0" if _implementation_seed(task, variant) else (
        f"sequence*{task['factor']}+(mode?{task['boost']}:0)"
    )
    logic = _clean(f"""
    export const score=(sequence:number,mode:boolean)=>{score_body};
    export async function loadParley(){{return {{{task['browser_export']}:(sequence:number,mode:boolean)=>BigInt(score(sequence,mode))}}}}
    """)
    capture = f"params['{task['path_parameter']}']??''"
    if task["id"] == "aviary_band_lookup_repair" and variant == "seed":
        capture = "params['band_code']??''"
    if task["id"] == "canal_gate_lookup_repair" and variant == "seed":
        capture = "rawPath"
    auth = ""
    if spec := task.get("authorization"):
        header, value = next(iter(spec["failure_headers"].items()))
        auth = (
            f"if((headers.get('{spec['header']}')??'')!=={json.dumps(spec['value'])})"
            f"return response(empty(capture,'authorization_required'),{spec['failure_status']},"
            f"{{'{header}':{json.dumps(value)}}});"
        )
    exact_body = json.dumps({
        task["path_parameter"]: task["exact_segment"],
        task["sequence_field"]: task["exact_sequence"],
        task["score_field"]: task["exact_sequence"] * task["factor"],
        task["state_field"]: task["exact_segment"],
    }, separators=(",", ":"))
    replacements = {
        "@@PREFIX@@": task["parameter_route"].split("{")[0],
        "@@EXACT@@": task["exact_route"], "@@PARAM@@": task["path_parameter"],
        "@@EMPTY_BODY@@": (
            f"{task['path_parameter']}:capture,{task['sequence_field']}:0,"
            f"{task['score_field']}:0,{task['state_field']}:state"
        ),
        "@@CAPTURE@@": capture, "@@AUTH@@": auth,
        "@@MODE_HEADER@@": task["mode_header"], "@@MODE_VALUE@@": task["mode_value"],
        "@@SUCCESS_BODY@@": (
            f"{task['path_parameter']}:capture,{task['sequence_field']}:sequence,"
            f"{task['score_field']}:score(sequence,mode),"
            f"{task['state_field']}:'{task['success_state']}'"
        ),
        "@@STATE_HEADER@@": task["state_header"],
        "@@SUCCESS_STATE@@": task["success_state"], "@@STATUS@@": task["status_route"],
        "@@SERVICE@@": task["service"], "@@EXACT_BODY@@": exact_body,
        "@@EXACT_SEGMENT@@": task["exact_segment"],
        "@@DYNAMIC@@": task["parameter_route"].replace("{" + task["path_parameter"] + "}", ":_capture"),
    }
    server = TS_SERVER
    for old, new in replacements.items():
        server = server.replace(old, new)
    return {
        "src/logic.ts": ScaffoldFile(logic, True),
        "src/server.ts": ScaffoldFile(_clean(server), True),
        "package.json": ScaffoldFile(
            (BENCHMARKS / "fullstack_035/typescript/package.json").read_text(), False
        ),
        "package-lock.json": ScaffoldFile(
            (BENCHMARKS / "fullstack_035/typescript/package-lock.json").read_text(), False
        ),
        "tsconfig.json": ScaffoldFile(
            (BENCHMARKS / "fullstack_035/typescript/tsconfig.json").read_text(), False
        ),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _rust_lib(task: dict[str, Any], variant: str) -> str:
    body = "0" if _implementation_seed(task, variant) else _score_expression(
        task, "sequence", "mode", "rust"
    )
    return _clean(f"""
    pub fn score(sequence:i64,mode:bool)->i64{{{body}}}
    #[unsafe(no_mangle)]pub extern "C" fn parley_browser_score(sequence:i64,mode:i32)->i64{{score(sequence,mode!=0)}}
    """)


RUST_MAIN = r'''use std::env;use axum::{Router,extract::OriginalUri,http::{HeaderMap,StatusCode,header},response::{IntoResponse,Response},routing::get};use fullstack_agent_047::score;use serde::Serialize;use serde_json::json;use tower_http::services::{ServeDir,ServeFile};const PREFIX:&str="@@PREFIX@@";const EXACT:&str="@@EXACT@@";const PARAM:&str="@@PARAM@@";const BROWSER:&str=r#"@@BROWSER@@"#;
fn response(value:impl Serialize,status:u16,headers:&[(&str,&str)])->Response{let mut r=(StatusCode::from_u16(status).unwrap(),serde_json::to_vec(&value).unwrap()).into_response();r.headers_mut().insert(header::CONTENT_TYPE,header::HeaderValue::from_static("application/json"));for(n,v)in headers{r.headers_mut().insert(header::HeaderName::from_bytes(n.as_bytes()).unwrap(),header::HeaderValue::from_str(v).unwrap());}r}fn error()->Response{response(json!({"error":"invalid_path_parameter","detail":"invalid path parameter"}),400,&[])}
fn decode_capture(raw:&str)->Result<String,()>{if raw.is_empty()||raw.as_bytes().contains(&b'/'){return Err(())}let bytes=raw.as_bytes();let mut out=Vec::new();let mut i=0;while i<bytes.len(){if bytes[i]==b'%'{if i+2>=bytes.len(){return Err(())}let hex=|v:u8|match v{b'0'..=b'9'=>Some(v-b'0'),b'a'..=b'f'=>Some(v-b'a'+10),b'A'..=b'F'=>Some(v-b'A'+10),_=>None};let(a,b)=(hex(bytes[i+1]).ok_or(())?,hex(bytes[i+2]).ok_or(())?);out.push(a*16+b);i+=3}else{out.push(bytes[i]);i+=1}}let value=String::from_utf8(out).map_err(|_|())?;if value.chars().any(|ch|ch<' '||ch=='\u{7f}'||ch=='/'||ch=='\\'){return Err(())}Ok(value)}
fn empty(capture:&str,state:&str)->serde_json::Value{json!({@@EMPTY_BODY@@})}fn decide(params:&serde_json::Value,headers:&HeaderMap,raw_path:&str)->Response{let capture=@@CAPTURE@@;@@AUTH@@let sequence=if capture.bytes().all(|v|v.is_ascii_digit()){capture.parse::<i64>().unwrap_or(0)}else{0};if sequence<=0{return response(empty(&capture,"invalid"),422,&[("x-validation",PARAM)])}let mode=headers.get("@@MODE_HEADER@@").and_then(|v|v.to_str().ok()).unwrap_or("")=="@@MODE_VALUE@@";response(json!({@@SUCCESS_BODY@@}),200,&[("@@STATE_HEADER@@","@@SUCCESS_STATE@@")])}
async fn status()->Response{response(json!({"service":"@@SERVICE@@","ready":true}),200,&[])}async fn endpoint(OriginalUri(uri):OriginalUri,headers:HeaderMap)->Response{let raw=uri.path();if raw==EXACT{return response(json!(@@EXACT_BODY@@),200,&[("@@STATE_HEADER@@","@@EXACT_SEGMENT@@")])}let Some(segment)=raw.strip_prefix(PREFIX)else{return response(json!({"error":"not_found","detail":"no route"}),404,&[])};let capture=match decode_capture(segment){Ok(v)=>v,Err(_)=>return error()};let params=json!({PARAM:capture});decide(&params,&headers,raw)}async fn browser()->Response{let mut r=BROWSER.into_response();r.headers_mut().insert(header::CONTENT_TYPE,header::HeaderValue::from_static("text/javascript; charset=utf-8"));r}
#[tokio::main]async fn main(){let wasm=env::var_os("FULLSTACK_047_WASM").map(std::path::PathBuf::from).unwrap();let app=Router::new().route("@@STATUS@@",get(status)).route("@@WILDCARD@@",get(endpoint)).route("/parley.js",get(browser)).route_service("/fullstack_agent_047.wasm",ServeFile::new(wasm)).fallback_service(ServeDir::new("public").append_index_html_on_directories(true));let port=env::var("PARLEY_WEB_PORT").unwrap().parse::<u16>().unwrap();let listener=tokio::net::TcpListener::bind(("127.0.0.1",port)).await.unwrap();axum::serve(listener,app).await.unwrap()}
'''


def _rust_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    capture = f"params.get(PARAM).and_then(|v|v.as_str()).unwrap_or(\"\").to_string()"
    if task["id"] == "aviary_band_lookup_repair" and variant == "seed":
        capture = "params.get(\"band_code\").and_then(|v|v.as_str()).unwrap_or(\"\").to_string()"
    if task["id"] == "canal_gate_lookup_repair" and variant == "seed":
        capture = "raw_path.to_string()"
    auth = ""
    if spec := task.get("authorization"):
        header_name, header_value = next(iter(spec["failure_headers"].items()))
        auth = (
            f"if headers.get(\"{spec['header']}\").and_then(|v|v.to_str().ok()).unwrap_or(\"\")"
            f"!=\"{spec['value']}\"{{return response(empty(&capture,\"authorization_required\"),"
            f"{spec['failure_status']},&[(\"{header_name}\",\"{header_value}\")])}}"
        )
    exact_body = json.dumps({
        task["path_parameter"]: task["exact_segment"],
        task["sequence_field"]: task["exact_sequence"],
        task["score_field"]: task["exact_sequence"] * task["factor"],
        task["state_field"]: task["exact_segment"],
    }, separators=(",", ":"))
    browser = (
        "const asI64=(v,n)=>{if(typeof v==='bigint')return v;if(!Number.isSafeInteger(v))"
        "throw new TypeError(`${n} must be a safe whole number`);return BigInt(v)};"
        "export async function loadParley(){const r=await fetch(new URL('/fullstack_agent_047.wasm',import.meta.url));"
        f"const m=(await WebAssembly.instantiateStreaming(r)).instance.exports;return {{{task['browser_export']}:(sequence,mode)=>m.parley_browser_score(asI64(sequence,'sequence'),mode?1:0)}}}}"
    )
    replacements = {
        "@@PREFIX@@": task["parameter_route"].split("{")[0],
        "@@EXACT@@": task["exact_route"], "@@PARAM@@": task["path_parameter"],
        "@@BROWSER@@": browser,
        "@@EMPTY_BODY@@": (
            f"\"{task['path_parameter']}\":capture,\"{task['sequence_field']}\":0,"
            f"\"{task['score_field']}\":0,\"{task['state_field']}\":state"
        ),
        "@@CAPTURE@@": capture, "@@AUTH@@": auth,
        "@@MODE_HEADER@@": task["mode_header"], "@@MODE_VALUE@@": task["mode_value"],
        "@@SUCCESS_BODY@@": (
            f"\"{task['path_parameter']}\":capture,\"{task['sequence_field']}\":sequence,"
            f"\"{task['score_field']}\":score(sequence,mode),"
            f"\"{task['state_field']}\":\"{task['success_state']}\""
        ),
        "@@STATE_HEADER@@": task["state_header"],
        "@@SUCCESS_STATE@@": task["success_state"], "@@SERVICE@@": task["service"],
        "@@EXACT_BODY@@": exact_body, "@@EXACT_SEGMENT@@": task["exact_segment"],
        "@@STATUS@@": task["status_route"],
        "@@WILDCARD@@": task["parameter_route"].split("{")[0] + "{*rest}",
    }
    main = RUST_MAIN
    for old, new in replacements.items():
        main = main.replace(old, new)
    return {
        "src/lib.rs": ScaffoldFile(_rust_lib(task, variant), True),
        "src/main.rs": ScaffoldFile(_clean(main), True),
        "Cargo.toml": ScaffoldFile(
            (BENCHMARKS / "fullstack_047/rust/Cargo.toml").read_text(), False
        ),
        "Cargo.lock": ScaffoldFile(
            (BENCHMARKS / "fullstack_047/rust/Cargo.lock").read_text(), False
        ),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def scaffold_files(
    task: dict[str, Any], language: str, variant: str = "seed"
) -> dict[str, ScaffoldFile]:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    if variant not in {"seed", "reference"}:
        raise ValueError(f"unsupported scaffold variant: {variant}")
    factory = {
        "parley": _parley_files,
        "python": _python_files,
        "typescript": _typescript_files,
        "rust": _rust_files,
    }[language]
    files = factory(task, variant)
    files["CONTRACT.md"] = ScaffoldFile(_contract(task), False)
    return files


ROOT_FILES: dict[str, tuple[str, ...]] = {
    "parley": ("main.par",),
    "python": ("app.py",),
    "typescript": ("src/server.ts",),
    "rust": ("src/main.rs",),
}
