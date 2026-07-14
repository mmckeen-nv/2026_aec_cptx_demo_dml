"""Create the datum-only Rhino starting file for the VP Studio demo.

This is deliberately not a studio builder. It writes reference curves and text
dots only: no Breps, Extrusions, Meshes, rooms, walls, LED volume, or equipment.
Hermes must author all design geometry through bounded Rhino MCP calls.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import rhino3dm


PROJECT_ID = "vp-studio-01"


def add_layer(model: rhino3dm.File3dm, name: str) -> int:
    layer = rhino3dm.Layer()
    layer.Name = name
    layer.Locked = True
    layer.SetUserString("project", PROJECT_ID)
    layer.SetUserString("role", "locked_reference_datum")
    return model.Layers.Add(layer)


def attributes(layer_index: int, name: str, guide_type: str) -> rhino3dm.ObjectAttributes:
    attrs = rhino3dm.ObjectAttributes()
    attrs.LayerIndex = layer_index
    attrs.Name = name
    attrs.SetUserString("project", PROJECT_ID)
    attrs.SetUserString("template_role", guide_type)
    attrs.SetUserString("export_to_blender", "false")
    attrs.SetUserString("assumption_status", "REFERENCE_ONLY")
    return attrs


def add_closed_rectangle(
    model: rhino3dm.File3dm,
    layer_index: int,
    name: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z: float = 0.0,
) -> None:
    points = [
        rhino3dm.Point3d(x0, y0, z),
        rhino3dm.Point3d(x1, y0, z),
        rhino3dm.Point3d(x1, y1, z),
        rhino3dm.Point3d(x0, y1, z),
        rhino3dm.Point3d(x0, y0, z),
    ]
    model.Objects.AddPolyline(points, attributes(layer_index, name, "plan_guide"))


def add_line(
    model: rhino3dm.File3dm,
    layer_index: int,
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    guide_type: str,
) -> None:
    model.Objects.AddLine(
        rhino3dm.Point3d(*start),
        rhino3dm.Point3d(*end),
        attributes(layer_index, name, guide_type),
    )


def add_note(
    model: rhino3dm.File3dm,
    layer_index: int,
    name: str,
    text: str,
    point: tuple[float, float, float],
) -> None:
    model.Objects.AddTextDot(
        text,
        rhino3dm.Point3d(*point),
        attributes(layer_index, name, "instruction"),
    )


def build_template(output: Path) -> None:
    model = rhino3dm.File3dm()
    model.Settings.ModelUnitSystem = rhino3dm.UnitSystem.Inches
    model.Settings.ModelAbsoluteTolerance = 0.01
    model.Settings.ModelAngleToleranceDegrees = 0.1
    model.Settings.ModelRelativeTolerance = 0.01

    property_layer = add_layer(model, "VP00_TEMPLATE_PROPERTY")
    planning_layer = add_layer(model, "VP00_TEMPLATE_PLANNING_ENVELOPES")
    datum_layer = add_layer(model, "VP00_TEMPLATE_DATUMS")
    notes_layer = add_layer(model, "VP00_TEMPLATE_NOTES")

    # 400 ft x 300 ft concept lot. The southwest property corner is the origin.
    add_closed_rectangle(model, property_layer, "GUIDE_PROPERTY_400FT_X_300FT", 0, 0, 4800, 3600)

    # Movable planning envelopes, not accepted building or stage geometry.
    add_closed_rectangle(model, planning_layer, "GUIDE_BUILDING_180FT_X_150FT_MOVE_BEFORE_USE", 1320, 900, 3480, 2700)
    add_closed_rectangle(model, planning_layer, "GUIDE_STAGE_MIN_120FT_X_100FT_MOVE_BEFORE_USE", 1680, 1200, 3120, 2400)

    # Origin, north, and representative vertical datum rack.
    add_line(model, datum_layer, "GUIDE_ORIGIN_X", (-240, 0, 0), (600, 0, 0), "axis")
    add_line(model, datum_layer, "GUIDE_ORIGIN_Y", (0, -240, 0), (0, 600, 0), "axis")
    add_line(model, datum_layer, "GUIDE_NORTH", (240, 240, 0), (240, 720, 0), "north")
    add_line(model, datum_layer, "DATUM_GROUND_0IN", (-480, -480, 0), (720, -480, 0), "elevation")
    add_line(model, datum_layer, "DATUM_STAGE_CLEAR_480IN", (-480, -480, 480), (720, -480, 480), "elevation")
    add_line(model, datum_layer, "DATUM_EXPECTED_MAX_630IN", (-480, -480, 630), (720, -480, 630), "elevation")

    # Three scale bars make unit mistakes obvious in plan and axonometric views.
    add_line(model, datum_layer, "SCALE_1FT", (0, 3840, 0), (12, 3840, 0), "scale_bar")
    add_line(model, datum_layer, "SCALE_10FT", (0, 3900, 0), (120, 3900, 0), "scale_bar")
    add_line(model, datum_layer, "SCALE_100FT", (0, 3960, 0), (1200, 3960, 0), "scale_bar")

    add_note(model, notes_layer, "NOTE_TEMPLATE", "VP STUDIO 01 — DATUM TEMPLATE ONLY", (120, 3480, 0))
    add_note(model, notes_layer, "NOTE_UNITS", "MODEL UNITS: INCHES | ABS TOL: 0.01 IN | ANGLE: 0.1 DEG", (120, 3390, 0))
    add_note(model, notes_layer, "NOTE_AGENT_AUTHORITY", "GUIDES ARE LOCKED REFERENCES. AGENT MUST AUTHOR ALL DESIGN GEOMETRY.", (120, 3300, 0))
    add_note(model, notes_layer, "NOTE_NO_EXPORT", "VP00_TEMPLATE_* OBJECTS: export_to_blender=false", (120, 3210, 0))

    output.parent.mkdir(parents=True, exist_ok=True)
    if not model.Write(str(output), 8):
        raise RuntimeError(f"Rhino failed to write template: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "demos"
        / "virtual_production_studio"
        / "source"
        / "vp_studio_01_template.3dm",
    )
    args = parser.parse_args()
    build_template(args.output.resolve())
    print(args.output.resolve())


if __name__ == "__main__":
    main()
