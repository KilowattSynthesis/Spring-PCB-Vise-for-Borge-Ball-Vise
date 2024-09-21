import os
from pathlib import Path

import build123d as bd

# from . import calc

# Constants
spring_d = 20

big_plate_od = 150
big_plate_t = 2
# Border around the edge to the gape in the middle.
big_plate_border_w = 22

# M8 specs
nut_flats_width = 13 + 0.2
nut_height = 8


# Rail must fit within the spring, but should be a rectangle.
rail_d = spring_d - 2
rail_thickness_z = spring_d * 0.66
rail_raise_dist_z = 8  # Distance from bottom of spring to the base.
rail_length_x = 220

rail_plate_t = 4
rail_plate_w = 40

rail_pillar_d = rail_d * 0.75

rail_pillar_screw_d = 3.2
rail_pillar_nut_w = 5.5  # M3
rail_pillar_nut_h = 4


def cad_rail_body():
    """Make the rail, the vertical end pieces, and the horizontal plate underneath."""
    rail_cyl = bd.Cylinder(radius=rail_d / 2, height=rail_length_x, rotation=(0, 90, 0))
    rail_intersect = bd.Box(rail_length_x, rail_d * 3, rail_thickness_z)

    # Make the long X part.
    rail = rail_cyl & rail_intersect

    # Remove the screw holes.
    for i in (1, -1):
        rail -= bd.Cylinder(
            radius=rail_pillar_screw_d / 2,
            height=rail_thickness_z,
            align=(
                bd.Align.CENTER,
                bd.Align.CENTER,
                bd.Align.CENTER,
            ),
        ).translate(
            (
                (rail_length_x - rail_pillar_d) / 2 * i,
                0,
                0,
            )
        )

    # TODO: remove divots for the main M8 holder bolt

    return rail


def cad_rail_plate():
    # Load the rail body to get the Z values. Not used for the actual rail.
    rail_body = cad_rail_body()
    _rail_top_z = rail_body.faces().sort_by(bd.Axis.Z)[-1].center().Z
    rail_bottom_z = rail_body.faces().sort_by(bd.Axis.Z)[0].center().Z

    rail_plate = bd.Part()

    # Add end caps that go downwards.
    for i in (1, -1):
        rail_plate += bd.Cylinder(
            radius=rail_pillar_d / 2,
            height=rail_raise_dist_z,
            align=(
                bd.Align.CENTER,
                bd.Align.CENTER,
                bd.Align.MAX,
            ),
            # TODO: round the top-size of this cylinder.
        ).translate(
            (
                (rail_length_x - rail_pillar_d) / 2 * i,
                0,
                rail_bottom_z,
            )
        )

    # Add the horizontal rail plate.
    with bd.BuildPart() as rail_plate_base:
        bd.Box(
            rail_length_x,
            rail_plate_w,
            rail_plate_t,
            align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX),
        )
        # Fillet the ends.
        bd.fillet(
            list(rail_plate_base.edges().filter_by(bd.Axis.Z)),
            radius=rail_plate_w * 0.4,
        )
    rail_plate += rail_plate_base.part.translate(
        (0, 0, rail_bottom_z - rail_raise_dist_z)
    )

    # Remove the screw holes and captive nut.
    for i in (1, -1):
        hole_loc_vector = (
            (rail_length_x - rail_pillar_d) / 2 * i,
            0,
            rail_plate.faces().sort_by(bd.Axis.Z)[0].center().Z,
        )
        rail_plate -= bd.Cylinder(
            radius=rail_pillar_screw_d / 2,
            height=1000,
        ).translate(hole_loc_vector)

        rail_plate -= (
            # Add the nut holder.
            bd.extrude(
                bd.RegularPolygon(
                    radius=rail_pillar_nut_w / 2, side_count=6, major_radius=False
                ),
                amount=rail_pillar_nut_h,
            ).translate(hole_loc_vector)
        )

    return rail_plate


def assemble_entire_unit():
    """Combine the rail and the plate."""
    rail = cad_rail_body()
    rail_plate = cad_rail_plate()

    part = rail + rail_plate
    return part


if __name__ == "__main__":
    parts = {
        "rail": cad_rail_body(),
        "rail_plate": cad_rail_plate(),
        "entire_unit": assemble_entire_unit(),
    }

    if not os.getenv("CI"):
        from ocp_vscode import show

        print("Showing CAD model(s)")
        # show(parts["rail"])
        # show(parts["rail_plate"])
        show(parts["entire_unit"])

    (export_folder := Path(__file__).parent.with_name("build")).mkdir(exist_ok=True)
    for name, part in parts.items():
        bd.export_stl(part, str(export_folder / f"{name}.stl"))
        bd.export_step(part, str(export_folder / f"{name}.step"))
        print(f"Exported {name}")
