"""Frozen task-specific reference and seed logic for full-stack agent study 044."""

PARLEY_LOGIC = {
    "seismic_array_build": {
        "seed": """
to seismic_array_score with short_sensors as number, deep_sensors as number, relay_towers as number, ash_warning as yesno giving number:
    give back 0
""",
        "reference": """
to seismic_array_score with short_sensors as number, deep_sensors as number, relay_towers as number, ash_warning as yesno giving number:
    let required be short_sensors times 12 plus deep_sensors times 20
    if ash_warning:
        set required to required plus relay_towers times 7
    let capacity be relay_towers times 48
    let processed be required
    if processed is more than capacity:
        set processed to capacity
    let backlogged be required minus capacity
    if backlogged is less than 0:
        set backlogged to 0
    let rounds be number from (required divided by 37)
    give back processed plus backlogged times 6 plus rounds times 10
""",
    },
    "museum_conservation_build": {
        "seed": """
to museum_conservation_score with canvas_crates as number, textile_crates as number, work_tables as number, emergency_drying as yesno giving number:
    give back 0
""",
        "reference": """
to museum_conservation_score with canvas_crates as number, textile_crates as number, work_tables as number, emergency_drying as yesno giving number:
    let required be canvas_crates times 9 plus textile_crates times 15
    if emergency_drying:
        set required to required plus work_tables times 6
    let capacity be work_tables times 43
    let completed be required
    if completed is more than capacity:
        set completed to capacity
    let deferred be required minus capacity
    if deferred is less than 0:
        set deferred to 0
    let rounds be number from (required divided by 34)
    give back completed plus deferred times 7 plus rounds times 11
""",
    },
    "canal_lock_repair": {
        "seed": """
to canal_clearance_units with freight_barges as number, tour_barges as number, lock_chambers as number, flood_protocol as yesno giving number:
    let required be freight_barges times 10 plus tour_barges times 17
    if not flood_protocol:
        set required to required plus lock_chambers times 8
    let capacity be lock_chambers times 45
    let passed be required
    if passed is more than capacity:
        set passed to capacity
    let clearance be capacity minus passed
    if clearance is less than 0:
        set clearance to 0
    give back clearance
""",
        "reference": """
to canal_clearance_units with freight_barges as number, tour_barges as number, lock_chambers as number, flood_protocol as yesno giving number:
    let required be freight_barges times 10 plus tour_barges times 17
    if flood_protocol:
        set required to required plus lock_chambers times 8
    let capacity be lock_chambers times 45
    let passed be required
    if passed is more than capacity:
        set passed to capacity
    let clearance be capacity minus passed
    if clearance is less than 0:
        set clearance to 0
    give back clearance
""",
    },
    "thermal_greenhouse_repair": {
        "seed": """
to thermal_greenhouse_score with seedling_rows as number, fruit_rows as number, heat_pumps as number, frost_cycle as yesno giving number:
    let required be seedling_rows times 8 plus fruit_rows times 14
    if frost_cycle:
        set required to required plus heat_pumps times 5
    let capacity be heat_pumps times 41
    let delivered be required
    if delivered is more than capacity:
        set delivered to capacity
    let deficit be required minus capacity
    if deficit is less than 0:
        set deficit to 0
    let cycles be number from (required divided by 23)
    give back delivered plus deficit times 5 plus cycles times 7
""",
        "reference": """
to thermal_greenhouse_score with seedling_rows as number, fruit_rows as number, heat_pumps as number, frost_cycle as yesno giving number:
    let required be seedling_rows times 8 plus fruit_rows times 14
    if frost_cycle:
        set required to required plus heat_pumps times 5
    let capacity be heat_pumps times 41
    let delivered be required
    if delivered is more than capacity:
        set delivered to capacity
    let deficit be required minus capacity
    if deficit is less than 0:
        set deficit to 0
    let cycles be number from (required divided by 29)
    give back delivered plus deficit times 5 plus cycles times 7
""",
    },
}

PARLEY_MAIN = {
    "seismic_array_build": """
include "logic.par"
a seismic_request has short_sensors as number, deep_sensors as number, relay_towers as number, ash_warning as yesno
a seismic_response has sensor_total as number, short_scan_seconds as number, deep_scan_seconds as number, ash_sync_seconds as number, array_required_seconds as number, relay_capacity_seconds as number, processed_seconds as number, backlogged_seconds as number, scan_rounds as number, array_score as number, array_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Seismic Array", ready yes
to handle_request with request as seismic_request giving seismic_response:
    let short be request's short_sensors times 12
    let deep be request's deep_sensors times 20
    let ash be 0
    if request's ash_warning:
        set ash to request's relay_towers times 7
    let required be short plus deep plus ash
    let capacity be request's relay_towers times 48
    let processed be required
    if processed is more than capacity:
        set processed to capacity
    let backlogged be required minus capacity
    if backlogged is less than 0:
        set backlogged to 0
    let rounds be number from (required divided by 37)
    let state be "aligned"
    if backlogged is more than 0:
        set state to "routine_backlog"
        if request's ash_warning:
            set state to "ash_backlog"
    give back a seismic_response with sensor_total (request's short_sensors plus request's deep_sensors), short_scan_seconds short, deep_scan_seconds deep, ash_sync_seconds ash, array_required_seconds required, relay_capacity_seconds capacity, processed_seconds processed, backlogged_seconds backlogged, scan_rounds rounds, array_score (seismic_array_score with request's short_sensors, request's deep_sensors, request's relay_towers, request's ash_warning), array_state state
""",
    "museum_conservation_build": """
include "logic.par"
a conservation_request has canvas_crates as number, textile_crates as number, work_tables as number, emergency_drying as yesno
a conservation_response has crate_total as number, canvas_work_minutes as number, textile_work_minutes as number, drying_setup_minutes as number, conservation_required_minutes as number, table_capacity_minutes as number, completed_minutes as number, deferred_minutes as number, conservation_rounds as number, conservation_score as number, conservation_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Museum Conservation", ready yes
to handle_request with request as conservation_request giving conservation_response:
    let canvas be request's canvas_crates times 9
    let textile be request's textile_crates times 15
    let drying be 0
    if request's emergency_drying:
        set drying to request's work_tables times 6
    let required be canvas plus textile plus drying
    let capacity be request's work_tables times 43
    let completed be required
    if completed is more than capacity:
        set completed to capacity
    let deferred be required minus capacity
    if deferred is less than 0:
        set deferred to 0
    let rounds be number from (required divided by 34)
    let state be "preserved"
    if deferred is more than 0:
        set state to "routine_queue"
        if request's emergency_drying:
            set state to "emergency_queue"
    give back a conservation_response with crate_total (request's canvas_crates plus request's textile_crates), canvas_work_minutes canvas, textile_work_minutes textile, drying_setup_minutes drying, conservation_required_minutes required, table_capacity_minutes capacity, completed_minutes completed, deferred_minutes deferred, conservation_rounds rounds, conservation_score (museum_conservation_score with request's canvas_crates, request's textile_crates, request's work_tables, request's emergency_drying), conservation_state state
""",
    "canal_lock_repair": """
include "logic.par"
a canal_request has freight_barges as number, tour_barges as number, lock_chambers as number, flood_protocol as yesno
a canal_response has barge_total as number, freight_lock_units as number, tour_lock_units as number, flood_lock_units as number, lock_required_units as number, lock_capacity_units as number, passed_lock_units as number, held_lock_units as number, clearance_units as number, canal_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Canal Lock", ready yes
to handle_request with request as canal_request giving canal_response:
    let freight be request's freight_barges times 10
    let tour be request's tour_barges times 17
    let flood be 0
    if request's flood_protocol:
        set flood to request's lock_chambers times 8
    let required be freight plus tour plus flood
    let capacity be request's lock_chambers times 45
    let passed be required
    if passed is more than capacity:
        set passed to capacity
    let held be required minus capacity
    if held is less than 0:
        set held to 0
    let state be "clear"
    if held is more than 0:
        set state to "routine_hold"
        if request's flood_protocol:
            set state to "flood_hold"
    give back a canal_response with barge_total (request's freight_barges plus request's tour_barges), freight_lock_units freight, tour_lock_units tour, flood_lock_units flood, lock_required_units required, lock_capacity_units capacity, passed_lock_units passed, held_lock_units held, clearance_units (canal_clearance_units with request's freight_barges, request's tour_barges, request's lock_chambers, request's flood_protocol), canal_state state
""",
    "thermal_greenhouse_repair": """
include "logic.par"
a greenhouse_request has seedling_rows as number, fruit_rows as number, heat_pumps as number, frost_cycle as yesno
a greenhouse_response has row_total as number, seedling_heat_units as number, fruit_heat_units as number, frost_heat_units as number, heat_required_units as number, pump_capacity_units as number, delivered_heat_units as number, heat_deficit_units as number, heat_reserve_units as number, heating_cycles as number, greenhouse_score as number, greenhouse_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Thermal Greenhouse", ready yes
to handle_request with request as greenhouse_request giving greenhouse_response:
    let seedling be request's seedling_rows times 8
    let fruit be request's fruit_rows times 14
    let frost be 0
    if request's frost_cycle:
        set frost to request's heat_pumps times 5
    let required be seedling plus fruit plus frost
    let capacity be request's heat_pumps times 41
    let delivered be required
    if delivered is more than capacity:
        set delivered to capacity
    let deficit be required minus capacity
    if deficit is less than 0:
        set deficit to 0
    let reserve be capacity minus delivered
    if reserve is less than 0:
        set reserve to 0
    let cycles be number from (required divided by 29)
    let state be "balanced"
    if deficit is more than 0:
        set state to "heat_shortage"
        if request's frost_cycle:
            set state to "frost_shortage"
    give back a greenhouse_response with row_total (request's seedling_rows plus request's fruit_rows), seedling_heat_units seedling, fruit_heat_units fruit, frost_heat_units frost, heat_required_units required, pump_capacity_units capacity, delivered_heat_units delivered, heat_deficit_units deficit, heat_reserve_units reserve, heating_cycles cycles, greenhouse_score (thermal_greenhouse_score with request's seedling_rows, request's fruit_rows, request's heat_pumps, request's frost_cycle), greenhouse_state state
""",
}

PYTHON_LOGIC = {
    "seismic_array_build": {v: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); short_sensors:int=Field(ge=0); deep_sensors:int=Field(ge=0); relay_towers:int=Field(ge=0); ash_warning:bool
def seismic_array_score(s:int,d:int,t:int,a:bool)->int: {'return 0' if v=='seed' else 'r=s*12+d*20+(t*7 if a else 0); c=t*48; return min(r,c)+max(r-c,0)*6+(r//37)*10'}
def handle(v:RequestInput)->dict[str,object]:
 s=v.short_sensors*12; d=v.deep_sensors*20; a=v.relay_towers*7 if v.ash_warning else 0; r=s+d+a; c=v.relay_towers*48; b=max(r-c,0)
 return {{'sensor_total':v.short_sensors+v.deep_sensors,'short_scan_seconds':s,'deep_scan_seconds':d,'ash_sync_seconds':a,'array_required_seconds':r,'relay_capacity_seconds':c,'processed_seconds':min(r,c),'backlogged_seconds':b,'scan_rounds':r//37,'array_score':seismic_array_score(v.short_sensors,v.deep_sensors,v.relay_towers,v.ash_warning),'array_state':'aligned' if b==0 else 'ash_backlog' if v.ash_warning else 'routine_backlog'}}
""" for v in ('seed','reference')},
    "museum_conservation_build": {v: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); canvas_crates:int=Field(ge=0); textile_crates:int=Field(ge=0); work_tables:int=Field(ge=0); emergency_drying:bool
def museum_conservation_score(c:int,t:int,w:int,e:bool)->int: {'return 0' if v=='seed' else 'r=c*9+t*15+(w*6 if e else 0); x=w*43; return min(r,x)+max(r-x,0)*7+(r//34)*11'}
def handle(v:RequestInput)->dict[str,object]:
 c=v.canvas_crates*9; t=v.textile_crates*15; d=v.work_tables*6 if v.emergency_drying else 0; r=c+t+d; x=v.work_tables*43; q=max(r-x,0)
 return {{'crate_total':v.canvas_crates+v.textile_crates,'canvas_work_minutes':c,'textile_work_minutes':t,'drying_setup_minutes':d,'conservation_required_minutes':r,'table_capacity_minutes':x,'completed_minutes':min(r,x),'deferred_minutes':q,'conservation_rounds':r//34,'conservation_score':museum_conservation_score(v.canvas_crates,v.textile_crates,v.work_tables,v.emergency_drying),'conservation_state':'preserved' if q==0 else 'emergency_queue' if v.emergency_drying else 'routine_queue'}}
""" for v in ('seed','reference')},
    "canal_lock_repair": {v: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); freight_barges:int=Field(ge=0); tour_barges:int=Field(ge=0); lock_chambers:int=Field(ge=0); flood_protocol:bool
def canal_clearance_units(f:int,t:int,c:int,p:bool)->int:
 r=f*10+t*17+(c*8 if {'not p' if v=='seed' else 'p'} else 0); return max(c*45-min(r,c*45),0)
def handle(v:RequestInput)->dict[str,object]:
 f=v.freight_barges*10; t=v.tour_barges*17; p=v.lock_chambers*8 if v.flood_protocol else 0; r=f+t+p; c=v.lock_chambers*45; h=max(r-c,0)
 return {{'barge_total':v.freight_barges+v.tour_barges,'freight_lock_units':f,'tour_lock_units':t,'flood_lock_units':p,'lock_required_units':r,'lock_capacity_units':c,'passed_lock_units':min(r,c),'held_lock_units':h,'clearance_units':canal_clearance_units(v.freight_barges,v.tour_barges,v.lock_chambers,v.flood_protocol),'canal_state':'clear' if h==0 else 'flood_hold' if v.flood_protocol else 'routine_hold'}}
""" for v in ('seed','reference')},
    "thermal_greenhouse_repair": {v: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); seedling_rows:int=Field(ge=0); fruit_rows:int=Field(ge=0); heat_pumps:int=Field(ge=0); frost_cycle:bool
def thermal_greenhouse_score(s:int,f:int,p:int,c:bool)->int:
 r=s*8+f*14+(p*5 if c else 0); x=p*41; return min(r,x)+max(r-x,0)*5+(r//{'23' if v=='seed' else '29'})*7
def handle(v:RequestInput)->dict[str,object]:
 s=v.seedling_rows*8; f=v.fruit_rows*14; c=v.heat_pumps*5 if v.frost_cycle else 0; r=s+f+c; p=v.heat_pumps*41; d=max(r-p,0); delivered=min(r,p)
 return {{'row_total':v.seedling_rows+v.fruit_rows,'seedling_heat_units':s,'fruit_heat_units':f,'frost_heat_units':c,'heat_required_units':r,'pump_capacity_units':p,'delivered_heat_units':delivered,'heat_deficit_units':d,'heat_reserve_units':max(p-delivered,0),'heating_cycles':r//29,'greenhouse_score':thermal_greenhouse_score(v.seedling_rows,v.fruit_rows,v.heat_pumps,v.frost_cycle),'greenhouse_state':'balanced' if d==0 else 'frost_shortage' if v.frost_cycle else 'heat_shortage'}}
""" for v in ('seed','reference')},
}

PYTHON_BROWSER = {
    "seismic_array_build": {"seed": "const seismicArrayScore=()=>0n;", "reference": "const seismicArrayScore=(s,d,t,a)=>{const r=s*12+d*20+(a?t*7:0),c=t*48;return BigInt(Math.min(r,c)+Math.max(r-c,0)*6+Math.trunc(r/37)*10);};"},
    "museum_conservation_build": {"seed": "const museumConservationScore=()=>0n;", "reference": "const museumConservationScore=(c,t,w,e)=>{const r=c*9+t*15+(e?w*6:0),x=w*43;return BigInt(Math.min(r,x)+Math.max(r-x,0)*7+Math.trunc(r/34)*11);};"},
    "canal_lock_repair": {"seed": "const canalClearanceUnits=(f,t,c,p)=>{const r=f*10+t*17+(!p?c*8:0);return BigInt(Math.max(c*45-Math.min(r,c*45),0));};", "reference": "const canalClearanceUnits=(f,t,c,p)=>{const r=f*10+t*17+(p?c*8:0);return BigInt(Math.max(c*45-Math.min(r,c*45),0));};"},
    "thermal_greenhouse_repair": {"seed": "const thermalGreenhouseScore=(s,f,p,c)=>{const r=s*8+f*14+(c?p*5:0),x=p*41;return BigInt(Math.min(r,x)+Math.max(r-x,0)*5+Math.trunc(r/23)*7);};", "reference": "const thermalGreenhouseScore=(s,f,p,c)=>{const r=s*8+f*14+(c?p*5:0),x=p*41;return BigInt(Math.min(r,x)+Math.max(r-x,0)*5+Math.trunc(r/29)*7);};"},
}

PYTHON_BROWSER_EXPORT = {
    "seismic_array_build": ("seismic_array_score", "seismicArrayScore"),
    "museum_conservation_build": ("museum_conservation_score", "museumConservationScore"),
    "canal_lock_repair": ("canal_clearance_units", "canalClearanceUnits"),
    "thermal_greenhouse_repair": ("thermal_greenhouse_score", "thermalGreenhouseScore"),
}

TYPESCRIPT_LOGIC = {
    "seismic_array_build": {v: f"""export type RequestInput={{short_sensors:number;deep_sensors:number;relay_towers:number;ash_warning:boolean}};export const score=(s:number,d:number,t:number,a:boolean)=>{{{'return 0' if v=='seed' else 'const r=s*12+d*20+(a?t*7:0),c=t*48;return Math.min(r,c)+Math.max(r-c,0)*6+Math.trunc(r/37)*10'}}};export const handle=(v:RequestInput)=>{{const s=v.short_sensors*12,d=v.deep_sensors*20,a=v.ash_warning?v.relay_towers*7:0,r=s+d+a,c=v.relay_towers*48,b=Math.max(r-c,0);return {{sensor_total:v.short_sensors+v.deep_sensors,short_scan_seconds:s,deep_scan_seconds:d,ash_sync_seconds:a,array_required_seconds:r,relay_capacity_seconds:c,processed_seconds:Math.min(r,c),backlogged_seconds:b,scan_rounds:Math.trunc(r/37),array_score:score(v.short_sensors,v.deep_sensors,v.relay_towers,v.ash_warning),array_state:b===0?'aligned':v.ash_warning?'ash_backlog':'routine_backlog'}}}};export async function loadParley(){{return {{seismic_array_score:(a:number,b:number,c:number,d:boolean)=>BigInt(score(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "museum_conservation_build": {v: f"""export type RequestInput={{canvas_crates:number;textile_crates:number;work_tables:number;emergency_drying:boolean}};export const score=(c:number,t:number,w:number,e:boolean)=>{{{'return 0' if v=='seed' else 'const r=c*9+t*15+(e?w*6:0),x=w*43;return Math.min(r,x)+Math.max(r-x,0)*7+Math.trunc(r/34)*11'}}};export const handle=(v:RequestInput)=>{{const c=v.canvas_crates*9,t=v.textile_crates*15,d=v.emergency_drying?v.work_tables*6:0,r=c+t+d,x=v.work_tables*43,q=Math.max(r-x,0);return {{crate_total:v.canvas_crates+v.textile_crates,canvas_work_minutes:c,textile_work_minutes:t,drying_setup_minutes:d,conservation_required_minutes:r,table_capacity_minutes:x,completed_minutes:Math.min(r,x),deferred_minutes:q,conservation_rounds:Math.trunc(r/34),conservation_score:score(v.canvas_crates,v.textile_crates,v.work_tables,v.emergency_drying),conservation_state:q===0?'preserved':v.emergency_drying?'emergency_queue':'routine_queue'}}}};export async function loadParley(){{return {{museum_conservation_score:(a:number,b:number,c:number,d:boolean)=>BigInt(score(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "canal_lock_repair": {v: f"""export type RequestInput={{freight_barges:number;tour_barges:number;lock_chambers:number;flood_protocol:boolean}};export const clearance=(f:number,t:number,c:number,p:boolean)=>{{const r=f*10+t*17+({'!p' if v=='seed' else 'p'}?c*8:0);return Math.max(c*45-Math.min(r,c*45),0)}};export const handle=(v:RequestInput)=>{{const f=v.freight_barges*10,t=v.tour_barges*17,p=v.flood_protocol?v.lock_chambers*8:0,r=f+t+p,c=v.lock_chambers*45,h=Math.max(r-c,0);return {{barge_total:v.freight_barges+v.tour_barges,freight_lock_units:f,tour_lock_units:t,flood_lock_units:p,lock_required_units:r,lock_capacity_units:c,passed_lock_units:Math.min(r,c),held_lock_units:h,clearance_units:clearance(v.freight_barges,v.tour_barges,v.lock_chambers,v.flood_protocol),canal_state:h===0?'clear':v.flood_protocol?'flood_hold':'routine_hold'}}}};export async function loadParley(){{return {{canal_clearance_units:(a:number,b:number,c:number,d:boolean)=>BigInt(clearance(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "thermal_greenhouse_repair": {v: f"""export type RequestInput={{seedling_rows:number;fruit_rows:number;heat_pumps:number;frost_cycle:boolean}};export const score=(s:number,f:number,p:number,c:boolean)=>{{const r=s*8+f*14+(c?p*5:0),x=p*41;return Math.min(r,x)+Math.max(r-x,0)*5+Math.trunc(r/{'23' if v=='seed' else '29'})*7}};export const handle=(v:RequestInput)=>{{const s=v.seedling_rows*8,f=v.fruit_rows*14,c=v.frost_cycle?v.heat_pumps*5:0,r=s+f+c,p=v.heat_pumps*41,d=Math.max(r-p,0),delivered=Math.min(r,p);return {{row_total:v.seedling_rows+v.fruit_rows,seedling_heat_units:s,fruit_heat_units:f,frost_heat_units:c,heat_required_units:r,pump_capacity_units:p,delivered_heat_units:delivered,heat_deficit_units:d,heat_reserve_units:Math.max(p-delivered,0),heating_cycles:Math.trunc(r/29),greenhouse_score:score(v.seedling_rows,v.fruit_rows,v.heat_pumps,v.frost_cycle),greenhouse_state:d===0?'balanced':v.frost_cycle?'frost_shortage':'heat_shortage'}}}};export async function loadParley(){{return {{thermal_greenhouse_score:(a:number,b:number,c:number,d:boolean)=>BigInt(score(a,b,c,d))}}}}""" for v in ('seed','reference')},
}

TS_SCHEMA = {
    "seismic_array_build": "z.object({ short_sensors:z.number().int().nonnegative(), deep_sensors:z.number().int().nonnegative(), relay_towers:z.number().int().nonnegative(), ash_warning:z.boolean() }).strict()",
    "museum_conservation_build": "z.object({ canvas_crates:z.number().int().nonnegative(), textile_crates:z.number().int().nonnegative(), work_tables:z.number().int().nonnegative(), emergency_drying:z.boolean() }).strict()",
    "canal_lock_repair": "z.object({ freight_barges:z.number().int().nonnegative(), tour_barges:z.number().int().nonnegative(), lock_chambers:z.number().int().nonnegative(), flood_protocol:z.boolean() }).strict()",
    "thermal_greenhouse_repair": "z.object({ seedling_rows:z.number().int().nonnegative(), fruit_rows:z.number().int().nonnegative(), heat_pumps:z.number().int().nonnegative(), frost_cycle:z.boolean() }).strict()",
}

RUST_LIB = {
    "seismic_array_build": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub short_sensors:i64,pub deep_sensors:i64,pub relay_towers:i64,pub ash_warning:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.short_sensors>=0&&self.deep_sensors>=0&&self.relay_towers>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub sensor_total:i64,pub short_scan_seconds:i64,pub deep_scan_seconds:i64,pub ash_sync_seconds:i64,pub array_required_seconds:i64,pub relay_capacity_seconds:i64,pub processed_seconds:i64,pub backlogged_seconds:i64,pub scan_rounds:i64,pub array_score:i64,pub array_state:String}}pub fn score(s:i64,d:i64,t:i64,a:bool)->i64{{{'0' if v=='seed' else 'let r=s*12+d*20+if a{t*7}else{0};let c=t*48;r.min(c)+(r-c).max(0)*6+(r/37)*10'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let s=v.short_sensors*12;let d=v.deep_sensors*20;let a=if v.ash_warning{{v.relay_towers*7}}else{{0}};let r=s+d+a;let c=v.relay_towers*48;let b=(r-c).max(0);ResponseOutput{{sensor_total:v.short_sensors+v.deep_sensors,short_scan_seconds:s,deep_scan_seconds:d,ash_sync_seconds:a,array_required_seconds:r,relay_capacity_seconds:c,processed_seconds:r.min(c),backlogged_seconds:b,scan_rounds:r/37,array_score:score(v.short_sensors,v.deep_sensors,v.relay_towers,v.ash_warning),array_state:if b==0{{"aligned"}}else if v.ash_warning{{"ash_backlog"}}else{{"routine_backlog"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_seismic_array_score(a:i64,b:i64,c:i64,d:i32)->i64{{score(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "museum_conservation_build": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub canvas_crates:i64,pub textile_crates:i64,pub work_tables:i64,pub emergency_drying:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.canvas_crates>=0&&self.textile_crates>=0&&self.work_tables>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub crate_total:i64,pub canvas_work_minutes:i64,pub textile_work_minutes:i64,pub drying_setup_minutes:i64,pub conservation_required_minutes:i64,pub table_capacity_minutes:i64,pub completed_minutes:i64,pub deferred_minutes:i64,pub conservation_rounds:i64,pub conservation_score:i64,pub conservation_state:String}}pub fn score(c:i64,t:i64,w:i64,e:bool)->i64{{{'0' if v=='seed' else 'let r=c*9+t*15+if e{w*6}else{0};let x=w*43;r.min(x)+(r-x).max(0)*7+(r/34)*11'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let c=v.canvas_crates*9;let t=v.textile_crates*15;let d=if v.emergency_drying{{v.work_tables*6}}else{{0}};let r=c+t+d;let x=v.work_tables*43;let q=(r-x).max(0);ResponseOutput{{crate_total:v.canvas_crates+v.textile_crates,canvas_work_minutes:c,textile_work_minutes:t,drying_setup_minutes:d,conservation_required_minutes:r,table_capacity_minutes:x,completed_minutes:r.min(x),deferred_minutes:q,conservation_rounds:r/34,conservation_score:score(v.canvas_crates,v.textile_crates,v.work_tables,v.emergency_drying),conservation_state:if q==0{{"preserved"}}else if v.emergency_drying{{"emergency_queue"}}else{{"routine_queue"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_museum_conservation_score(a:i64,b:i64,c:i64,d:i32)->i64{{score(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "canal_lock_repair": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub freight_barges:i64,pub tour_barges:i64,pub lock_chambers:i64,pub flood_protocol:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.freight_barges>=0&&self.tour_barges>=0&&self.lock_chambers>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub barge_total:i64,pub freight_lock_units:i64,pub tour_lock_units:i64,pub flood_lock_units:i64,pub lock_required_units:i64,pub lock_capacity_units:i64,pub passed_lock_units:i64,pub held_lock_units:i64,pub clearance_units:i64,pub canal_state:String}}pub fn clearance(f:i64,t:i64,c:i64,p:bool)->i64{{let r=f*10+t*17+if {'!p' if v=='seed' else 'p'}{{c*8}}else{{0}};(c*45-r.min(c*45)).max(0)}}pub fn handle(v:RequestInput)->ResponseOutput{{let f=v.freight_barges*10;let t=v.tour_barges*17;let p=if v.flood_protocol{{v.lock_chambers*8}}else{{0}};let r=f+t+p;let c=v.lock_chambers*45;let h=(r-c).max(0);ResponseOutput{{barge_total:v.freight_barges+v.tour_barges,freight_lock_units:f,tour_lock_units:t,flood_lock_units:p,lock_required_units:r,lock_capacity_units:c,passed_lock_units:r.min(c),held_lock_units:h,clearance_units:clearance(v.freight_barges,v.tour_barges,v.lock_chambers,v.flood_protocol),canal_state:if h==0{{"clear"}}else if v.flood_protocol{{"flood_hold"}}else{{"routine_hold"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_canal_clearance_units(a:i64,b:i64,c:i64,d:i32)->i64{{clearance(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "thermal_greenhouse_repair": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub seedling_rows:i64,pub fruit_rows:i64,pub heat_pumps:i64,pub frost_cycle:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.seedling_rows>=0&&self.fruit_rows>=0&&self.heat_pumps>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub row_total:i64,pub seedling_heat_units:i64,pub fruit_heat_units:i64,pub frost_heat_units:i64,pub heat_required_units:i64,pub pump_capacity_units:i64,pub delivered_heat_units:i64,pub heat_deficit_units:i64,pub heat_reserve_units:i64,pub heating_cycles:i64,pub greenhouse_score:i64,pub greenhouse_state:String}}pub fn score(s:i64,f:i64,p:i64,c:bool)->i64{{let r=s*8+f*14+if c{{p*5}}else{{0}};let x=p*41;r.min(x)+(r-x).max(0)*5+(r/{'23' if v=='seed' else '29'})*7}}pub fn handle(v:RequestInput)->ResponseOutput{{let s=v.seedling_rows*8;let f=v.fruit_rows*14;let c=if v.frost_cycle{{v.heat_pumps*5}}else{{0}};let r=s+f+c;let p=v.heat_pumps*41;let d=(r-p).max(0);let delivered=r.min(p);ResponseOutput{{row_total:v.seedling_rows+v.fruit_rows,seedling_heat_units:s,fruit_heat_units:f,frost_heat_units:c,heat_required_units:r,pump_capacity_units:p,delivered_heat_units:delivered,heat_deficit_units:d,heat_reserve_units:(p-delivered).max(0),heating_cycles:r/29,greenhouse_score:score(v.seedling_rows,v.fruit_rows,v.heat_pumps,v.frost_cycle),greenhouse_state:if d==0{{"balanced"}}else if v.frost_cycle{{"frost_shortage"}}else{{"heat_shortage"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_thermal_greenhouse_score(a:i64,b:i64,c:i64,d:i32)->i64{{score(a,b,c,d!=0)}}""" for v in ('seed','reference')},
}

RUST_WASM = {
    "seismic_array_build": ("parley_seismic_array_score", ["a", "b", "c", "d ? 1 : 0"]),
    "museum_conservation_build": ("parley_museum_conservation_score", ["a", "b", "c", "d ? 1 : 0"]),
    "canal_lock_repair": ("parley_canal_clearance_units", ["a", "b", "c", "d ? 1 : 0"]),
    "thermal_greenhouse_repair": ("parley_thermal_greenhouse_score", ["a", "b", "c", "d ? 1 : 0"]),
}
