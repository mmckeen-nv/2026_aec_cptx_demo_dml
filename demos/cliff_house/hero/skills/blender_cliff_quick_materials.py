"""Harden the approved Cliff House quick master's materials without changing geometry."""

from __future__ import annotations

import bpy


def _input(node, name, value):
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def _principled(material_name, base_color, roughness, metallic=0.0):
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.name = "Cliff House Principled"
    output = nodes.new("ShaderNodeOutputMaterial")
    output.name = "Cliff House Material Output"
    _input(shader, "Base Color", (*base_color, 1.0))
    _input(shader, "Roughness", roughness)
    _input(shader, "Metallic", metallic)
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material, shader, output


def _add_micro_surface(material, shader, scale, detail, strength, distance):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.65
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])


def _set_viewport_color(material, rgba):
    material.diffuse_color = rgba


def build_materials():
    white, shader, _ = _principled(
        "WhiteConcrete", (0.72, 0.68, 0.59), roughness=0.72
    )
    _add_micro_surface(white, shader, scale=7.5, detail=4.0, strength=0.16, distance=0.055)
    _set_viewport_color(white, (0.72, 0.68, 0.59, 1.0))

    gray, shader, _ = _principled(
        "GrayConcrete", (0.30, 0.28, 0.25), roughness=0.78
    )
    _add_micro_surface(gray, shader, scale=9.0, detail=5.0, strength=0.22, distance=0.07)
    _set_viewport_color(gray, (0.30, 0.28, 0.25, 1.0))

    terrain, shader, _ = _principled(
        "CoastalCliff", (0.24, 0.16, 0.095), roughness=0.92
    )
    _add_micro_surface(
        terrain, shader, scale=2.2, detail=8.0, strength=0.55, distance=0.32
    )
    _set_viewport_color(terrain, (0.24, 0.16, 0.095, 1.0))

    wood, shader, _ = _principled("Wood", (0.23, 0.075, 0.025), roughness=0.48)
    _add_micro_surface(wood, shader, scale=5.0, detail=3.0, strength=0.18, distance=0.035)
    _set_viewport_color(wood, (0.23, 0.075, 0.025, 1.0))

    bronze, shader, _ = _principled(
        "Bronze", (0.28, 0.105, 0.025), roughness=0.26, metallic=0.92
    )
    _set_viewport_color(bronze, (0.28, 0.105, 0.025, 1.0))

    steel, shader, _ = _principled(
        "DarkSteel", (0.028, 0.032, 0.038), roughness=0.24, metallic=0.88
    )
    _set_viewport_color(steel, (0.028, 0.032, 0.038, 1.0))

    glass, shader, _ = _principled("Glass", (0.035, 0.075, 0.085), roughness=0.08)
    _input(shader, "Transmission Weight", 0.72)
    _input(shader, "IOR", 1.45)
    _input(shader, "Alpha", 0.58)
    glass.surface_render_method = "DITHERED"
    _set_viewport_color(glass, (0.035, 0.075, 0.085, 0.58))

    water, shader, _ = _principled(
        "PoolWater", (0.008, 0.12, 0.17), roughness=0.12, metallic=0.0
    )
    _input(shader, "Transmission Weight", 0.45)
    _input(shader, "IOR", 1.333)
    _add_micro_surface(water, shader, scale=4.0, detail=3.0, strength=0.12, distance=0.025)
    _set_viewport_color(water, (0.008, 0.12, 0.17, 0.8))

    slats = bpy.data.materials.get("WoodSlats_Vertical")
    if slats is None:
        slats, shader, _ = _principled(
            "WoodSlats_Vertical", (0.20, 0.055, 0.018), roughness=0.42
        )
        _add_micro_surface(
            slats, shader, scale=6.0, detail=3.0, strength=0.2, distance=0.04
        )
    _set_viewport_color(slats, (0.20, 0.055, 0.018, 1.0))

    terrain_object = bpy.data.objects.get("SITE_TERRAIN")
    if terrain_object is None or terrain_object.type != "MESH":
        raise RuntimeError("SITE_TERRAIN mesh is missing")
    terrain_object.data.materials.clear()
    terrain_object.data.materials.append(terrain)

    # The approved live scene already used this finish on the three main facade
    # masses. Reapply deterministically so the master and working copy agree.
    for object_name in ("L1_east", "L1_west", "L2_east", "L2_west", "L3_main"):
        obj = bpy.data.objects.get(object_name)
        if obj is not None and obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(slats)

    return {
        "objects": len(bpy.data.objects),
        "meshes": sum(1 for obj in bpy.data.objects if obj.type == "MESH"),
        "materials": sorted(material.name for material in bpy.data.materials),
        "unassigned": [
            obj.name
            for obj in bpy.data.objects
            if obj.type == "MESH" and not obj.data.materials
        ],
    }


if __name__ == "__main__":
    print(f"CLIFF_QUICK_MATERIALS_PASS={build_materials()}")
