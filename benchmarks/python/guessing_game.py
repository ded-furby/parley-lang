import random


def main() -> None:
    secret = random.randint(1, 10)
    tries = 0
    print("I picked a number from 1 to 10.")
    while True:
        try:
            text = input("your guess: ")
        except EOFError:
            return
        try:
            guess = int(text)
        except ValueError:
            print("numbers only, please")
            continue
        tries += 1
        if guess == secret:
            print(f"You got it in {tries} tries!")
            return
        if guess < secret:
            print("higher")
        else:
            print("lower")


if __name__ == "__main__":
    main()
