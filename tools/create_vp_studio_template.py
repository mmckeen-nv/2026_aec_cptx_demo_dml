"""Create the minimal datum-only Rhino starting file for the VP Studio demo.

This is deliberately not a studio builder. It writes four reference curves
only: no Breps, Extrusions, Meshes, rooms, walls, LED volume, circulation,
or equipment. Every guide uses the same centered world datum as the locked
manifest. Hermes authors all design geometry through Rhino MCP C# calls.
"""

from __future__ import annotations

import argparse
import hashlib
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


def add_circle(
    model: rhino3dm.File3dm,
    layer_index: int,
    name: str,
    center: tuple[float, float, float],
    radius: float,
    guide_type: str,
) -> None:
    circle = rhino3dm.Circle(rhino3dm.Point3d(*center), radius)
    model.Objects.AddCircle(circle, attributes(layer_index, name, guide_type))


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


def add_named_view(
    model: rhino3dm.File3dm,
    name: str,
    location: tuple[float, float, float],
    target: tuple[float, float, float],
    parallel: bool = False,
) -> None:
    viewport = (
        rhino3dm.ViewportInfo.DefaultTop()
        if parallel
        else rhino3dm.ViewportInfo.DefaultPerspective()
    )
    viewport.SetCameraLocation(rhino3dm.Point3d(*location))
    viewport.SetCameraDirection(
        rhino3dm.Vector3d(
            target[0] - location[0],
            target[1] - location[1],
            target[2] - location[2],
        )
    )
    viewport.SetCameraUp(rhino3dm.Vector3d(0, 0, 1))
    if parallel:
        viewport.ChangeToParallelProjection(True)
    else:
        viewport.ChangeToPerspectiveProjection(3600.0, True, 35.0)
    viewport.DollyExtents(
        rhino3dm.BoundingBox(
            rhino3dm.Point3d(-2400, -1800, 0),
            rhino3dm.Point3d(2400, 1800, 630),
        ),
        1.1,
    )
    view = rhino3dm.ViewInfo()
    view.Name = name
    view.Viewport = viewport
    model.NamedViews.Add(view)


def build_template(output: Path) -> None:
    model = rhino3dm.File3dm()
    model.Settings.ModelUnitSystem = rhino3dm.UnitSystem.Inches
    model.Settings.ModelAbsoluteTolerance = 0.01
    model.Settings.ModelAngleToleranceDegrees = 0.1
    model.Settings.ModelRelativeTolerance = 0.01

    datum_layer = add_layer(model, "VP00_TEMPLATE_DATUMS")

    # Four locked curves, all on the manifest's single centered world datum.
    # They communicate scale only and are never accepted design geometry.
    add_closed_rectangle(model, datum_layer, "GUIDE_PROPERTY_ENVELOPE", -2400, -1800, 2400, 1800)
    add_closed_rectangle(model, datum_layer, "GUIDE_BUILDING_ENVELOPE", -1080, -900, 1080, 900)
    add_closed_rectangle(model, datum_layer, "GUIDE_STAGE_ENVELOPE", -720, -600, 720, 600)
    add_circle(model, datum_layer, "GUIDE_LED_ACTIVE_RADIUS", (-120, 0, 0), 480, "curvature_datum")

    # Standard review compositions prevent the agent from spending turns
    # rediscovering useful cameras. They contain no design geometry.
    add_named_view(model, "VP_PLAN", (0, 0, 7200), (0, 0, 0), parallel=True)
    add_named_view(model, "VP_EXTERIOR_AXON", (3600, -3600, 2400), (0, 0, 240))
    add_named_view(model, "VP_STAGE_INTERIOR", (0, -720, 180), (-120, 0, 180))

    output.parent.mkdir(parents=True, exist_ok=True)
    if not model.Write(str(output), 8):
        raise RuntimeError(f"Rhino failed to write template: {output}")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(
        digest + "  " + output.name + "\n", encoding="ascii"
    )


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
