"""Frozen task-specific reference and seed logic for full-stack study 042."""

PARLEY_LOGIC = {
    "radio_archive_build": {
        "seed": """
to radio_archive_score with spoken_segments as number, music_segments as number, language_tracks as number, live_broadcast as yesno giving number:
    give back 0
""",
        "reference": """
to radio_archive_score with spoken_segments as number, music_segments as number, language_tracks as number, live_broadcast as yesno giving number:
    let archive be spoken_segments times 14 plus music_segments times 24
    if live_broadcast:
        set archive to archive plus language_tracks times 9
    let blocks be number from (archive divided by 64)
    give back archive times language_tracks plus blocks times 17 plus (spoken_segments plus music_segments) times 3
""",
    },
    "theatre_turnaround_build": {
        "seed": """
to theatre_turnaround_score with matinee_shows as number, evening_shows as number, stage_crews as number, touring_production as yesno giving number:
    give back 0
""",
        "reference": """
to theatre_turnaround_score with matinee_shows as number, evening_shows as number, stage_crews as number, touring_production as yesno giving number:
    let required be matinee_shows times 18 plus evening_shows times 27
    if touring_production:
        set required to required plus stage_crews times 6
    let capacity be stage_crews times 45
    let covered be required
    if covered is more than capacity:
        set covered to capacity
    let delayed be required minus capacity
    if delayed is less than 0:
        set delayed to 0
    let windows be number from (required divided by 30)
    give back covered plus delayed times 8 plus windows times 11
""",
    },
    "bakery_batch_repair": {
        "seed": """
to bakery_tray_batches with sourdough_loaves as number, rye_loaves as number, oven_decks as number, overnight_proof as yesno giving number:
    let loaves be sourdough_loaves plus rye_loaves
    give back number from (loaves divided by 12)
""",
        "reference": """
to bakery_tray_batches with sourdough_loaves as number, rye_loaves as number, oven_decks as number, overnight_proof as yesno giving number:
    let loaves be sourdough_loaves plus rye_loaves
    give back number from ((loaves plus 11) divided by 12)
""",
    },
    "subsea_relay_repair": {
        "seed": """
to subsea_relay_reserve with shore_packets as number, vessel_packets as number, relay_nodes as number, storm_routing as yesno giving number:
    let required be shore_packets times 4 plus vessel_packets times 7
    if storm_routing:
        set required to required minus relay_nodes times 5
        if required is less than 0:
            set required to 0
    let capacity be relay_nodes times 24
    let forwarded be required
    if forwarded is more than capacity:
        set forwarded to capacity
    give back capacity minus forwarded
""",
        "reference": """
to subsea_relay_reserve with shore_packets as number, vessel_packets as number, relay_nodes as number, storm_routing as yesno giving number:
    let required be shore_packets times 4 plus vessel_packets times 7
    if storm_routing:
        set required to required plus relay_nodes times 5
    let capacity be relay_nodes times 24
    let forwarded be required
    if forwarded is more than capacity:
        set forwarded to capacity
    give back capacity minus forwarded
""",
    },
}

PARLEY_MAIN = {
    "radio_archive_build": """
include "logic.par"
a radio_request has spoken_segments as number, music_segments as number, language_tracks as number, live_broadcast as yesno
a radio_response has segment_total as number, speech_megabytes as number, music_megabytes as number, translation_megabytes as number, archive_megabytes as number, replica_megabytes as number, upload_blocks as number, archive_score as number, archive_mode as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Radio Archive", ready yes
to handle_request with request as radio_request giving radio_response:
    let segments be request's spoken_segments plus request's music_segments
    let speech be request's spoken_segments times 14
    let music be request's music_segments times 24
    let translation be 0
    if request's live_broadcast:
        set translation to request's language_tracks times 9
    let archive be speech plus music plus translation
    let blocks be number from (archive divided by 64)
    let mode be "catalog"
    if request's live_broadcast:
        set mode to "live"
        if request's language_tracks is more than 1:
            set mode to "multilingual_live"
    give back a radio_response with segment_total segments, speech_megabytes speech, music_megabytes music, translation_megabytes translation, archive_megabytes archive, replica_megabytes (archive times request's language_tracks), upload_blocks blocks, archive_score (radio_archive_score with request's spoken_segments, request's music_segments, request's language_tracks, request's live_broadcast), archive_mode mode
""",
    "theatre_turnaround_build": """
include "logic.par"
a theatre_request has matinee_shows as number, evening_shows as number, stage_crews as number, touring_production as yesno
a theatre_response has show_total as number, base_reset_minutes as number, touring_minutes as number, required_minutes as number, crew_capacity_minutes as number, covered_minutes as number, delayed_minutes as number, handoff_windows as number, turnaround_score as number, turnaround_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Theatre Turnaround", ready yes
to handle_request with request as theatre_request giving theatre_response:
    let base be request's matinee_shows times 18 plus request's evening_shows times 27
    let touring be 0
    if request's touring_production:
        set touring to request's stage_crews times 6
    let required be base plus touring
    let capacity be request's stage_crews times 45
    let covered be required
    if covered is more than capacity:
        set covered to capacity
    let delayed be required minus capacity
    if delayed is less than 0:
        set delayed to 0
    let windows be number from (required divided by 30)
    let state be "on_time"
    if delayed is more than 0:
        set state to "repertory_delay"
        if request's touring_production:
            set state to "touring_delay"
    give back a theatre_response with show_total (request's matinee_shows plus request's evening_shows), base_reset_minutes base, touring_minutes touring, required_minutes required, crew_capacity_minutes capacity, covered_minutes covered, delayed_minutes delayed, handoff_windows windows, turnaround_score (theatre_turnaround_score with request's matinee_shows, request's evening_shows, request's stage_crews, request's touring_production), turnaround_state state
""",
    "bakery_batch_repair": """
include "logic.par"
a bakery_request has sourdough_loaves as number, rye_loaves as number, oven_decks as number, overnight_proof as yesno
a bakery_response has loaf_total as number, sourdough_minutes as number, rye_minutes as number, proof_minutes as number, bake_minutes as number, rack_capacity_minutes as number, oven_minutes_used as number, unscheduled_minutes as number, tray_batches as number, bakery_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Bakery Batch", ready yes
to handle_request with request as bakery_request giving bakery_response:
    let loaves be request's sourdough_loaves plus request's rye_loaves
    let sourdough be request's sourdough_loaves times 11
    let rye be request's rye_loaves times 8
    let proof be 0
    if request's overnight_proof:
        set proof to loaves times 2
    let bake be sourdough plus rye plus proof
    let capacity be request's oven_decks times 48
    let used be bake
    if used is more than capacity:
        set used to capacity
    let unscheduled be bake minus capacity
    if unscheduled is less than 0:
        set unscheduled to 0
    let state be "ready"
    if unscheduled is more than 0:
        set state to "daytime_backlog"
        if request's overnight_proof:
            set state to "overnight_backlog"
    give back a bakery_response with loaf_total loaves, sourdough_minutes sourdough, rye_minutes rye, proof_minutes proof, bake_minutes bake, rack_capacity_minutes capacity, oven_minutes_used used, unscheduled_minutes unscheduled, tray_batches (bakery_tray_batches with request's sourdough_loaves, request's rye_loaves, request's oven_decks, request's overnight_proof), bakery_state state
""",
    "subsea_relay_repair": """
include "logic.par"
a relay_request has shore_packets as number, vessel_packets as number, relay_nodes as number, storm_routing as yesno
a relay_response has packet_total as number, shore_units as number, vessel_units as number, storm_units as number, required_units as number, relay_capacity_units as number, forwarded_units as number, dropped_units as number, reserve_units as number, relay_state as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Subsea Relay", ready yes
to handle_request with request as relay_request giving relay_response:
    let shore be request's shore_packets times 4
    let vessel be request's vessel_packets times 7
    let storm be 0
    if request's storm_routing:
        set storm to request's relay_nodes times 5
    let required be shore plus vessel plus storm
    let capacity be request's relay_nodes times 24
    let forwarded be required
    if forwarded is more than capacity:
        set forwarded to capacity
    let dropped be required minus capacity
    if dropped is less than 0:
        set dropped to 0
    let state be "clear"
    if dropped is more than 0:
        set state to "packet_loss"
        if request's storm_routing:
            set state to "storm_loss"
    give back a relay_response with packet_total (request's shore_packets plus request's vessel_packets), shore_units shore, vessel_units vessel, storm_units storm, required_units required, relay_capacity_units capacity, forwarded_units forwarded, dropped_units dropped, reserve_units (subsea_relay_reserve with request's shore_packets, request's vessel_packets, request's relay_nodes, request's storm_routing), relay_state state
""",
}

PYTHON_LOGIC = {
    "radio_archive_build": {variant: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); spoken_segments:int=Field(ge=0); music_segments:int=Field(ge=0); language_tracks:int=Field(ge=0); live_broadcast:bool
def radio_archive_score(s:int,m:int,l:int,v:bool)->int: {'return 0' if variant=='seed' else 'a=s*14+m*24+(l*9 if v else 0); return a*l+(a//64)*17+(s+m)*3'}
def handle(v:RequestInput)->dict[str,object]:
 p=v.spoken_segments*14; m=v.music_segments*24; t=v.language_tracks*9 if v.live_broadcast else 0; a=p+m+t
 return {{'segment_total':v.spoken_segments+v.music_segments,'speech_megabytes':p,'music_megabytes':m,'translation_megabytes':t,'archive_megabytes':a,'replica_megabytes':a*v.language_tracks,'upload_blocks':a//64,'archive_score':radio_archive_score(v.spoken_segments,v.music_segments,v.language_tracks,v.live_broadcast),'archive_mode':'multilingual_live' if v.live_broadcast and v.language_tracks>1 else 'live' if v.live_broadcast else 'catalog'}}
""" for variant in ('seed','reference')},
    "theatre_turnaround_build": {variant: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); matinee_shows:int=Field(ge=0); evening_shows:int=Field(ge=0); stage_crews:int=Field(ge=0); touring_production:bool
def theatre_turnaround_score(m:int,e:int,c:int,t:bool)->int: {'return 0' if variant=='seed' else 'r=m*18+e*27+(c*6 if t else 0); x=c*45; return min(r,x)+max(r-x,0)*8+(r//30)*11'}
def handle(v:RequestInput)->dict[str,object]:
 b=v.matinee_shows*18+v.evening_shows*27; t=v.stage_crews*6 if v.touring_production else 0; r=b+t; c=v.stage_crews*45; d=max(r-c,0)
 return {{'show_total':v.matinee_shows+v.evening_shows,'base_reset_minutes':b,'touring_minutes':t,'required_minutes':r,'crew_capacity_minutes':c,'covered_minutes':min(r,c),'delayed_minutes':d,'handoff_windows':r//30,'turnaround_score':theatre_turnaround_score(v.matinee_shows,v.evening_shows,v.stage_crews,v.touring_production),'turnaround_state':'on_time' if d==0 else 'touring_delay' if v.touring_production else 'repertory_delay'}}
""" for variant in ('seed','reference')},
    "bakery_batch_repair": {variant: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); sourdough_loaves:int=Field(ge=0); rye_loaves:int=Field(ge=0); oven_decks:int=Field(ge=0); overnight_proof:bool
def bakery_tray_batches(s:int,r:int,_d:int,_o:bool)->int: return {'(s+r)//12' if variant=='seed' else '(s+r+11)//12'}
def handle(v:RequestInput)->dict[str,object]:
 l=v.sourdough_loaves+v.rye_loaves; s=v.sourdough_loaves*11; r=v.rye_loaves*8; p=l*2 if v.overnight_proof else 0; b=s+r+p; c=v.oven_decks*48; u=max(b-c,0)
 return {{'loaf_total':l,'sourdough_minutes':s,'rye_minutes':r,'proof_minutes':p,'bake_minutes':b,'rack_capacity_minutes':c,'oven_minutes_used':min(b,c),'unscheduled_minutes':u,'tray_batches':bakery_tray_batches(v.sourdough_loaves,v.rye_loaves,v.oven_decks,v.overnight_proof),'bakery_state':'ready' if u==0 else 'overnight_backlog' if v.overnight_proof else 'daytime_backlog'}}
""" for variant in ('seed','reference')},
    "subsea_relay_repair": {variant: f"""from pydantic import BaseModel,ConfigDict,Field
class RequestInput(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True); shore_packets:int=Field(ge=0); vessel_packets:int=Field(ge=0); relay_nodes:int=Field(ge=0); storm_routing:bool
def subsea_relay_reserve(s:int,v:int,n:int,t:bool)->int:
 b=s*4+v*7; r={'max(b-(n*5 if t else 0),0)' if variant=='seed' else 'b+(n*5 if t else 0)'}; return max(n*24-min(r,n*24),0)
def handle(v:RequestInput)->dict[str,object]:
 s=v.shore_packets*4; x=v.vessel_packets*7; t=v.relay_nodes*5 if v.storm_routing else 0; r=s+x+t; c=v.relay_nodes*24; d=max(r-c,0)
 return {{'packet_total':v.shore_packets+v.vessel_packets,'shore_units':s,'vessel_units':x,'storm_units':t,'required_units':r,'relay_capacity_units':c,'forwarded_units':min(r,c),'dropped_units':d,'reserve_units':subsea_relay_reserve(v.shore_packets,v.vessel_packets,v.relay_nodes,v.storm_routing),'relay_state':'clear' if d==0 else 'storm_loss' if v.storm_routing else 'packet_loss'}}
""" for variant in ('seed','reference')},
}

PYTHON_BROWSER = {
    "radio_archive_build": {"seed": "const radioArchiveScore=()=>0n;", "reference": "const radioArchiveScore=(s,m,l,v)=>{const a=s*14+m*24+(v?l*9:0);return BigInt(a*l+Math.trunc(a/64)*17+(s+m)*3);};"},
    "theatre_turnaround_build": {"seed": "const theatreTurnaroundScore=()=>0n;", "reference": "const theatreTurnaroundScore=(m,e,c,t)=>{const r=m*18+e*27+(t?c*6:0),x=c*45;return BigInt(Math.min(r,x)+Math.max(r-x,0)*8+Math.trunc(r/30)*11);};"},
    "bakery_batch_repair": {"seed": "const bakeryTrayBatches=(s,r,d,o)=>BigInt(Math.trunc((s+r)/12));", "reference": "const bakeryTrayBatches=(s,r,d,o)=>BigInt(Math.trunc((s+r+11)/12));"},
    "subsea_relay_repair": {"seed": "const subseaRelayReserve=(s,v,n,t)=>{const r=Math.max(s*4+v*7-(t?n*5:0),0);return BigInt(Math.max(n*24-Math.min(r,n*24),0));};", "reference": "const subseaRelayReserve=(s,v,n,t)=>{const r=s*4+v*7+(t?n*5:0);return BigInt(Math.max(n*24-Math.min(r,n*24),0));};"},
}

PYTHON_BROWSER_EXPORT = {
    "radio_archive_build": ("radio_archive_score", "radioArchiveScore"),
    "theatre_turnaround_build": ("theatre_turnaround_score", "theatreTurnaroundScore"),
    "bakery_batch_repair": ("bakery_tray_batches", "bakeryTrayBatches"),
    "subsea_relay_repair": ("subsea_relay_reserve", "subseaRelayReserve"),
}

TYPESCRIPT_LOGIC = {
    "radio_archive_build": {v: f"""export type RequestInput={{spoken_segments:number;music_segments:number;language_tracks:number;live_broadcast:boolean}};export const score=(s:number,m:number,l:number,v:boolean)=>{{{'return 0' if v=='seed' else 'const a=s*14+m*24+(v?l*9:0);return a*l+Math.trunc(a/64)*17+(s+m)*3'}}};export const handle=(v:RequestInput)=>{{const p=v.spoken_segments*14,m=v.music_segments*24,t=v.live_broadcast?v.language_tracks*9:0,a=p+m+t;return {{segment_total:v.spoken_segments+v.music_segments,speech_megabytes:p,music_megabytes:m,translation_megabytes:t,archive_megabytes:a,replica_megabytes:a*v.language_tracks,upload_blocks:Math.trunc(a/64),archive_score:score(v.spoken_segments,v.music_segments,v.language_tracks,v.live_broadcast),archive_mode:v.live_broadcast&&v.language_tracks>1?'multilingual_live':v.live_broadcast?'live':'catalog'}}}};export async function loadParley(){{return {{radio_archive_score:(a:number,b:number,c:number,d:boolean)=>BigInt(score(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "theatre_turnaround_build": {v: f"""export type RequestInput={{matinee_shows:number;evening_shows:number;stage_crews:number;touring_production:boolean}};export const score=(m:number,e:number,c:number,t:boolean)=>{{{'return 0' if v=='seed' else 'const r=m*18+e*27+(t?c*6:0),x=c*45;return Math.min(r,x)+Math.max(r-x,0)*8+Math.trunc(r/30)*11'}}};export const handle=(v:RequestInput)=>{{const b=v.matinee_shows*18+v.evening_shows*27,t=v.touring_production?v.stage_crews*6:0,r=b+t,c=v.stage_crews*45,d=Math.max(r-c,0);return {{show_total:v.matinee_shows+v.evening_shows,base_reset_minutes:b,touring_minutes:t,required_minutes:r,crew_capacity_minutes:c,covered_minutes:Math.min(r,c),delayed_minutes:d,handoff_windows:Math.trunc(r/30),turnaround_score:score(v.matinee_shows,v.evening_shows,v.stage_crews,v.touring_production),turnaround_state:d===0?'on_time':v.touring_production?'touring_delay':'repertory_delay'}}}};export async function loadParley(){{return {{theatre_turnaround_score:(a:number,b:number,c:number,d:boolean)=>BigInt(score(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "bakery_batch_repair": {v: f"""export type RequestInput={{sourdough_loaves:number;rye_loaves:number;oven_decks:number;overnight_proof:boolean}};export const batches=(s:number,r:number,_d:number,_o:boolean)=>Math.trunc((s+r+{'0' if v=='seed' else '11'})/12);export const handle=(v:RequestInput)=>{{const l=v.sourdough_loaves+v.rye_loaves,s=v.sourdough_loaves*11,r=v.rye_loaves*8,p=v.overnight_proof?l*2:0,b=s+r+p,c=v.oven_decks*48,u=Math.max(b-c,0);return {{loaf_total:l,sourdough_minutes:s,rye_minutes:r,proof_minutes:p,bake_minutes:b,rack_capacity_minutes:c,oven_minutes_used:Math.min(b,c),unscheduled_minutes:u,tray_batches:batches(v.sourdough_loaves,v.rye_loaves,v.oven_decks,v.overnight_proof),bakery_state:u===0?'ready':v.overnight_proof?'overnight_backlog':'daytime_backlog'}}}};export async function loadParley(){{return {{bakery_tray_batches:(a:number,b:number,c:number,d:boolean)=>BigInt(batches(a,b,c,d))}}}}""" for v in ('seed','reference')},
    "subsea_relay_repair": {v: f"""export type RequestInput={{shore_packets:number;vessel_packets:number;relay_nodes:number;storm_routing:boolean}};export const reserve=(s:number,v:number,n:number,t:boolean)=>{{const b=s*4+v*7,r={'Math.max(b-(t?n*5:0),0)' if v=='seed' else 'b+(t?n*5:0)'};return Math.max(n*24-Math.min(r,n*24),0)}};export const handle=(v:RequestInput)=>{{const s=v.shore_packets*4,x=v.vessel_packets*7,t=v.storm_routing?v.relay_nodes*5:0,r=s+x+t,c=v.relay_nodes*24,d=Math.max(r-c,0);return {{packet_total:v.shore_packets+v.vessel_packets,shore_units:s,vessel_units:x,storm_units:t,required_units:r,relay_capacity_units:c,forwarded_units:Math.min(r,c),dropped_units:d,reserve_units:reserve(v.shore_packets,v.vessel_packets,v.relay_nodes,v.storm_routing),relay_state:d===0?'clear':v.storm_routing?'storm_loss':'packet_loss'}}}};export async function loadParley(){{return {{subsea_relay_reserve:(a:number,b:number,c:number,d:boolean)=>BigInt(reserve(a,b,c,d))}}}}""" for v in ('seed','reference')},
}

TS_SCHEMA = {
    "radio_archive_build": "z.object({ spoken_segments:z.number().int().nonnegative(), music_segments:z.number().int().nonnegative(), language_tracks:z.number().int().nonnegative(), live_broadcast:z.boolean() }).strict()",
    "theatre_turnaround_build": "z.object({ matinee_shows:z.number().int().nonnegative(), evening_shows:z.number().int().nonnegative(), stage_crews:z.number().int().nonnegative(), touring_production:z.boolean() }).strict()",
    "bakery_batch_repair": "z.object({ sourdough_loaves:z.number().int().nonnegative(), rye_loaves:z.number().int().nonnegative(), oven_decks:z.number().int().nonnegative(), overnight_proof:z.boolean() }).strict()",
    "subsea_relay_repair": "z.object({ shore_packets:z.number().int().nonnegative(), vessel_packets:z.number().int().nonnegative(), relay_nodes:z.number().int().nonnegative(), storm_routing:z.boolean() }).strict()",
}

RUST_LIB = {
    "radio_archive_build": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub spoken_segments:i64,pub music_segments:i64,pub language_tracks:i64,pub live_broadcast:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.spoken_segments>=0&&self.music_segments>=0&&self.language_tracks>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub segment_total:i64,pub speech_megabytes:i64,pub music_megabytes:i64,pub translation_megabytes:i64,pub archive_megabytes:i64,pub replica_megabytes:i64,pub upload_blocks:i64,pub archive_score:i64,pub archive_mode:String}}pub fn score(s:i64,m:i64,l:i64,v:bool)->i64{{{'0' if v=='seed' else 'let a=s*14+m*24+if v{l*9}else{0};a*l+(a/64)*17+(s+m)*3'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let p=v.spoken_segments*14;let m=v.music_segments*24;let t=if v.live_broadcast{{v.language_tracks*9}}else{{0}};let a=p+m+t;ResponseOutput{{segment_total:v.spoken_segments+v.music_segments,speech_megabytes:p,music_megabytes:m,translation_megabytes:t,archive_megabytes:a,replica_megabytes:a*v.language_tracks,upload_blocks:a/64,archive_score:score(v.spoken_segments,v.music_segments,v.language_tracks,v.live_broadcast),archive_mode:if v.live_broadcast&&v.language_tracks>1{{"multilingual_live"}}else if v.live_broadcast{{"live"}}else{{"catalog"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_radio_archive_score(a:i64,b:i64,c:i64,d:i32)->i64{{score(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "theatre_turnaround_build": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub matinee_shows:i64,pub evening_shows:i64,pub stage_crews:i64,pub touring_production:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.matinee_shows>=0&&self.evening_shows>=0&&self.stage_crews>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub show_total:i64,pub base_reset_minutes:i64,pub touring_minutes:i64,pub required_minutes:i64,pub crew_capacity_minutes:i64,pub covered_minutes:i64,pub delayed_minutes:i64,pub handoff_windows:i64,pub turnaround_score:i64,pub turnaround_state:String}}pub fn score(m:i64,e:i64,c:i64,t:bool)->i64{{{'0' if v=='seed' else 'let r=m*18+e*27+if t{c*6}else{0};let x=c*45;r.min(x)+(r-x).max(0)*8+(r/30)*11'}}}pub fn handle(v:RequestInput)->ResponseOutput{{let b=v.matinee_shows*18+v.evening_shows*27;let t=if v.touring_production{{v.stage_crews*6}}else{{0}};let r=b+t;let c=v.stage_crews*45;let d=(r-c).max(0);ResponseOutput{{show_total:v.matinee_shows+v.evening_shows,base_reset_minutes:b,touring_minutes:t,required_minutes:r,crew_capacity_minutes:c,covered_minutes:r.min(c),delayed_minutes:d,handoff_windows:r/30,turnaround_score:score(v.matinee_shows,v.evening_shows,v.stage_crews,v.touring_production),turnaround_state:if d==0{{"on_time"}}else if v.touring_production{{"touring_delay"}}else{{"repertory_delay"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_theatre_turnaround_score(a:i64,b:i64,c:i64,d:i32)->i64{{score(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "bakery_batch_repair": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub sourdough_loaves:i64,pub rye_loaves:i64,pub oven_decks:i64,pub overnight_proof:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.sourdough_loaves>=0&&self.rye_loaves>=0&&self.oven_decks>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub loaf_total:i64,pub sourdough_minutes:i64,pub rye_minutes:i64,pub proof_minutes:i64,pub bake_minutes:i64,pub rack_capacity_minutes:i64,pub oven_minutes_used:i64,pub unscheduled_minutes:i64,pub tray_batches:i64,pub bakery_state:String}}pub fn batches(s:i64,r:i64,_d:i64,_o:bool)->i64{{(s+r+{'0' if v=='seed' else '11'})/12}}pub fn handle(v:RequestInput)->ResponseOutput{{let l=v.sourdough_loaves+v.rye_loaves;let s=v.sourdough_loaves*11;let r=v.rye_loaves*8;let p=if v.overnight_proof{{l*2}}else{{0}};let b=s+r+p;let c=v.oven_decks*48;let u=(b-c).max(0);ResponseOutput{{loaf_total:l,sourdough_minutes:s,rye_minutes:r,proof_minutes:p,bake_minutes:b,rack_capacity_minutes:c,oven_minutes_used:b.min(c),unscheduled_minutes:u,tray_batches:batches(v.sourdough_loaves,v.rye_loaves,v.oven_decks,v.overnight_proof),bakery_state:if u==0{{"ready"}}else if v.overnight_proof{{"overnight_backlog"}}else{{"daytime_backlog"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_bakery_batches(a:i64,b:i64,c:i64,d:i32)->i64{{batches(a,b,c,d!=0)}}""" for v in ('seed','reference')},
    "subsea_relay_repair": {v: f"""use serde::{{Deserialize,Serialize}};#[derive(Deserialize)]#[serde(deny_unknown_fields)]pub struct RequestInput{{pub shore_packets:i64,pub vessel_packets:i64,pub relay_nodes:i64,pub storm_routing:bool}}impl RequestInput{{pub fn valid(&self)->bool{{self.shore_packets>=0&&self.vessel_packets>=0&&self.relay_nodes>=0}}}}#[derive(Serialize)]pub struct ResponseOutput{{pub packet_total:i64,pub shore_units:i64,pub vessel_units:i64,pub storm_units:i64,pub required_units:i64,pub relay_capacity_units:i64,pub forwarded_units:i64,pub dropped_units:i64,pub reserve_units:i64,pub relay_state:String}}pub fn reserve(s:i64,v:i64,n:i64,t:bool)->i64{{let b=s*4+v*7;let r={'(b-if t{n*5}else{0}).max(0)' if v=='seed' else 'b+if t{n*5}else{0}'};(n*24-r.min(n*24)).max(0)}}pub fn handle(v:RequestInput)->ResponseOutput{{let s=v.shore_packets*4;let x=v.vessel_packets*7;let t=if v.storm_routing{{v.relay_nodes*5}}else{{0}};let r=s+x+t;let c=v.relay_nodes*24;let d=(r-c).max(0);ResponseOutput{{packet_total:v.shore_packets+v.vessel_packets,shore_units:s,vessel_units:x,storm_units:t,required_units:r,relay_capacity_units:c,forwarded_units:r.min(c),dropped_units:d,reserve_units:reserve(v.shore_packets,v.vessel_packets,v.relay_nodes,v.storm_routing),relay_state:if d==0{{"clear"}}else if v.storm_routing{{"storm_loss"}}else{{"packet_loss"}}.into()}}}}#[unsafe(no_mangle)]pub extern "C" fn parley_subsea_relay_reserve(a:i64,b:i64,c:i64,d:i32)->i64{{reserve(a,b,c,d!=0)}}""" for v in ('seed','reference')},
}

RUST_WASM = {
    "radio_archive_build": ("parley_radio_archive_score", ["a", "b", "c", "d ? 1 : 0"]),
    "theatre_turnaround_build": ("parley_theatre_turnaround_score", ["a", "b", "c", "d ? 1 : 0"]),
    "bakery_batch_repair": ("parley_bakery_batches", ["a", "b", "c", "d ? 1 : 0"]),
    "subsea_relay_repair": ("parley_subsea_relay_reserve", ["a", "b", "c", "d ? 1 : 0"]),
}
