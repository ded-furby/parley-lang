use serde::{Deserialize, Serialize};

#[derive(Deserialize, Serialize)]
pub struct FreezeProbe {
    pub value: i64,
}

#[unsafe(no_mangle)]
pub extern "C" fn fullstack_freeze_probe_038(value: i64) -> i64 {
    value
}
