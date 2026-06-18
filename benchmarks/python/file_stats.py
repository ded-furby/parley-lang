from pathlib import Path


def main() -> None:
    lines = ["the quick brown fox", "jumps over", "the lazy dog"]
    path = Path("parley_demo.txt")
    path.write_text("\n".join(lines), encoding="utf-8")

    content = path.read_text(encoding="utf-8")
    rows = content.split("\n")
    print(f"the file has {len(rows)} lines")
    for row in rows:
        if "lazy" in row:
            print(f"found it: {row}")


if __name__ == "__main__":
    main()
