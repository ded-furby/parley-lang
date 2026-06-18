from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Rectangle:
    corner: Point
    width: int
    height: int


def area(r: Rectangle) -> int:
    return r.width * r.height


def move_right(p: Point, amount: int) -> None:
    p.x = p.x + amount


def main() -> None:
    origin = Point(x=0, y=0)
    frame = Rectangle(corner=deepcopy(origin), width=4, height=3)
    print(f"area: {area(frame)}")

    move_right(origin, 10)
    print(f"origin moved to x {origin.x}")
    print(f"frame's corner is still at x {frame.corner.x}")


if __name__ == "__main__":
    main()
