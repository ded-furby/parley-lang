"""Frozen task-specific reference and seed logic for full-stack study 039."""

PARLEY_LOGIC = {
    "festival_power_build": {
        "seed": """
to festival_power_score with speaker_towers as number, watts_each as number, light_rigs as number, weather_cover as yesno giving number:
    give back 0
""",
        "reference": """
to festival_power_score with speaker_towers as number, watts_each as number, light_rigs as number, weather_cover as yesno giving number:
    let speaker_watts be speaker_towers multiplied by watts_each
    let lighting_watts be light_rigs multiplied by 900
    let weather_watts be 0
    if weather_cover:
        set weather_watts to (speaker_towers plus light_rigs) multiplied by 75
    let connection_points be speaker_towers multiplied by 3 plus light_rigs multiplied by 5
    give back speaker_watts plus lighting_watts plus weather_watts plus connection_points multiplied by 20
""",
    },
    "clinic_queue_build": {
        "seed": """
to waiting_groups with overflow_count as number giving number:
    give back 0
to clinic_queue_pressure with scheduled_count as number, walk_in_count as number, clinician_count as number, urgent_open as yesno giving number:
    give back 0
""",
        "reference": """
to waiting_groups with overflow_count as number giving number:
    give back number from ((overflow_count plus 4) divided by 5)
to clinic_queue_pressure with scheduled_count as number, walk_in_count as number, clinician_count as number, urgent_open as yesno giving number:
    let urgent_slots be 0
    if urgent_open:
        set urgent_slots to clinician_count multiplied by 2
    let overflow_count be scheduled_count plus walk_in_count minus (clinician_count multiplied by 8 plus urgent_slots)
    if overflow_count is less than 0:
        set overflow_count to 0
    give back overflow_count multiplied by 4 plus (waiting_groups with overflow_count) multiplied by 3
""",
    },
    "event_credit_repair": {
        "seed": """
to event_amount_due with full_price_guests as number, concession_guests as number, prepaid_credit_cents as number, weekend_event as yesno giving number:
    let base_charge be full_price_guests times 1800 plus concession_guests times 950
    let credit_used be prepaid_credit_cents
    if credit_used is more than base_charge:
        set credit_used to base_charge
    let weekend_fee be 0
    if weekend_event:
        set weekend_fee to (full_price_guests plus concession_guests) times 175
    let due be base_charge minus credit_used plus weekend_fee
    give back due
""",
        "reference": """
to event_amount_due with full_price_guests as number, concession_guests as number, prepaid_credit_cents as number, weekend_event as yesno giving number:
    let gross_charge be full_price_guests times 1800 plus concession_guests times 950
    if weekend_event:
        set gross_charge to gross_charge plus (full_price_guests plus concession_guests) times 175
    let due be gross_charge minus prepaid_credit_cents
    if due is less than 0:
        set due to 0
    give back due
""",
    },
    "seedling_dispatch_repair": {
        "seed": """
to seedling_overflow with tray_count as number, reserved_trays as number, van_count as number, chilled_transport as yesno giving number:
    let shippable be tray_count minus reserved_trays
    if shippable is less than 0:
        set shippable to 0
    let overflow be shippable minus van_count times 24
    if overflow is less than 0:
        set overflow to 0
    give back overflow
""",
        "reference": """
to seedling_overflow with tray_count as number, reserved_trays as number, van_count as number, chilled_transport as yesno giving number:
    let shippable be tray_count minus reserved_trays
    if shippable is less than 0:
        set shippable to 0
    let capacity be van_count times 24
    if chilled_transport:
        set capacity to capacity minus van_count times 3
    let overflow be shippable minus capacity
    if overflow is less than 0:
        set overflow to 0
    give back overflow
""",
    },
}

PARLEY_MAIN = {
    "festival_power_build": """
include "logic.par"
a festival_request has speaker_towers as number, watts_each as number, light_rigs as number, weather_cover as yesno
a festival_response has speaker_watts as number, lighting_watts as number, weather_watts as number, total_watts as number, connection_points as number, power_score as number, power_mode as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Festival Power", ready yes
to handle_request with request as festival_request giving festival_response:
    let speaker_watts be request's speaker_towers times request's watts_each
    let lighting_watts be request's light_rigs times 900
    let weather_watts be 0
    if request's weather_cover:
        set weather_watts to (request's speaker_towers plus request's light_rigs) times 75
    let total_watts be speaker_watts plus lighting_watts plus weather_watts
    let connection_points be request's speaker_towers times 3 plus request's light_rigs times 5
    let mode be "audio"
    if request's light_rigs is more than 0:
        set mode to "lighting"
        if request's speaker_towers is more than 0:
            set mode to "mixed"
    give back a festival_response with speaker_watts speaker_watts, lighting_watts lighting_watts, weather_watts weather_watts, total_watts total_watts, connection_points connection_points, power_score (festival_power_score with request's speaker_towers, request's watts_each, request's light_rigs, request's weather_cover), power_mode mode
""",
    "clinic_queue_build": """
include "logic.par"
a clinic_request has scheduled_count as number, walk_in_count as number, clinician_count as number, urgent_open as yesno
a clinic_response has patient_total as number, urgent_slots as number, service_slots as number, overflow_count as number, waiting_groups as number, queue_pressure as number, queue_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Clinic Queue", ready yes
to handle_request with request as clinic_request giving clinic_response:
    let patient_total be request's scheduled_count plus request's walk_in_count
    let urgent_slots be 0
    if request's urgent_open:
        set urgent_slots to request's clinician_count times 2
    let service_slots be request's clinician_count times 8 plus urgent_slots
    let overflow_count be patient_total minus service_slots
    if overflow_count is less than 0:
        set overflow_count to 0
    let groups be (waiting_groups with overflow_count)
    let state be "clear"
    if overflow_count is more than 0:
        set state to "delayed"
        if request's urgent_open:
            set state to "urgent"
    give back a clinic_response with patient_total patient_total, urgent_slots urgent_slots, service_slots service_slots, overflow_count overflow_count, waiting_groups groups, queue_pressure (clinic_queue_pressure with request's scheduled_count, request's walk_in_count, request's clinician_count, request's urgent_open), queue_state state
""",
    "event_credit_repair": """
include "logic.par"
an event_request has full_price_guests as number, concession_guests as number, prepaid_credit_cents as number, weekend_event as yesno
an event_response has full_price_charge_cents as number, concession_charge_cents as number, weekend_fee_cents as number, gross_charge_cents as number, credit_used_cents as number, amount_due_cents as number, payment_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Event Credit", ready yes
to handle_request with request as event_request giving event_response:
    let full_price be request's full_price_guests times 1800
    let concession be request's concession_guests times 950
    let weekend_fee be 0
    if request's weekend_event:
        set weekend_fee to (request's full_price_guests plus request's concession_guests) times 175
    let gross be full_price plus concession plus weekend_fee
    let credit_used be request's prepaid_credit_cents
    if credit_used is more than gross:
        set credit_used to gross
    let due be (event_amount_due with request's full_price_guests, request's concession_guests, request's prepaid_credit_cents, request's weekend_event)
    let state be "due"
    if due is 0:
        set state to "covered"
    give back an event_response with full_price_charge_cents full_price, concession_charge_cents concession, weekend_fee_cents weekend_fee, gross_charge_cents gross, credit_used_cents credit_used, amount_due_cents due, payment_state state
""",
    "seedling_dispatch_repair": """
include "logic.par"
a seedling_request has tray_count as number, reserved_trays as number, van_count as number, chilled_transport as yesno
a seedling_response has shippable_trays as number, base_capacity as number, chill_buffer as number, dispatch_capacity as number, overflow_trays as number, loaded_trays as number, space_remaining as number, dispatch_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Seedling Dispatch", ready yes
to handle_request with request as seedling_request giving seedling_response:
    let shippable be request's tray_count minus request's reserved_trays
    if shippable is less than 0:
        set shippable to 0
    let base_capacity be request's van_count times 24
    let chill_buffer be 0
    if request's chilled_transport:
        set chill_buffer to request's van_count times 3
    let capacity be base_capacity minus chill_buffer
    let overflow be (seedling_overflow with request's tray_count, request's reserved_trays, request's van_count, request's chilled_transport)
    let loaded be shippable
    if loaded is more than capacity:
        set loaded to capacity
    let remaining be capacity minus loaded
    let state be "idle"
    if loaded is more than 0:
        set state to "loaded"
    if overflow is more than 0:
        set state to "overflow"
    give back a seedling_response with shippable_trays shippable, base_capacity base_capacity, chill_buffer chill_buffer, dispatch_capacity capacity, overflow_trays overflow, loaded_trays loaded, space_remaining remaining, dispatch_state state
""",
}

PYTHON_LOGIC = {
    "festival_power_build": {
        variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    speaker_towers: int = Field(ge=0); watts_each: int = Field(ge=0); light_rigs: int = Field(ge=0); weather_cover: bool
def festival_power_score(s: int, w: int, l: int, cover: bool) -> int: return {'0' if variant == 'seed' else 's*w+l*900+((s+l)*75 if cover else 0)+(s*3+l*5)*20'}
def handle(v: RequestInput) -> dict[str, object]:
    speaker=v.speaker_towers*v.watts_each; lighting=v.light_rigs*900; weather=(v.speaker_towers+v.light_rigs)*75 if v.weather_cover else 0; points=v.speaker_towers*3+v.light_rigs*5
    return {{"speaker_watts":speaker,"lighting_watts":lighting,"weather_watts":weather,"total_watts":speaker+lighting+weather,"connection_points":points,"power_score":festival_power_score(v.speaker_towers,v.watts_each,v.light_rigs,v.weather_cover),"power_mode":"mixed" if v.speaker_towers and v.light_rigs else "lighting" if v.light_rigs else "audio"}}
""" for variant in ("seed", "reference")
    },
    "clinic_queue_build": {
        variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scheduled_count: int = Field(ge=0); walk_in_count: int = Field(ge=0); clinician_count: int = Field(ge=0); urgent_open: bool
def clinic_queue_pressure(s: int, w: int, c: int, urgent: bool) -> int: {'return 0' if variant == 'seed' else 'overflow=max(s+w-(c*8+(c*2 if urgent else 0)),0); return overflow*4+(overflow+4)//5*3'}
def handle(v: RequestInput) -> dict[str, object]:
    total=v.scheduled_count+v.walk_in_count; urgent_slots=v.clinician_count*2 if v.urgent_open else 0; slots=v.clinician_count*8+urgent_slots; overflow=max(total-slots,0); groups=(overflow+4)//5
    return {{"patient_total":total,"urgent_slots":urgent_slots,"service_slots":slots,"overflow_count":overflow,"waiting_groups":groups,"queue_pressure":clinic_queue_pressure(v.scheduled_count,v.walk_in_count,v.clinician_count,v.urgent_open),"queue_state":"clear" if overflow==0 else "urgent" if v.urgent_open else "delayed"}}
""" for variant in ("seed", "reference")
    },
    "event_credit_repair": {
        variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    full_price_guests: int = Field(ge=0); concession_guests: int = Field(ge=0); prepaid_credit_cents: int = Field(ge=0); weekend_event: bool
def event_amount_due(f: int, c: int, credit: int, weekend: bool) -> int:
    base=f*1800+c*950; fee=(f+c)*175 if weekend else 0
    return {'base-min(credit,base)+fee' if variant == 'seed' else 'max(base+fee-credit,0)'}
def handle(v: RequestInput) -> dict[str, object]:
    full=v.full_price_guests*1800; concession=v.concession_guests*950; fee=(v.full_price_guests+v.concession_guests)*175 if v.weekend_event else 0; gross=full+concession+fee; due=event_amount_due(v.full_price_guests,v.concession_guests,v.prepaid_credit_cents,v.weekend_event)
    return {{"full_price_charge_cents":full,"concession_charge_cents":concession,"weekend_fee_cents":fee,"gross_charge_cents":gross,"credit_used_cents":min(v.prepaid_credit_cents,gross),"amount_due_cents":due,"payment_state":"covered" if due==0 else "due"}}
""" for variant in ("seed", "reference")
    },
    "seedling_dispatch_repair": {
        variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tray_count: int = Field(ge=0); reserved_trays: int = Field(ge=0); van_count: int = Field(ge=0); chilled_transport: bool
def dispatch_capacity(vans: int, chilled: bool) -> int: return vans*24{'' if variant == 'seed' else '-(vans*3 if chilled else 0)'}
def handle(v: RequestInput) -> dict[str, object]:
    ship=max(v.tray_count-v.reserved_trays,0); base=v.van_count*24; buffer=v.van_count*3 if v.chilled_transport else 0; cap=dispatch_capacity(v.van_count,v.chilled_transport); overflow=max(ship-cap,0); loaded=min(ship,cap)
    return {{"shippable_trays":ship,"base_capacity":base,"chill_buffer":buffer,"dispatch_capacity":cap,"overflow_trays":overflow,"loaded_trays":loaded,"space_remaining":max(cap-loaded,0),"dispatch_state":"overflow" if overflow else "loaded" if loaded else "idle"}}
""" for variant in ("seed", "reference")
    },
}

PYTHON_BROWSER = {
    "festival_power_build": {
        "seed": "const festivalPowerScore=()=>0n;",
        "reference": "const festivalPowerScore=(s,w,l,c)=>BigInt(s*w+l*900+(c?(s+l)*75:0)+(s*3+l*5)*20);",
    },
    "clinic_queue_build": {
        "seed": "const clinicQueuePressure=()=>0n;",
        "reference": "const clinicQueuePressure=(s,w,c,u)=>{const o=Math.max(s+w-(c*8+(u?c*2:0)),0);return BigInt(o*4+Math.trunc((o+4)/5)*3);};",
    },
    "event_credit_repair": {
        "seed": "const eventAmountDue=(f,c,credit,w)=>{const b=f*1800+c*950;const fee=w?(f+c)*175:0;return BigInt(b-Math.min(credit,b)+fee);};",
        "reference": "const eventAmountDue=(f,c,credit,w)=>{const b=f*1800+c*950;const fee=w?(f+c)*175:0;return BigInt(Math.max(b+fee-credit,0));};",
    },
    "seedling_dispatch_repair": {
        "seed": "const seedlingOverflow=(t,r,v,c)=>BigInt(Math.max(Math.max(t-r,0)-v*24,0));",
        "reference": "const seedlingOverflow=(t,r,v,c)=>BigInt(Math.max(Math.max(t-r,0)-(v*24-(c?v*3:0)),0));",
    },
}

PYTHON_BROWSER_EXPORT = {
    "festival_power_build": ("festival_power_score", "festivalPowerScore"),
    "clinic_queue_build": ("clinic_queue_pressure", "clinicQueuePressure"),
    "event_credit_repair": ("event_amount_due", "eventAmountDue"),
    "seedling_dispatch_repair": ("seedling_overflow", "seedlingOverflow"),
}

TYPESCRIPT_LOGIC = {
    "festival_power_build": {variant: f"""export type RequestInput={{speaker_towers:number;watts_each:number;light_rigs:number;weather_cover:boolean}};
export const festivalPowerScore=(s:number,w:number,l:number,c:boolean)=>{'0' if variant == 'seed' else 's*w+l*900+(c?(s+l)*75:0)+(s*3+l*5)*20'};
export const handle=(v:RequestInput)=>{{const speaker=v.speaker_towers*v.watts_each,lighting=v.light_rigs*900,weather=v.weather_cover?(v.speaker_towers+v.light_rigs)*75:0,points=v.speaker_towers*3+v.light_rigs*5;return {{speaker_watts:speaker,lighting_watts:lighting,weather_watts:weather,total_watts:speaker+lighting+weather,connection_points:points,power_score:festivalPowerScore(v.speaker_towers,v.watts_each,v.light_rigs,v.weather_cover),power_mode:v.speaker_towers&&v.light_rigs?"mixed":v.light_rigs?"lighting":"audio"}};}};
export async function loadParley(){{return {{festival_power_score:(s:number,w:number,l:number,c:boolean)=>BigInt(festivalPowerScore(s,w,l,c))}};}}""" for variant in ("seed", "reference")},
    "clinic_queue_build": {
        "seed": """export type RequestInput={scheduled_count:number;walk_in_count:number;clinician_count:number;urgent_open:boolean};
export const clinicQueuePressure=(_s:number,_w:number,_c:number,_u:boolean)=>0;
export const handle=(v:RequestInput)=>{const total=v.scheduled_count+v.walk_in_count,urgent=v.urgent_open?v.clinician_count*2:0,slots=v.clinician_count*8+urgent,overflow=Math.max(total-slots,0),groups=Math.trunc((overflow+4)/5);return {patient_total:total,urgent_slots:urgent,service_slots:slots,overflow_count:overflow,waiting_groups:groups,queue_pressure:clinicQueuePressure(v.scheduled_count,v.walk_in_count,v.clinician_count,v.urgent_open),queue_state:overflow===0?"clear":v.urgent_open?"urgent":"delayed"};};
export async function loadParley(){return {clinic_queue_pressure:(s:number,w:number,c:number,u:boolean)=>BigInt(clinicQueuePressure(s,w,c,u))};}""",
        "reference": """export type RequestInput={scheduled_count:number;walk_in_count:number;clinician_count:number;urgent_open:boolean};
export const clinicQueuePressure=(s:number,w:number,c:number,u:boolean)=>{const o=Math.max(s+w-(c*8+(u?c*2:0)),0);return o*4+Math.trunc((o+4)/5)*3;};
export const handle=(v:RequestInput)=>{const total=v.scheduled_count+v.walk_in_count,urgent=v.urgent_open?v.clinician_count*2:0,slots=v.clinician_count*8+urgent,overflow=Math.max(total-slots,0),groups=Math.trunc((overflow+4)/5);return {patient_total:total,urgent_slots:urgent,service_slots:slots,overflow_count:overflow,waiting_groups:groups,queue_pressure:clinicQueuePressure(v.scheduled_count,v.walk_in_count,v.clinician_count,v.urgent_open),queue_state:overflow===0?"clear":v.urgent_open?"urgent":"delayed"};};
export async function loadParley(){return {clinic_queue_pressure:(s:number,w:number,c:number,u:boolean)=>BigInt(clinicQueuePressure(s,w,c,u))};}""",
    },
    "event_credit_repair": {variant: f"""export type RequestInput={{full_price_guests:number;concession_guests:number;prepaid_credit_cents:number;weekend_event:boolean}};
export const eventAmountDue=(f:number,c:number,credit:number,w:boolean)=>{{const base=f*1800+c*950,fee=w?(f+c)*175:0;return {'base-Math.min(credit,base)+fee' if variant == 'seed' else 'Math.max(base+fee-credit,0)'};}};
export const handle=(v:RequestInput)=>{{const full=v.full_price_guests*1800,concession=v.concession_guests*950,fee=v.weekend_event?(v.full_price_guests+v.concession_guests)*175:0,gross=full+concession+fee,due=eventAmountDue(v.full_price_guests,v.concession_guests,v.prepaid_credit_cents,v.weekend_event);return {{full_price_charge_cents:full,concession_charge_cents:concession,weekend_fee_cents:fee,gross_charge_cents:gross,credit_used_cents:Math.min(v.prepaid_credit_cents,gross),amount_due_cents:due,payment_state:due===0?"covered":"due"}};}};
export async function loadParley(){{return {{event_amount_due:(f:number,c:number,credit:number,w:boolean)=>BigInt(eventAmountDue(f,c,credit,w))}};}}""" for variant in ("seed", "reference")},
    "seedling_dispatch_repair": {variant: f"""export type RequestInput={{tray_count:number;reserved_trays:number;van_count:number;chilled_transport:boolean}};
export const dispatchCapacity=(v:number,c:boolean)=>{'v*24' if variant == 'seed' else 'v*24-(c?v*3:0)'};
export const seedlingOverflow=(t:number,r:number,v:number,c:boolean)=>Math.max(Math.max(t-r,0)-dispatchCapacity(v,c),0);
export const handle=(v:RequestInput)=>{{const ship=Math.max(v.tray_count-v.reserved_trays,0),base=v.van_count*24,buffer=v.chilled_transport?v.van_count*3:0,cap=dispatchCapacity(v.van_count,v.chilled_transport),overflow=Math.max(ship-cap,0),loaded=Math.min(ship,cap);return {{shippable_trays:ship,base_capacity:base,chill_buffer:buffer,dispatch_capacity:cap,overflow_trays:overflow,loaded_trays:loaded,space_remaining:Math.max(cap-loaded,0),dispatch_state:overflow?"overflow":loaded?"loaded":"idle"}};}};
export async function loadParley(){{return {{seedling_overflow:(t:number,r:number,v:number,c:boolean)=>BigInt(seedlingOverflow(t,r,v,c))}};}}""" for variant in ("seed", "reference")},
}

TS_SCHEMA = {
    "festival_power_build": "z.object({ speaker_towers:z.number().int().nonnegative(), watts_each:z.number().int().nonnegative(), light_rigs:z.number().int().nonnegative(), weather_cover:z.boolean() }).strict()",
    "clinic_queue_build": "z.object({ scheduled_count:z.number().int().nonnegative(), walk_in_count:z.number().int().nonnegative(), clinician_count:z.number().int().nonnegative(), urgent_open:z.boolean() }).strict()",
    "event_credit_repair": "z.object({ full_price_guests:z.number().int().nonnegative(), concession_guests:z.number().int().nonnegative(), prepaid_credit_cents:z.number().int().nonnegative(), weekend_event:z.boolean() }).strict()",
    "seedling_dispatch_repair": "z.object({ tray_count:z.number().int().nonnegative(), reserved_trays:z.number().int().nonnegative(), van_count:z.number().int().nonnegative(), chilled_transport:z.boolean() }).strict()",
}

RUST_LIB = {
    "festival_power_build": {variant: f"""use serde::{{Deserialize,Serialize}};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput{{pub speaker_towers:i64,pub watts_each:i64,pub light_rigs:i64,pub weather_cover:bool}} impl RequestInput{{pub fn valid(&self)->bool{{self.speaker_towers>=0&&self.watts_each>=0&&self.light_rigs>=0}}}}
#[derive(Serialize)] pub struct ResponseOutput{{pub speaker_watts:i64,pub lighting_watts:i64,pub weather_watts:i64,pub total_watts:i64,pub connection_points:i64,pub power_score:i64,pub power_mode:String}}
pub fn festival_power_score(s:i64,w:i64,l:i64,c:bool)->i64{{{'0' if variant == 'seed' else 's*w+l*900+if c{(s+l)*75}else{0}+(s*3+l*5)*20'}}}
pub fn handle(v:RequestInput)->ResponseOutput{{let speaker=v.speaker_towers*v.watts_each;let lighting=v.light_rigs*900;let weather=if v.weather_cover{{(v.speaker_towers+v.light_rigs)*75}}else{{0}};let points=v.speaker_towers*3+v.light_rigs*5;ResponseOutput{{speaker_watts:speaker,lighting_watts:lighting,weather_watts:weather,total_watts:speaker+lighting+weather,connection_points:points,power_score:festival_power_score(v.speaker_towers,v.watts_each,v.light_rigs,v.weather_cover),power_mode:if v.speaker_towers>0&&v.light_rigs>0{{"mixed"}}else if v.light_rigs>0{{"lighting"}}else{{"audio"}}.into()}}}}
#[unsafe(no_mangle)] pub extern "C" fn parley_festival_power_score(a:i64,b:i64,c:i64,d:i32)->i64{{festival_power_score(a,b,c,d!=0)}}""" for variant in ("seed", "reference")},
    "clinic_queue_build": {variant: f"""use serde::{{Deserialize,Serialize}};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput{{pub scheduled_count:i64,pub walk_in_count:i64,pub clinician_count:i64,pub urgent_open:bool}} impl RequestInput{{pub fn valid(&self)->bool{{self.scheduled_count>=0&&self.walk_in_count>=0&&self.clinician_count>=0}}}}
#[derive(Serialize)] pub struct ResponseOutput{{pub patient_total:i64,pub urgent_slots:i64,pub service_slots:i64,pub overflow_count:i64,pub waiting_groups:i64,pub queue_pressure:i64,pub queue_state:String}}
pub fn clinic_queue_pressure(s:i64,w:i64,c:i64,u:bool)->i64{{{'0' if variant == 'seed' else 'let o=(s+w-(c*8+if u{c*2}else{0})).max(0);o*4+(o+4)/5*3'}}}
pub fn handle(v:RequestInput)->ResponseOutput{{let total=v.scheduled_count+v.walk_in_count;let urgent=if v.urgent_open{{v.clinician_count*2}}else{{0}};let slots=v.clinician_count*8+urgent;let overflow=(total-slots).max(0);ResponseOutput{{patient_total:total,urgent_slots:urgent,service_slots:slots,overflow_count:overflow,waiting_groups:(overflow+4)/5,queue_pressure:clinic_queue_pressure(v.scheduled_count,v.walk_in_count,v.clinician_count,v.urgent_open),queue_state:if overflow==0{{"clear"}}else if v.urgent_open{{"urgent"}}else{{"delayed"}}.into()}}}}
#[unsafe(no_mangle)] pub extern "C" fn parley_clinic_queue_pressure(a:i64,b:i64,c:i64,d:i32)->i64{{clinic_queue_pressure(a,b,c,d!=0)}}""" for variant in ("seed", "reference")},
    "event_credit_repair": {variant: f"""use serde::{{Deserialize,Serialize}};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput{{pub full_price_guests:i64,pub concession_guests:i64,pub prepaid_credit_cents:i64,pub weekend_event:bool}} impl RequestInput{{pub fn valid(&self)->bool{{self.full_price_guests>=0&&self.concession_guests>=0&&self.prepaid_credit_cents>=0}}}}
#[derive(Serialize)] pub struct ResponseOutput{{pub full_price_charge_cents:i64,pub concession_charge_cents:i64,pub weekend_fee_cents:i64,pub gross_charge_cents:i64,pub credit_used_cents:i64,pub amount_due_cents:i64,pub payment_state:String}}
pub fn event_amount_due(f:i64,c:i64,credit:i64,w:bool)->i64{{let base=f*1800+c*950;let fee=if w{{(f+c)*175}}else{{0}};{'base-credit.min(base)+fee' if variant == 'seed' else '(base+fee-credit).max(0)'}}}
pub fn handle(v:RequestInput)->ResponseOutput{{let full=v.full_price_guests*1800;let concession=v.concession_guests*950;let fee=if v.weekend_event{{(v.full_price_guests+v.concession_guests)*175}}else{{0}};let gross=full+concession+fee;let due=event_amount_due(v.full_price_guests,v.concession_guests,v.prepaid_credit_cents,v.weekend_event);ResponseOutput{{full_price_charge_cents:full,concession_charge_cents:concession,weekend_fee_cents:fee,gross_charge_cents:gross,credit_used_cents:v.prepaid_credit_cents.min(gross),amount_due_cents:due,payment_state:if due==0{{"covered"}}else{{"due"}}.into()}}}}
#[unsafe(no_mangle)] pub extern "C" fn parley_event_amount_due(a:i64,b:i64,c:i64,d:i32)->i64{{event_amount_due(a,b,c,d!=0)}}""" for variant in ("seed", "reference")},
    "seedling_dispatch_repair": {variant: f"""use serde::{{Deserialize,Serialize}};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput{{pub tray_count:i64,pub reserved_trays:i64,pub van_count:i64,pub chilled_transport:bool}} impl RequestInput{{pub fn valid(&self)->bool{{self.tray_count>=0&&self.reserved_trays>=0&&self.van_count>=0}}}}
#[derive(Serialize)] pub struct ResponseOutput{{pub shippable_trays:i64,pub base_capacity:i64,pub chill_buffer:i64,pub dispatch_capacity:i64,pub overflow_trays:i64,pub loaded_trays:i64,pub space_remaining:i64,pub dispatch_state:String}}
pub fn dispatch_capacity(v:i64,c:bool)->i64{{{'v*24' if variant == 'seed' else 'v*24-if c{v*3}else{0}'}}} pub fn seedling_overflow(t:i64,r:i64,v:i64,c:bool)->i64{{((t-r).max(0)-dispatch_capacity(v,c)).max(0)}}
pub fn handle(v:RequestInput)->ResponseOutput{{let ship=(v.tray_count-v.reserved_trays).max(0);let base=v.van_count*24;let buffer=if v.chilled_transport{{v.van_count*3}}else{{0}};let cap=dispatch_capacity(v.van_count,v.chilled_transport);let overflow=(ship-cap).max(0);let loaded=ship.min(cap);ResponseOutput{{shippable_trays:ship,base_capacity:base,chill_buffer:buffer,dispatch_capacity:cap,overflow_trays:overflow,loaded_trays:loaded,space_remaining:(cap-loaded).max(0),dispatch_state:if overflow>0{{"overflow"}}else if loaded>0{{"loaded"}}else{{"idle"}}.into()}}}}
#[unsafe(no_mangle)] pub extern "C" fn parley_seedling_overflow(a:i64,b:i64,c:i64,d:i32)->i64{{seedling_overflow(a,b,c,d!=0)}}""" for variant in ("seed", "reference")},
}

RUST_WASM = {
    "festival_power_build": ("parley_festival_power_score", ["a", "b", "c", "d ? 1 : 0"]),
    "clinic_queue_build": ("parley_clinic_queue_pressure", ["a", "b", "c", "d ? 1 : 0"]),
    "event_credit_repair": ("parley_event_amount_due", ["a", "b", "c", "d ? 1 : 0"]),
    "seedling_dispatch_repair": ("parley_seedling_overflow", ["a", "b", "c", "d ? 1 : 0"]),
}
