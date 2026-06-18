def show(items: list[str]) -> None:
    if len(items) == 0:
        print("nothing to do!")
        return
    for i, entry in enumerate(items, start=1):
        print(f"{i}. {entry}")


def main() -> None:
    items: list[str] = []
    while True:
        try:
            command = input("todo> ")
        except EOFError:
            return
        if command == "quit":
            print("bye")
            return
        if command == "list":
            show(items)
        elif command.startswith("add "):
            items.append(command.split("add ", 1)[1])
            print("added")
        elif command.startswith("done "):
            piece = command.split("done ", 1)[1]
            try:
                n = int(piece)
            except ValueError:
                print("say which number to finish")
                continue
            try:
                items.pop(n - 1)
                print("done!")
            except IndexError:
                print(f"Cannot remove item {n} - the list has {len(items)} item(s).")
        else:
            print("commands: add <thing>, done <number>, list, quit")


if __name__ == "__main__":
    main()
