use std::fs;

fn main() {
    let lines = ["the quick brown fox", "jumps over", "the lazy dog"];
    fs::write("parley_demo.txt", lines.join("\n")).expect("write file");

    let content = fs::read_to_string("parley_demo.txt").expect("read file");
    let rows: Vec<&str> = content.split('\n').collect();
    println!("the file has {} lines", rows.len());
    for row in rows {
        if row.contains("lazy") {
            println!("found it: {}", row);
        }
    }
}
