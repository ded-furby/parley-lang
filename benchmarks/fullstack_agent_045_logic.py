"""Frozen task logic generators for full-stack agent study 045."""

from __future__ import annotations

from typing import Any


def _implementation_seed(task: dict[str, Any], variant: str) -> bool:
    return task["kind"] == "implementation" and variant == "seed"


PYTHON_CALCULATIONS = {
    "artifact_accession_build": """
def score(stable_units:int,fragile_units:int,packing_stations:int,expedited:bool)->int:
    packing=stable_units*6+fragile_units*11+(packing_stations*4 if expedited else 0)
    overflow=max(packing-packing_stations*40,0)
    return packing+overflow*5+((stable_units+fragile_units)//5)*7
def calculate(v:RequestInput)->dict[str,object]:
    total=v.stable_units+v.fragile_units; packing=v.stable_units*6+v.fragile_units*11+(v.packing_stations*4 if v.expedited else 0); capacity=v.packing_stations*40; overflow=max(packing-capacity,0)
    return {'accession_key':v.accession_key,'artifact_total':total,'packing_units':packing,'capacity_units':capacity,'overflow_units':overflow,'inspection_rounds':total//5,'priority_score':score(v.stable_units,v.fragile_units,v.packing_stations,v.expedited),'accession_state':'accepted' if overflow==0 else 'queued'}
""",
    "microgrid_bid_build": """
def score(solar_arrays:int,wind_turbines:int,storage_banks:int,interconnects:int,emergency_mode:bool)->int:
    generation=solar_arrays*9+wind_turbines*13; required=generation+storage_banks*(7 if emergency_mode else 3); capacity=interconnects*55
    return min(required,capacity)+max(required-capacity,0)*4+(required//31)*9
def calculate(v:RequestInput)->dict[str,object]:
    generation=v.solar_arrays*9+v.wind_turbines*13; buffer=v.storage_banks*(7 if v.emergency_mode else 3); required=generation+buffer; capacity=v.interconnects*55; shortfall=max(required-capacity,0)
    return {'bid_key':v.bid_key,'generation_units':generation,'battery_buffer_units':buffer,'grid_required_units':required,'grid_capacity_units':capacity,'delivered_units':min(required,capacity),'shortfall_units':shortfall,'dispatch_windows':required//31,'bid_score':score(v.solar_arrays,v.wind_turbines,v.storage_banks,v.interconnects,v.emergency_mode),'bid_state':'accepted' if shortfall==0 else 'emergency_shortfall' if v.emergency_mode else 'routine_shortfall'}
""",
    "trail_permit_repair": """
def score(day_hikers:int,overnight_hikers:int,trail_guides:int,storm_alert:bool)->int:
    required=day_hikers*5+overnight_hikers*12+(trail_guides*6 if storm_alert else 0); capacity=trail_guides*38
    return min(required,capacity)+max(required-capacity,0)*6
def calculate(v:RequestInput)->dict[str,object]:
    total=v.day_hikers+v.overnight_hikers; required=v.day_hikers*5+v.overnight_hikers*12+(v.trail_guides*6 if v.storm_alert else 0); capacity=v.trail_guides*38; waiting=max(required-capacity,0)
    return {'permit_code':v.permit_code,'visitor_total':total,'trail_units':required,'guide_capacity_units':capacity,'admitted_units':min(required,capacity),'waiting_units':waiting,'permit_score':score(v.day_hikers,v.overnight_hikers,v.trail_guides,v.storm_alert),'permit_state':'issued' if waiting==0 else 'storm_queue' if v.storm_alert else 'routine_queue'}
""",
    "cold_chain_booking_repair": """
def score(chilled_crates:int,frozen_crates:int,loading_docks:int,rush_load:bool)->int:
    total=chilled_crates+frozen_crates; required=chilled_crates*7+frozen_crates*15+(loading_docks*5 if rush_load else 0); capacity=loading_docks*44
    return min(required,capacity)+max(required-capacity,0)*5+(total//6)*8
def calculate(v:RequestInput)->dict[str,object]:
    total=v.chilled_crates+v.frozen_crates; required=v.chilled_crates*7+v.frozen_crates*15+(v.loading_docks*5 if v.rush_load else 0); capacity=v.loading_docks*44; deferred=max(required-capacity,0)
    return {'booking_code':v.booking_code,'shipment_total':total,'cooling_units':required,'dock_capacity_units':capacity,'loaded_units':min(required,capacity),'deferred_units':deferred,'loading_rounds':total//6,'booking_score':score(v.chilled_crates,v.frozen_crates,v.loading_docks,v.rush_load),'booking_state':'booked' if deferred==0 else 'rush_queue' if v.rush_load else 'routine_queue'}
""",
}


JS_SCORES = {
    "artifact_accession_build": "const score=(s,f,p,e)=>{const x=s*6+f*11+(e?p*4:0),o=Math.max(x-p*40,0);return x+o*5+Math.trunc((s+f)/5)*7};",
    "microgrid_bid_build": "const score=(s,w,b,i,e)=>{const r=s*9+w*13+b*(e?7:3),c=i*55;return Math.min(r,c)+Math.max(r-c,0)*4+Math.trunc(r/31)*9};",
    "trail_permit_repair": "const score=(d,o,g,s)=>{const r=d*5+o*12+(s?g*6:0),c=g*38;return Math.min(r,c)+Math.max(r-c,0)*6};",
    "cold_chain_booking_repair": "const score=(c,f,d,r)=>{const t=c+f,x=c*7+f*15+(r?d*5:0),k=d*44;return Math.min(x,k)+Math.max(x-k,0)*5+Math.trunc(t/6)*8};",
}


TS_CALCULATIONS = {
    "artifact_accession_build": "export const score=(s:number,f:number,p:number,e:boolean)=>{const x=s*6+f*11+(e?p*4:0),o=Math.max(x-p*40,0);return x+o*5+Math.trunc((s+f)/5)*7};export const calculate=(v:RequestInput)=>{const t=v.stable_units+v.fragile_units,x=v.stable_units*6+v.fragile_units*11+(v.expedited?v.packing_stations*4:0),c=v.packing_stations*40,o=Math.max(x-c,0);return {accession_key:v.accession_key,artifact_total:t,packing_units:x,capacity_units:c,overflow_units:o,inspection_rounds:Math.trunc(t/5),priority_score:score(v.stable_units,v.fragile_units,v.packing_stations,v.expedited),accession_state:o===0?'accepted':'queued'}};",
    "microgrid_bid_build": "export const score=(s:number,w:number,b:number,i:number,e:boolean)=>{const r=s*9+w*13+b*(e?7:3),c=i*55;return Math.min(r,c)+Math.max(r-c,0)*4+Math.trunc(r/31)*9};export const calculate=(v:RequestInput)=>{const g=v.solar_arrays*9+v.wind_turbines*13,b=v.storage_banks*(v.emergency_mode?7:3),r=g+b,c=v.interconnects*55,s=Math.max(r-c,0);return {bid_key:v.bid_key,generation_units:g,battery_buffer_units:b,grid_required_units:r,grid_capacity_units:c,delivered_units:Math.min(r,c),shortfall_units:s,dispatch_windows:Math.trunc(r/31),bid_score:score(v.solar_arrays,v.wind_turbines,v.storage_banks,v.interconnects,v.emergency_mode),bid_state:s===0?'accepted':v.emergency_mode?'emergency_shortfall':'routine_shortfall'}};",
    "trail_permit_repair": "export const score=(d:number,o:number,g:number,s:boolean)=>{const r=d*5+o*12+(s?g*6:0),c=g*38;return Math.min(r,c)+Math.max(r-c,0)*6};export const calculate=(v:RequestInput)=>{const t=v.day_hikers+v.overnight_hikers,r=v.day_hikers*5+v.overnight_hikers*12+(v.storm_alert?v.trail_guides*6:0),c=v.trail_guides*38,w=Math.max(r-c,0);return {permit_code:v.permit_code,visitor_total:t,trail_units:r,guide_capacity_units:c,admitted_units:Math.min(r,c),waiting_units:w,permit_score:score(v.day_hikers,v.overnight_hikers,v.trail_guides,v.storm_alert),permit_state:w===0?'issued':v.storm_alert?'storm_queue':'routine_queue'}};",
    "cold_chain_booking_repair": "export const score=(a:number,b:number,d:number,r:boolean)=>{const t=a+b,x=a*7+b*15+(r?d*5:0),c=d*44;return Math.min(x,c)+Math.max(x-c,0)*5+Math.trunc(t/6)*8};export const calculate=(v:RequestInput)=>{const t=v.chilled_crates+v.frozen_crates,x=v.chilled_crates*7+v.frozen_crates*15+(v.rush_load?v.loading_docks*5:0),c=v.loading_docks*44,d=Math.max(x-c,0);return {booking_code:v.booking_code,shipment_total:t,cooling_units:x,dock_capacity_units:c,loaded_units:Math.min(x,c),deferred_units:d,loading_rounds:Math.trunc(t/6),booking_score:score(v.chilled_crates,v.frozen_crates,v.loading_docks,v.rush_load),booking_state:d===0?'booked':v.rush_load?'rush_queue':'routine_queue'}};",
}


RUST_CALCULATIONS = {
    "artifact_accession_build": "pub fn score(s:i64,f:i64,p:i64,e:bool)->i64{let x=s*6+f*11+if e{p*4}else{0};x+(x-p*40).max(0)*5+((s+f)/5)*7}pub fn calculate(v:&RequestInput)->ResponseOutput{let t=v.stable_units+v.fragile_units;let x=v.stable_units*6+v.fragile_units*11+if v.expedited{v.packing_stations*4}else{0};let c=v.packing_stations*40;let o=(x-c).max(0);ResponseOutput{accession_key:v.accession_key.clone(),artifact_total:t,packing_units:x,capacity_units:c,overflow_units:o,inspection_rounds:t/5,priority_score:score(v.stable_units,v.fragile_units,v.packing_stations,v.expedited),accession_state:if o==0{\"accepted\"}else{\"queued\"}.into()}}",
    "microgrid_bid_build": "pub fn score(s:i64,w:i64,b:i64,i:i64,e:bool)->i64{let r=s*9+w*13+b*if e{7}else{3};let c=i*55;r.min(c)+(r-c).max(0)*4+(r/31)*9}pub fn calculate(v:&RequestInput)->ResponseOutput{let g=v.solar_arrays*9+v.wind_turbines*13;let b=v.storage_banks*if v.emergency_mode{7}else{3};let r=g+b;let c=v.interconnects*55;let s=(r-c).max(0);ResponseOutput{bid_key:v.bid_key.clone(),generation_units:g,battery_buffer_units:b,grid_required_units:r,grid_capacity_units:c,delivered_units:r.min(c),shortfall_units:s,dispatch_windows:r/31,bid_score:score(v.solar_arrays,v.wind_turbines,v.storage_banks,v.interconnects,v.emergency_mode),bid_state:if s==0{\"accepted\"}else if v.emergency_mode{\"emergency_shortfall\"}else{\"routine_shortfall\"}.into()}}",
    "trail_permit_repair": "pub fn score(d:i64,o:i64,g:i64,s:bool)->i64{let r=d*5+o*12+if s{g*6}else{0};let c=g*38;r.min(c)+(r-c).max(0)*6}pub fn calculate(v:&RequestInput)->ResponseOutput{let t=v.day_hikers+v.overnight_hikers;let r=v.day_hikers*5+v.overnight_hikers*12+if v.storm_alert{v.trail_guides*6}else{0};let c=v.trail_guides*38;let w=(r-c).max(0);ResponseOutput{permit_code:v.permit_code.clone(),visitor_total:t,trail_units:r,guide_capacity_units:c,admitted_units:r.min(c),waiting_units:w,permit_score:score(v.day_hikers,v.overnight_hikers,v.trail_guides,v.storm_alert),permit_state:if w==0{\"issued\"}else if v.storm_alert{\"storm_queue\"}else{\"routine_queue\"}.into()}}",
    "cold_chain_booking_repair": "pub fn score(a:i64,b:i64,d:i64,r:bool)->i64{let t=a+b;let x=a*7+b*15+if r{d*5}else{0};let c=d*44;x.min(c)+(x-c).max(0)*5+(t/6)*8}pub fn calculate(v:&RequestInput)->ResponseOutput{let t=v.chilled_crates+v.frozen_crates;let x=v.chilled_crates*7+v.frozen_crates*15+if v.rush_load{v.loading_docks*5}else{0};let c=v.loading_docks*44;let d=(x-c).max(0);ResponseOutput{booking_code:v.booking_code.clone(),shipment_total:t,cooling_units:x,dock_capacity_units:c,loaded_units:x.min(c),deferred_units:d,loading_rounds:t/6,booking_score:score(v.chilled_crates,v.frozen_crates,v.loading_docks,v.rush_load),booking_state:if d==0{\"booked\"}else if v.rush_load{\"rush_queue\"}else{\"routine_queue\"}.into()}}",
}


def python_logic(task: dict[str, Any], variant: str) -> str:
    annotations = "; ".join(
        f"{name}:{'int' if kind == 'number' else 'bool' if kind == 'yesno' else 'str'}"
        for name, kind in task["request_fields"].items()
    )
    calculation = PYTHON_CALCULATIONS[task["id"]]
    if _implementation_seed(task, variant):
        start = calculation.index("def score(")
        end = calculation.index("def calculate(")
        signature = calculation[start:calculation.index("\n", start)]
        calculation = calculation[:start] + signature + "\n    return 0\n" + calculation[end:]
    return f"from pydantic import BaseModel,ConfigDict\nclass RequestInput(BaseModel):\n    model_config=ConfigDict(extra='forbid',strict=True); {annotations}\n{calculation.strip()}\n"


def python_browser(task: dict[str, Any], variant: str) -> str:
    score = "const score=()=>0;" if _implementation_seed(task, variant) else JS_SCORES[task["id"]]
    return f"{score}\nexport async function loadParley(){{return {{{task['browser_export']}:(...args)=>BigInt(score(...args))}}}}\n"


def typescript_logic(task: dict[str, Any], variant: str) -> str:
    fields = ";".join(
        f"{name}:{'number' if kind == 'number' else 'boolean' if kind == 'yesno' else 'string'}"
        for name, kind in task["request_fields"].items()
    )
    calculation = TS_CALCULATIONS[task["id"]]
    if _implementation_seed(task, variant):
        calculation = calculation.replace(
            calculation[: calculation.index("export const calculate")],
            "export const score=(..._args:unknown[])=>0;",
            1,
        )
    args = ",".join(f"a{index}:{'boolean' if task['request_fields'][name] == 'yesno' else 'number'}" for index, name in enumerate(task["browser_fields"]))
    values = ",".join(f"a{index}" for index in range(len(task["browser_fields"])))
    return f"export type RequestInput={{{fields}}};{calculation}export async function loadParley(){{return {{{task['browser_export']}:({args})=>BigInt(score({values}))}}}}\n"


def rust_logic(task: dict[str, Any], variant: str) -> str:
    request = ",".join(
        f"pub {name}:{'i64' if kind == 'number' else 'bool' if kind == 'yesno' else 'String'}"
        for name, kind in task["request_fields"].items()
    )
    response = ",".join(
        f"pub {name}:{'i64' if kind == 'number' else 'String'}"
        for name, kind in task["response_fields"].items()
    )
    calculation = RUST_CALCULATIONS[task["id"]]
    if _implementation_seed(task, variant):
        calculation = "pub fn score(" + calculation.split("pub fn score(", 1)[1]
        signature, rest = calculation.split("{", 1)
        _, calculate = rest.split("pub fn calculate", 1)
        calculation = signature + "{0}pub fn calculate" + calculate
    args = ",".join(f"a{i}:{'i32' if task['request_fields'][name] == 'yesno' else 'i64'}" for i, name in enumerate(task["browser_fields"]))
    values = ",".join(f"a{i}!=0" if task["request_fields"][name] == "yesno" else f"a{i}" for i, name in enumerate(task["browser_fields"]))
    return f"use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{{request}}}#[derive(Serialize)]pub struct ResponseOutput{{{response}}}{calculation}#[unsafe(no_mangle)]pub extern \"C\" fn parley_browser_score({args})->i64{{score({values})}}\n"


PARLEY_SCORES = {
    "artifact_accession_build": """to artifact_priority_score with stable_units as number, fragile_units as number, packing_stations as number, expedited as yesno giving number:
    let packing be stable_units times 6 plus fragile_units times 11
    if expedited:
        set packing to packing plus packing_stations times 4
    let overflow be packing minus packing_stations times 40
    if overflow is less than 0:
        set overflow to 0
    let rounds be number from ((stable_units plus fragile_units) divided by 5)
    give back packing plus overflow times 5 plus rounds times 7
""",
    "microgrid_bid_build": """to microgrid_bid_score with solar_arrays as number, wind_turbines as number, storage_banks as number, interconnects as number, emergency_mode as yesno giving number:
    let buffer be storage_banks times 3
    if emergency_mode:
        set buffer to storage_banks times 7
    let required be solar_arrays times 9 plus wind_turbines times 13 plus buffer
    let capacity be interconnects times 55
    let delivered be required
    if delivered is more than capacity:
        set delivered to capacity
    let shortfall be required minus capacity
    if shortfall is less than 0:
        set shortfall to 0
    give back delivered plus shortfall times 4 plus number from (required divided by 31) times 9
""",
    "trail_permit_repair": """to trail_permit_score with day_hikers as number, overnight_hikers as number, trail_guides as number, storm_alert as yesno giving number:
    let required be day_hikers times 5 plus overnight_hikers times 12
    if storm_alert:
        set required to required plus trail_guides times 6
    let capacity be trail_guides times 38
    let admitted be required
    if admitted is more than capacity:
        set admitted to capacity
    let waiting be required minus capacity
    if waiting is less than 0:
        set waiting to 0
    give back admitted plus waiting times 6
""",
    "cold_chain_booking_repair": """to cold_chain_booking_score with chilled_crates as number, frozen_crates as number, loading_docks as number, rush_load as yesno giving number:
    let cooling be chilled_crates times 7 plus frozen_crates times 15
    if rush_load:
        set cooling to cooling plus loading_docks times 5
    let capacity be loading_docks times 44
    let loaded be cooling
    if loaded is more than capacity:
        set loaded to capacity
    let deferred be cooling minus capacity
    if deferred is less than 0:
        set deferred to 0
    give back loaded plus deferred times 5 plus number from ((chilled_crates plus frozen_crates) divided by 6) times 8
""",
}


def parley_logic(task: dict[str, Any], variant: str) -> str:
    if _implementation_seed(task, variant):
        fields = ", ".join(f"{name} as {'yesno' if task['request_fields'][name] == 'yesno' else 'number'}" for name in task["browser_fields"])
        return f"to {task['browser_export']} with {fields} giving number:\n    give back 0\n"
    return PARLEY_SCORES[task["id"]]
