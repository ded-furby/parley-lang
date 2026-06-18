def main() -> None:
    primes = [2, 3, 5, 7, 11]
    print(f"I have {len(primes)} primes; their sum is {sum(primes)}")
    primes.append(13)
    print(f"item 3 is {primes[2]}")
    if 7 in primes:
        print("7 is in the list")

    shuffled = [9, 1, 8, 2]
    in_order: list[str] = []
    for n in sorted(shuffled):
        in_order.append(str(n))
    print(" < ".join(in_order))

    ages: dict[str, int] = {}
    ages["ada"] = 36
    ages["alan"] = 41
    ada_age = ages["ada"]
    print(f"ada is {ada_age}")
    print(f"people: {', '.join(sorted(ages.keys()))}")


if __name__ == "__main__":
    main()
