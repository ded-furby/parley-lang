from enum import Enum


class Mood(Enum):
    HAPPY = "happy"
    NEUTRAL = "neutral"
    GRUMPY = "grumpy"


def describe(m: Mood) -> str:
    if m is Mood.HAPPY:
        return "all sunshine"
    if m is Mood.NEUTRAL:
        return "perfectly balanced"
    return "approach with snacks"


def main() -> None:
    today = Mood.GRUMPY
    print(f"the cat is {today.value}")
    print(describe(today))
    if today is Mood.HAPPY:
        print("pet it")
    else:
        print("feed it first")


if __name__ == "__main__":
    main()
