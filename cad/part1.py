import os
from pathlib import Path
from typing import Literal

import build123d as bd

# from . import calc

# Constants
spring_d = 20

big_plate_od = 150
big_plate_t = 2
# Border around the edge to the gape in the middle.
big_plate_border_w = 22

# M8 specs
m8_nut_flats_width = 13 + 0.2
m8_nut_height = 8


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

jaw_to_rail_interference = 0.2
jaw_width_y = 50
jaw_height_z = 20
jaw_thickness_x = 10
jaw_min_thickness = 3

jaw_pcb_thickness = 4
jaw_pcb_dist_from_top = 3
jaw_meat_above_nut_thickness = 4


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
        # TODO: Add side-rails to the plate to increase strength.
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


def cad_make_vise_jaw(jaw_mode: Literal["m3", "m8", "backstop", "no_hole"]):
    """Make a jaw with a hole in it.

    Args:
    ----
        jaw_mode: Literal["m3", "m8", "backstop", "no_hole"]
            m3 = M3 hole, no nut.
            m8 = M8 hole, with nut.
            backstop = M8 hole, with nut. Meant to be used as a backstop
                against the spring. No wide jaw.
            no_hole = No hole, just a jaw.
    """

    if jaw_mode == "m3":
        hole_d = 3.2
        grip_length_x = hole_d + 7
        nut_flats_width = None
        nut_height = None
        grip_height_z = 8
    elif jaw_mode == "m8":
        hole_d = 8.3
        grip_length_x = hole_d + 10
        nut_flats_width = m8_nut_flats_width
        nut_height = m8_nut_height
        grip_height_z = nut_height + jaw_meat_above_nut_thickness
    elif jaw_mode == "backstop":
        hole_d = 8.3
        grip_length_x = hole_d + 10
        nut_flats_width = m8_nut_flats_width
        nut_height = m8_nut_height
        grip_height_z = nut_height + jaw_meat_above_nut_thickness
    elif jaw_mode == "no_hole":
        hole_d = 0
        grip_length_x = 5
        nut_flats_width = None
        nut_height = None
        grip_height_z = 8
    else:
        raise ValueError(f"Unknown jaw_mode={jaw_mode}")

    print(f"Making jaw for {jaw_mode=}, hole_d={hole_d}, {grip_length_x=}")

    jaw = bd.Part()

    # Above-the-rail jaw.
    if jaw_mode != "backstop":
        jaw += bd.Box(
            jaw_thickness_x,
            jaw_width_y,
            jaw_height_z,
            align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN),
        )

    # Above-the-rail nut hole.
    if grip_length_x:
        jaw += bd.Box(
            grip_length_x,
            m8_nut_flats_width + 2 * 5,
            grip_height_z,
            align=(bd.Align.MAX, bd.Align.CENTER, bd.Align.MIN),
        )

    # Below-the-rail jaw.
    jaw += bd.Box(
        grip_length_x + (jaw_thickness_x if jaw_mode != "backstop" else 0),
        rail_d + 2 * (jaw_min_thickness + jaw_to_rail_interference + 5),
        rail_thickness_z + jaw_min_thickness,
        align=(bd.Align.MAX, bd.Align.CENTER, bd.Align.MAX),
    ).translate(
        (
            (jaw_thickness_x if jaw_mode != "backstop" else 0),
            0,
            jaw.faces().sort_by(bd.Axis.Z)[0].center().Z,
        )
    )

    # Round everything, except the clamping face (for printing and clamping purposes).
    edge_list = jaw.edges() - jaw.faces().sort_by(bd.Axis.X)[-1].edges()
    jaw = jaw.fillet(
        radius=jaw.max_fillet(edge_list=edge_list, max_iterations=100),
        edge_list=list(edge_list),
    )

    # Remove the rail hole.
    rail_cyl = bd.Cylinder(
        radius=rail_d / 2 + jaw_to_rail_interference,
        height=rail_length_x,
        rotation=(0, 90, 0),
    )
    rail_intersect = bd.Box(
        rail_length_x, rail_d * 3, rail_thickness_z + jaw_to_rail_interference * 2
    )
    rail = rail_cyl & rail_intersect
    rail_bottom_z = jaw.faces().sort_by(bd.Axis.Z)[0].center().Z + jaw_min_thickness
    jaw -= rail.translate(
        (
            0,
            0,
            rail_bottom_z + rail_thickness_z / 2,
        )
    )

    # Remove the bolt hole.
    jaw -= bd.Cylinder(
        radius=hole_d / 2,
        height=1000,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    ).translate((-grip_length_x / 2, 0, rail_bottom_z))

    if nut_flats_width:
        # Remove the nut hole.
        jaw -= bd.extrude(
            bd.RegularPolygon(
                radius=nut_flats_width / 2, side_count=6, major_radius=False
            ),
            amount=nut_height,
        ).translate((-grip_length_x / 2, 0, rail_bottom_z + rail_thickness_z))

    # Remove the PCB clamping bits.
    jaw -= bd.Box(
        jaw_pcb_thickness,
        jaw_width_y,
        jaw_pcb_thickness,
        rotation=(0, 45, 0),
    ).translate(
        (
            jaw.faces().sort_by(bd.Axis.X)[-1].center().X,
            0,
            jaw.faces().sort_by(bd.Axis.Z)[-1].center().Z - jaw_pcb_dist_from_top,
        )
    )

    return jaw


def assemble_entire_unit():
    """Combine the rail and the plate."""
    rail = cad_rail_body()
    rail_plate = cad_rail_plate()

    part = rail + rail_plate
    return part


def demo_all_jaws():
    part = bd.Part()
    for i, jaw_mode in enumerate(["m3", "m8", "backstop", "no_hole"], -1):
        part += cad_make_vise_jaw(jaw_mode).translate((0, i * (jaw_width_y + 10), 0))

    return part


if __name__ == "__main__":
    parts = {
        "rail": cad_rail_body(),
        "rail_plate": cad_rail_plate(),
        # "vise_jaw_m3": cad_make_vise_jaw("m3"),
        "vise_jaw_m8": cad_make_vise_jaw("m8"),
        # "vise_jaw_backstop": cad_make_vise_jaw("backstop"),
        "vise_jaw_no_hole": cad_make_vise_jaw("no_hole"),
        "entire_unit": assemble_entire_unit(),
        "demo_all_jaws": demo_all_jaws(),
    }

    if not os.getenv("CI"):
        from ocp_vscode import show

        print("Showing CAD model(s)")
        # show(parts["rail"])
        # show(parts["rail_plate"])
        # show(parts["entire_unit"])
        # show(parts["vise_jaw_m3"])
        # show(parts["vise_jaw_m8"])
        # show(parts["vise_jaw_backstop"])
        show(parts["demo_all_jaws"])

    (export_folder := Path(__file__).parent.with_name("build")).mkdir(exist_ok=True)
    for name, part in parts.items():
        bd.export_stl(part, str(export_folder / f"{name}.stl"))
        bd.export_step(part, str(export_folder / f"{name}.step"))
        print(f"Exported {name}")
