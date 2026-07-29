"""Validate canonical Cliff House prompt, source-geometry, and HERO integrity."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import rhino3dm


ROOT = Path(__file__).resolve().parents[1]
# Pin the last reviewed geometry-contract revision. This includes the approved
# bounded-network-surface terrain fix while preserving exact prompt validation.
UPSTREAM_COMMIT = "54725a79b0abafa460c27135687d9d45c3c7aeaa"
UPSTREAM_PROJECT = "aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md"
EXACT_PROMPTS = (
    UPSTREAM_PROJECT,
    "system_prompts/02_phase_site_prep.md",
    "system_prompts/03_phase_massing.md",
    "system_prompts/05_phase_floorplan_3d.md",
    "system_prompts/06_phase_detailing.md",
)
SINGLE_FRAME_PROJECT = (
    "aa_demo_versions/cliff_house_single_frame_01/user_prompts/project_prompt.md"
)
HERO_HASHES = {
    "demos/cliff_house/source/renders/cliff_house_02_hero_20260615_0920.png":
        "68dab75009a9214339229e95a4bbe055c9cbea56a7f7de640230e433066ff188",
    "demos/cliff_house/source/base_model_final_20260615_0920.blend":
        "58ac4070f5d2369fa36ee01eaa959dafccb52fbe37f70852cb75589e9dc7ef17",
    "demos/cliff_house/hero/cliff_house_02_HERO.blend":
        "d0756bfa299b89d51642bf5688eba875f68cf99a9a72978bc24fac1f23d4413a",
}
SOURCE_PLAN_BOUNDS = {
    "building_plan": ((1.5, -15.5, 0.0), (13.5, 4.5, 0.0)),
    "driveway_plan": ((17.0, 6.5, 0.0), (25.0, 13.5, 0.0)),
    "garage_plan": ((7.0, 4.5, 0.0), (17.0, 15.0, 0.0)),
    "patio_stairs_plan": ((-3.0, -3.0, 0.0), (1.0, -1.0, 0.0)),
    "patio_plan": ((-6.0, -16.0, -1.0), (0.0, 5.0, -1.0)),
}
TERRAIN_POINTS = (
    ((25, -20, 0), (5, -20, 0), (-8, -20, -2.435513), (-15, -20, -5)),
    ((25, 16, 0), (5, 16, 0), (-4, 16, 0), (-15, 16, -2)),
    ((25, 16, 0), (25, 6.349829, 0), (25, -11.812446, 0), (25, -20, 0)),
    ((-15, 16, -1.800003), (-15, 7.633730, -1),
     (-15, -11.713384, -3.569228), (-15, -20, -5)),
    ((-0.049451, 16, -0.264660), (-0.049451, 6, -0.264660),
     (-0.049451, -9, 0), (-0.118379, -20, -1.572709)),
)


def git_blob(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{UPSTREAM_COMMIT}:{path}"], cwd=ROOT
    )


def normalized(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xyz(point) -> tuple[float, float, float]:
    return tuple(round(float(v), 6) for v in (point.X, point.Y, point.Z))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    for relative in EXACT_PROMPTS:
        require(
            normalized((ROOT / relative).read_bytes()) == normalized(git_blob(relative)),
            f"prompt drift: {relative}",
        )

    require(
        normalized((ROOT / SINGLE_FRAME_PROJECT).read_bytes())
        == normalized(git_blob(UPSTREAM_PROJECT)),
        f"prompt drift: {SINGLE_FRAME_PROJECT}",
    )

    for relative, expected in HERO_HASHES.items():
        require(sha256(ROOT / relative) == expected, f"HERO integrity drift: {relative}")

    model = rhino3dm.File3dm.FromByteArray(
        git_blob("aa_demo_versions/cliff_house_02/rhino_assets/base_model.3dm")
    )
    named = {}
    for obj in model.Objects:
        name = obj.Attributes.Name
        layer = model.Layers[obj.Attributes.LayerIndex].FullPath
        if not name and layer.endswith("::patio_plan"):
            name = "patio_plan"
        if name:
            named[name] = obj.Geometry
    for name, (expected_min, expected_max) in SOURCE_PLAN_BOUNDS.items():
        box = named[name].GetBoundingBox()
        require(xyz(box.Min) == expected_min, f"{name} minimum bounds drift")
        require(xyz(box.Max) == expected_max, f"{name} maximum bounds drift")

    curves = [
        obj.Geometry for obj in model.Objects
        if isinstance(obj.Geometry, rhino3dm.NurbsCurve)
    ]
    require(len(curves) == 5, f"expected five terrain curves, found {len(curves)}")
    actual_curves = []
    for curve in curves:
        require(curve.Degree == 3, "terrain curve degree drift")
        actual_curves.append(tuple(xyz(curve.Points[i]) for i in range(len(curve.Points))))
    expected_curves = [tuple(tuple(round(float(v), 6) for v in p) for p in c)
                       for c in TERRAIN_POINTS]
    require(sorted(actual_curves) == sorted(expected_curves), "terrain control points drift")

    profile = ROOT / "deployment/aec-cptx-profile"
    launch_prompts = (
        profile / "single-frame-benchmark.txt",
        profile / "cliff-house-real-workload.txt",
        profile / "cliff-house-continue-workload.txt",
        profile / "cliff-house-animation-continuation.txt",
    )
    for path in launch_prompts:
        text = path.read_text(encoding="utf-8")
        require("canonical-cliff-house-geometry.txt" in text, f"missing geometry oracle: {path}")

    benchmark = (profile / "single-frame-benchmark.txt").read_text(encoding="utf-8")
    for forbidden in ("75% glazing", "below 20%", "at least two punched"):
        require(forbidden not in benchmark, f"invented geometry rule returned: {forbidden}")
    for receipt in ("geometry_parity.json", "hero_geometry_validation.json",
                    "site_validation.json"):
        require(receipt in benchmark, f"missing benchmark gate: {receipt}")

    print(
        "CLIFF_GEOMETRY_CONTRACT_PASS "
        f"prompts={len(EXACT_PROMPTS) + 1} plans={len(SOURCE_PLAN_BOUNDS)} "
        f"terrain_curves={len(curves)} hero_assets={len(HERO_HASHES)}"
    )


if __name__ == "__main__":
    main()
