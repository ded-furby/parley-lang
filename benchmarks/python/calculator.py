def main() -> None:
    print("I can add, subtract, multiply and divide.")
    a_text = input("first number: ")
    b_text = input("second number: ")
    op = input("operation (+ - * /): ")
    try:
        x = float(a_text)
        y = float(b_text)
    except ValueError:
        print("those were not numbers")
        return

    try:
        if op == "+":
            print(x + y)
        elif op == "-":
            print(x - y)
        elif op == "*":
            print(x * y)
        elif op == "/":
            if y == 0:
                raise ZeroDivisionError("Cannot divide by zero.")
            print(x / y)
        else:
            print(f"I don't know the operation {op}")
    except ZeroDivisionError as exc:
        print(exc)


if __name__ == "__main__":
    main()
