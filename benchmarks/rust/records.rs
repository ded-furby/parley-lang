#[derive(Clone)]
#[allow(dead_code)]
struct Point {
    x: i64,
    y: i64,
}

struct Rectangle {
    corner: Point,
    width: i64,
    height: i64,
}

fn area(r: &Rectangle) -> i64 {
    r.width * r.height
}

fn move_right(p: &mut Point, amount: i64) {
    p.x = p.x + amount;
}

fn main() {
    let mut origin = Point { x: 0, y: 0 };
    let frame = Rectangle {
        corner: origin.clone(),
        width: 4,
        height: 3,
    };
    println!("area: {}", area(&frame));

    move_right(&mut origin, 10);
    println!("origin moved to x {}", origin.x);
    println!("frame's corner is still at x {}", frame.corner.x);
}
