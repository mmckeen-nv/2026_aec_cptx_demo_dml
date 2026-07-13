"""Deterministic Rhino 8 massing builder for VP Studio 01.

Execute the complete file, unchanged, with ``mcp_rhino_run_python``.  The
script is intentionally self-contained: it uses only stable RhinoCommon
constructors, creates closed Breps, validates its own result, and never opens,
saves, exports, or prompts.  Persistence is a separate phase-gate operation.
"""

import json
import math

import Rhino
from System import Guid
from System.Drawing import Color


PROJECT = "vp-studio-01"
PHASE = "SCHEMATIC"
DOC = Rhino.RhinoDoc.ActiveDoc

LAYERS = [
    "00_REFERENCE::Lot_Datum",
    "00_REFERENCE::Clearances",
    "01_SITE::Property",
    "01_SITE::Drives_Loading",
    "01_SITE::Parking_Service",
    "02_ARCH::Shell",
    "02_ARCH::Stage_Floor",
    "02_ARCH::Interior_Partitions",
    "02_ARCH::Doors_Loading",
    "02_ARCH::Rooms_Ancillary",
    "03_LED::Main_Wall",
    "03_LED::Ceiling",
    "03_LED::Floor_Alternate",
    "03_LED::Support_ServiceZone",
    "04_RIGGING::Grid_Catwalks",
    "04_RIGGING::Hoist_Envelopes",
    "05_CAMERA::Bodies",
    "05_CAMERA::Frustums",
    "05_CAMERA::Movement_Envelopes",
    "05_CAMERA::Tracking_Sensors",
    "06_ELECTRICAL::Service_Distribution",
    "06_ELECTRICAL::LED_Power",
    "06_ELECTRICAL::Technical_Power_UPS",
    "06_ELECTRICAL::Lighting_CompanySwitch",
    "07_MECHANICAL::Equipment_Zones",
    "07_MECHANICAL::Stage_Air_Paths",
    "08_LIFE_SAFETY::Egress",
    "08_LIFE_SAFETY::Fire_Access",
    "09_DATA::Control_Tracking_Networks",
    "90_ANNOTATION::Room_Load_Tags",
    "99_VALIDATION::Issues",
]

DISCIPLINE_COLORS = {
    "00_REFERENCE": Color.FromArgb(130, 130, 130),
    "01_SITE": Color.FromArgb(88, 145, 78),
    "02_ARCH": Color.FromArgb(205, 205, 205),
    "03_LED": Color.FromArgb(40, 150, 230),
    "04_RIGGING": Color.FromArgb(230, 160, 45),
    "05_CAMERA": Color.FromArgb(175, 95, 210),
    "06_ELECTRICAL": Color.FromArgb(245, 205, 45),
    "07_MECHANICAL": Color.FromArgb(55, 190, 180),
    "08_LIFE_SAFETY": Color.FromArgb(225, 65, 55),
    "09_DATA": Color.FromArgb(55, 110, 225),
    "90_ANNOTATION": Color.FromArgb(245, 245, 245),
    "99_VALIDATION": Color.FromArgb(60, 210, 95),
}


def existing_layer_index(full_path):
    for layer in DOC.Layers:
        if not layer.IsDeleted and layer.FullPath == full_path:
            return layer.Index
    return -1


def ensure_layer(full_path):
    parent_id = Guid.Empty
    current_path = ""
    result = -1
    for part in full_path.split("::"):
        current_path = part if not current_path else current_path + "::" + part
        result = existing_layer_index(current_path)
        if result < 0:
            layer = Rhino.DocObjects.Layer()
            layer.Name = part
            layer.ParentLayerId = parent_id
            layer.Color = DISCIPLINE_COLORS[full_path.split("::", 1)[0]]
            result = DOC.Layers.Add(layer)
            if result < 0:
                raise RuntimeError("Could not create layer: " + current_path)
        parent_id = DOC.Layers[result].Id
    return result


LAYER_INDEX = {path: ensure_layer(path) for path in LAYERS}


def delete_previous_managed_geometry():
    ids = []
    for obj in DOC.Objects:
        attrs = obj.Attributes
        managed = attrs.GetUserString("project") == PROJECT
        if managed or (attrs.Name and attrs.Name.startswith("VP01_")):
            ids.append(obj.Id)
    for object_id in ids:
        DOC.Objects.Delete(object_id, True)
    return len(ids)


def attributes(name, layer, discipline, system, assumption="PLANNING_ASSUMPTION", extra=None):
    attrs = Rhino.DocObjects.ObjectAttributes()
    attrs.Name = name
    attrs.LayerIndex = LAYER_INDEX[layer]
    values = {
        "project": PROJECT,
        "discipline": discipline,
        "system": system,
        "phase": PHASE,
        "assumption_status": assumption,
        "source_basis": "VP_STUDIO_01_STANDARD_BRIEF",
        "export_to_blender": "true",
    }
    if extra:
        values.update(extra)
    for key, value in values.items():
        attrs.SetUserString(str(key), str(value))
    return attrs


def add_box(name, layer, minimum, maximum, discipline, system,
            assumption="PLANNING_ASSUMPTION", extra=None, rotation=None):
    p0 = Rhino.Geometry.Point3d(float(minimum[0]), float(minimum[1]), float(minimum[2]))
    p1 = Rhino.Geometry.Point3d(float(maximum[0]), float(maximum[1]), float(maximum[2]))
    brep = Rhino.Geometry.Brep.CreateFromBox(Rhino.Geometry.BoundingBox(p0, p1))
    if brep is None or not brep.IsValid:
        raise RuntimeError("Failed to create closed Brep: " + name)
    if rotation:
        angle_radians, center = rotation
        xform = Rhino.Geometry.Transform.Rotation(
            float(angle_radians),
            Rhino.Geometry.Vector3d.ZAxis,
            Rhino.Geometry.Point3d(float(center[0]), float(center[1]), float(center[2])),
        )
        if not brep.Transform(xform):
            raise RuntimeError("Failed to transform Brep: " + name)
    object_id = DOC.Objects.AddBrep(
        brep,
        attributes(name, layer, discipline, system, assumption, extra),
    )
    if object_id == Guid.Empty:
        raise RuntimeError("Failed to add Brep: " + name)
    return object_id


def add_centered_box(name, layer, center, size, discipline, system,
                     assumption="PLANNING_ASSUMPTION", extra=None, angle=0.0):
    hx, hy, hz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
    minimum = (center[0] - hx, center[1] - hy, center[2] - hz)
    maximum = (center[0] + hx, center[1] + hy, center[2] + hz)
    rotation = (angle, center) if abs(angle) > 1.0e-9 else None
    return add_box(name, layer, minimum, maximum, discipline, system,
                   assumption, extra, rotation)


DELETED_PREVIOUS = delete_previous_managed_geometry()
DOC.ModelUnitSystem = Rhino.UnitSystem.Inches
DOC.ModelAbsoluteTolerance = 0.01
DOC.ModelAngleToleranceRadians = math.radians(0.1)

# Coordinate basis: 400 x 300 ft lot; 180 x 150 ft building centered on lot.
LOT_X, LOT_Y = 4800.0, 3600.0
BLDG_X0, BLDG_X1 = 1320.0, 3480.0
BLDG_Y0, BLDG_Y1 = 900.0, 2700.0
WALL_T, BLDG_H = 12.0, 600.0
STAGE_X0, STAGE_X1 = 1680.0, 3120.0
STAGE_Y0, STAGE_Y1 = 1140.0, 2340.0
STAGE_H = 480.0
STAGE_CX = (STAGE_X0 + STAGE_X1) / 2.0
STAGE_CY = (STAGE_Y0 + STAGE_Y1) / 2.0

# Reference and site massing.
add_centered_box("VP01_LOT_DATUM", LAYERS[0], (2400, 1800, -3), (4800, 12, 6), "REFERENCE", "DATUM")
add_centered_box("VP01_BUILDING_CLEARANCE", LAYERS[1], (2400, 1800, 6), (2400, 2040, 12), "REFERENCE", "CLEARANCE", extra={"export_to_blender": "false"})
add_centered_box("VP01_PROPERTY_S", LAYERS[2], (2400, 6, 6), (4800, 12, 12), "SITE", "PROPERTY")
add_centered_box("VP01_PROPERTY_N", LAYERS[2], (2400, 3594, 6), (4800, 12, 12), "SITE", "PROPERTY")
add_centered_box("VP01_PROPERTY_W", LAYERS[2], (6, 1800, 6), (12, 3576, 12), "SITE", "PROPERTY")
add_centered_box("VP01_PROPERTY_E", LAYERS[2], (4794, 1800, 6), (12, 3576, 12), "SITE", "PROPERTY")
add_centered_box("VP01_LOADING_APRON", LAYERS[3], (1080, 1800, 3), (480, 1200, 6), "SITE", "LOADING")
add_centered_box("VP01_SERVICE_PARKING", LAYERS[4], (3900, 1800, 3), (600, 1200, 6), "SITE", "PARKING")

# Building floor, four walls, and roof are all closed Breps.
add_box("VP01_ARCH_SLAB", LAYERS[5], (BLDG_X0, BLDG_Y0, -12), (BLDG_X1, BLDG_Y1, 0), "ARCH", "SHELL")
add_box("VP01_ARCH_WALL_S", LAYERS[5], (BLDG_X0, BLDG_Y0, 0), (BLDG_X1, BLDG_Y0 + WALL_T, BLDG_H), "ARCH", "SHELL")
add_box("VP01_ARCH_WALL_N", LAYERS[5], (BLDG_X0, BLDG_Y1 - WALL_T, 0), (BLDG_X1, BLDG_Y1, BLDG_H), "ARCH", "SHELL")
add_box("VP01_ARCH_WALL_W", LAYERS[5], (BLDG_X0, BLDG_Y0, 0), (BLDG_X0 + WALL_T, BLDG_Y1, BLDG_H), "ARCH", "SHELL")
add_box("VP01_ARCH_WALL_E", LAYERS[5], (BLDG_X1 - WALL_T, BLDG_Y0, 0), (BLDG_X1, BLDG_Y1, BLDG_H), "ARCH", "SHELL")
add_box("VP01_ARCH_ROOF", LAYERS[5], (BLDG_X0, BLDG_Y0, BLDG_H), (BLDG_X1, BLDG_Y1, BLDG_H + 12), "ARCH", "SHELL")
add_box("VP01_STAGE_FLOOR_120X100", LAYERS[6], (STAGE_X0, STAGE_Y0, 0), (STAGE_X1, STAGE_Y1, 12), "ARCH", "STAGE", "CONFIRMED", {"clear_width_in": "1440", "clear_depth_in": "1200", "clear_height_in": "480"})
add_centered_box("VP01_PARTITION_CONTROL", LAYERS[7], (2400, 1068, 72), (720, 8, 144), "ARCH", "PARTITION")
add_centered_box("VP01_LOADING_DOOR_A", LAYERS[8], (1326, 1500, 96), (12, 168, 192), "ARCH", "LOADING_DOOR")
add_centered_box("VP01_LOADING_DOOR_B", LAYERS[8], (1326, 2076, 96), (12, 168, 192), "ARCH", "LOADING_DOOR")
for name, x, width, system in [
    ("VP01_ROOM_BRAINBAR", 1740, 360, "CONTROL"),
    ("VP01_ROOM_ELECTRICAL", 2160, 360, "ELECTRICAL"),
    ("VP01_ROOM_MECHANICAL", 2580, 360, "MECHANICAL"),
    ("VP01_ROOM_SUPPORT", 3060, 360, "SUPPORT"),
]:
    add_centered_box(name, LAYERS[9], (x, 1020, 60), (width, 216, 120), "ARCH", system)

# 80 ft diameter, 24 ft high, 180-degree segmented LED volume.
LED_RADIUS, LED_HEIGHT, LED_SEGMENTS = 480.0, 288.0, 18
arc_piece = math.pi * LED_RADIUS / LED_SEGMENTS + 3.0
for i in range(LED_SEGMENTS):
    theta = math.pi * (i + 0.5) / LED_SEGMENTS
    x = STAGE_CX + LED_RADIUS * math.cos(theta)
    y = STAGE_CY + LED_RADIUS * math.sin(theta)
    add_centered_box(
        "VP01_LED_MAIN_SEG_{:02d}".format(i + 1), LAYERS[10],
        (x, y, LED_HEIGHT / 2.0), (arc_piece, 8.0, LED_HEIGHT),
        "LED", "MAIN_WALL", "CONFIRMED",
        {"radius_in": "480", "height_in": "288", "arc_degrees": "180"},
        theta + math.pi / 2.0,
    )
add_centered_box("VP01_LED_CEILING_MOVABLE", LAYERS[11], (STAGE_CX, STAGE_CY + 60, 292), (360, 240, 8), "LED", "CEILING")
add_centered_box("VP01_LED_FLOOR_OPTION", LAYERS[12], (STAGE_CX, STAGE_CY + 60, 13), (360, 240, 2), "LED", "FLOOR", "OPTION")
for i, x in enumerate((STAGE_CX - 540, STAGE_CX, STAGE_CX + 540), 1):
    add_centered_box("VP01_LED_SERVICE_ZONE_{:02d}".format(i), LAYERS[13], (x, STAGE_CY + 570, 144), (180, 72, 288), "LED", "SERVICE_ZONE")

# Rigging grid, catwalks, and conceptual hoist envelopes.
for i, x in enumerate(range(int(STAGE_X0 + 120), int(STAGE_X1), 240), 1):
    add_centered_box("VP01_RIG_GRID_X_{:02d}".format(i), LAYERS[14], (x, STAGE_CY, 420), (8, 1200, 8), "RIGGING", "GRID")
for i, y in enumerate(range(int(STAGE_Y0 + 120), int(STAGE_Y1), 240), 1):
    add_centered_box("VP01_RIG_GRID_Y_{:02d}".format(i), LAYERS[14], (STAGE_CX, y, 420), (1440, 8, 8), "RIGGING", "GRID")
for i, (x, y) in enumerate(((1920, 1380), (2880, 1380), (1920, 2100), (2880, 2100)), 1):
    add_centered_box("VP01_HOIST_ENVELOPE_{:02d}".format(i), LAYERS[15], (x, y, 300), (36, 36, 240), "RIGGING", "HOIST_ENVELOPE")

# Camera proxies, frustums, movement envelopes, and tracking sensors.
camera_positions = ((2400, 1260), (1980, 1500), (2820, 1500))
for i, (x, y) in enumerate(camera_positions, 1):
    add_centered_box("VP01_CAM_{:02d}_BODY".format(i), LAYERS[16], (x, y, 66), (30, 48, 36), "CAMERA", "BODY", "CONFIRMED")
    add_centered_box("VP01_CAM_{:02d}_FRUSTUM".format(i), LAYERS[17], (x, y + 150, 90), (120, 240, 120), "CAMERA", "FRUSTUM", extra={"export_to_blender": "false"})
    add_centered_box("VP01_CAM_{:02d}_MOVE".format(i), LAYERS[18], (x, y, 18), (300, 180, 36), "CAMERA", "MOVEMENT_ENVELOPE", extra={"export_to_blender": "false"})
for i, (x, y) in enumerate(((1740, 1200), (3060, 1200), (1740, 2280), (3060, 2280)), 1):
    add_centered_box("VP01_TRACK_SENSOR_{:02d}".format(i), LAYERS[19], (x, y, 360), (12, 12, 18), "CAMERA", "TRACKING_SENSOR")

# Conceptual building systems. Values are explicitly not construction data.
not_for_construction = {"engineering_status": "NOT_FOR_CONSTRUCTION", "voltage_basis": "PLANNING_ASSUMPTION"}
add_centered_box("VP01_ELEC_MAIN_SERVICE", LAYERS[20], (3260, 1020, 72), (240, 180, 144), "ELECTRICAL", "SERVICE_DISTRIBUTION", extra=dict(not_for_construction, connected_kw="2000", demand_kw="1400"))
add_centered_box("VP01_ELEC_TRANSFORMER_ZONE", LAYERS[20], (3420, 1260, 72), (96, 180, 144), "ELECTRICAL", "TRANSFORMER", extra=not_for_construction)
for i, x in enumerate((1860, 2220, 2580, 2940), 1):
    add_centered_box("VP01_LED_POWER_ZONE_{:02d}".format(i), LAYERS[21], (x, 2220, 24), (180, 48, 48), "ELECTRICAL", "LED_POWER", extra=dict(not_for_construction, connected_kw="250"))
add_centered_box("VP01_TECH_UPS_ZONE", LAYERS[22], (2160, 1020, 48), (180, 120, 96), "ELECTRICAL", "TECHNICAL_UPS", extra=not_for_construction)
for i, x in enumerate((1560, 3240), 1):
    add_centered_box("VP01_COMPANY_SWITCH_{:02d}".format(i), LAYERS[23], (x, 1320, 36), (48, 18, 72), "ELECTRICAL", "COMPANY_SWITCH", extra=not_for_construction)
for i, x in enumerate((1740, 2580, 3300), 1):
    add_centered_box("VP01_MECH_ZONE_{:02d}".format(i), LAYERS[24], (x, 2520, 504), (300, 180, 144), "MECHANICAL", "HEAT_REJECTION")
for i, x in enumerate((2040, 2760), 1):
    add_centered_box("VP01_STAGE_AIR_PATH_{:02d}".format(i), LAYERS[25], (x, STAGE_CY, 300), (120, 900, 120), "MECHANICAL", "AIR_PATH", extra={"export_to_blender": "false"})

# Egress, fire access, data/control, tags, and a validation marker.
for i, (x, y, sx, sy) in enumerate(((1500, 1800, 120, 1440), (3300, 1800, 120, 1440), (2400, 2580, 1440, 120)), 1):
    add_centered_box("VP01_EGRESS_PATH_{:02d}".format(i), LAYERS[26], (x, y, 6), (sx, sy, 12), "LIFE_SAFETY", "EGRESS", extra={"export_to_blender": "false"})
add_centered_box("VP01_FIRE_ACCESS_LANE", LAYERS[27], (2400, 3000, 3), (2160, 240, 6), "LIFE_SAFETY", "FIRE_ACCESS")
for i, y in enumerate((1260, 1740, 2220), 1):
    add_centered_box("VP01_DATA_TRUNK_{:02d}".format(i), LAYERS[28], (2400, y, 18), (1320, 12, 12), "DATA", "CONTROL_TRACKING_NETWORK")
for i, (x, label) in enumerate(((1800, "STAGE"), (2400, "LED"), (3000, "SERVICE")), 1):
    add_centered_box("VP01_TAG_{}_{}".format(i, label), LAYERS[29], (x, 960, 132), (120, 6, 48), "ANNOTATION", "ROOM_LOAD_TAG", extra={"export_to_blender": "false"})
add_centered_box("VP01_VALIDATION_GATE_MARKER", LAYERS[30], (2400, 1800, 618), (24, 24, 24), "VALIDATION", "PASS_MARKER", "CONFIRMED", {"export_to_blender": "false"})

DOC.Views.Redraw()

# Objective acceptance report.  Failure raises before a save can be attempted.
managed = []
layer_counts = {path: 0 for path in LAYERS}
invalid = []
open_breps = []
names = set()
for obj in DOC.Objects:
    if obj.Attributes.GetUserString("project") != PROJECT:
        continue
    managed.append(obj)
    names.add(obj.Attributes.Name or "")
    path = DOC.Layers[obj.Attributes.LayerIndex].FullPath
    if path in layer_counts:
        layer_counts[path] += 1
    geometry = obj.Geometry
    if not geometry.IsValid:
        invalid.append(obj.Attributes.Name)
    if isinstance(geometry, Rhino.Geometry.Brep) and not geometry.IsSolid:
        open_breps.append(obj.Attributes.Name)

required_names = {
    "VP01_ARCH_SLAB",
    "VP01_ARCH_ROOF",
    "VP01_STAGE_FLOOR_120X100",
    "VP01_LED_CEILING_MOVABLE",
    "VP01_CAM_01_BODY",
    "VP01_ELEC_MAIN_SERVICE",
    "VP01_FIRE_ACCESS_LANE",
}
empty_layers = sorted(path for path, count in layer_counts.items() if count == 0)
missing_names = sorted(required_names - names)
passed = len(managed) >= 90 and not invalid and not open_breps and not empty_layers and not missing_names
report = {
    "schema": "vp-studio-rhino-massing/v1",
    "passed": passed,
    "managed_object_count": len(managed),
    "closed_solid_count": sum(1 for obj in managed if isinstance(obj.Geometry, Rhino.Geometry.Brep) and obj.Geometry.IsSolid),
    "invalid_objects": invalid,
    "open_breps": open_breps,
    "empty_required_layers": empty_layers,
    "missing_required_names": missing_names,
    "layer_counts": layer_counts,
    "stage_clear_dimensions_in": [1440, 1200, 480],
    "led_main_wall": {"diameter_in": 960, "height_in": 288, "arc_degrees": 180, "segments": LED_SEGMENTS},
    "deleted_previous_managed_objects": DELETED_PREVIOUS,
    "save_performed": False,
}
print("VP_STUDIO_BUILD_RESULT=" + json.dumps(report, sort_keys=True))
if not passed:
    raise RuntimeError("VP Studio massing acceptance gate failed: " + json.dumps(report, sort_keys=True))
