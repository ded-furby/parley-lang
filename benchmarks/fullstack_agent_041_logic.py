"""Frozen task-specific reference and seed logic for full-stack study 041."""

PARLEY_LOGIC = {
    "observatory_schedule_build": {
        "seed": """
to observatory_coordination_score with public_talks as number, research_tracks as number, dome_sections as number, cloud_monitoring as yesno giving number:
    give back 0
""",
        "reference": """
to observatory_coordination_score with public_talks as number, research_tracks as number, dome_sections as number, cloud_monitoring as yesno giving number:
    let scheduled be public_talks times 22 plus research_tracks times 31
    if cloud_monitoring:
        set scheduled to scheduled plus dome_sections times 7
    let rest_breaks be number from (scheduled divided by 90)
    give back scheduled times dome_sections plus rest_breaks times 13 plus (public_talks plus research_tracks) times 5
""",
    },
    "reef_nursery_build": {
        "seed": """
to reef_nursery_index with coral_trays as number, algae_trays as number, circulation_pumps as number, night_cycle as yesno giving number:
    give back 0
""",
        "reference": """
to reef_nursery_index with coral_trays as number, algae_trays as number, circulation_pumps as number, night_cycle as yesno giving number:
    let required be coral_trays times 12 plus algae_trays times 7
    if night_cycle:
        set required to required plus circulation_pumps times 5
    let capacity be circulation_pumps times 20
    let served be required
    if served is more than capacity:
        set served to capacity
    let overflow be required minus capacity
    if overflow is less than 0:
        set overflow to 0
    give back served plus overflow times 9 plus coral_trays times 3
""",
    },
    "rescue_shelter_repair": {
        "seed": """
to shelter_unused_capacity with arriving_hikers as number, injured_hikers as number, heater_packs as number, storm_lockdown as yesno giving number:
    let baseline be arriving_hikers times 3 plus injured_hikers times 6
    let capacity be heater_packs times 8
    let delivered be baseline
    if delivered is more than capacity:
        set delivered to capacity
    give back capacity minus delivered
""",
        "reference": """
to shelter_unused_capacity with arriving_hikers as number, injured_hikers as number, heater_packs as number, storm_lockdown as yesno giving number:
    let required be arriving_hikers times 3 plus injured_hikers times 6
    if storm_lockdown:
        set required to required minus heater_packs times 2
        if required is less than 0:
            set required to 0
    let capacity be heater_packs times 8
    let delivered be required
    if delivered is more than capacity:
        set delivered to capacity
    give back capacity minus delivered
""",
    },
    "aviary_feeding_repair": {
        "seed": """
to aviary_required_scoops with resident_birds as number, rehab_birds as number, feed_bins as number, winter_ration as yesno giving number:
    let required be resident_birds times 2 plus rehab_birds times 3
    if winter_ration:
        set required to required plus resident_birds
    give back required
""",
        "reference": """
to aviary_required_scoops with resident_birds as number, rehab_birds as number, feed_bins as number, winter_ration as yesno giving number:
    let required be resident_birds times 2 plus rehab_birds times 3
    if winter_ration:
        set required to required plus resident_birds plus rehab_birds
    give back required
""",
    },
}

PARLEY_MAIN = {
    "observatory_schedule_build": """
include "logic.par"
an observatory_request has public_talks as number, research_tracks as number, dome_sections as number, cloud_monitoring as yesno
an observatory_response has session_total as number, open_minutes as number, weather_minutes as number, scheduled_minutes as number, staff_minutes as number, rest_breaks as number, coordination_score as number, observatory_mode as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Observatory Schedule", ready yes
to handle_request with request as observatory_request giving observatory_response:
    let sessions be request's public_talks plus request's research_tracks
    let opened be request's public_talks times 22 plus request's research_tracks times 31
    let weather be 0
    if request's cloud_monitoring:
        set weather to request's dome_sections times 7
    let scheduled be opened plus weather
    let breaks be number from (scheduled divided by 90)
    let mode be "standby"
    if request's public_talks is more than 0:
        set mode to "outreach"
    if request's research_tracks is more than request's public_talks:
        set mode to "research_first"
    give back an observatory_response with session_total sessions, open_minutes opened, weather_minutes weather, scheduled_minutes scheduled, staff_minutes (scheduled times request's dome_sections), rest_breaks breaks, coordination_score (observatory_coordination_score with request's public_talks, request's research_tracks, request's dome_sections, request's cloud_monitoring), observatory_mode mode
""",
    "reef_nursery_build": """
include "logic.par"
a reef_request has coral_trays as number, algae_trays as number, circulation_pumps as number, night_cycle as yesno
a reef_response has nursery_trays as number, base_flow_liters as number, night_flush_liters as number, required_flow_liters as number, pump_capacity_liters as number, served_flow_liters as number, overflow_flow_liters as number, reef_index as number, nursery_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Reef Nursery", ready yes
to handle_request with request as reef_request giving reef_response:
    let base be request's coral_trays times 12 plus request's algae_trays times 7
    let flush be 0
    if request's night_cycle:
        set flush to request's circulation_pumps times 5
    let required be base plus flush
    let capacity be request's circulation_pumps times 20
    let served be required
    if served is more than capacity:
        set served to capacity
    let overflow be required minus capacity
    if overflow is less than 0:
        set overflow to 0
    let state be "balanced"
    if overflow is more than 0:
        set state to "daytime_overflow"
        if request's night_cycle:
            set state to "night_overflow"
    give back a reef_response with nursery_trays (request's coral_trays plus request's algae_trays), base_flow_liters base, night_flush_liters flush, required_flow_liters required, pump_capacity_liters capacity, served_flow_liters served, overflow_flow_liters overflow, reef_index (reef_nursery_index with request's coral_trays, request's algae_trays, request's circulation_pumps, request's night_cycle), nursery_state state
""",
    "rescue_shelter_repair": """
include "logic.par"
a shelter_request has arriving_hikers as number, injured_hikers as number, heater_packs as number, storm_lockdown as yesno
a shelter_response has hiker_total as number, baseline_warmth as number, lockdown_reduction as number, required_warmth as number, pack_capacity as number, delivered_warmth as number, uncovered_warmth as number, unused_capacity as number, shelter_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Rescue Shelter", ready yes
to handle_request with request as shelter_request giving shelter_response:
    let baseline be request's arriving_hikers times 3 plus request's injured_hikers times 6
    let reduction be 0
    if request's storm_lockdown:
        set reduction to request's heater_packs times 2
    let required be baseline minus reduction
    if required is less than 0:
        set required to 0
    let capacity be request's heater_packs times 8
    let unused be (shelter_unused_capacity with request's arriving_hikers, request's injured_hikers, request's heater_packs, request's storm_lockdown)
    let delivered be capacity minus unused
    let uncovered be required minus delivered
    if uncovered is less than 0:
        set uncovered to 0
    let state be "covered"
    if uncovered is more than 0:
        set state to "supply_gap"
        if request's storm_lockdown:
            set state to "storm_gap"
    give back a shelter_response with hiker_total (request's arriving_hikers plus request's injured_hikers), baseline_warmth baseline, lockdown_reduction reduction, required_warmth required, pack_capacity capacity, delivered_warmth delivered, uncovered_warmth uncovered, unused_capacity unused, shelter_state state
""",
    "aviary_feeding_repair": """
include "logic.par"
an aviary_request has resident_birds as number, rehab_birds as number, feed_bins as number, winter_ration as yesno
an aviary_response has bird_total as number, resident_scoops as number, rehab_scoops as number, winter_scoops as number, required_scoops as number, available_scoops as number, served_scoops as number, shortage_scoops as number, feed_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Aviary Feeding", ready yes
to handle_request with request as aviary_request giving aviary_response:
    let birds be request's resident_birds plus request's rehab_birds
    let resident be request's resident_birds times 2
    let rehab be request's rehab_birds times 3
    let winter be 0
    if request's winter_ration:
        set winter to birds
    let required be (aviary_required_scoops with request's resident_birds, request's rehab_birds, request's feed_bins, request's winter_ration)
    let available be request's feed_bins times 10
    let served be required
    if served is more than available:
        set served to available
    let shortage be required minus available
    if shortage is less than 0:
        set shortage to 0
    let state be "stocked"
    if shortage is more than 0:
        set state to "shortage"
        if request's winter_ration:
            set state to "winter_shortage"
    give back an aviary_response with bird_total birds, resident_scoops resident, rehab_scoops rehab, winter_scoops winter, required_scoops required, available_scoops available, served_scoops served, shortage_scoops shortage, feed_state state
""",
}

PYTHON_LOGIC = {
    "observatory_schedule_build": {variant: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); public_talks:int=Field(ge=0); research_tracks:int=Field(ge=0); dome_sections:int=Field(ge=0); cloud_monitoring:bool
def observatory_coordination_score(p:int,r:int,d:int,c:bool)->int: {'return 0' if variant=='seed' else 's=p*22+r*31+(d*7 if c else 0); return s*d+(s//90)*13+(p+r)*5'}
def handle(v:RequestInput)->dict[str,object]:
 o=v.public_talks*22+v.research_tracks*31; w=v.dome_sections*7 if v.cloud_monitoring else 0; s=o+w
 return {{'session_total':v.public_talks+v.research_tracks,'open_minutes':o,'weather_minutes':w,'scheduled_minutes':s,'staff_minutes':s*v.dome_sections,'rest_breaks':s//90,'coordination_score':observatory_coordination_score(v.public_talks,v.research_tracks,v.dome_sections,v.cloud_monitoring),'observatory_mode':'research_first' if v.research_tracks>v.public_talks else 'outreach' if v.public_talks else 'standby'}}
""" for variant in ('seed','reference')},
    "reef_nursery_build": {variant: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); coral_trays:int=Field(ge=0); algae_trays:int=Field(ge=0); circulation_pumps:int=Field(ge=0); night_cycle:bool
def reef_nursery_index(c:int,a:int,p:int,n:bool)->int: {'return 0' if variant=='seed' else 'r=c*12+a*7+(p*5 if n else 0); cap=p*20; return min(r,cap)+max(r-cap,0)*9+c*3'}
def handle(v:RequestInput)->dict[str,object]:
 b=v.coral_trays*12+v.algae_trays*7; f=v.circulation_pumps*5 if v.night_cycle else 0; r=b+f; c=v.circulation_pumps*20; s=min(r,c); o=max(r-c,0)
 return {{'nursery_trays':v.coral_trays+v.algae_trays,'base_flow_liters':b,'night_flush_liters':f,'required_flow_liters':r,'pump_capacity_liters':c,'served_flow_liters':s,'overflow_flow_liters':o,'reef_index':reef_nursery_index(v.coral_trays,v.algae_trays,v.circulation_pumps,v.night_cycle),'nursery_state':'balanced' if o==0 else 'night_overflow' if v.night_cycle else 'daytime_overflow'}}
""" for variant in ('seed','reference')},
    "rescue_shelter_repair": {variant: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); arriving_hikers:int=Field(ge=0); injured_hikers:int=Field(ge=0); heater_packs:int=Field(ge=0); storm_lockdown:bool
def shelter_unused_capacity(a:int,i:int,p:int,s:bool)->int:
 b=a*3+i*6; r={'b' if variant=='seed' else 'max(b-(p*2 if s else 0),0)'}; return max(p*8-min(r,p*8),0)
def handle(v:RequestInput)->dict[str,object]:
 b=v.arriving_hikers*3+v.injured_hikers*6; x=v.heater_packs*2 if v.storm_lockdown else 0; r=max(b-x,0); c=v.heater_packs*8; u=shelter_unused_capacity(v.arriving_hikers,v.injured_hikers,v.heater_packs,v.storm_lockdown); d=c-u; g=max(r-d,0)
 return {{'hiker_total':v.arriving_hikers+v.injured_hikers,'baseline_warmth':b,'lockdown_reduction':x,'required_warmth':r,'pack_capacity':c,'delivered_warmth':d,'uncovered_warmth':g,'unused_capacity':u,'shelter_state':'covered' if g==0 else 'storm_gap' if v.storm_lockdown else 'supply_gap'}}
""" for variant in ('seed','reference')},
    "aviary_feeding_repair": {variant: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); resident_birds:int=Field(ge=0); rehab_birds:int=Field(ge=0); feed_bins:int=Field(ge=0); winter_ration:bool
def aviary_required_scoops(r:int,h:int,b:int,w:bool)->int: return r*2+h*3+( ({'r' if variant=='seed' else 'r+h'}) if w else 0)
def handle(v:RequestInput)->dict[str,object]:
 t=v.resident_birds+v.rehab_birds; r=v.resident_birds*2; h=v.rehab_birds*3; w=t if v.winter_ration else 0; q=aviary_required_scoops(v.resident_birds,v.rehab_birds,v.feed_bins,v.winter_ration); a=v.feed_bins*10; s=min(q,a); g=max(q-a,0)
 return {{'bird_total':t,'resident_scoops':r,'rehab_scoops':h,'winter_scoops':w,'required_scoops':q,'available_scoops':a,'served_scoops':s,'shortage_scoops':g,'feed_state':'stocked' if g==0 else 'winter_shortage' if v.winter_ration else 'shortage'}}
""" for variant in ('seed','reference')},
}

PYTHON_BROWSER = {
 "observatory_schedule_build":{"seed":"const observatoryCoordinationScore=()=>0n;","reference":"const observatoryCoordinationScore=(p,r,d,c)=>{const s=p*22+r*31+(c?d*7:0);return BigInt(s*d+Math.trunc(s/90)*13+(p+r)*5);};"},
 "reef_nursery_build":{"seed":"const reefNurseryIndex=()=>0n;","reference":"const reefNurseryIndex=(c,a,p,n)=>{const r=c*12+a*7+(n?p*5:0),cap=p*20;return BigInt(Math.min(r,cap)+Math.max(r-cap,0)*9+c*3);};"},
 "rescue_shelter_repair":{"seed":"const shelterUnusedCapacity=(a,i,p,s)=>{const b=a*3+i*6;return BigInt(Math.max(p*8-Math.min(b,p*8),0));};","reference":"const shelterUnusedCapacity=(a,i,p,s)=>{const r=Math.max(a*3+i*6-(s?p*2:0),0);return BigInt(Math.max(p*8-Math.min(r,p*8),0));};"},
 "aviary_feeding_repair":{"seed":"const aviaryRequiredScoops=(r,h,b,w)=>BigInt(r*2+h*3+(w?r:0));","reference":"const aviaryRequiredScoops=(r,h,b,w)=>BigInt(r*2+h*3+(w?r+h:0));"},
}

PYTHON_BROWSER_EXPORT = {
 "observatory_schedule_build":("observatory_coordination_score","observatoryCoordinationScore"),
 "reef_nursery_build":("reef_nursery_index","reefNurseryIndex"),
 "rescue_shelter_repair":("shelter_unused_capacity","shelterUnusedCapacity"),
 "aviary_feeding_repair":("aviary_required_scoops","aviaryRequiredScoops"),
}

TYPESCRIPT_LOGIC = {
 "observatory_schedule_build":{v:f"""export type RequestInput={{public_talks:number;research_tracks:number;dome_sections:number;cloud_monitoring:boolean}};export const score=(p:number,r:number,d:number,c:boolean)=>{{{'return 0' if v=='seed' else 'const s=p*22+r*31+(c?d*7:0);return s*d+Math.trunc(s/90)*13+(p+r)*5'}}};export const handle=(v:RequestInput)=>{{const o=v.public_talks*22+v.research_tracks*31,w=v.cloud_monitoring?v.dome_sections*7:0,s=o+w;return {{session_total:v.public_talks+v.research_tracks,open_minutes:o,weather_minutes:w,scheduled_minutes:s,staff_minutes:s*v.dome_sections,rest_breaks:Math.trunc(s/90),coordination_score:score(v.public_talks,v.research_tracks,v.dome_sections,v.cloud_monitoring),observatory_mode:v.research_tracks>v.public_talks?'research_first':v.public_talks?'outreach':'standby'}}}};export async function loadParley(){{return {{observatory_coordination_score:(a:number,b:number,c:number,d:boolean)=>BigInt(score(a,b,c,d))}}}}""" for v in ('seed','reference')},
 "reef_nursery_build":{v:f"""export type RequestInput={{coral_trays:number;algae_trays:number;circulation_pumps:number;night_cycle:boolean}};export const index=(c:number,a:number,p:number,n:boolean)=>{{{'return 0' if v=='seed' else 'const r=c*12+a*7+(n?p*5:0),x=p*20;return Math.min(r,x)+Math.max(r-x,0)*9+c*3'}}};export const handle=(v:RequestInput)=>{{const b=v.coral_trays*12+v.algae_trays*7,f=v.night_cycle?v.circulation_pumps*5:0,r=b+f,c=v.circulation_pumps*20,s=Math.min(r,c),o=Math.max(r-c,0);return {{nursery_trays:v.coral_trays+v.algae_trays,base_flow_liters:b,night_flush_liters:f,required_flow_liters:r,pump_capacity_liters:c,served_flow_liters:s,overflow_flow_liters:o,reef_index:index(v.coral_trays,v.algae_trays,v.circulation_pumps,v.night_cycle),nursery_state:o===0?'balanced':v.night_cycle?'night_overflow':'daytime_overflow'}}}};export async function loadParley(){{return {{reef_nursery_index:(a:number,b:number,c:number,d:boolean)=>BigInt(index(a,b,c,d))}}}}""" for v in ('seed','reference')},
 "rescue_shelter_repair":{v:f"""export type RequestInput={{arriving_hikers:number;injured_hikers:number;heater_packs:number;storm_lockdown:boolean}};export const unused=(a:number,i:number,p:number,s:boolean)=>{{const b=a*3+i*6,r={'b' if v=='seed' else 'Math.max(b-(s?p*2:0),0)'};return Math.max(p*8-Math.min(r,p*8),0)}};export const handle=(v:RequestInput)=>{{const b=v.arriving_hikers*3+v.injured_hikers*6,x=v.storm_lockdown?v.heater_packs*2:0,r=Math.max(b-x,0),c=v.heater_packs*8,u=unused(v.arriving_hikers,v.injured_hikers,v.heater_packs,v.storm_lockdown),d=c-u,g=Math.max(r-d,0);return {{hiker_total:v.arriving_hikers+v.injured_hikers,baseline_warmth:b,lockdown_reduction:x,required_warmth:r,pack_capacity:c,delivered_warmth:d,uncovered_warmth:g,unused_capacity:u,shelter_state:g===0?'covered':v.storm_lockdown?'storm_gap':'supply_gap'}}}};export async function loadParley(){{return {{shelter_unused_capacity:(a:number,b:number,c:number,d:boolean)=>BigInt(unused(a,b,c,d))}}}}""" for v in ('seed','reference')},
 "aviary_feeding_repair":{v:f"""export type RequestInput={{resident_birds:number;rehab_birds:number;feed_bins:number;winter_ration:boolean}};export const required=(r:number,h:number,b:number,w:boolean)=>r*2+h*3+(w?{'r' if v=='seed' else 'r+h'}:0);export const handle=(v:RequestInput)=>{{const t=v.resident_birds+v.rehab_birds,r=v.resident_birds*2,h=v.rehab_birds*3,w=v.winter_ration?t:0,q=required(v.resident_birds,v.rehab_birds,v.feed_bins,v.winter_ration),a=v.feed_bins*10,s=Math.min(q,a),g=Math.max(q-a,0);return {{bird_total:t,resident_scoops:r,rehab_scoops:h,winter_scoops:w,required_scoops:q,available_scoops:a,served_scoops:s,shortage_scoops:g,feed_state:g===0?'stocked':v.winter_ration?'winter_shortage':'shortage'}}}};export async function loadParley(){{return {{aviary_required_scoops:(a:number,b:number,c:number,d:boolean)=>BigInt(required(a,b,c,d))}}}}""" for v in ('seed','reference')},
}

TS_SCHEMA={
 "observatory_schedule_build":"z.object({ public_talks:z.number().int().nonnegative(), research_tracks:z.number().int().nonnegative(), dome_sections:z.number().int().nonnegative(), cloud_monitoring:z.boolean() }).strict()",
 "reef_nursery_build":"z.object({ coral_trays:z.number().int().nonnegative(), algae_trays:z.number().int().nonnegative(), circulation_pumps:z.number().int().nonnegative(), night_cycle:z.boolean() }).strict()",
 "rescue_shelter_repair":"z.object({ arriving_hikers:z.number().int().nonnegative(), injured_hikers:z.number().int().nonnegative(), heater_packs:z.number().int().nonnegative(), storm_lockdown:z.boolean() }).strict()",
 "aviary_feeding_repair":"z.object({ resident_birds:z.number().int().nonnegative(), rehab_birds:z.number().int().nonnegative(), feed_bins:z.number().int().nonnegative(), winter_ration:z.boolean() }).strict()",
}

RUST_LIB={
 "observatory_schedule_build":{v:f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub public_talks:i64,pub research_tracks:i64,pub dome_sections:i64,pub cloud_monitoring:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.public_talks>=0&&self.research_tracks>=0&&self.dome_sections>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub session_total:i64,pub open_minutes:i64,pub weather_minutes:i64,pub scheduled_minutes:i64,pub staff_minutes:i64,pub rest_breaks:i64,pub coordination_score:i64,pub observatory_mode:String}}pub fn score(p:i64,r:i64,d:i64,c:bool)->i64{{{'0' if v=='seed' else 'let s=p*22+r*31+if c{d*7}else{0};s*d+(s/90)*13+(p+r)*5'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let o=v.public_talks*22+v.research_tracks*31;let w=if v.cloud_monitoring{{v.dome_sections*7}}else{{0}};let s=o+w;ResponseOutput{{session_total:v.public_talks+v.research_tracks,open_minutes:o,weather_minutes:w,scheduled_minutes:s,staff_minutes:s*v.dome_sections,rest_breaks:s/90,coordination_score:score(v.public_talks,v.research_tracks,v.dome_sections,v.cloud_monitoring),observatory_mode:if v.research_tracks>v.public_talks{{"research_first"}}else if v.public_talks>0{{"outreach"}}else{{"standby"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_observatory_score(a:i64,b:i64,c:i64,d:i32)->i64{{score(a,b,c,d!=0)}}""" for v in ('seed','reference')},
 "reef_nursery_build":{v:f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub coral_trays:i64,pub algae_trays:i64,pub circulation_pumps:i64,pub night_cycle:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.coral_trays>=0&&self.algae_trays>=0&&self.circulation_pumps>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub nursery_trays:i64,pub base_flow_liters:i64,pub night_flush_liters:i64,pub required_flow_liters:i64,pub pump_capacity_liters:i64,pub served_flow_liters:i64,pub overflow_flow_liters:i64,pub reef_index:i64,pub nursery_state:String}}pub fn index(c:i64,a:i64,p:i64,n:bool)->i64{{{'0' if v=='seed' else 'let r=c*12+a*7+if n{p*5}else{0};let x=p*20;r.min(x)+(r-x).max(0)*9+c*3'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let b=v.coral_trays*12+v.algae_trays*7;let f=if v.night_cycle{{v.circulation_pumps*5}}else{{0}};let r=b+f;let c=v.circulation_pumps*20;let o=(r-c).max(0);ResponseOutput{{nursery_trays:v.coral_trays+v.algae_trays,base_flow_liters:b,night_flush_liters:f,required_flow_liters:r,pump_capacity_liters:c,served_flow_liters:r.min(c),overflow_flow_liters:o,reef_index:index(v.coral_trays,v.algae_trays,v.circulation_pumps,v.night_cycle),nursery_state:if o==0{{"balanced"}}else if v.night_cycle{{"night_overflow"}}else{{"daytime_overflow"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_reef_index(a:i64,b:i64,c:i64,d:i32)->i64{{index(a,b,c,d!=0)}}""" for v in ('seed','reference')},
 "rescue_shelter_repair":{v:f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub arriving_hikers:i64,pub injured_hikers:i64,pub heater_packs:i64,pub storm_lockdown:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.arriving_hikers>=0&&self.injured_hikers>=0&&self.heater_packs>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub hiker_total:i64,pub baseline_warmth:i64,pub lockdown_reduction:i64,pub required_warmth:i64,pub pack_capacity:i64,pub delivered_warmth:i64,pub uncovered_warmth:i64,pub unused_capacity:i64,pub shelter_state:String}}pub fn unused(a:i64,i:i64,p:i64,s:bool)->i64{{let b=a*3+i*6;let r={'b' if v=='seed' else '(b-if s{p*2}else{0}).max(0)'};(p*8-r.min(p*8)).max(0)}}pub fn handle(v:RequestInput)->ResponseOutput{{let b=v.arriving_hikers*3+v.injured_hikers*6;let x=if v.storm_lockdown{{v.heater_packs*2}}else{{0}};let r=(b-x).max(0);let c=v.heater_packs*8;let u=unused(v.arriving_hikers,v.injured_hikers,v.heater_packs,v.storm_lockdown);let d=c-u;let g=(r-d).max(0);ResponseOutput{{hiker_total:v.arriving_hikers+v.injured_hikers,baseline_warmth:b,lockdown_reduction:x,required_warmth:r,pack_capacity:c,delivered_warmth:d,uncovered_warmth:g,unused_capacity:u,shelter_state:if g==0{{"covered"}}else if v.storm_lockdown{{"storm_gap"}}else{{"supply_gap"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_shelter_unused(a:i64,b:i64,c:i64,d:i32)->i64{{unused(a,b,c,d!=0)}}""" for v in ('seed','reference')},
 "aviary_feeding_repair":{v:f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub resident_birds:i64,pub rehab_birds:i64,pub feed_bins:i64,pub winter_ration:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.resident_birds>=0&&self.rehab_birds>=0&&self.feed_bins>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub bird_total:i64,pub resident_scoops:i64,pub rehab_scoops:i64,pub winter_scoops:i64,pub required_scoops:i64,pub available_scoops:i64,pub served_scoops:i64,pub shortage_scoops:i64,pub feed_state:String}}pub fn required(r:i64,h:i64,_b:i64,w:bool)->i64{{r*2+h*3+if w{{{'r' if v=='seed' else 'r+h'}}}else{{0}}}}pub fn handle(v:RequestInput)->ResponseOutput{{let t=v.resident_birds+v.rehab_birds;let r=v.resident_birds*2;let h=v.rehab_birds*3;let w=if v.winter_ration{{t}}else{{0}};let q=required(v.resident_birds,v.rehab_birds,v.feed_bins,v.winter_ration);let a=v.feed_bins*10;let g=(q-a).max(0);ResponseOutput{{bird_total:t,resident_scoops:r,rehab_scoops:h,winter_scoops:w,required_scoops:q,available_scoops:a,served_scoops:q.min(a),shortage_scoops:g,feed_state:if g==0{{"stocked"}}else if v.winter_ration{{"winter_shortage"}}else{{"shortage"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_aviary_required(a:i64,b:i64,c:i64,d:i32)->i64{{required(a,b,c,d!=0)}}""" for v in ('seed','reference')},
}

RUST_WASM={
 "observatory_schedule_build":("parley_observatory_score",["a","b","c","d ? 1 : 0"]),
 "reef_nursery_build":("parley_reef_index",["a","b","c","d ? 1 : 0"]),
 "rescue_shelter_repair":("parley_shelter_unused",["a","b","c","d ? 1 : 0"]),
 "aviary_feeding_repair":("parley_aviary_required",["a","b","c","d ? 1 : 0"]),
}
