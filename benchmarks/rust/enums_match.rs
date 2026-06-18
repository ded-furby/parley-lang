use std::fmt;

#[allow(dead_code)]
enum Mood {
    Happy,
    Neutral,
    Grumpy,
}

impl fmt::Display for Mood {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Mood::Happy => write!(f, "happy"),
            Mood::Neutral => write!(f, "neutral"),
            Mood::Grumpy => write!(f, "grumpy"),
        }
    }
}

fn describe(m: &Mood) -> &'static str {
    match m {
        Mood::Happy => "all sunshine",
        Mood::Neutral => "perfectly balanced",
        Mood::Grumpy => "approach with snacks",
    }
}

fn main() {
    let today = Mood::Grumpy;
    println!("the cat is {}", today);
    println!("{}", describe(&today));
    match today {
        Mood::Happy => println!("pet it"),
        _ => println!("feed it first"),
    }
}
