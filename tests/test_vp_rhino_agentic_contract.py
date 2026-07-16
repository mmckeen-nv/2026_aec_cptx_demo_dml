from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demos" / "virtual_production_studio"
CONTRACT = DEMO / "prompts" / "02_rhino_modeling_contract.md"
MANIFEST = DEMO / "prompts" / "01a_locked_scene_manifest.md"


class VpRhinoAgenticContractTests(unittest.TestCase):
    def test_no_checked_in_geometry_builder_exists(self):
        scripts = DEMO / "scripts"
        geometry_scripts = [p for p in scripts.glob("*rhino*.py") if "capture" not in p.name]
        self.assertEqual([], geometry_scripts)
        self.assertFalse((scripts / "build_rhino_massing.py").exists())

    def test_contract_requires_agent_authored_visible_mcp_geometry(self):
        text = CONTRACT.read_text(encoding="utf-8")
        for required in (
            "Hermes designs and models the studio in Rhino",
            "one manifest-defined assembly per",
            "Never write a complete phase or studio builder",
            "current phase explicitly excludes all later phases",
            "`project=vp-studio-01`",
            "Save useful checkpoints",
        ):
            self.assertIn(required, text)

    def test_locked_manifest_removes_spatial_discretion(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for required in (
            "Rhino model units: **inches**",
            "Building center and project datum: **(0, 0, 0)**",
            "Entire building exterior | -1080 | 1080 | -900 | 900",
            "Main stage planning zone | -720 | 720 | -600 | 600",
            "C = (-120, 0, 0)",
            "Active-face radius: **480 in**",
            "Start angle: **0 degrees**",
            "End angle: **180 degrees**",
            "CAM_A_HERO_TRACKED",
            "Six workstations, each **72 W x 30 D x 30 H in**",
            "Report each new object's world bounding box",
            "stop the phase and correct that object",
        ):
            self.assertIn(required, text)

    def test_template_uses_one_centered_datum_and_no_design_layout(self):
        text = (ROOT / "tools" / "create_vp_studio_template.py").read_text(encoding="utf-8")
        for required in (
            '"GUIDE_PROPERTY_ENVELOPE", -2400, -1800, 2400, 1800',
            '"GUIDE_BUILDING_ENVELOPE", -1080, -900, 1080, 900',
            '"GUIDE_STAGE_ENVELOPE", -720, -600, 720, 600',
            '"GUIDE_LED_ACTIVE_RADIUS", (-120, 0, 0), 480',
        ):
            self.assertIn(required, text)
        for prohibited in (
            "MOVE_BEFORE_USE",
            "GUIDE_ANCILLARY_BAR",
            "GUIDE_LOADING_APRON",
            "GUIDE_SCENERY_ROUTE_CENTERLINE",
        ):
            self.assertNotIn(prohibited, text)

    def test_every_phase_reads_and_enforces_manifest(self):
        startup = (DEMO / "system_prompts" / "00_session_startup.md").read_text(encoding="utf-8")
        agents = (DEMO / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("prompts/01a_locked_scene_manifest.md", startup)
        self.assertIn("prompts/01a_locked_scene_manifest.md", agents)
        for filename in (
            "02a_phase_site_shell.md",
            "02b_phase_stage_led.md",
            "02c_phase_rooms_access.md",
            "02d_phase_rigging_cameras.md",
        ):
            phase = (DEMO / "prompts" / filename).read_text(encoding="utf-8")
            self.assertIn("01a_locked_scene_manifest.md", phase)
            self.assertIn("Print", phase)

    def test_cliff_house_style_phase_prompts_exist(self):
        expected = (
            "02a_phase_site_shell.md",
            "02b_phase_stage_led.md",
            "02c_phase_rooms_access.md",
            "02d_phase_rigging_cameras.md",
        )
        for filename in expected:
            text = (DEMO / "prompts" / filename).read_text(encoding="utf-8")
            for heading in (
                "## Purpose",
                "## Pre-Phase Audit Checklist",
                "## Execution Steps",
                "## Post-Phase Cleanup Checklist",
                "## REVIEW GATE",
                "## Checkpoint Save",
            ):
                self.assertIn(heading, text)
            self.assertIn("## Hard Scope Boundary", text)
        self.assertFalse((DEMO / "prompts" / "02e_phase_electrical_mechanical.md").exists())
        self.assertFalse((DEMO / "prompts" / "02f_phase_life_safety_data.md").exists())

    def test_every_rhino_phase_embeds_tested_csharp_execution(self):
        phases = {
            "02a_phase_site_shell.md": ("mcp_rhino_run_csharp", "System.Func<string,int,double,double,double,double,double,double,System.Guid> SB", "WALL_SOUTH_UPPER"),
            "02b_phase_stage_led.md": ("mcp_rhino_run_csharp", "System.Func<double,double,double,double,Rhino.Geometry.Curve> RING", "LED_ACTIVE_WALL"),
            "02c_phase_rooms_access.md": ("mcp_rhino_run_csharp", "System.Action<string,int,double,double,double,double,double,double> XW", "PART_Y_NEG720"),
            "02d_phase_rigging_cameras.md": ("mcp_rhino_run_csharp", "System.Action<string,double,double,double,double,double,double> CAM", "TRUSS_EW_Y_", "CAM_D_HANDHELD_TRACKED"),
        }
        for filename, required in phases.items():
            text = (DEMO / "prompts" / filename).read_text(encoding="utf-8")
            for token in required:
                self.assertIn(token, text)
            self.assertIn("```csharp", text)

        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Python is read-only inspection/capture", contract)
        self.assertIn("Shared C# prelude for Phases 2-4", contract)
        self.assertIn("treat every `Objects.Add*` result as a `Guid`", contract)

    def test_physical_demo_skips_mep_geometry_and_writes_load_note(self):
        contract = CONTRACT.read_text(encoding="utf-8")
        brief = (DEMO / "prompts" / "01_standard_vp_studio_brief.md").read_text(encoding="utf-8")
        self.assertIn("The four Rhino phases are", contract)
        self.assertIn("vp_studio_01_estimated_load.md", contract)
        self.assertIn("Do not model electrical rooms", brief)
        self.assertIn("six operator chairs", brief)
        self.assertIn("12 movable production chairs", brief)

    def test_backend_requires_smooth_led_assets_and_lighting(self):
        brief = (DEMO / "prompts" / "01_standard_vp_studio_brief.md").read_text(encoding="utf-8")
        led = (DEMO / "prompts" / "02b_phase_stage_led.md").read_text(encoding="utf-8")
        assets = (DEMO / "prompts" / "03_asset_sourcing_contract.md").read_text(encoding="utf-8")
        handoff = (DEMO / "prompts" / "07_phase_export_blender.md").read_text(encoding="utf-8")
        self.assertIn("thin, smooth, continuous curve", brief)
        self.assertIn("faceted ring of boxes", led)
        self.assertIn("LED_Z_PASS", led)
        self.assertIn("bb.Min.Z < -0.001", led)
        self.assertIn("replaces the visible proxies", assets)
        self.assertIn("key, fill, rim/backlight", handoff)
        self.assertIn("approved\n   ComfyUI source render", handoff)
        self.assertIn("launcher-owned generic Blender scene", handoff)
        self.assertIn("import_current_handoff", handoff)
        self.assertIn("output-only", handoff)

    def test_current_dml_policy_supersedes_builder_recipe(self):
        policy = (DEMO / "knowledge" / "dml" / "rhino_agent_authored_workflow_current_20260713.md").read_text(encoding="utf-8")
        self.assertIn("status: CURRENT_POLICY", policy)
        self.assertIn("supersedes: build_rhino_massing.py", policy)
        self.assertIn("target 98 objects", policy)
        self.assertIn("thin smooth continuous curved assembly", policy)
        self.assertIn("replace every visible required", policy)

    def test_blender_handoff_policy_names_real_tool_and_paths(self):
        policy = (DEMO / "knowledge" / "dml" / "blender_handoff_tool_contract_current_20260713.md").read_text(encoding="utf-8")
        self.assertIn("status: CURRENT_POLICY", policy)
        self.assertIn("mcp_blender_execute_blender_code", policy)
        self.assertIn("../../skills/import_with_metadata.py", policy)
        self.assertIn("no generic `run` tool", policy)

    def test_blender_handoff_is_joined_mesh_3dm_only(self):
        handoff = (DEMO / "prompts" / "07_phase_export_blender.md").read_text(encoding="utf-8")
        importer = (ROOT / "skills" / "import_with_metadata.py").read_text(encoding="utf-8")
        for required in (
            "HANDOFF_MESH_PASS",
            "Mesh.CreateFromBrep",
            "joined.Append(part)",
            'os.environ["AEC_DEMO_ROOT"]',
            'root_name="VP_STUDIO_RHINO"',
            "VP_HANDOFF_PASS",
            "HANDOFF_LED_Z_FAIL",
            "assert_import_matches_source",
        ):
            self.assertIn(required, handoff)
        self.assertIn("OBJ and FBX are prohibited", handoff)
        self.assertIn("prefer_joined_meshes", importer)
        self.assertIn("Rhino and Blender are both Z-up", importer)
        self.assertIn("vertex.Y * unit_scale,\n                    vertex.Z * unit_scale", importer)

    def test_handoff_memory_rejects_first_mesh_part_and_count_only_gate(self):
        policy = (DEMO / "knowledge" / "dml" / "rhino_mesh_first_part_failure_20260713.md").read_text(encoding="utf-8")
        self.assertIn("status: CURRENT_POLICY", policy)
        self.assertIn("retained only the first face mesh", policy)
        self.assertIn("bounding-box parity", policy)
        self.assertIn("count equality alone never passes", policy)


if __name__ == "__main__":
    unittest.main()
