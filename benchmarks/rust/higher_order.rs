fn double(x: i64) -> i64 {
    x * 2
}

fn triple(x: i64) -> i64 {
    x * 3
}

fn apply_twice(f: fn(i64) -> i64, x: i64) -> i64 {
    f(f(x))
}

fn describe(f: fn(i64) -> i64, label: &str) {
    println!("{} says {}", label, f(5));
}

fn main() {
    let d = double as fn(i64) -> i64;
    println!("double twice: {}", apply_twice(d, 5));
    println!("triple twice: {}", apply_twice(triple, 5));
    describe(d, "double");
    describe(triple, "triple");
}
