"""Frozen task-specific reference and seed logic for full-stack study 040."""

PARLEY_LOGIC = {
    "museum_rotation_build": {
        "seed": """
to museum_rotation_index with permanent_pieces as number, borrowed_pieces as number, room_count as number, late_opening as yesno giving number:
    give back 0
""",
        "reference": """
to museum_rotation_index with permanent_pieces as number, borrowed_pieces as number, room_count as number, late_opening as yesno giving number:
    let program_minutes be permanent_pieces times 9 plus borrowed_pieces times 14
    if late_opening:
        set program_minutes to program_minutes plus room_count times 20
    let tour_blocks be number from ((program_minutes plus 59) divided by 60)
    let label_points be borrowed_pieces times 5 plus room_count times 4
    give back program_minutes plus tour_blocks times 7 plus label_points
""",
    },
    "harbor_signal_build": {
        "seed": """
to harbor_signal_index with freight_arrivals as number, service_boats as number, channel_crews as number, fog_alert as yesno giving number:
    give back 0
""",
        "reference": """
to harbor_signal_index with freight_arrivals as number, service_boats as number, channel_crews as number, fog_alert as yesno giving number:
    let active_beacons be channel_crews times 6
    if fog_alert:
        set active_beacons to active_beacons minus channel_crews times 2
    let vessel_count be freight_arrivals plus service_boats
    let unsignaled be vessel_count minus active_beacons
    if unsignaled is less than 0:
        set unsignaled to 0
    let signaled be vessel_count
    if signaled is more than active_beacons:
        set signaled to active_beacons
    give back unsignaled times 11 plus signaled times 3
""",
    },
    "rooftop_battery_repair": {
        "seed": """
to rooftop_utility_draw with solar_units as number, household_units as number, stored_units as number, reserve_enabled as yesno giving number:
    let gap be household_units minus solar_units
    if gap is less than 0:
        set gap to 0
    let delivery be gap
    if delivery is more than stored_units:
        set delivery to stored_units
    give back gap minus delivery
""",
        "reference": """
to rooftop_utility_draw with solar_units as number, household_units as number, stored_units as number, reserve_enabled as yesno giving number:
    let gap be household_units minus solar_units
    if gap is less than 0:
        set gap to 0
    let protected be 0
    if reserve_enabled:
        set protected to stored_units
        if protected is more than 4:
            set protected to 4
    let ceiling be stored_units minus protected
    let delivery be gap
    if delivery is more than ceiling:
        set delivery to ceiling
    give back gap minus delivery
""",
    },
    "bookmobile_loading_repair": {
        "seed": """
to bookmobile_deferred_crates with requested_crates as number, damaged_crates as number, truck_count as number, lift_assist as yesno giving number:
    let sound be requested_crates minus damaged_crates
    if sound is less than 0:
        set sound to 0
    let slots be truck_count times 16
    if lift_assist:
        set slots to slots minus truck_count times 2
    let deferred be sound minus slots
    if deferred is less than 0:
        set deferred to 0
    give back deferred
""",
        "reference": """
to bookmobile_deferred_crates with requested_crates as number, damaged_crates as number, truck_count as number, lift_assist as yesno giving number:
    let sound be requested_crates minus damaged_crates
    if sound is less than 0:
        set sound to 0
    let slots be truck_count times 16
    if lift_assist:
        set slots to slots plus truck_count times 2
    let deferred be sound minus slots
    if deferred is less than 0:
        set deferred to 0
    give back deferred
""",
    },
}

PARLEY_MAIN = {
    "museum_rotation_build": """
include "logic.par"
a museum_request has permanent_pieces as number, borrowed_pieces as number, room_count as number, late_opening as yesno
a museum_response has collection_size as number, viewing_minutes as number, late_minutes as number, program_minutes as number, tour_blocks as number, label_points as number, rotation_index as number, exhibit_mode as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Museum Rotation", ready yes
to handle_request with request as museum_request giving museum_response:
    let collection be request's permanent_pieces plus request's borrowed_pieces
    let viewing be request's permanent_pieces times 9 plus request's borrowed_pieces times 14
    let late be 0
    if request's late_opening:
        set late to request's room_count times 20
    let program be viewing plus late
    let blocks be number from ((program plus 59) divided by 60)
    let labels be request's borrowed_pieces times 5 plus request's room_count times 4
    let mode be "permanent"
    if request's borrowed_pieces is more than 0:
        set mode to "blended"
        if request's borrowed_pieces is more than request's permanent_pieces:
            set mode to "loan_focus"
    give back a museum_response with collection_size collection, viewing_minutes viewing, late_minutes late, program_minutes program, tour_blocks blocks, label_points labels, rotation_index (museum_rotation_index with request's permanent_pieces, request's borrowed_pieces, request's room_count, request's late_opening), exhibit_mode mode
""",
    "harbor_signal_build": """
include "logic.par"
a harbor_request has freight_arrivals as number, service_boats as number, channel_crews as number, fog_alert as yesno
a harbor_response has vessel_count as number, base_beacons as number, fog_beacons as number, active_beacons as number, unsignaled_vessels as number, crew_load as number, signal_index as number, harbor_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Harbor Signal", ready yes
to handle_request with request as harbor_request giving harbor_response:
    let vessels be request's freight_arrivals plus request's service_boats
    let base be request's channel_crews times 6
    let fog be 0
    if request's fog_alert:
        set fog to request's channel_crews times 2
    let active be base minus fog
    let unsignaled be vessels minus active
    if unsignaled is less than 0:
        set unsignaled to 0
    let signaled be vessels
    if signaled is more than active:
        set signaled to active
    let state be "clear"
    if unsignaled is more than 0:
        set state to "congested"
        if request's fog_alert:
            set state to "fog_hold"
    give back a harbor_response with vessel_count vessels, base_beacons base, fog_beacons fog, active_beacons active, unsignaled_vessels unsignaled, crew_load (signaled times 3), signal_index (harbor_signal_index with request's freight_arrivals, request's service_boats, request's channel_crews, request's fog_alert), harbor_state state
""",
    "rooftop_battery_repair": """
include "logic.par"
a rooftop_request has solar_units as number, household_units as number, stored_units as number, reserve_enabled as yesno
a rooftop_response has energy_gap as number, protected_units as number, discharge_ceiling as number, battery_delivery as number, utility_units as number, storage_balance as number, reserve_margin as number, supply_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Rooftop Battery", ready yes
to handle_request with request as rooftop_request giving rooftop_response:
    let gap be request's household_units minus request's solar_units
    if gap is less than 0:
        set gap to 0
    let protected be 0
    if request's reserve_enabled:
        set protected to request's stored_units
        if protected is more than 4:
            set protected to 4
    let ceiling be request's stored_units minus protected
    let utility be (rooftop_utility_draw with request's solar_units, request's household_units, request's stored_units, request's reserve_enabled)
    let delivery be gap minus utility
    let balance be request's stored_units minus delivery
    let margin be balance minus protected
    if margin is less than 0:
        set margin to 0
    let state be "grid"
    if utility is 0:
        set state to "battery"
        if gap is 0:
            set state to "self_powered"
    give back a rooftop_response with energy_gap gap, protected_units protected, discharge_ceiling ceiling, battery_delivery delivery, utility_units utility, storage_balance balance, reserve_margin margin, supply_state state
""",
    "bookmobile_loading_repair": """
include "logic.par"
a bookmobile_request has requested_crates as number, damaged_crates as number, truck_count as number, lift_assist as yesno
a bookmobile_response has sound_crates as number, deck_slots as number, lift_slots as number, loading_slots as number, deferred_crates as number, boarded_crates as number, empty_slots as number, loading_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Bookmobile Loading", ready yes
to handle_request with request as bookmobile_request giving bookmobile_response:
    let sound be request's requested_crates minus request's damaged_crates
    if sound is less than 0:
        set sound to 0
    let deck be request's truck_count times 16
    let lift be 0
    if request's lift_assist:
        set lift to request's truck_count times 2
    let slots be deck plus lift
    let deferred be (bookmobile_deferred_crates with request's requested_crates, request's damaged_crates, request's truck_count, request's lift_assist)
    let boarded be sound
    if boarded is more than slots:
        set boarded to slots
    let empty be slots minus boarded
    let state be "idle"
    if boarded is more than 0:
        set state to "loaded"
    if deferred is more than 0:
        set state to "deferred"
    give back a bookmobile_response with sound_crates sound, deck_slots deck, lift_slots lift, loading_slots slots, deferred_crates deferred, boarded_crates boarded, empty_slots empty, loading_state state
""",
}

PYTHON_LOGIC = {
    "museum_rotation_build": {variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    permanent_pieces:int=Field(ge=0); borrowed_pieces:int=Field(ge=0); room_count:int=Field(ge=0); late_opening:bool
def museum_rotation_index(p:int,b:int,r:int,l:bool)->int: {'return 0' if variant == 'seed' else 'program=p*9+b*14+(r*20 if l else 0); return program+(program+59)//60*7+b*5+r*4'}
def handle(v:RequestInput)->dict[str,object]:
    viewing=v.permanent_pieces*9+v.borrowed_pieces*14; late=v.room_count*20 if v.late_opening else 0; program=viewing+late; blocks=(program+59)//60; labels=v.borrowed_pieces*5+v.room_count*4
    return {{"collection_size":v.permanent_pieces+v.borrowed_pieces,"viewing_minutes":viewing,"late_minutes":late,"program_minutes":program,"tour_blocks":blocks,"label_points":labels,"rotation_index":museum_rotation_index(v.permanent_pieces,v.borrowed_pieces,v.room_count,v.late_opening),"exhibit_mode":"loan_focus" if v.borrowed_pieces>v.permanent_pieces else "blended" if v.borrowed_pieces else "permanent"}}
""" for variant in ("seed", "reference")},
    "harbor_signal_build": {variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    freight_arrivals:int=Field(ge=0); service_boats:int=Field(ge=0); channel_crews:int=Field(ge=0); fog_alert:bool
def harbor_signal_index(f:int,s:int,c:int,fog:bool)->int: {'return 0' if variant == 'seed' else 'v=f+s; active=c*6-(c*2 if fog else 0); return max(v-active,0)*11+min(v,active)*3'}
def handle(v:RequestInput)->dict[str,object]:
    vessels=v.freight_arrivals+v.service_boats; base=v.channel_crews*6; fog=v.channel_crews*2 if v.fog_alert else 0; active=max(base-fog,0); unsignaled=max(vessels-active,0); crew=min(vessels,active)*3
    return {{"vessel_count":vessels,"base_beacons":base,"fog_beacons":fog,"active_beacons":active,"unsignaled_vessels":unsignaled,"crew_load":crew,"signal_index":harbor_signal_index(v.freight_arrivals,v.service_boats,v.channel_crews,v.fog_alert),"harbor_state":"clear" if unsignaled==0 else "fog_hold" if v.fog_alert else "congested"}}
""" for variant in ("seed", "reference")},
    "rooftop_battery_repair": {variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    solar_units:int=Field(ge=0); household_units:int=Field(ge=0); stored_units:int=Field(ge=0); reserve_enabled:bool
def rooftop_utility_draw(s:int,h:int,stored:int,reserve:bool)->int:
    gap=max(h-s,0); protected=min(stored,4) if reserve else 0
    return max(gap-min(gap,{'stored' if variant == 'seed' else 'max(stored-protected,0)'}),0)
def handle(v:RequestInput)->dict[str,object]:
    gap=max(v.household_units-v.solar_units,0); protected=min(v.stored_units,4) if v.reserve_enabled else 0; ceiling=max(v.stored_units-protected,0); utility=rooftop_utility_draw(v.solar_units,v.household_units,v.stored_units,v.reserve_enabled); delivery=gap-utility; balance=max(v.stored_units-delivery,0)
    return {{"energy_gap":gap,"protected_units":protected,"discharge_ceiling":ceiling,"battery_delivery":delivery,"utility_units":utility,"storage_balance":balance,"reserve_margin":max(balance-protected,0),"supply_state":"self_powered" if gap==0 else "battery" if utility==0 else "grid"}}
""" for variant in ("seed", "reference")},
    "bookmobile_loading_repair": {variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    requested_crates:int=Field(ge=0); damaged_crates:int=Field(ge=0); truck_count:int=Field(ge=0); lift_assist:bool
def loading_slots(t:int,lift:bool)->int: return t*16 {'-' if variant == 'seed' else '+'} (t*2 if lift else 0)
def bookmobile_deferred_crates(r:int,d:int,t:int,lift:bool)->int: return max(max(r-d,0)-loading_slots(t,lift),0)
def handle(v:RequestInput)->dict[str,object]:
    sound=max(v.requested_crates-v.damaged_crates,0); deck=v.truck_count*16; lift=v.truck_count*2 if v.lift_assist else 0; slots=deck+lift; deferred=bookmobile_deferred_crates(v.requested_crates,v.damaged_crates,v.truck_count,v.lift_assist); boarded=min(sound,slots)
    return {{"sound_crates":sound,"deck_slots":deck,"lift_slots":lift,"loading_slots":slots,"deferred_crates":deferred,"boarded_crates":boarded,"empty_slots":max(slots-boarded,0),"loading_state":"deferred" if deferred else "loaded" if boarded else "idle"}}
""" for variant in ("seed", "reference")},
}

PYTHON_BROWSER = {
    "museum_rotation_build": {"seed":"const museumRotationIndex=()=>0n;","reference":"const museumRotationIndex=(p,b,r,l)=>{const m=p*9+b*14+(l?r*20:0);return BigInt(m+Math.trunc((m+59)/60)*7+b*5+r*4);};"},
    "harbor_signal_build": {"seed":"const harborSignalIndex=()=>0n;","reference":"const harborSignalIndex=(f,s,c,g)=>{const v=f+s,a=c*6-(g?c*2:0);return BigInt(Math.max(v-a,0)*11+Math.min(v,a)*3);};"},
    "rooftop_battery_repair": {"seed":"const rooftopUtilityDraw=(s,h,b,r)=>BigInt(Math.max(Math.max(h-s,0)-Math.min(Math.max(h-s,0),b),0));","reference":"const rooftopUtilityDraw=(s,h,b,r)=>{const g=Math.max(h-s,0),p=r?Math.min(b,4):0;return BigInt(Math.max(g-Math.min(g,Math.max(b-p,0)),0));};"},
    "bookmobile_loading_repair": {"seed":"const bookmobileDeferredCrates=(r,d,t,l)=>BigInt(Math.max(Math.max(r-d,0)-(t*16-(l?t*2:0)),0));","reference":"const bookmobileDeferredCrates=(r,d,t,l)=>BigInt(Math.max(Math.max(r-d,0)-(t*16+(l?t*2:0)),0));"},
}

PYTHON_BROWSER_EXPORT = {
    "museum_rotation_build": ("museum_rotation_index", "museumRotationIndex"),
    "harbor_signal_build": ("harbor_signal_index", "harborSignalIndex"),
    "rooftop_battery_repair": ("rooftop_utility_draw", "rooftopUtilityDraw"),
    "bookmobile_loading_repair": ("bookmobile_deferred_crates", "bookmobileDeferredCrates"),
}

TYPESCRIPT_LOGIC = {
    "museum_rotation_build": {variant: f"""export type RequestInput={{permanent_pieces:number;borrowed_pieces:number;room_count:number;late_opening:boolean}};
export const museumRotationIndex=(p:number,b:number,r:number,l:boolean)=>{'0' if variant == 'seed' else 'p*9+b*14+(l?r*20:0)+Math.trunc((p*9+b*14+(l?r*20:0)+59)/60)*7+b*5+r*4'};
export const handle=(v:RequestInput)=>{{const viewing=v.permanent_pieces*9+v.borrowed_pieces*14,late=v.late_opening?v.room_count*20:0,program=viewing+late,blocks=Math.trunc((program+59)/60),labels=v.borrowed_pieces*5+v.room_count*4;return {{collection_size:v.permanent_pieces+v.borrowed_pieces,viewing_minutes:viewing,late_minutes:late,program_minutes:program,tour_blocks:blocks,label_points:labels,rotation_index:museumRotationIndex(v.permanent_pieces,v.borrowed_pieces,v.room_count,v.late_opening),exhibit_mode:v.borrowed_pieces>v.permanent_pieces?"loan_focus":v.borrowed_pieces?"blended":"permanent"}};}};
export async function loadParley(){{return {{museum_rotation_index:(p:number,b:number,r:number,l:boolean)=>BigInt(museumRotationIndex(p,b,r,l))}};}}""" for variant in ("seed","reference")},
    "harbor_signal_build": {variant: f"""export type RequestInput={{freight_arrivals:number;service_boats:number;channel_crews:number;fog_alert:boolean}};
export const harborSignalIndex=(f:number,s:number,c:number,g:boolean)=>{'0' if variant == 'seed' else 'Math.max(f+s-(c*6-(g?c*2:0)),0)*11+Math.min(f+s,c*6-(g?c*2:0))*3'};
export const handle=(v:RequestInput)=>{{const vessels=v.freight_arrivals+v.service_boats,base=v.channel_crews*6,fog=v.fog_alert?v.channel_crews*2:0,active=Math.max(base-fog,0),unsignaled=Math.max(vessels-active,0),crew=Math.min(vessels,active)*3;return {{vessel_count:vessels,base_beacons:base,fog_beacons:fog,active_beacons:active,unsignaled_vessels:unsignaled,crew_load:crew,signal_index:harborSignalIndex(v.freight_arrivals,v.service_boats,v.channel_crews,v.fog_alert),harbor_state:unsignaled===0?"clear":v.fog_alert?"fog_hold":"congested"}};}};
export async function loadParley(){{return {{harbor_signal_index:(f:number,s:number,c:number,g:boolean)=>BigInt(harborSignalIndex(f,s,c,g))}};}}""" for variant in ("seed","reference")},
    "rooftop_battery_repair": {variant: f"""export type RequestInput={{solar_units:number;household_units:number;stored_units:number;reserve_enabled:boolean}};
export const rooftopUtilityDraw=(s:number,h:number,b:number,r:boolean)=>{{const g=Math.max(h-s,0),p=r?Math.min(b,4):0;return Math.max(g-Math.min(g,{'b' if variant == 'seed' else 'Math.max(b-p,0)'}),0);}};
export const handle=(v:RequestInput)=>{{const gap=Math.max(v.household_units-v.solar_units,0),protectedUnits=v.reserve_enabled?Math.min(v.stored_units,4):0,ceiling=Math.max(v.stored_units-protectedUnits,0),utility=rooftopUtilityDraw(v.solar_units,v.household_units,v.stored_units,v.reserve_enabled),delivery=gap-utility,balance=Math.max(v.stored_units-delivery,0);return {{energy_gap:gap,protected_units:protectedUnits,discharge_ceiling:ceiling,battery_delivery:delivery,utility_units:utility,storage_balance:balance,reserve_margin:Math.max(balance-protectedUnits,0),supply_state:gap===0?"self_powered":utility===0?"battery":"grid"}};}};
export async function loadParley(){{return {{rooftop_utility_draw:(s:number,h:number,b:number,r:boolean)=>BigInt(rooftopUtilityDraw(s,h,b,r))}};}}""" for variant in ("seed","reference")},
    "bookmobile_loading_repair": {variant: f"""export type RequestInput={{requested_crates:number;damaged_crates:number;truck_count:number;lift_assist:boolean}};
export const defectSlots=(t:number,l:boolean)=>t*16{'-' if variant == 'seed' else '+'}(l?t*2:0);export const bookmobileDeferredCrates=(r:number,d:number,t:number,l:boolean)=>Math.max(Math.max(r-d,0)-defectSlots(t,l),0);
export const handle=(v:RequestInput)=>{{const sound=Math.max(v.requested_crates-v.damaged_crates,0),deck=v.truck_count*16,lift=v.lift_assist?v.truck_count*2:0,slots=deck+lift,deferred=bookmobileDeferredCrates(v.requested_crates,v.damaged_crates,v.truck_count,v.lift_assist),boarded=Math.min(sound,slots);return {{sound_crates:sound,deck_slots:deck,lift_slots:lift,loading_slots:slots,deferred_crates:deferred,boarded_crates:boarded,empty_slots:Math.max(slots-boarded,0),loading_state:deferred?"deferred":boarded?"loaded":"idle"}};}};
export async function loadParley(){{return {{bookmobile_deferred_crates:(r:number,d:number,t:number,l:boolean)=>BigInt(bookmobileDeferredCrates(r,d,t,l))}};}}""" for variant in ("seed","reference")},
}

TS_SCHEMA = {
    "museum_rotation_build": "z.object({ permanent_pieces:z.number().int().nonnegative(), borrowed_pieces:z.number().int().nonnegative(), room_count:z.number().int().nonnegative(), late_opening:z.boolean() }).strict()",
    "harbor_signal_build": "z.object({ freight_arrivals:z.number().int().nonnegative(), service_boats:z.number().int().nonnegative(), channel_crews:z.number().int().nonnegative(), fog_alert:z.boolean() }).strict()",
    "rooftop_battery_repair": "z.object({ solar_units:z.number().int().nonnegative(), household_units:z.number().int().nonnegative(), stored_units:z.number().int().nonnegative(), reserve_enabled:z.boolean() }).strict()",
    "bookmobile_loading_repair": "z.object({ requested_crates:z.number().int().nonnegative(), damaged_crates:z.number().int().nonnegative(), truck_count:z.number().int().nonnegative(), lift_assist:z.boolean() }).strict()",
}

RUST_LIB = {
    "museum_rotation_build": {variant: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub permanent_pieces:i64,pub borrowed_pieces:i64,pub room_count:i64,pub late_opening:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.permanent_pieces>=0&&self.borrowed_pieces>=0&&self.room_count>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub collection_size:i64,pub viewing_minutes:i64,pub late_minutes:i64,pub program_minutes:i64,pub tour_blocks:i64,pub label_points:i64,pub rotation_index:i64,pub exhibit_mode:String}}pub fn museum_rotation_index(p:i64,b:i64,r:i64,l:bool)->i64{{{'0' if variant == 'seed' else 'let m=p*9+b*14+if l{r*20}else{0};m+(m+59)/60*7+b*5+r*4'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let viewing=v.permanent_pieces*9+v.borrowed_pieces*14;let late=if v.late_opening{{v.room_count*20}}else{{0}};let program=viewing+late;ResponseOutput{{collection_size:v.permanent_pieces+v.borrowed_pieces,viewing_minutes:viewing,late_minutes:late,program_minutes:program,tour_blocks:(program+59)/60,label_points:v.borrowed_pieces*5+v.room_count*4,rotation_index:museum_rotation_index(v.permanent_pieces,v.borrowed_pieces,v.room_count,v.late_opening),exhibit_mode:if v.borrowed_pieces>v.permanent_pieces{{"loan_focus"}}else if v.borrowed_pieces>0{{"blended"}}else{{"permanent"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_museum_rotation_index(a:i64,b:i64,c:i64,d:i32)->i64{{museum_rotation_index(a,b,c,d!=0)}}""" for variant in ("seed","reference")},
    "harbor_signal_build": {variant: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub freight_arrivals:i64,pub service_boats:i64,pub channel_crews:i64,pub fog_alert:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.freight_arrivals>=0&&self.service_boats>=0&&self.channel_crews>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub vessel_count:i64,pub base_beacons:i64,pub fog_beacons:i64,pub active_beacons:i64,pub unsignaled_vessels:i64,pub crew_load:i64,pub signal_index:i64,pub harbor_state:String}}pub fn harbor_signal_index(f:i64,s:i64,c:i64,g:bool)->i64{{{'0' if variant == 'seed' else 'let v=f+s;let a=c*6-if g{c*2}else{0};(v-a).max(0)*11+v.min(a)*3'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let vessels=v.freight_arrivals+v.service_boats;let base=v.channel_crews*6;let fog=if v.fog_alert{{v.channel_crews*2}}else{{0}};let active=(base-fog).max(0);let unsignaled=(vessels-active).max(0);ResponseOutput{{vessel_count:vessels,base_beacons:base,fog_beacons:fog,active_beacons:active,unsignaled_vessels:unsignaled,crew_load:vessels.min(active)*3,signal_index:harbor_signal_index(v.freight_arrivals,v.service_boats,v.channel_crews,v.fog_alert),harbor_state:if unsignaled==0{{"clear"}}else if v.fog_alert{{"fog_hold"}}else{{"congested"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_harbor_signal_index(a:i64,b:i64,c:i64,d:i32)->i64{{harbor_signal_index(a,b,c,d!=0)}}""" for variant in ("seed","reference")},
    "rooftop_battery_repair": {variant: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub solar_units:i64,pub household_units:i64,pub stored_units:i64,pub reserve_enabled:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.solar_units>=0&&self.household_units>=0&&self.stored_units>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub energy_gap:i64,pub protected_units:i64,pub discharge_ceiling:i64,pub battery_delivery:i64,pub utility_units:i64,pub storage_balance:i64,pub reserve_margin:i64,pub supply_state:String}}pub fn rooftop_utility_draw(s:i64,h:i64,b:i64,r:bool)->i64{{let g=(h-s).max(0);let p=if r{{b.min(4)}}else{{0}};(g-g.min({'b' if variant == 'seed' else '(b-p).max(0)'})).max(0)}}pub fn handle(v:RequestInput)->ResponseOutput{{let gap=(v.household_units-v.solar_units).max(0);let protected=if v.reserve_enabled{{v.stored_units.min(4)}}else{{0}};let ceiling=(v.stored_units-protected).max(0);let utility=rooftop_utility_draw(v.solar_units,v.household_units,v.stored_units,v.reserve_enabled);let delivery=gap-utility;let balance=(v.stored_units-delivery).max(0);ResponseOutput{{energy_gap:gap,protected_units:protected,discharge_ceiling:ceiling,battery_delivery:delivery,utility_units:utility,storage_balance:balance,reserve_margin:(balance-protected).max(0),supply_state:if gap==0{{"self_powered"}}else if utility==0{{"battery"}}else{{"grid"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_rooftop_utility_draw(a:i64,b:i64,c:i64,d:i32)->i64{{rooftop_utility_draw(a,b,c,d!=0)}}""" for variant in ("seed","reference")},
    "bookmobile_loading_repair": {variant: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub requested_crates:i64,pub damaged_crates:i64,pub truck_count:i64,pub lift_assist:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.requested_crates>=0&&self.damaged_crates>=0&&self.truck_count>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub sound_crates:i64,pub deck_slots:i64,pub lift_slots:i64,pub loading_slots:i64,pub deferred_crates:i64,pub boarded_crates:i64,pub empty_slots:i64,pub loading_state:String}}pub fn defect_slots(t:i64,l:bool)->i64{{t*16{'-' if variant == 'seed' else '+'}if l{{t*2}}else{{0}}}}pub fn bookmobile_deferred_crates(r:i64,d:i64,t:i64,l:bool)->i64{{((r-d).max(0)-defect_slots(t,l)).max(0)}}pub fn handle(v:RequestInput)->ResponseOutput{{let sound=(v.requested_crates-v.damaged_crates).max(0);let deck=v.truck_count*16;let lift=if v.lift_assist{{v.truck_count*2}}else{{0}};let slots=deck+lift;let deferred=bookmobile_deferred_crates(v.requested_crates,v.damaged_crates,v.truck_count,v.lift_assist);let boarded=sound.min(slots);ResponseOutput{{sound_crates:sound,deck_slots:deck,lift_slots:lift,loading_slots:slots,deferred_crates:deferred,boarded_crates:boarded,empty_slots:(slots-boarded).max(0),loading_state:if deferred>0{{"deferred"}}else if boarded>0{{"loaded"}}else{{"idle"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_bookmobile_deferred_crates(a:i64,b:i64,c:i64,d:i32)->i64{{bookmobile_deferred_crates(a,b,c,d!=0)}}""" for variant in ("seed","reference")},
}

RUST_WASM = {
    "museum_rotation_build": ("parley_museum_rotation_index", ["a","b","c","d ? 1 : 0"]),
    "harbor_signal_build": ("parley_harbor_signal_index", ["a","b","c","d ? 1 : 0"]),
    "rooftop_battery_repair": ("parley_rooftop_utility_draw", ["a","b","c","d ? 1 : 0"]),
    "bookmobile_loading_repair": ("parley_bookmobile_deferred_crates", ["a","b","c","d ? 1 : 0"]),
}
