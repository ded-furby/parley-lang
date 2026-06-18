from collections.abc import Callable


def double(x: int) -> int:
    return x * 2


def triple(x: int) -> int:
    return x * 3


def apply_twice(f: Callable[[int], int], x: int) -> int:
    return f(f(x))


def describe(f: Callable[[int], int], label: str) -> None:
    print(f"{label} says {f(5)}")


def main() -> None:
    d = double
    print(f"double twice: {apply_twice(d, 5)}")
    print(f"triple twice: {apply_twice(triple, 5)}")
    describe(d, "double")
    describe(triple, "triple")


if __name__ == "__main__":
    main()
