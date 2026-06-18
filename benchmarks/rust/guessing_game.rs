use std::io::{self, Write};
use std::time::{SystemTime, UNIX_EPOCH};

fn ask(prompt: &str) -> Option<String> {
    print!("{}", prompt);
    io::stdout().flush().unwrap();
    let mut line = String::new();
    let read = io::stdin().read_line(&mut line).ok()?;
    if read == 0 {
        return None;
    }
    Some(line.trim_end().to_string())
}

fn main() {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .subsec_nanos();
    let secret = (nanos % 10 + 1) as i64;
    let mut tries = 0;
    println!("I picked a number from 1 to 10.");
    loop {
        let Some(text) = ask("your guess: ") else {
            return;
        };
        let Ok(guess) = text.parse::<i64>() else {
            println!("numbers only, please");
            continue;
        };
        tries += 1;
        if guess == secret {
            println!("You got it in {} tries!", tries);
            return;
        } else if guess < secret {
            println!("higher");
        } else {
            println!("lower");
        }
    }
}
