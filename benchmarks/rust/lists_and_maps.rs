use std::collections::BTreeMap;

fn main() {
    let mut primes = vec![2, 3, 5, 7, 11];
    let total: i64 = primes.iter().sum();
    println!("I have {} primes; their sum is {}", primes.len(), total);
    primes.push(13);
    println!("item 3 is {}", primes[2]);
    if primes.contains(&7) {
        println!("7 is in the list");
    }

    let mut shuffled = vec![9, 1, 8, 2];
    shuffled.sort();
    let in_order: Vec<String> = shuffled.iter().map(|n| n.to_string()).collect();
    println!("{}", in_order.join(" < "));

    let mut ages = BTreeMap::new();
    ages.insert("ada".to_string(), 36);
    ages.insert("alan".to_string(), 41);
    let ada_age = ages.get("ada").unwrap();
    println!("ada is {}", ada_age);
    let people: Vec<String> = ages.keys().cloned().collect();
    println!("people: {}", people.join(", "));
}
