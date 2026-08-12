"""Frozen task-specific reference and seed logic for full-stack study 038."""

PARLEY_LOGIC = {
    "ferry_manifest_build": {
        "seed": """
to traveller_total with adult_count as number, youth_count as number giving number:
    give back 0
to passenger_charge with adult_count as number, youth_count as number giving number:
    give back 0
to vehicle_charge with vehicle_count as number giving number:
    give back 0
to peak_charge with adult_count as number, youth_count as number, vehicle_count as number, peak_departure as yesno giving number:
    give back 0
to manifest_charge with adult_count as number, youth_count as number, vehicle_count as number, peak_departure as yesno giving number:
    give back 0
""",
        "reference": """
to traveller_total with adult_count as number, youth_count as number giving number:
    give back adult_count plus youth_count
to passenger_charge with adult_count as number, youth_count as number giving number:
    give back adult_count times 1100 plus youth_count times 650
to vehicle_charge with vehicle_count as number giving number:
    give back vehicle_count times 2400
to peak_charge with adult_count as number, youth_count as number, vehicle_count as number, peak_departure as yesno giving number:
    if peak_departure:
        give back (traveller_total with adult_count, youth_count) times 125 plus vehicle_count times 350
    give back 0
to manifest_charge with adult_count as number, youth_count as number, vehicle_count as number, peak_departure as yesno giving number:
    give back (passenger_charge with adult_count, youth_count) plus (vehicle_charge with vehicle_count) plus (peak_charge with adult_count, youth_count, vehicle_count, peak_departure)
""",
    },
    "archive_retention_build": {
        "seed": """
to page_total with document_count as number, pages_each as number giving number:
    give back 0
to base_months with requested_years as number giving number:
    give back 0
to retained_months with requested_years as number, legal_hold as yesno giving number:
    give back 0
to review_batches with document_count as number, pages_each as number giving number:
    give back 0
to retention_index with document_count as number, pages_each as number, requested_years as number, legal_hold as yesno giving number:
    give back 0
""",
        "reference": """
to page_total with document_count as number, pages_each as number giving number:
    give back document_count times pages_each
to base_months with requested_years as number giving number:
    give back requested_years times 12
to retained_months with requested_years as number, legal_hold as yesno giving number:
    let months be (base_months with requested_years)
    if legal_hold:
        if months is less than 84:
            give back 84
    give back months
to review_batches with document_count as number, pages_each as number giving number:
    let pages be (page_total with document_count, pages_each)
    give back number from ((pages plus 199) divided by 200)
to retention_index with document_count as number, pages_each as number, requested_years as number, legal_hold as yesno giving number:
    give back (retained_months with requested_years, legal_hold) plus (review_batches with document_count, pages_each) times 3
""",
    },
    "loyalty_stamps_repair": {
        "seed": """
to base_stamps with purchase_count as number, stamps_each as number giving number:
    give back purchase_count times stamps_each
to bonus_stamps with purchase_count as number, double_day as yesno giving number:
    if double_day:
        give back purchase_count
    give back 0
to spendable_stamps with purchase_count as number, stamps_each as number, claimed_stamps as number, double_day as yesno giving number:
    let spendable be (base_stamps with purchase_count, stamps_each) plus (bonus_stamps with purchase_count, double_day) minus claimed_stamps
    if spendable is less than 0:
        give back 0
    give back spendable
to claimable_rewards with purchase_count as number, stamps_each as number, claimed_stamps as number, double_day as yesno giving number:
    let earned be (base_stamps with purchase_count, stamps_each) plus (bonus_stamps with purchase_count, double_day)
    give back number from (earned divided by 10)
""",
        "reference": """
to base_stamps with purchase_count as number, stamps_each as number giving number:
    give back purchase_count times stamps_each
to bonus_stamps with purchase_count as number, double_day as yesno giving number:
    if double_day:
        give back purchase_count
    give back 0
to spendable_stamps with purchase_count as number, stamps_each as number, claimed_stamps as number, double_day as yesno giving number:
    let spendable be (base_stamps with purchase_count, stamps_each) plus (bonus_stamps with purchase_count, double_day) minus claimed_stamps
    if spendable is less than 0:
        give back 0
    give back spendable
to claimable_rewards with purchase_count as number, stamps_each as number, claimed_stamps as number, double_day as yesno giving number:
    give back number from ((spendable_stamps with purchase_count, stamps_each, claimed_stamps, double_day) divided by 10)
""",
    },
    "cold_storage_repair": {
        "seed": """
to corrected_degrees with measured_degrees as number, door_open as yesno giving number:
    give back measured_degrees
to required_cooling with measured_degrees as number, target_degrees as number, allowed_drift as number, door_open as yesno giving number:
    let excess be (corrected_degrees with measured_degrees, door_open) minus target_degrees minus allowed_drift
    if excess is less than 0:
        set excess to 0
    give back number from ((excess plus 2) divided by 3)
""",
        "reference": """
to corrected_degrees with measured_degrees as number, door_open as yesno giving number:
    if door_open:
        give back measured_degrees plus 2
    give back measured_degrees
to required_cooling with measured_degrees as number, target_degrees as number, allowed_drift as number, door_open as yesno giving number:
    let excess be (corrected_degrees with measured_degrees, door_open) minus target_degrees minus allowed_drift
    if excess is less than 0:
        set excess to 0
    give back number from ((excess plus 2) divided by 3)
""",
    },
}

PARLEY_MAIN = {
    "ferry_manifest_build": """
include "logic.par"
a ferry_request has adult_count as number, youth_count as number, vehicle_count as number, peak_departure as yesno
a ferry_response has traveller_total as number, passenger_charge_cents as number, vehicle_charge_cents as number, peak_charge_cents as number, manifest_charge_cents as number, boarding_load as number, travel_mode as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Ferry Manifest", ready yes
to handle_request with request as ferry_request giving ferry_response:
    let travellers be (traveller_total with request's adult_count, request's youth_count)
    let passenger be (passenger_charge with request's adult_count, request's youth_count)
    let vehicle be (vehicle_charge with request's vehicle_count)
    let peak be (peak_charge with request's adult_count, request's youth_count, request's vehicle_count, request's peak_departure)
    let mode be "foot"
    if request's vehicle_count is more than 0:
        set mode to "vehicle"
        if travellers is more than 0:
            set mode to "mixed"
    give back a ferry_response with traveller_total travellers, passenger_charge_cents passenger, vehicle_charge_cents vehicle, peak_charge_cents peak, manifest_charge_cents (manifest_charge with request's adult_count, request's youth_count, request's vehicle_count, request's peak_departure), boarding_load travellers plus request's vehicle_count times 3, travel_mode mode
""",
    "archive_retention_build": """
include "logic.par"
an archive_request has document_count as number, pages_each as number, requested_years as number, legal_hold as yesno
an archive_response has page_total as number, base_months as number, retained_months as number, review_batches as number, retention_score as number, retention_class as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Archive Retention", ready yes
to handle_request with request as archive_request giving archive_response:
    let pages be (page_total with request's document_count, request's pages_each)
    let base be (base_months with request's requested_years)
    let retained be (retained_months with request's requested_years, request's legal_hold)
    let batches be (review_batches with request's document_count, request's pages_each)
    let classification be "standard"
    if request's legal_hold:
        set classification to "held"
    give back an archive_response with page_total pages, base_months base, retained_months retained, review_batches batches, retention_score (retention_index with request's document_count, request's pages_each, request's requested_years, request's legal_hold), retention_class classification
""",
    "loyalty_stamps_repair": """
include "logic.par"
a loyalty_request has purchase_count as number, stamps_each as number, claimed_stamps as number, double_day as yesno
a loyalty_response has base_stamps as number, bonus_stamps as number, spendable_stamps as number, reward_count as number, leftover_stamps as number, reward_stage as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Loyalty Stamps", ready yes
to handle_request with request as loyalty_request giving loyalty_response:
    let base be (base_stamps with request's purchase_count, request's stamps_each)
    let bonus be (bonus_stamps with request's purchase_count, request's double_day)
    let spendable be (spendable_stamps with request's purchase_count, request's stamps_each, request's claimed_stamps, request's double_day)
    let rewards be (claimable_rewards with request's purchase_count, request's stamps_each, request's claimed_stamps, request's double_day)
    let stage be "collecting"
    if rewards is more than 0:
        set stage to "ready"
    give back a loyalty_response with base_stamps base, bonus_stamps bonus, spendable_stamps spendable, reward_count rewards, leftover_stamps spendable minus rewards times 10, reward_stage stage
""",
    "cold_storage_repair": """
include "logic.par"
a cold_request has measured_degrees as number, target_degrees as number, allowed_drift as number, door_open as yesno
a cold_response has corrected_degrees as number, temperature_gap as number, excess_heat as number, cooling_steps as number, safe_flag as yesno, storage_condition as text
a service_status has service as text, ready as yesno
to project_status giving service_status:
    give back a service_status with service "Cold Storage", ready yes
to handle_request with request as cold_request giving cold_response:
    let corrected be (corrected_degrees with request's measured_degrees, request's door_open)
    let gap be corrected minus request's target_degrees
    if gap is less than 0:
        set gap to 0 minus gap
    let excess be corrected minus request's target_degrees minus request's allowed_drift
    if excess is less than 0:
        set excess to 0
    let steps be (required_cooling with request's measured_degrees, request's target_degrees, request's allowed_drift, request's door_open)
    let safe be no
    let condition be "warming"
    if gap is less than request's allowed_drift plus 1:
        set safe to yes
        set condition to "stable"
    otherwise:
        if corrected is more than request's target_degrees:
            set condition to "cooling"
    give back a cold_response with corrected_degrees corrected, temperature_gap gap, excess_heat excess, cooling_steps steps, safe_flag safe, storage_condition condition
""",
}

PYTHON_LOGIC = {
    "ferry_manifest_build": {},
    "archive_retention_build": {},
    "loyalty_stamps_repair": {},
    "cold_storage_repair": {},
}

PYTHON_LOGIC["ferry_manifest_build"] = {
    "seed": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    adult_count: int = Field(ge=0); youth_count: int = Field(ge=0); vehicle_count: int = Field(ge=0); peak_departure: bool
def traveller_total(adults: int, youths: int) -> int: return 0
def passenger_charge(adults: int, youths: int) -> int: return 0
def vehicle_charge(vehicles: int) -> int: return 0
def peak_charge(adults: int, youths: int, vehicles: int, peak: bool) -> int: return 0
def manifest_charge(adults: int, youths: int, vehicles: int, peak: bool) -> int: return 0
def handle(value: RequestInput) -> dict[str, object]:
    travellers = traveller_total(value.adult_count, value.youth_count); vehicle = vehicle_charge(value.vehicle_count)
    mode = "mixed" if value.vehicle_count > 0 and travellers > 0 else "vehicle" if value.vehicle_count > 0 else "foot"
    return {"traveller_total": travellers, "passenger_charge_cents": passenger_charge(value.adult_count, value.youth_count), "vehicle_charge_cents": vehicle, "peak_charge_cents": peak_charge(value.adult_count, value.youth_count, value.vehicle_count, value.peak_departure), "manifest_charge_cents": manifest_charge(value.adult_count, value.youth_count, value.vehicle_count, value.peak_departure), "boarding_load": travellers + value.vehicle_count * 3, "travel_mode": mode}
""",
    "reference": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    adult_count: int = Field(ge=0); youth_count: int = Field(ge=0); vehicle_count: int = Field(ge=0); peak_departure: bool
def traveller_total(adults: int, youths: int) -> int: return adults + youths
def passenger_charge(adults: int, youths: int) -> int: return adults * 1100 + youths * 650
def vehicle_charge(vehicles: int) -> int: return vehicles * 2400
def peak_charge(adults: int, youths: int, vehicles: int, peak: bool) -> int: return traveller_total(adults, youths) * 125 + vehicles * 350 if peak else 0
def manifest_charge(adults: int, youths: int, vehicles: int, peak: bool) -> int: return passenger_charge(adults, youths) + vehicle_charge(vehicles) + peak_charge(adults, youths, vehicles, peak)
def handle(value: RequestInput) -> dict[str, object]:
    travellers = traveller_total(value.adult_count, value.youth_count); vehicle = vehicle_charge(value.vehicle_count)
    mode = "mixed" if value.vehicle_count > 0 and travellers > 0 else "vehicle" if value.vehicle_count > 0 else "foot"
    return {"traveller_total": travellers, "passenger_charge_cents": passenger_charge(value.adult_count, value.youth_count), "vehicle_charge_cents": vehicle, "peak_charge_cents": peak_charge(value.adult_count, value.youth_count, value.vehicle_count, value.peak_departure), "manifest_charge_cents": manifest_charge(value.adult_count, value.youth_count, value.vehicle_count, value.peak_departure), "boarding_load": travellers + value.vehicle_count * 3, "travel_mode": mode}
""",
}

PYTHON_LOGIC["archive_retention_build"] = {
    "seed": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    document_count: int = Field(ge=0); pages_each: int = Field(ge=0); requested_years: int = Field(ge=0); legal_hold: bool
def page_total(documents: int, pages: int) -> int: return 0
def base_months(years: int) -> int: return 0
def retained_months(years: int, held: bool) -> int: return 0
def review_batches(documents: int, pages: int) -> int: return 0
def retention_index(documents: int, pages: int, years: int, held: bool) -> int: return 0
def handle(value: RequestInput) -> dict[str, object]:
    total = page_total(value.document_count, value.pages_each); base = base_months(value.requested_years); retained = retained_months(value.requested_years, value.legal_hold); batches = review_batches(value.document_count, value.pages_each)
    return {"page_total": total, "base_months": base, "retained_months": retained, "review_batches": batches, "retention_score": retention_index(value.document_count, value.pages_each, value.requested_years, value.legal_hold), "retention_class": "held" if value.legal_hold else "standard"}
""",
    "reference": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    document_count: int = Field(ge=0); pages_each: int = Field(ge=0); requested_years: int = Field(ge=0); legal_hold: bool
def page_total(documents: int, pages: int) -> int: return documents * pages
def base_months(years: int) -> int: return years * 12
def retained_months(years: int, held: bool) -> int: return max(base_months(years), 84) if held else base_months(years)
def review_batches(documents: int, pages: int) -> int: return (page_total(documents, pages) + 199) // 200
def retention_index(documents: int, pages: int, years: int, held: bool) -> int: return retained_months(years, held) + review_batches(documents, pages) * 3
def handle(value: RequestInput) -> dict[str, object]:
    total = page_total(value.document_count, value.pages_each); base = base_months(value.requested_years); retained = retained_months(value.requested_years, value.legal_hold); batches = review_batches(value.document_count, value.pages_each)
    return {"page_total": total, "base_months": base, "retained_months": retained, "review_batches": batches, "retention_score": retention_index(value.document_count, value.pages_each, value.requested_years, value.legal_hold), "retention_class": "held" if value.legal_hold else "standard"}
""",
}

PYTHON_LOGIC["loyalty_stamps_repair"] = {
    "seed": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    purchase_count: int = Field(ge=0); stamps_each: int = Field(ge=0); claimed_stamps: int = Field(ge=0); double_day: bool
def base_stamps(purchases: int, each: int) -> int: return purchases * each
def bonus_stamps(purchases: int, double: bool) -> int: return purchases if double else 0
def spendable_stamps(purchases: int, each: int, claimed: int, double: bool) -> int: return max(base_stamps(purchases, each) + bonus_stamps(purchases, double) - claimed, 0)
def reward_count(purchases: int, each: int, claimed: int, double: bool) -> int: return (base_stamps(purchases, each) + bonus_stamps(purchases, double)) // 10
def handle(value: RequestInput) -> dict[str, object]:
    base = base_stamps(value.purchase_count, value.stamps_each); bonus = bonus_stamps(value.purchase_count, value.double_day); spendable = spendable_stamps(value.purchase_count, value.stamps_each, value.claimed_stamps, value.double_day); rewards = reward_count(value.purchase_count, value.stamps_each, value.claimed_stamps, value.double_day)
    return {"base_stamps": base, "bonus_stamps": bonus, "spendable_stamps": spendable, "reward_count": rewards, "leftover_stamps": spendable - rewards * 10, "reward_stage": "ready" if rewards > 0 else "collecting"}
""",
    "reference": """
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    purchase_count: int = Field(ge=0); stamps_each: int = Field(ge=0); claimed_stamps: int = Field(ge=0); double_day: bool
def base_stamps(purchases: int, each: int) -> int: return purchases * each
def bonus_stamps(purchases: int, double: bool) -> int: return purchases if double else 0
def spendable_stamps(purchases: int, each: int, claimed: int, double: bool) -> int: return max(base_stamps(purchases, each) + bonus_stamps(purchases, double) - claimed, 0)
def reward_count(purchases: int, each: int, claimed: int, double: bool) -> int: return spendable_stamps(purchases, each, claimed, double) // 10
def handle(value: RequestInput) -> dict[str, object]:
    base = base_stamps(value.purchase_count, value.stamps_each); bonus = bonus_stamps(value.purchase_count, value.double_day); spendable = spendable_stamps(value.purchase_count, value.stamps_each, value.claimed_stamps, value.double_day); rewards = reward_count(value.purchase_count, value.stamps_each, value.claimed_stamps, value.double_day)
    return {"base_stamps": base, "bonus_stamps": bonus, "spendable_stamps": spendable, "reward_count": rewards, "leftover_stamps": spendable - rewards * 10, "reward_stage": "ready" if rewards > 0 else "collecting"}
""",
}

PYTHON_LOGIC["cold_storage_repair"] = {
    variant: f"""
from pydantic import BaseModel, ConfigDict, Field
class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    measured_degrees: int = Field(ge=0); target_degrees: int = Field(ge=0); allowed_drift: int = Field(ge=0); door_open: bool
def corrected_degrees(measured: int, door: bool) -> int: return measured{'' if variant == 'seed' else ' + (2 if door else 0)'}
def handle(value: RequestInput) -> dict[str, object]:
    corrected = corrected_degrees(value.measured_degrees, value.door_open); gap = abs(corrected - value.target_degrees); excess = max(corrected - value.target_degrees - value.allowed_drift, 0); steps = (excess + 2) // 3; safe = gap <= value.allowed_drift
    return {{"corrected_degrees": corrected, "temperature_gap": gap, "excess_heat": excess, "cooling_steps": steps, "safe_flag": safe, "storage_condition": "stable" if safe else "cooling" if corrected > value.target_degrees else "warming"}}
"""
    for variant in ("seed", "reference")
}

PYTHON_BROWSER = {
    "ferry_manifest_build": {"seed": "const manifestCharge = () => 0n;", "reference": "const manifestCharge = (adults, youths, vehicles, peak) => BigInt(adults * 1100 + youths * 650 + vehicles * 2400 + (peak ? (adults + youths) * 125 + vehicles * 350 : 0));"},
    "archive_retention_build": {"seed": "const retentionIndex = () => 0n;", "reference": "const retentionIndex = (documents, pages, years, held) => { const total = documents * pages; const months = held ? Math.max(years * 12, 84) : years * 12; return BigInt(months + Math.trunc((total + 199) / 200) * 3); };"},
    "loyalty_stamps_repair": {"seed": "const claimableRewards = (purchases, each, claimed, doubleDay) => BigInt(Math.trunc((purchases * each + (doubleDay ? purchases : 0)) / 10));", "reference": "const claimableRewards = (purchases, each, claimed, doubleDay) => BigInt(Math.trunc(Math.max(purchases * each + (doubleDay ? purchases : 0) - claimed, 0) / 10));"},
    "cold_storage_repair": {"seed": "const requiredCooling = (measured, target, drift, doorOpen) => BigInt(Math.trunc((Math.max(measured - target - drift, 0) + 2) / 3));", "reference": "const requiredCooling = (measured, target, drift, doorOpen) => BigInt(Math.trunc((Math.max(measured + (doorOpen ? 2 : 0) - target - drift, 0) + 2) / 3));"},
}

PYTHON_BROWSER_EXPORT = {
    "ferry_manifest_build": ("manifest_charge", "manifestCharge"),
    "archive_retention_build": ("retention_index", "retentionIndex"),
    "loyalty_stamps_repair": ("claimable_rewards", "claimableRewards"),
    "cold_storage_repair": ("required_cooling", "requiredCooling"),
}

TYPESCRIPT_LOGIC = {
    task: {variant: PYTHON_LOGIC[task][variant] for variant in ("seed", "reference")}
    for task in ()
}

TYPESCRIPT_LOGIC = {
    "ferry_manifest_build": {
        "seed": """export type RequestInput = { adult_count: number; youth_count: number; vehicle_count: number; peak_departure: boolean };
export const manifestCharge = (_a: number, _y: number, _v: number, _p: boolean) => 0;
export const handle = (v: RequestInput) => { const travellers=v.adult_count+v.youth_count; const passenger=v.adult_count*1100+v.youth_count*650; const vehicle=v.vehicle_count*2400; const peak=v.peak_departure?travellers*125+v.vehicle_count*350:0; return { traveller_total:travellers, passenger_charge_cents:passenger, vehicle_charge_cents:vehicle, peak_charge_cents:peak, manifest_charge_cents:manifestCharge(v.adult_count,v.youth_count,v.vehicle_count,v.peak_departure), boarding_load:travellers+v.vehicle_count*3, travel_mode:v.vehicle_count>0?(travellers>0?"mixed":"vehicle"):"foot" }; };
export async function loadParley(){return {manifest_charge:(a:number,y:number,v:number,p:boolean)=>BigInt(manifestCharge(a,y,v,p))};}""",
        "reference": """export type RequestInput = { adult_count: number; youth_count: number; vehicle_count: number; peak_departure: boolean };
export const manifestCharge = (a: number, y: number, v: number, p: boolean) => a*1100+y*650+v*2400+(p?(a+y)*125+v*350:0);
export const handle = (v: RequestInput) => { const travellers=v.adult_count+v.youth_count; const passenger=v.adult_count*1100+v.youth_count*650; const vehicle=v.vehicle_count*2400; const peak=v.peak_departure?travellers*125+v.vehicle_count*350:0; return { traveller_total:travellers, passenger_charge_cents:passenger, vehicle_charge_cents:vehicle, peak_charge_cents:peak, manifest_charge_cents:manifestCharge(v.adult_count,v.youth_count,v.vehicle_count,v.peak_departure), boarding_load:travellers+v.vehicle_count*3, travel_mode:v.vehicle_count>0?(travellers>0?"mixed":"vehicle"):"foot" }; };
export async function loadParley(){return {manifest_charge:(a:number,y:number,v:number,p:boolean)=>BigInt(manifestCharge(a,y,v,p))};}""",
    },
    "archive_retention_build": {
        "seed": """export type RequestInput={document_count:number;pages_each:number;requested_years:number;legal_hold:boolean};
export const retentionIndex=(_d:number,_p:number,_y:number,_h:boolean)=>0;
export const handle=(v:RequestInput)=>{const total=v.document_count*v.pages_each;const base=v.requested_years*12;const retained=v.legal_hold?Math.max(base,84):base;const batches=Math.trunc((total+199)/200);return {page_total:total,base_months:base,retained_months:retained,review_batches:batches,retention_score:retentionIndex(v.document_count,v.pages_each,v.requested_years,v.legal_hold),retention_class:v.legal_hold?"held":"standard"};};
export async function loadParley(){return {retention_index:(d:number,p:number,y:number,h:boolean)=>BigInt(retentionIndex(d,p,y,h))};}""",
        "reference": """export type RequestInput={document_count:number;pages_each:number;requested_years:number;legal_hold:boolean};
export const retentionIndex=(d:number,p:number,y:number,h:boolean)=>(h?Math.max(y*12,84):y*12)+Math.trunc((d*p+199)/200)*3;
export const handle=(v:RequestInput)=>{const total=v.document_count*v.pages_each;const base=v.requested_years*12;const retained=v.legal_hold?Math.max(base,84):base;const batches=Math.trunc((total+199)/200);return {page_total:total,base_months:base,retained_months:retained,review_batches:batches,retention_score:retentionIndex(v.document_count,v.pages_each,v.requested_years,v.legal_hold),retention_class:v.legal_hold?"held":"standard"};};
export async function loadParley(){return {retention_index:(d:number,p:number,y:number,h:boolean)=>BigInt(retentionIndex(d,p,y,h))};}""",
    },
    "loyalty_stamps_repair": {
        variant: f"""export type RequestInput={{purchase_count:number;stamps_each:number;claimed_stamps:number;double_day:boolean}};
export const claimableRewards=(p:number,e:number,c:number,d:boolean)=>Math.trunc({('(p*e+(d?p:0))' if variant == 'seed' else 'Math.max(p*e+(d?p:0)-c,0)')}/10);
export const handle=(v:RequestInput)=>{{const base=v.purchase_count*v.stamps_each;const bonus=v.double_day?v.purchase_count:0;const spendable=Math.max(base+bonus-v.claimed_stamps,0);const rewards=claimableRewards(v.purchase_count,v.stamps_each,v.claimed_stamps,v.double_day);return {{base_stamps:base,bonus_stamps:bonus,spendable_stamps:spendable,reward_count:rewards,leftover_stamps:spendable-rewards*10,reward_stage:rewards>0?"ready":"collecting"}};}};
export async function loadParley(){{return {{claimable_rewards:(p:number,e:number,c:number,d:boolean)=>BigInt(claimableRewards(p,e,c,d))}};}}"""
        for variant in ("seed", "reference")
    },
    "cold_storage_repair": {
        variant: f"""export type RequestInput={{measured_degrees:number;target_degrees:number;allowed_drift:number;door_open:boolean}};
export const correctedDegrees=(m:number,d:boolean)=>m{'' if variant == 'seed' else '+(d?2:0)'};
export const requiredCooling=(m:number,t:number,a:number,d:boolean)=>Math.trunc((Math.max(correctedDegrees(m,d)-t-a,0)+2)/3);
export const handle=(v:RequestInput)=>{{const corrected=correctedDegrees(v.measured_degrees,v.door_open);const gap=Math.abs(corrected-v.target_degrees);const excess=Math.max(corrected-v.target_degrees-v.allowed_drift,0);const safe=gap<=v.allowed_drift;return {{corrected_degrees:corrected,temperature_gap:gap,excess_heat:excess,cooling_steps:requiredCooling(v.measured_degrees,v.target_degrees,v.allowed_drift,v.door_open),safe_flag:safe,storage_condition:safe?"stable":corrected>v.target_degrees?"cooling":"warming"}};}};
export async function loadParley(){{return {{required_cooling:(m:number,t:number,a:number,d:boolean)=>BigInt(requiredCooling(m,t,a,d))}};}}"""
        for variant in ("seed", "reference")
    },
}

TS_SCHEMA = {
    "ferry_manifest_build": "z.object({ adult_count:z.number().int().nonnegative(), youth_count:z.number().int().nonnegative(), vehicle_count:z.number().int().nonnegative(), peak_departure:z.boolean() }).strict()",
    "archive_retention_build": "z.object({ document_count:z.number().int().nonnegative(), pages_each:z.number().int().nonnegative(), requested_years:z.number().int().nonnegative(), legal_hold:z.boolean() }).strict()",
    "loyalty_stamps_repair": "z.object({ purchase_count:z.number().int().nonnegative(), stamps_each:z.number().int().nonnegative(), claimed_stamps:z.number().int().nonnegative(), double_day:z.boolean() }).strict()",
    "cold_storage_repair": "z.object({ measured_degrees:z.number().int().nonnegative(), target_degrees:z.number().int().nonnegative(), allowed_drift:z.number().int().nonnegative(), door_open:z.boolean() }).strict()",
}

RUST_LIB = {
    "ferry_manifest_build": {
        variant: f"""use serde::{{Deserialize,Serialize}};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput{{pub adult_count:i64,pub youth_count:i64,pub vehicle_count:i64,pub peak_departure:bool}}
impl RequestInput{{pub fn valid(&self)->bool{{self.adult_count>=0&&self.youth_count>=0&&self.vehicle_count>=0}}}}
#[derive(Serialize)] pub struct ResponseOutput{{pub traveller_total:i64,pub passenger_charge_cents:i64,pub vehicle_charge_cents:i64,pub peak_charge_cents:i64,pub manifest_charge_cents:i64,pub boarding_load:i64,pub travel_mode:String}}
pub fn manifest_charge(a:i64,y:i64,v:i64,p:bool)->i64{{{'0' if variant == 'seed' else 'a*1100+y*650+v*2400+if p{(a+y)*125+v*350}else{0}'}}}
pub fn handle(x:RequestInput)->ResponseOutput{{let travellers=x.adult_count+x.youth_count;let passenger=x.adult_count*1100+x.youth_count*650;let vehicle=x.vehicle_count*2400;let peak=if x.peak_departure{{travellers*125+x.vehicle_count*350}}else{{0}};let mode=if x.vehicle_count>0{{if travellers>0{{"mixed"}}else{{"vehicle"}}}}else{{"foot"}};ResponseOutput{{traveller_total:travellers,passenger_charge_cents:passenger,vehicle_charge_cents:vehicle,peak_charge_cents:peak,manifest_charge_cents:manifest_charge(x.adult_count,x.youth_count,x.vehicle_count,x.peak_departure),boarding_load:travellers+x.vehicle_count*3,travel_mode:mode.into()}}}}
#[unsafe(no_mangle)] pub extern "C" fn parley_manifest_charge(a:i64,y:i64,v:i64,p:i32)->i64{{manifest_charge(a,y,v,p!=0)}}"""
        for variant in ("seed", "reference")
    },
    "archive_retention_build": {
        variant: f"""use serde::{{Deserialize,Serialize}};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput{{pub document_count:i64,pub pages_each:i64,pub requested_years:i64,pub legal_hold:bool}}
impl RequestInput{{pub fn valid(&self)->bool{{self.document_count>=0&&self.pages_each>=0&&self.requested_years>=0}}}}
#[derive(Serialize)] pub struct ResponseOutput{{pub page_total:i64,pub base_months:i64,pub retained_months:i64,pub review_batches:i64,pub retention_score:i64,pub retention_class:String}}
pub fn retention_index(d:i64,p:i64,y:i64,h:bool)->i64{{{'0' if variant == 'seed' else '(if h{(y*12).max(84)}else{y*12})+(d*p+199)/200*3'}}}
pub fn handle(x:RequestInput)->ResponseOutput{{let total=x.document_count*x.pages_each;let base=x.requested_years*12;let retained=if x.legal_hold{{base.max(84)}}else{{base}};let batches=(total+199)/200;ResponseOutput{{page_total:total,base_months:base,retained_months:retained,review_batches:batches,retention_score:retention_index(x.document_count,x.pages_each,x.requested_years,x.legal_hold),retention_class:if x.legal_hold{{"held".into()}}else{{"standard".into()}}}}}}
#[unsafe(no_mangle)] pub extern "C" fn parley_retention_index(d:i64,p:i64,y:i64,h:i32)->i64{{retention_index(d,p,y,h!=0)}}"""
        for variant in ("seed", "reference")
    },
    "loyalty_stamps_repair": {
        variant: f"""use serde::{{Deserialize,Serialize}};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput{{pub purchase_count:i64,pub stamps_each:i64,pub claimed_stamps:i64,pub double_day:bool}}
impl RequestInput{{pub fn valid(&self)->bool{{self.purchase_count>=0&&self.stamps_each>=0&&self.claimed_stamps>=0}}}}
#[derive(Serialize)] pub struct ResponseOutput{{pub base_stamps:i64,pub bonus_stamps:i64,pub spendable_stamps:i64,pub reward_count:i64,pub leftover_stamps:i64,pub reward_stage:String}}
pub fn claimable_rewards(p:i64,e:i64,c:i64,d:bool)->i64{{{('(p*e+if d{p}else{0})/10' if variant == 'seed' else '(p*e+if d{p}else{0}-c).max(0)/10')}}}
pub fn handle(x:RequestInput)->ResponseOutput{{let base=x.purchase_count*x.stamps_each;let bonus=if x.double_day{{x.purchase_count}}else{{0}};let spendable=(base+bonus-x.claimed_stamps).max(0);let rewards=claimable_rewards(x.purchase_count,x.stamps_each,x.claimed_stamps,x.double_day);ResponseOutput{{base_stamps:base,bonus_stamps:bonus,spendable_stamps:spendable,reward_count:rewards,leftover_stamps:spendable-rewards*10,reward_stage:if rewards>0{{"ready".into()}}else{{"collecting".into()}}}}}}
#[unsafe(no_mangle)] pub extern "C" fn parley_claimable_rewards(p:i64,e:i64,c:i64,d:i32)->i64{{claimable_rewards(p,e,c,d!=0)}}"""
        for variant in ("seed", "reference")
    },
    "cold_storage_repair": {
        variant: f"""use serde::{{Deserialize,Serialize}};
#[derive(Deserialize)] #[serde(deny_unknown_fields)] pub struct RequestInput{{pub measured_degrees:i64,pub target_degrees:i64,pub allowed_drift:i64,pub door_open:bool}}
impl RequestInput{{pub fn valid(&self)->bool{{self.measured_degrees>=0&&self.target_degrees>=0&&self.allowed_drift>=0}}}}
#[derive(Serialize)] pub struct ResponseOutput{{pub corrected_degrees:i64,pub temperature_gap:i64,pub excess_heat:i64,pub cooling_steps:i64,pub safe_flag:bool,pub storage_condition:String}}
pub fn corrected_degrees(m:i64,d:bool)->i64{{m{'' if variant == 'seed' else '+if d{2}else{0}'}}}
pub fn required_cooling(m:i64,t:i64,a:i64,d:bool)->i64{{((corrected_degrees(m,d)-t-a).max(0)+2)/3}}
pub fn handle(x:RequestInput)->ResponseOutput{{let corrected=corrected_degrees(x.measured_degrees,x.door_open);let gap=(corrected-x.target_degrees).abs();let excess=(corrected-x.target_degrees-x.allowed_drift).max(0);let safe=gap<=x.allowed_drift;ResponseOutput{{corrected_degrees:corrected,temperature_gap:gap,excess_heat:excess,cooling_steps:required_cooling(x.measured_degrees,x.target_degrees,x.allowed_drift,x.door_open),safe_flag:safe,storage_condition:if safe{{"stable".into()}}else if corrected>x.target_degrees{{"cooling".into()}}else{{"warming".into()}}}}}}
#[unsafe(no_mangle)] pub extern "C" fn parley_required_cooling(m:i64,t:i64,a:i64,d:i32)->i64{{required_cooling(m,t,a,d!=0)}}"""
        for variant in ("seed", "reference")
    },
}

RUST_WASM = {
    "ferry_manifest_build": ("parley_manifest_charge", ["a", "b", "c", "d ? 1 : 0"]),
    "archive_retention_build": ("parley_retention_index", ["a", "b", "c", "d ? 1 : 0"]),
    "loyalty_stamps_repair": ("parley_claimable_rewards", ["a", "b", "c", "d ? 1 : 0"]),
    "cold_storage_repair": ("parley_required_cooling", ["a", "b", "c", "d ? 1 : 0"]),
}
