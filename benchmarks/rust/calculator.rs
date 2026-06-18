use std::io::{self, Write};

fn ask(prompt: &str) -> String {
    print!("{}", prompt);
    io::stdout().flush().unwrap();
    let mut line = String::new();
    io::stdin().read_line(&mut line).unwrap();
    line.trim_end().to_string()
}

fn main() {
    println!("I can add, subtract, multiply and divide.");
    let a_text = ask("first number: ");
    let b_text = ask("second number: ");
    let op = ask("operation (+ - * /): ");
    let first = a_text.parse::<f64>().ok();
    let second = b_text.parse::<f64>().ok();
    if first.is_none() || second.is_none() {
        println!("those were not numbers");
        return;
    }
    let x = first.unwrap();
    let y = second.unwrap();

    match op.as_str() {
        "+" => println!("{}", x + y),
        "-" => println!("{}", x - y),
        "*" => println!("{}", x * y),
        "/" => {
            if y == 0.0 {
                println!("Cannot divide by zero.");
            } else {
                println!("{}", x / y);
            }
        }
        _ => println!("I don't know the operation {}", op),
    }
}
