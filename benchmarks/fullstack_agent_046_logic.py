"""Frozen task logic generators for full-stack agent study 046."""

from __future__ import annotations

from typing import Any


def _implementation_seed(task: dict[str, Any], variant: str) -> bool:
    return task["kind"] == "implementation" and variant == "seed"


PYTHON_CALCULATIONS = {
    "orbital_clearance_build": """
def score(pressurized_pods:int,vacuum_pods:int,docking_arms:int,solar_flare:bool)->int:
    effort=pressurized_pods*8+vacuum_pods*14+(docking_arms*5 if solar_flare else 0); allowance=docking_arms*47; total=pressurized_pods+vacuum_pods
    return min(effort,allowance)+max(effort-allowance,0)*7+((total+3)//4)*6
def calculate(v:RequestInput)->dict[str,object]:
    total=v.pressurized_pods+v.vacuum_pods; effort=v.pressurized_pods*8+v.vacuum_pods*14+(v.docking_arms*5 if v.solar_flare else 0); allowance=v.docking_arms*47; spillover=max(effort-allowance,0)
    return {'clearance_slug':v.clearance_slug,'payload_tally':total,'transfer_effort':effort,'berth_allowance':allowance,'approved_effort':min(effort,allowance),'spillover_effort':spillover,'orbit_passes':(total+3)//4,'clearance_rating':score(v.pressurized_pods,v.vacuum_pods,v.docking_arms,v.solar_flare),'clearance_phase':'cleared' if spillover==0 else 'flare_hold' if v.solar_flare else 'routine_hold'}
""",
    "estuary_assay_build": """
def score(inlet_vials:int,outlet_vials:int,reagent_cartridges:int,assay_benches:int,contamination_alert:bool)->int:
    effort=inlet_vials*11+outlet_vials*7+reagent_cartridges*9+(reagent_cartridges*4 if contamination_alert else 0); allowance=assay_benches*52
    return min(effort,allowance)+max(effort-allowance,0)*4+((effort+26)//27)*8
def calculate(v:RequestInput)->dict[str,object]:
    total=v.inlet_vials+v.outlet_vials; effort=v.inlet_vials*11+v.outlet_vials*7+v.reagent_cartridges*9+(v.reagent_cartridges*4 if v.contamination_alert else 0); allowance=v.assay_benches*52; pending=max(effort-allowance,0)
    return {'assay_ref':v.assay_ref,'sample_tally':total,'assay_effort':effort,'bench_allowance':allowance,'examined_effort':min(effort,allowance),'pending_assay':pending,'assay_cycles':(effort+26)//27,'assay_rating':score(v.inlet_vials,v.outlet_vials,v.reagent_cartridges,v.assay_benches,v.contamination_alert),'assay_phase':'dispatched' if pending==0 else 'contamination_queue' if v.contamination_alert else 'routine_queue'}
""",
    "archive_transfer_repair": """
def score(folio_boxes:int,atlas_tubes:int,catalog_carts:int,humidity_warning:bool)->int:
    total=folio_boxes+atlas_tubes; effort=folio_boxes*6+atlas_tubes*17+(catalog_carts*3 if humidity_warning else 0); allowance=catalog_carts*43
    return min(effort,allowance)+max(effort-allowance,0)*6+((total+4)//5)*7
def calculate(v:RequestInput)->dict[str,object]:
    total=v.folio_boxes+v.atlas_tubes; effort=v.folio_boxes*6+v.atlas_tubes*17+(v.catalog_carts*3 if v.humidity_warning else 0); allowance=v.catalog_carts*43; quarantine=max(effort-allowance,0)
    return {'transfer_tag':v.transfer_tag,'volume_tally':total,'relocation_effort':effort,'cart_allowance':allowance,'shelved_effort':min(effort,allowance),'quarantined_effort':quarantine,'transfer_rounds':(total+4)//5,'transfer_rating':score(v.folio_boxes,v.atlas_tubes,v.catalog_carts,v.humidity_warning),'transfer_phase':'shelved' if quarantine==0 else 'humidity_hold' if v.humidity_warning else 'routine_hold'}
""",
    "beacon_enrollment_repair": """
def score(analog_transponders:int,digital_transponders:int,calibration_frames:int,whiteout_warning:bool)->int:
    total=analog_transponders+digital_transponders; effort=analog_transponders*9+digital_transponders*16+(calibration_frames*7 if whiteout_warning else 0); allowance=calibration_frames*50
    return min(effort,allowance)+max(effort-allowance,0)*8+((total+5)//6)*5
def calculate(v:RequestInput)->dict[str,object]:
    total=v.analog_transponders+v.digital_transponders; effort=v.analog_transponders*9+v.digital_transponders*16+(v.calibration_frames*7 if v.whiteout_warning else 0); allowance=v.calibration_frames*50; remainder=max(effort-allowance,0)
    return {'enrollment_ref':v.enrollment_ref,'transponder_tally':total,'tuning_effort':effort,'frame_allowance':allowance,'commissioned_effort':min(effort,allowance),'uncommissioned_effort':remainder,'tuning_rounds':(total+5)//6,'enrollment_rating':score(v.analog_transponders,v.digital_transponders,v.calibration_frames,v.whiteout_warning),'enrollment_phase':'enrolled' if remainder==0 else 'whiteout_hold' if v.whiteout_warning else 'routine_hold'}
""",
}


JS_SCORES = {
    "orbital_clearance_build": "const score=(p,v,d,s)=>{const t=p+v,e=p*8+v*14+(s?d*5:0),a=d*47;return Math.min(e,a)+Math.max(e-a,0)*7+Math.trunc((t+3)/4)*6};",
    "estuary_assay_build": "const score=(i,o,r,b,c)=>{const e=i*11+o*7+r*9+(c?r*4:0),a=b*52;return Math.min(e,a)+Math.max(e-a,0)*4+Math.trunc((e+26)/27)*8};",
    "archive_transfer_repair": "const score=(f,a,c,h)=>{const t=f+a,e=f*6+a*17+(h?c*3:0),x=c*43;return Math.min(e,x)+Math.max(e-x,0)*6+Math.trunc((t+4)/5)*7};",
    "beacon_enrollment_repair": "const score=(a,d,c,w)=>{const t=a+d,e=a*9+d*16+(w?c*7:0),x=c*50;return Math.min(e,x)+Math.max(e-x,0)*8+Math.trunc((t+5)/6)*5};",
}


TS_CALCULATIONS = {
    "orbital_clearance_build": "export const score=(p:number,v:number,d:number,s:boolean)=>{const t=p+v,e=p*8+v*14+(s?d*5:0),a=d*47;return Math.min(e,a)+Math.max(e-a,0)*7+Math.trunc((t+3)/4)*6};export const calculate=(v:RequestInput)=>{const t=v.pressurized_pods+v.vacuum_pods,e=v.pressurized_pods*8+v.vacuum_pods*14+(v.solar_flare?v.docking_arms*5:0),a=v.docking_arms*47,x=Math.max(e-a,0);return {clearance_slug:v.clearance_slug,payload_tally:t,transfer_effort:e,berth_allowance:a,approved_effort:Math.min(e,a),spillover_effort:x,orbit_passes:Math.trunc((t+3)/4),clearance_rating:score(v.pressurized_pods,v.vacuum_pods,v.docking_arms,v.solar_flare),clearance_phase:x===0?'cleared':v.solar_flare?'flare_hold':'routine_hold'}};",
    "estuary_assay_build": "export const score=(i:number,o:number,r:number,b:number,c:boolean)=>{const e=i*11+o*7+r*9+(c?r*4:0),a=b*52;return Math.min(e,a)+Math.max(e-a,0)*4+Math.trunc((e+26)/27)*8};export const calculate=(v:RequestInput)=>{const t=v.inlet_vials+v.outlet_vials,e=v.inlet_vials*11+v.outlet_vials*7+v.reagent_cartridges*9+(v.contamination_alert?v.reagent_cartridges*4:0),a=v.assay_benches*52,p=Math.max(e-a,0);return {assay_ref:v.assay_ref,sample_tally:t,assay_effort:e,bench_allowance:a,examined_effort:Math.min(e,a),pending_assay:p,assay_cycles:Math.trunc((e+26)/27),assay_rating:score(v.inlet_vials,v.outlet_vials,v.reagent_cartridges,v.assay_benches,v.contamination_alert),assay_phase:p===0?'dispatched':v.contamination_alert?'contamination_queue':'routine_queue'}};",
    "archive_transfer_repair": "export const score=(f:number,a:number,c:number,h:boolean)=>{const t=f+a,e=f*6+a*17+(h?c*3:0),x=c*43;return Math.min(e,x)+Math.max(e-x,0)*6+Math.trunc((t+4)/5)*7};export const calculate=(v:RequestInput)=>{const t=v.folio_boxes+v.atlas_tubes,e=v.folio_boxes*6+v.atlas_tubes*17+(v.humidity_warning?v.catalog_carts*3:0),a=v.catalog_carts*43,q=Math.max(e-a,0);return {transfer_tag:v.transfer_tag,volume_tally:t,relocation_effort:e,cart_allowance:a,shelved_effort:Math.min(e,a),quarantined_effort:q,transfer_rounds:Math.trunc((t+4)/5),transfer_rating:score(v.folio_boxes,v.atlas_tubes,v.catalog_carts,v.humidity_warning),transfer_phase:q===0?'shelved':v.humidity_warning?'humidity_hold':'routine_hold'}};",
    "beacon_enrollment_repair": "export const score=(a:number,d:number,c:number,w:boolean)=>{const t=a+d,e=a*9+d*16+(w?c*7:0),x=c*50;return Math.min(e,x)+Math.max(e-x,0)*8+Math.trunc((t+5)/6)*5};export const calculate=(v:RequestInput)=>{const t=v.analog_transponders+v.digital_transponders,e=v.analog_transponders*9+v.digital_transponders*16+(v.whiteout_warning?v.calibration_frames*7:0),a=v.calibration_frames*50,r=Math.max(e-a,0);return {enrollment_ref:v.enrollment_ref,transponder_tally:t,tuning_effort:e,frame_allowance:a,commissioned_effort:Math.min(e,a),uncommissioned_effort:r,tuning_rounds:Math.trunc((t+5)/6),enrollment_rating:score(v.analog_transponders,v.digital_transponders,v.calibration_frames,v.whiteout_warning),enrollment_phase:r===0?'enrolled':v.whiteout_warning?'whiteout_hold':'routine_hold'}};",
}


RUST_CALCULATIONS = {
    "orbital_clearance_build": "pub fn score(p:i64,v:i64,d:i64,s:bool)->i64{let t=p+v;let e=p*8+v*14+if s{d*5}else{0};let a=d*47;e.min(a)+(e-a).max(0)*7+((t+3)/4)*6}pub fn calculate(v:&RequestInput)->ResponseOutput{let t=v.pressurized_pods+v.vacuum_pods;let e=v.pressurized_pods*8+v.vacuum_pods*14+if v.solar_flare{v.docking_arms*5}else{0};let a=v.docking_arms*47;let x=(e-a).max(0);ResponseOutput{clearance_slug:v.clearance_slug.clone(),payload_tally:t,transfer_effort:e,berth_allowance:a,approved_effort:e.min(a),spillover_effort:x,orbit_passes:(t+3)/4,clearance_rating:score(v.pressurized_pods,v.vacuum_pods,v.docking_arms,v.solar_flare),clearance_phase:if x==0{\"cleared\"}else if v.solar_flare{\"flare_hold\"}else{\"routine_hold\"}.into()}}",
    "estuary_assay_build": "pub fn score(i:i64,o:i64,r:i64,b:i64,c:bool)->i64{let e=i*11+o*7+r*9+if c{r*4}else{0};let a=b*52;e.min(a)+(e-a).max(0)*4+((e+26)/27)*8}pub fn calculate(v:&RequestInput)->ResponseOutput{let t=v.inlet_vials+v.outlet_vials;let e=v.inlet_vials*11+v.outlet_vials*7+v.reagent_cartridges*9+if v.contamination_alert{v.reagent_cartridges*4}else{0};let a=v.assay_benches*52;let p=(e-a).max(0);ResponseOutput{assay_ref:v.assay_ref.clone(),sample_tally:t,assay_effort:e,bench_allowance:a,examined_effort:e.min(a),pending_assay:p,assay_cycles:(e+26)/27,assay_rating:score(v.inlet_vials,v.outlet_vials,v.reagent_cartridges,v.assay_benches,v.contamination_alert),assay_phase:if p==0{\"dispatched\"}else if v.contamination_alert{\"contamination_queue\"}else{\"routine_queue\"}.into()}}",
    "archive_transfer_repair": "pub fn score(f:i64,a:i64,c:i64,h:bool)->i64{let t=f+a;let e=f*6+a*17+if h{c*3}else{0};let x=c*43;e.min(x)+(e-x).max(0)*6+((t+4)/5)*7}pub fn calculate(v:&RequestInput)->ResponseOutput{let t=v.folio_boxes+v.atlas_tubes;let e=v.folio_boxes*6+v.atlas_tubes*17+if v.humidity_warning{v.catalog_carts*3}else{0};let a=v.catalog_carts*43;let q=(e-a).max(0);ResponseOutput{transfer_tag:v.transfer_tag.clone(),volume_tally:t,relocation_effort:e,cart_allowance:a,shelved_effort:e.min(a),quarantined_effort:q,transfer_rounds:(t+4)/5,transfer_rating:score(v.folio_boxes,v.atlas_tubes,v.catalog_carts,v.humidity_warning),transfer_phase:if q==0{\"shelved\"}else if v.humidity_warning{\"humidity_hold\"}else{\"routine_hold\"}.into()}}",
    "beacon_enrollment_repair": "pub fn score(a:i64,d:i64,c:i64,w:bool)->i64{let t=a+d;let e=a*9+d*16+if w{c*7}else{0};let x=c*50;e.min(x)+(e-x).max(0)*8+((t+5)/6)*5}pub fn calculate(v:&RequestInput)->ResponseOutput{let t=v.analog_transponders+v.digital_transponders;let e=v.analog_transponders*9+v.digital_transponders*16+if v.whiteout_warning{v.calibration_frames*7}else{0};let a=v.calibration_frames*50;let r=(e-a).max(0);ResponseOutput{enrollment_ref:v.enrollment_ref.clone(),transponder_tally:t,tuning_effort:e,frame_allowance:a,commissioned_effort:e.min(a),uncommissioned_effort:r,tuning_rounds:(t+5)/6,enrollment_rating:score(v.analog_transponders,v.digital_transponders,v.calibration_frames,v.whiteout_warning),enrollment_phase:if r==0{\"enrolled\"}else if v.whiteout_warning{\"whiteout_hold\"}else{\"routine_hold\"}.into()}}",
}


def python_logic(task: dict[str, Any], variant: str) -> str:
    annotations = "; ".join(
        f"{name}:{'int' if kind == 'number' else 'bool' if kind == 'yesno' else 'str'}"
        for name, kind in task["request_fields"].items()
    )
    calculation = PYTHON_CALCULATIONS[task["id"]]
    if _implementation_seed(task, variant):
        start, end = calculation.index("def score("), calculation.index("def calculate(")
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
            calculation[:calculation.index("export const calculate")],
            "export const score=(..._args:unknown[])=>0;", 1,
        )
    args = ",".join(
        f"a{index}:{'boolean' if task['request_fields'][name] == 'yesno' else 'number'}"
        for index, name in enumerate(task["browser_fields"])
    )
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
    args = ",".join(
        f"a{i}:{'i32' if task['request_fields'][name] == 'yesno' else 'i64'}"
        for i, name in enumerate(task["browser_fields"])
    )
    values = ",".join(
        f"a{i}!=0" if task["request_fields"][name] == "yesno" else f"a{i}"
        for i, name in enumerate(task["browser_fields"])
    )
    return f"use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{{request}}}#[derive(Serialize)]pub struct ResponseOutput{{{response}}}{calculation}#[unsafe(no_mangle)]pub extern \"C\" fn parley_browser_score({args})->i64{{score({values})}}\n"


PARLEY_SCORES = {
    "orbital_clearance_build": """to orbital_clearance_rating with pressurized_pods as number, vacuum_pods as number, docking_arms as number, solar_flare as yesno giving number:
    let effort be pressurized_pods times 8 plus vacuum_pods times 14
    if solar_flare:
        set effort to effort plus docking_arms times 5
    let allowance be docking_arms times 47
    let approved be effort
    if approved is more than allowance:
        set approved to allowance
    let spillover be effort minus allowance
    if spillover is less than 0:
        set spillover to 0
    let passes be number from ((pressurized_pods plus vacuum_pods plus 3) divided by 4)
    give back approved plus spillover times 7 plus passes times 6
""",
    "estuary_assay_build": """to estuary_assay_rating with inlet_vials as number, outlet_vials as number, reagent_cartridges as number, assay_benches as number, contamination_alert as yesno giving number:
    let effort be inlet_vials times 11 plus outlet_vials times 7 plus reagent_cartridges times 9
    if contamination_alert:
        set effort to effort plus reagent_cartridges times 4
    let allowance be assay_benches times 52
    let examined be effort
    if examined is more than allowance:
        set examined to allowance
    let pending be effort minus allowance
    if pending is less than 0:
        set pending to 0
    let cycles be number from ((effort plus 26) divided by 27)
    give back examined plus pending times 4 plus cycles times 8
""",
    "archive_transfer_repair": """to archive_transfer_rating with folio_boxes as number, atlas_tubes as number, catalog_carts as number, humidity_warning as yesno giving number:
    let effort be folio_boxes times 6 plus atlas_tubes times 17
    if humidity_warning:
        set effort to effort plus catalog_carts times 3
    let allowance be catalog_carts times 43
    let shelved be effort
    if shelved is more than allowance:
        set shelved to allowance
    let quarantine be effort minus allowance
    if quarantine is less than 0:
        set quarantine to 0
    let rounds be number from ((folio_boxes plus atlas_tubes plus 4) divided by 5)
    give back shelved plus quarantine times 6 plus rounds times 7
""",
    "beacon_enrollment_repair": """to beacon_enrollment_rating with analog_transponders as number, digital_transponders as number, calibration_frames as number, whiteout_warning as yesno giving number:
    let effort be analog_transponders times 9 plus digital_transponders times 16
    if whiteout_warning:
        set effort to effort plus calibration_frames times 7
    let allowance be calibration_frames times 50
    let commissioned be effort
    if commissioned is more than allowance:
        set commissioned to allowance
    let remainder be effort minus allowance
    if remainder is less than 0:
        set remainder to 0
    let rounds be number from ((analog_transponders plus digital_transponders plus 5) divided by 6)
    give back commissioned plus remainder times 8 plus rounds times 5
""",
}


def parley_logic(task: dict[str, Any], variant: str) -> str:
    if _implementation_seed(task, variant):
        fields = ", ".join(
            f"{name} as {'yesno' if task['request_fields'][name] == 'yesno' else 'number'}"
            for name in task["browser_fields"]
        )
        return f"to {task['browser_export']} with {fields} giving number:\n    give back 0\n"
    return PARLEY_SCORES[task["id"]]
