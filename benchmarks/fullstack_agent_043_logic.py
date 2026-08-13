"""Frozen task-specific reference and seed logic for full-stack study 043."""

PARLEY_LOGIC = {
    "wildfire_drone_build": {
        "seed": """
to wildfire_mission_score with scout_drones as number, cargo_drones as number, launch_pads as number, night_mission as yesno giving number:
    give back 0
""",
        "reference": """
to wildfire_mission_score with scout_drones as number, cargo_drones as number, launch_pads as number, night_mission as yesno giving number:
    let required be scout_drones times 13 plus cargo_drones times 21
    if night_mission:
        set required to required plus launch_pads times 8
    let capacity be launch_pads times 50
    let completed be required
    if completed is more than capacity:
        set completed to capacity
    let delayed be required minus capacity
    if delayed is less than 0:
        set delayed to 0
    let waves be number from (required divided by 40)
    give back completed plus delayed times 6 plus waves times 9
""",
    },
    "satellite_uplink_build": {
        "seed": """
to satellite_uplink_score with science_packets as number, navigation_packets as number, ground_antennas as number, solar_interference as yesno giving number:
    give back 0
""",
        "reference": """
to satellite_uplink_score with science_packets as number, navigation_packets as number, ground_antennas as number, solar_interference as yesno giving number:
    let required be science_packets times 6 plus navigation_packets times 10
    if solar_interference:
        set required to required plus ground_antennas times 7
    let capacity be ground_antennas times 44
    let sent be required
    if sent is more than capacity:
        set sent to capacity
    let queued be required minus capacity
    if queued is less than 0:
        set queued to 0
    let windows be number from (required divided by 25)
    give back sent plus queued times 7 plus windows times 12
""",
    },
    "alpine_gondola_repair": {
        "seed": """
to gondola_lift_margin with passenger_groups as number, supply_crates as number, gondola_cabins as number, express_service as yesno giving number:
    let required be passenger_groups times 13 plus supply_crates times 8
    if express_service:
        set required to required plus gondola_cabins times 5
    let capacity be gondola_cabins times 42
    let carried be required
    if carried is more than capacity:
        set carried to capacity
    give back capacity minus carried
""",
        "reference": """
to gondola_lift_margin with passenger_groups as number, supply_crates as number, gondola_cabins as number, express_service as yesno giving number:
    let required be passenger_groups times 8 plus supply_crates times 13
    if express_service:
        set required to required plus gondola_cabins times 5
    let capacity be gondola_cabins times 42
    let carried be required
    if carried is more than capacity:
        set carried to capacity
    give back capacity minus carried
""",
    },
    "kelp_hatchery_repair": {
        "seed": """
to hatchery_oxygen_delivered with juvenile_tanks as number, mature_tanks as number, aerators as number, heat_treatment as yesno giving number:
    let needed be juvenile_tanks times 9 plus mature_tanks times 16
    if heat_treatment:
        set needed to needed plus aerators times 4
    let capacity be aerators times 38
    let delivered be needed
    if capacity is more than delivered:
        set delivered to capacity
    give back delivered
""",
        "reference": """
to hatchery_oxygen_delivered with juvenile_tanks as number, mature_tanks as number, aerators as number, heat_treatment as yesno giving number:
    let needed be juvenile_tanks times 9 plus mature_tanks times 16
    if heat_treatment:
        set needed to needed plus aerators times 4
    let capacity be aerators times 38
    let delivered be needed
    if delivered is more than capacity:
        set delivered to capacity
    give back delivered
""",
    },
}

PARLEY_MAIN = {
    "wildfire_drone_build": """
include "logic.par"
a wildfire_request has scout_drones as number, cargo_drones as number, launch_pads as number, night_mission as yesno
a wildfire_response has drone_total as number, scout_flight_minutes as number, cargo_flight_minutes as number, night_setup_minutes as number, mission_load_minutes as number, launch_capacity_minutes as number, completed_flight_minutes as number, delayed_flight_minutes as number, flight_waves as number, wildfire_score as number, wildfire_mode as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Wildfire Drone", ready yes
to handle_request with request as wildfire_request giving wildfire_response:
    let scout be request's scout_drones times 13
    let cargo be request's cargo_drones times 21
    let night be 0
    if request's night_mission:
        set night to request's launch_pads times 8
    let required be scout plus cargo plus night
    let capacity be request's launch_pads times 50
    let completed be required
    if completed is more than capacity:
        set completed to capacity
    let delayed be required minus capacity
    if delayed is less than 0:
        set delayed to 0
    let waves be number from (required divided by 40)
    let mode be "ready"
    if delayed is more than 0:
        set mode to "day_delay"
        if request's night_mission:
            set mode to "night_delay"
    give back a wildfire_response with drone_total (request's scout_drones plus request's cargo_drones), scout_flight_minutes scout, cargo_flight_minutes cargo, night_setup_minutes night, mission_load_minutes required, launch_capacity_minutes capacity, completed_flight_minutes completed, delayed_flight_minutes delayed, flight_waves waves, wildfire_score (wildfire_mission_score with request's scout_drones, request's cargo_drones, request's launch_pads, request's night_mission), wildfire_mode mode
""",
    "satellite_uplink_build": """
include "logic.par"
a uplink_request has science_packets as number, navigation_packets as number, ground_antennas as number, solar_interference as yesno
a uplink_response has uplink_packet_total as number, science_transmit_seconds as number, navigation_transmit_seconds as number, interference_seconds as number, transmit_seconds as number, antenna_capacity_seconds as number, sent_seconds as number, queued_seconds as number, transmission_windows as number, uplink_score as number, uplink_mode as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Satellite Uplink", ready yes
to handle_request with request as uplink_request giving uplink_response:
    let science be request's science_packets times 6
    let navigation be request's navigation_packets times 10
    let interference be 0
    if request's solar_interference:
        set interference to request's ground_antennas times 7
    let required be science plus navigation plus interference
    let capacity be request's ground_antennas times 44
    let sent be required
    if sent is more than capacity:
        set sent to capacity
    let queued be required minus capacity
    if queued is less than 0:
        set queued to 0
    let windows be number from (required divided by 25)
    let mode be "synchronized"
    if queued is more than 0:
        set mode to "routine_queue"
        if request's solar_interference:
            set mode to "solar_queue"
    give back a uplink_response with uplink_packet_total (request's science_packets plus request's navigation_packets), science_transmit_seconds science, navigation_transmit_seconds navigation, interference_seconds interference, transmit_seconds required, antenna_capacity_seconds capacity, sent_seconds sent, queued_seconds queued, transmission_windows windows, uplink_score (satellite_uplink_score with request's science_packets, request's navigation_packets, request's ground_antennas, request's solar_interference), uplink_mode mode
""",
    "alpine_gondola_repair": """
include "logic.par"
a gondola_request has passenger_groups as number, supply_crates as number, gondola_cabins as number, express_service as yesno
a gondola_response has gondola_item_total as number, rider_load_units as number, freight_load_units as number, express_load_units as number, gondola_required_units as number, gondola_capacity_units as number, carried_load_units as number, stranded_load_units as number, lift_margin_units as number, gondola_condition as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Alpine Gondola", ready yes
to handle_request with request as gondola_request giving gondola_response:
    let rider be request's passenger_groups times 8
    let freight be request's supply_crates times 13
    let express be 0
    if request's express_service:
        set express to request's gondola_cabins times 5
    let required be rider plus freight plus express
    let capacity be request's gondola_cabins times 42
    let carried be required
    if carried is more than capacity:
        set carried to capacity
    let stranded be required minus capacity
    if stranded is less than 0:
        set stranded to 0
    let condition be "clear"
    if stranded is more than 0:
        set condition to "standard_stranded"
        if request's express_service:
            set condition to "express_stranded"
    give back a gondola_response with gondola_item_total (request's passenger_groups plus request's supply_crates), rider_load_units rider, freight_load_units freight, express_load_units express, gondola_required_units required, gondola_capacity_units capacity, carried_load_units carried, stranded_load_units stranded, lift_margin_units (gondola_lift_margin with request's passenger_groups, request's supply_crates, request's gondola_cabins, request's express_service), gondola_condition condition
""",
    "kelp_hatchery_repair": """
include "logic.par"
a hatchery_request has juvenile_tanks as number, mature_tanks as number, aerators as number, heat_treatment as yesno
a hatchery_response has hatchery_tank_total as number, juvenile_oxygen_units as number, mature_oxygen_units as number, treatment_oxygen_units as number, oxygen_needed_units as number, aeration_capacity_units as number, oxygen_delivered_units as number, oxygen_deficit_units as number, oxygen_buffer_units as number, hatchery_condition as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Kelp Hatchery", ready yes
to handle_request with request as hatchery_request giving hatchery_response:
    let juvenile be request's juvenile_tanks times 9
    let mature be request's mature_tanks times 16
    let treatment be 0
    if request's heat_treatment:
        set treatment to request's aerators times 4
    let needed be juvenile plus mature plus treatment
    let capacity be request's aerators times 38
    let delivered be (hatchery_oxygen_delivered with request's juvenile_tanks, request's mature_tanks, request's aerators, request's heat_treatment)
    let deficit be needed minus capacity
    if deficit is less than 0:
        set deficit to 0
    let buffer be capacity minus delivered
    if buffer is less than 0:
        set buffer to 0
    let condition be "balanced"
    if deficit is more than 0:
        set condition to "oxygen_shortage"
        if request's heat_treatment:
            set condition to "heat_shortage"
    give back a hatchery_response with hatchery_tank_total (request's juvenile_tanks plus request's mature_tanks), juvenile_oxygen_units juvenile, mature_oxygen_units mature, treatment_oxygen_units treatment, oxygen_needed_units needed, aeration_capacity_units capacity, oxygen_delivered_units delivered, oxygen_deficit_units deficit, oxygen_buffer_units buffer, hatchery_condition condition
""",
}

PYTHON_LOGIC = {
    "wildfire_drone_build": {v: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); scout_drones:int=Field(ge=0); cargo_drones:int=Field(ge=0); launch_pads:int=Field(ge=0); night_mission:bool
def wildfire_mission_score(s:int,c:int,p:int,n:bool)->int: {'return 0' if v=='seed' else 'r=s*13+c*21+(p*8 if n else 0); x=p*50; return min(r,x)+max(r-x,0)*6+(r//40)*9'}
def handle(v:RequestInput)->dict[str,object]:
 s=v.scout_drones*13; c=v.cargo_drones*21; n=v.launch_pads*8 if v.night_mission else 0; r=s+c+n; x=v.launch_pads*50; d=max(r-x,0)
 return {{'drone_total':v.scout_drones+v.cargo_drones,'scout_flight_minutes':s,'cargo_flight_minutes':c,'night_setup_minutes':n,'mission_load_minutes':r,'launch_capacity_minutes':x,'completed_flight_minutes':min(r,x),'delayed_flight_minutes':d,'flight_waves':r//40,'wildfire_score':wildfire_mission_score(v.scout_drones,v.cargo_drones,v.launch_pads,v.night_mission),'wildfire_mode':'ready' if d==0 else 'night_delay' if v.night_mission else 'day_delay'}}
""" for v in ('seed','reference')},
    "satellite_uplink_build": {v: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); science_packets:int=Field(ge=0); navigation_packets:int=Field(ge=0); ground_antennas:int=Field(ge=0); solar_interference:bool
def satellite_uplink_score(s:int,n:int,a:int,i:bool)->int: {'return 0' if v=='seed' else 'r=s*6+n*10+(a*7 if i else 0); x=a*44; return min(r,x)+max(r-x,0)*7+(r//25)*12'}
def handle(v:RequestInput)->dict[str,object]:
 s=v.science_packets*6; n=v.navigation_packets*10; i=v.ground_antennas*7 if v.solar_interference else 0; r=s+n+i; x=v.ground_antennas*44; q=max(r-x,0)
 return {{'uplink_packet_total':v.science_packets+v.navigation_packets,'science_transmit_seconds':s,'navigation_transmit_seconds':n,'interference_seconds':i,'transmit_seconds':r,'antenna_capacity_seconds':x,'sent_seconds':min(r,x),'queued_seconds':q,'transmission_windows':r//25,'uplink_score':satellite_uplink_score(v.science_packets,v.navigation_packets,v.ground_antennas,v.solar_interference),'uplink_mode':'synchronized' if q==0 else 'solar_queue' if v.solar_interference else 'routine_queue'}}
""" for v in ('seed','reference')},
    "alpine_gondola_repair": {v: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); passenger_groups:int=Field(ge=0); supply_crates:int=Field(ge=0); gondola_cabins:int=Field(ge=0); express_service:bool
def gondola_lift_margin(p:int,s:int,c:int,e:bool)->int:
 r={'p*13+s*8' if v=='seed' else 'p*8+s*13'}+(c*5 if e else 0); return max(c*42-min(r,c*42),0)
def handle(v:RequestInput)->dict[str,object]:
 p=v.passenger_groups*8; s=v.supply_crates*13; e=v.gondola_cabins*5 if v.express_service else 0; r=p+s+e; c=v.gondola_cabins*42; d=max(r-c,0)
 return {{'gondola_item_total':v.passenger_groups+v.supply_crates,'rider_load_units':p,'freight_load_units':s,'express_load_units':e,'gondola_required_units':r,'gondola_capacity_units':c,'carried_load_units':min(r,c),'stranded_load_units':d,'lift_margin_units':gondola_lift_margin(v.passenger_groups,v.supply_crates,v.gondola_cabins,v.express_service),'gondola_condition':'clear' if d==0 else 'express_stranded' if v.express_service else 'standard_stranded'}}
""" for v in ('seed','reference')},
    "kelp_hatchery_repair": {v: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); juvenile_tanks:int=Field(ge=0); mature_tanks:int=Field(ge=0); aerators:int=Field(ge=0); heat_treatment:bool
def hatchery_oxygen_delivered(j:int,m:int,a:int,h:bool)->int:
 n=j*9+m*16+(a*4 if h else 0); return {'max(n,a*38)' if v=='seed' else 'min(n,a*38)'}
def handle(v:RequestInput)->dict[str,object]:
 j=v.juvenile_tanks*9; m=v.mature_tanks*16; t=v.aerators*4 if v.heat_treatment else 0; n=j+m+t; c=v.aerators*38; d=hatchery_oxygen_delivered(v.juvenile_tanks,v.mature_tanks,v.aerators,v.heat_treatment); x=max(n-c,0)
 return {{'hatchery_tank_total':v.juvenile_tanks+v.mature_tanks,'juvenile_oxygen_units':j,'mature_oxygen_units':m,'treatment_oxygen_units':t,'oxygen_needed_units':n,'aeration_capacity_units':c,'oxygen_delivered_units':d,'oxygen_deficit_units':x,'oxygen_buffer_units':max(c-d,0),'hatchery_condition':'balanced' if x==0 else 'heat_shortage' if v.heat_treatment else 'oxygen_shortage'}}
""" for v in ('seed','reference')},
}

PYTHON_BROWSER = {
    "wildfire_drone_build": {"seed": "const wildfireMissionScore=()=>0n;", "reference": "const wildfireMissionScore=(s,c,p,n)=>{const r=s*13+c*21+(n?p*8:0),x=p*50;return BigInt(Math.min(r,x)+Math.max(r-x,0)*6+Math.trunc(r/40)*9);};"},
    "satellite_uplink_build": {"seed": "const satelliteUplinkScore=()=>0n;", "reference": "const satelliteUplinkScore=(s,n,a,i)=>{const r=s*6+n*10+(i?a*7:0),x=a*44;return BigInt(Math.min(r,x)+Math.max(r-x,0)*7+Math.trunc(r/25)*12);};"},
    "alpine_gondola_repair": {"seed": "const gondolaLiftMargin=(p,s,c,e)=>{const r=p*13+s*8+(e?c*5:0);return BigInt(Math.max(c*42-Math.min(r,c*42),0));};", "reference": "const gondolaLiftMargin=(p,s,c,e)=>{const r=p*8+s*13+(e?c*5:0);return BigInt(Math.max(c*42-Math.min(r,c*42),0));};"},
    "kelp_hatchery_repair": {"seed": "const hatcheryOxygenDelivered=(j,m,a,h)=>BigInt(Math.max(j*9+m*16+(h?a*4:0),a*38));", "reference": "const hatcheryOxygenDelivered=(j,m,a,h)=>BigInt(Math.min(j*9+m*16+(h?a*4:0),a*38));"},
}

PYTHON_BROWSER_EXPORT = {
    "wildfire_drone_build": ("wildfire_mission_score", "wildfireMissionScore"),
    "satellite_uplink_build": ("satellite_uplink_score", "satelliteUplinkScore"),
    "alpine_gondola_repair": ("gondola_lift_margin", "gondolaLiftMargin"),
    "kelp_hatchery_repair": ("hatchery_oxygen_delivered", "hatcheryOxygenDelivered"),
}

TYPESCRIPT_LOGIC = {
    "wildfire_drone_build": {v: f"""export type RequestInput={{scout_drones:number;cargo_drones:number;launch_pads:number;night_mission:boolean}};export const score=(s:number,c:number,p:number,n:boolean)=>{{{'return 0' if v=='seed' else 'const r=s*13+c*21+(n?p*8:0),x=p*50;return Math.min(r,x)+Math.max(r-x,0)*6+Math.trunc(r/40)*9'}}};export const handle=(v:RequestInput)=>{{const s=v.scout_drones*13,c=v.cargo_drones*21,n=v.night_mission?v.launch_pads*8:0,r=s+c+n,x=v.launch_pads*50,d=Math.max(r-x,0);return {{drone_total:v.scout_drones+v.cargo_drones,scout_flight_minutes:s,cargo_flight_minutes:c,night_setup_minutes:n,mission_load_minutes:r,launch_capacity_minutes:x,completed_flight_minutes:Math.min(r,x),delayed_flight_minutes:d,flight_waves:Math.trunc(r/40),wildfire_score:score(v.scout_drones,v.cargo_drones,v.launch_pads,v.night_mission),wildfire_mode:d===0?'ready':v.night_mission?'night_delay':'day_delay'}}}};export async function loadParley(){{return {{wildfire_mission_score:(a:number,b:number,c:number,d:boolean)=>BigInt(score(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "satellite_uplink_build": {v: f"""export type RequestInput={{science_packets:number;navigation_packets:number;ground_antennas:number;solar_interference:boolean}};export const score=(s:number,n:number,a:number,i:boolean)=>{{{'return 0' if v=='seed' else 'const r=s*6+n*10+(i?a*7:0),x=a*44;return Math.min(r,x)+Math.max(r-x,0)*7+Math.trunc(r/25)*12'}}};export const handle=(v:RequestInput)=>{{const s=v.science_packets*6,n=v.navigation_packets*10,i=v.solar_interference?v.ground_antennas*7:0,r=s+n+i,x=v.ground_antennas*44,q=Math.max(r-x,0);return {{uplink_packet_total:v.science_packets+v.navigation_packets,science_transmit_seconds:s,navigation_transmit_seconds:n,interference_seconds:i,transmit_seconds:r,antenna_capacity_seconds:x,sent_seconds:Math.min(r,x),queued_seconds:q,transmission_windows:Math.trunc(r/25),uplink_score:score(v.science_packets,v.navigation_packets,v.ground_antennas,v.solar_interference),uplink_mode:q===0?'synchronized':v.solar_interference?'solar_queue':'routine_queue'}}}};export async function loadParley(){{return {{satellite_uplink_score:(a:number,b:number,c:number,d:boolean)=>BigInt(score(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "alpine_gondola_repair": {v: f"""export type RequestInput={{passenger_groups:number;supply_crates:number;gondola_cabins:number;express_service:boolean}};export const margin=(p:number,s:number,c:number,e:boolean)=>{{const r={'p*13+s*8' if v=='seed' else 'p*8+s*13'}+(e?c*5:0);return Math.max(c*42-Math.min(r,c*42),0)}};export const handle=(v:RequestInput)=>{{const p=v.passenger_groups*8,s=v.supply_crates*13,e=v.express_service?v.gondola_cabins*5:0,r=p+s+e,c=v.gondola_cabins*42,d=Math.max(r-c,0);return {{gondola_item_total:v.passenger_groups+v.supply_crates,rider_load_units:p,freight_load_units:s,express_load_units:e,gondola_required_units:r,gondola_capacity_units:c,carried_load_units:Math.min(r,c),stranded_load_units:d,lift_margin_units:margin(v.passenger_groups,v.supply_crates,v.gondola_cabins,v.express_service),gondola_condition:d===0?'clear':v.express_service?'express_stranded':'standard_stranded'}}}};export async function loadParley(){{return {{gondola_lift_margin:(a:number,b:number,c:number,d:boolean)=>BigInt(margin(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "kelp_hatchery_repair": {v: f"""export type RequestInput={{juvenile_tanks:number;mature_tanks:number;aerators:number;heat_treatment:boolean}};export const delivered=(j:number,m:number,a:number,h:boolean)=>Math.{'max' if v=='seed' else 'min'}(j*9+m*16+(h?a*4:0),a*38);export const handle=(v:RequestInput)=>{{const j=v.juvenile_tanks*9,m=v.mature_tanks*16,t=v.heat_treatment?v.aerators*4:0,n=j+m+t,c=v.aerators*38,d=delivered(v.juvenile_tanks,v.mature_tanks,v.aerators,v.heat_treatment),x=Math.max(n-c,0);return {{hatchery_tank_total:v.juvenile_tanks+v.mature_tanks,juvenile_oxygen_units:j,mature_oxygen_units:m,treatment_oxygen_units:t,oxygen_needed_units:n,aeration_capacity_units:c,oxygen_delivered_units:d,oxygen_deficit_units:x,oxygen_buffer_units:Math.max(c-d,0),hatchery_condition:x===0?'balanced':v.heat_treatment?'heat_shortage':'oxygen_shortage'}}}};export async function loadParley(){{return {{hatchery_oxygen_delivered:(a:number,b:number,c:number,d:boolean)=>BigInt(delivered(a,b,c,d))}}}}""" for v in ('seed','reference')},
}

TS_SCHEMA = {
    "wildfire_drone_build": "z.object({ scout_drones:z.number().int().nonnegative(), cargo_drones:z.number().int().nonnegative(), launch_pads:z.number().int().nonnegative(), night_mission:z.boolean() }).strict()",
    "satellite_uplink_build": "z.object({ science_packets:z.number().int().nonnegative(), navigation_packets:z.number().int().nonnegative(), ground_antennas:z.number().int().nonnegative(), solar_interference:z.boolean() }).strict()",
    "alpine_gondola_repair": "z.object({ passenger_groups:z.number().int().nonnegative(), supply_crates:z.number().int().nonnegative(), gondola_cabins:z.number().int().nonnegative(), express_service:z.boolean() }).strict()",
    "kelp_hatchery_repair": "z.object({ juvenile_tanks:z.number().int().nonnegative(), mature_tanks:z.number().int().nonnegative(), aerators:z.number().int().nonnegative(), heat_treatment:z.boolean() }).strict()",
}

RUST_LIB = {
    "wildfire_drone_build": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub scout_drones:i64,pub cargo_drones:i64,pub launch_pads:i64,pub night_mission:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.scout_drones>=0&&self.cargo_drones>=0&&self.launch_pads>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub drone_total:i64,pub scout_flight_minutes:i64,pub cargo_flight_minutes:i64,pub night_setup_minutes:i64,pub mission_load_minutes:i64,pub launch_capacity_minutes:i64,pub completed_flight_minutes:i64,pub delayed_flight_minutes:i64,pub flight_waves:i64,pub wildfire_score:i64,pub wildfire_mode:String}}pub fn score(s:i64,c:i64,p:i64,n:bool)->i64{{{'0' if v=='seed' else 'let r=s*13+c*21+if n{p*8}else{0};let x=p*50;r.min(x)+(r-x).max(0)*6+(r/40)*9'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let s=v.scout_drones*13;let c=v.cargo_drones*21;let n=if v.night_mission{{v.launch_pads*8}}else{{0}};let r=s+c+n;let x=v.launch_pads*50;let d=(r-x).max(0);ResponseOutput{{drone_total:v.scout_drones+v.cargo_drones,scout_flight_minutes:s,cargo_flight_minutes:c,night_setup_minutes:n,mission_load_minutes:r,launch_capacity_minutes:x,completed_flight_minutes:r.min(x),delayed_flight_minutes:d,flight_waves:r/40,wildfire_score:score(v.scout_drones,v.cargo_drones,v.launch_pads,v.night_mission),wildfire_mode:if d==0{{"ready"}}else if v.night_mission{{"night_delay"}}else{{"day_delay"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_wildfire_mission_score(a:i64,b:i64,c:i64,d:i32)->i64{{score(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "satellite_uplink_build": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub science_packets:i64,pub navigation_packets:i64,pub ground_antennas:i64,pub solar_interference:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.science_packets>=0&&self.navigation_packets>=0&&self.ground_antennas>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub uplink_packet_total:i64,pub science_transmit_seconds:i64,pub navigation_transmit_seconds:i64,pub interference_seconds:i64,pub transmit_seconds:i64,pub antenna_capacity_seconds:i64,pub sent_seconds:i64,pub queued_seconds:i64,pub transmission_windows:i64,pub uplink_score:i64,pub uplink_mode:String}}pub fn score(s:i64,n:i64,a:i64,i:bool)->i64{{{'0' if v=='seed' else 'let r=s*6+n*10+if i{a*7}else{0};let x=a*44;r.min(x)+(r-x).max(0)*7+(r/25)*12'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let s=v.science_packets*6;let n=v.navigation_packets*10;let i=if v.solar_interference{{v.ground_antennas*7}}else{{0}};let r=s+n+i;let x=v.ground_antennas*44;let q=(r-x).max(0);ResponseOutput{{uplink_packet_total:v.science_packets+v.navigation_packets,science_transmit_seconds:s,navigation_transmit_seconds:n,interference_seconds:i,transmit_seconds:r,antenna_capacity_seconds:x,sent_seconds:r.min(x),queued_seconds:q,transmission_windows:r/25,uplink_score:score(v.science_packets,v.navigation_packets,v.ground_antennas,v.solar_interference),uplink_mode:if q==0{{"synchronized"}}else if v.solar_interference{{"solar_queue"}}else{{"routine_queue"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_satellite_uplink_score(a:i64,b:i64,c:i64,d:i32)->i64{{score(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "alpine_gondola_repair": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub passenger_groups:i64,pub supply_crates:i64,pub gondola_cabins:i64,pub express_service:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.passenger_groups>=0&&self.supply_crates>=0&&self.gondola_cabins>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub gondola_item_total:i64,pub rider_load_units:i64,pub freight_load_units:i64,pub express_load_units:i64,pub gondola_required_units:i64,pub gondola_capacity_units:i64,pub carried_load_units:i64,pub stranded_load_units:i64,pub lift_margin_units:i64,pub gondola_condition:String}}pub fn margin(p:i64,s:i64,c:i64,e:bool)->i64{{let r={'p*13+s*8' if v=='seed' else 'p*8+s*13'}+if e{{c*5}}else{{0}};(c*42-r.min(c*42)).max(0)}}pub fn handle(v:RequestInput)->ResponseOutput{{let p=v.passenger_groups*8;let s=v.supply_crates*13;let e=if v.express_service{{v.gondola_cabins*5}}else{{0}};let r=p+s+e;let c=v.gondola_cabins*42;let d=(r-c).max(0);ResponseOutput{{gondola_item_total:v.passenger_groups+v.supply_crates,rider_load_units:p,freight_load_units:s,express_load_units:e,gondola_required_units:r,gondola_capacity_units:c,carried_load_units:r.min(c),stranded_load_units:d,lift_margin_units:margin(v.passenger_groups,v.supply_crates,v.gondola_cabins,v.express_service),gondola_condition:if d==0{{"clear"}}else if v.express_service{{"express_stranded"}}else{{"standard_stranded"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_gondola_lift_margin(a:i64,b:i64,c:i64,d:i32)->i64{{margin(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "kelp_hatchery_repair": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub juvenile_tanks:i64,pub mature_tanks:i64,pub aerators:i64,pub heat_treatment:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.juvenile_tanks>=0&&self.mature_tanks>=0&&self.aerators>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub hatchery_tank_total:i64,pub juvenile_oxygen_units:i64,pub mature_oxygen_units:i64,pub treatment_oxygen_units:i64,pub oxygen_needed_units:i64,pub aeration_capacity_units:i64,pub oxygen_delivered_units:i64,pub oxygen_deficit_units:i64,pub oxygen_buffer_units:i64,pub hatchery_condition:String}}pub fn delivered(j:i64,m:i64,a:i64,h:bool)->i64{{let n=j*9+m*16+if h{{a*4}}else{{0}};{'n.max(a*38)' if v=='seed' else 'n.min(a*38)'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let j=v.juvenile_tanks*9;let m=v.mature_tanks*16;let t=if v.heat_treatment{{v.aerators*4}}else{{0}};let n=j+m+t;let c=v.aerators*38;let d=delivered(v.juvenile_tanks,v.mature_tanks,v.aerators,v.heat_treatment);let x=(n-c).max(0);ResponseOutput{{hatchery_tank_total:v.juvenile_tanks+v.mature_tanks,juvenile_oxygen_units:j,mature_oxygen_units:m,treatment_oxygen_units:t,oxygen_needed_units:n,aeration_capacity_units:c,oxygen_delivered_units:d,oxygen_deficit_units:x,oxygen_buffer_units:(c-d).max(0),hatchery_condition:if x==0{{"balanced"}}else if v.heat_treatment{{"heat_shortage"}}else{{"oxygen_shortage"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_hatchery_oxygen_delivered(a:i64,b:i64,c:i64,d:i32)->i64{{delivered(a,b,c,d!=0)}}""" for v in ('seed','reference')},
}

RUST_WASM = {
    "wildfire_drone_build": ("parley_wildfire_mission_score", ["a", "b", "c", "d ? 1 : 0"]),
    "satellite_uplink_build": ("parley_satellite_uplink_score", ["a", "b", "c", "d ? 1 : 0"]),
    "alpine_gondola_repair": ("parley_gondola_lift_margin", ["a", "b", "c", "d ? 1 : 0"]),
    "kelp_hatchery_repair": ("parley_hatchery_oxygen_delivered", ["a", "b", "c", "d ? 1 : 0"]),
}
