use std::io::{self, Write};

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

fn show(items: &[String]) {
    if items.is_empty() {
        println!("nothing to do!");
        return;
    }
    for (index, entry) in items.iter().enumerate() {
        println!("{}. {}", index + 1, entry);
    }
}

fn main() {
    let mut items: Vec<String> = Vec::new();
    loop {
        let Some(command) = ask("todo> ") else {
            return;
        };
        if command == "quit" {
            println!("bye");
            return;
        } else if command == "list" {
            show(&items);
        } else if command.starts_with("add ") {
            items.push(command.replacen("add ", "", 1));
            println!("added");
        } else if command.starts_with("done ") {
            let piece = command.replacen("done ", "", 1);
            let Ok(n) = piece.parse::<usize>() else {
                println!("say which number to finish");
                continue;
            };
            if n == 0 || n > items.len() {
                println!("Cannot remove item {} - the list has {} item(s).", n, items.len());
            } else {
                items.remove(n - 1);
                println!("done!");
            }
        } else {
            println!("commands: add <thing>, done <number>, list, quit");
        }
    }
}
