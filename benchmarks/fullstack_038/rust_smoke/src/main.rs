fn main() {
    let encoded = serde_json::to_string(&fullstack_freeze_smoke_038::FreezeProbe { value: 38 })
        .expect("probe serialization");
    assert_eq!(encoded, r#"{"value":38}"#);
}
