import os
from pathlib import Path

import build123d as bd

# Constants


def make_part1():
    # Orientation: ...
    with bd.BuildPart() as part1:
        bd.Cylinder(radius=20, height=20)

    return part1


if __name__ == "__main__":
    part1 = make_part1()

    if not os.getenv("CI"):
        from ocp_vscode import show

        print("Showing CAD model(s)")
        show(part1)

    (export_folder := Path(__file__).parent.with_name("build")).mkdir(exist_ok=True)
    bd.export_stl(part1.part, str(export_folder / "part1.stl"))
    bd.export_step(part1.part, str(export_folder / "part1.step"))
