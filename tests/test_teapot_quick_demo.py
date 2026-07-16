from pathlib import Path
import hashlib
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEAPOT = ROOT / "demos" / "teapot"
HERO = ROOT / "demos" / "cliff_house" / "hero"


class TeapotQuickDemoTests(unittest.TestCase):
    def test_startup_is_blender_only_and_gated(self):
        text = (TEAPOT / "system_prompts" / "00_session_startup.md").read_text(encoding="utf-8")
        for token in (
            "prompts/01_locked_teapot_manifest.md",
            "Blender-only",
            "WAITING_FOR_BUILD_REQUEST",
            "let's build a Utah teapot",
            "Before an explicit build request, make no Blender mutation calls",
            "build_canonical_teapot(root, reset_scene=True)",
            "CANONICAL_DATA_PASS",
            "TEAPOT_BUILD_PASS",
            "open audience interaction loop",
            "Daystrom DML",
        ):
            self.assertIn(token, text)

    def test_blender_phase_uses_canonical_constructor(self):
        text = (TEAPOT / "prompts" / "02_phase_blender_build.md").read_text(encoding="utf-8")
        for token in (
            "```python",
            "blender_teapot_interactions.py",
            "build_canonical_teapot(root, reset_scene=True)",
            "CANONICAL_DATA_PASS",
            "TEAPOT_BUILD_PASS",
            "mcp_blender_execute_blender_code(code=...)",
        ):
            self.assertIn(token, text)
        self.assertIn("Never\ncall Rhino", text)

    def test_canonical_obj_fingerprint_and_counts(self):
        source = TEAPOT / "utah_teapot.obj"
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            "a447b8936e70678c70438a4155b6ef5310c4d0a647cee362f84d53c8b38baf9f",
        )
        vertices = faces = groups = 0
        for line in source.read_text(encoding="utf-8").splitlines():
            vertices += line.startswith("v ")
            faces += line.startswith("f ")
            groups += line.startswith("g ")
        self.assertEqual((vertices, faces, groups), (18530, 18432, 4))
        provenance = (TEAPOT / "UTAH_TEAPOT_SOURCE.md").read_text(encoding="utf-8")
        self.assertIn("1987 — Frank Crow", provenance)
        self.assertIn("graphics.cs.utah.edu/teapot", provenance)
        self.assertIn("32 cubic Bézier patches", provenance)

    def test_blender_stage_uses_live_canonical_meshes(self):
        text = (TEAPOT / "prompts" / "03_phase_blender_stage.md").read_text(encoding="utf-8")
        for token in (
            "TEAPOT_BUILD_PASS",
            "prepare_product_stage",
            "TEAPOT_LOOK_PASS",
            "TEAPOT_PREVIEW_PASS",
        ):
            self.assertIn(token, text)
        self.assertIn("Do not rebuild, reimport, or", text)

    def test_blender_interactions_are_reversible_and_open_ended(self):
        helper = (TEAPOT / "skills" / "blender_teapot_interactions.py").read_text(encoding="utf-8")
        for preset in (
            "glazed_ceramic", "white_porcelain", "copper", "brushed_steel",
            "chrome", "glass", "matte_black",
        ):
            self.assertIn('"' + preset + '"', helper)
        for token in (
            "def apply_custom_material",
            "def build_canonical_teapot",
            "def set_camera_view",
            "def _world_bounds",
            "TEAPOT_PREVIEW_PASS",
            "CANONICAL_SHA256",
            "TARGET_WIDTH_M = 0.30",
            '"TEAPOT_BODY", "TEAPOT_LID", "TEAPOT_SPOUT", "TEAPOT_HANDLE"',
        ):
            self.assertIn(token, helper)

    def test_teapot_profile_enables_narrow_receipt_rails(self):
        config = (ROOT / "deployment" / "bac-teapot-profile" / "config.example.yaml").read_text(encoding="utf-8")
        launcher = (ROOT / "deployment" / "bac-teapot-profile" / "Start-BAC_Teapot.ps1").read_text(encoding="utf-8")
        plugin = (ROOT / "deployment" / "plugins" / "teapot_execution_rails" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("teapot_execution_rails", config)
        self.assertIn("AEC_DEMO_ID = 'teapot-01'", launcher)
        self.assertIn("-SkipRhino", launcher)
        self.assertIn("Start gate: waiting for you", launcher)
        self.assertNotIn("  rhino:", config)
        self.assertIn('tool.startswith("mcp_rhino_")', plugin)
        self.assertIn("Rhino is prohibited because BAC Teapot is Blender-only", plugin)
        self.assertIn("build_canonical_teapot", plugin)
        self.assertIn("START GATE: session startup is idle", plugin)
        self.assertIn("_BLENDER_HOST_EXIT", plugin)
        self.assertIn("never terminate the Blender host", plugin)
        self.assertIn("New-Item -ItemType Directory -Force", launcher)

    def test_shared_preflight_keeps_rhino_for_other_demos(self):
        preflight = (ROOT / "deployment" / "rtx-pro-profile" / "Test-RTX-Pro-Preflight.ps1").read_text(encoding="utf-8")
        self.assertIn("[switch]$SkipRhino", preflight)
        self.assertIn("if (-not $SkipRhino)", preflight)
        self.assertIn("else { @('rhino', 'blender', 'daystrom_dml', 'cma') }", preflight)

    def test_cliff_hero_lane_uses_verified_scene_and_comfy_wrapper(self):
        self.assertGreater((HERO / "cliff_house_02_HERO.blend").stat().st_size, 100_000)
        helper = (HERO / "skills" / "blender_cliff_hero.py").read_text(encoding="utf-8")
        cookbook = (HERO / "QUICK_DEMO.md").read_text(encoding="utf-8")
        wrapper = (HERO / "skills" / "comfyui_cliff_hero.py").read_text(encoding="utf-8")
        self.assertIn('EXPECTED = {"objects": 183, "meshes": 174, "cameras": 7, "lights": 2}', helper)
        self.assertIn("MASTER_SHA256", helper)
        self.assertIn("cliff_house_02_HERO_working.blend", helper)
        self.assertIn("shutil.copy2(master, working)", helper)
        self.assertIn("CLIFF_HERO_RENDER_PASS", helper)
        self.assertIn("COMFY_OUTPUT_PASS", cookbook)
        self.assertIn("comfyui_vp_stylize.py", wrapper)
        self.assertIn("comfy_style_prompt.txt", wrapper)

    def test_teapot_lane_has_deterministic_hero_transition(self):
        transition = (TEAPOT / "system_prompts" / "05_phase_comfyui.md").read_text(encoding="utf-8")
        interaction = (TEAPOT / "prompts" / "04_phase_material_interactions.md").read_text(encoding="utf-8")
        plugin = (ROOT / "deployment" / "plugins" / "teapot_execution_rails" / "__init__.py").read_text(encoding="utf-8")
        for text in (transition, interaction, plugin):
            self.assertIn("demos/cliff_house/hero/cliff_house_02_HERO.blend", text)
        self.assertIn("hero.open_verified_hero(root)", transition)
        self.assertIn("ComfyUI never runs inside Blender MCP", transition)
        self.assertIn("comfyui_cliff_hero.py", transition)
        self.assertIn("Never look under", plugin)

    def test_teapot_rails_block_blender_host_exit_but_allow_comfy_wrapper(self):
        import importlib.util
        import os
        path = ROOT / "deployment" / "plugins" / "teapot_execution_rails" / "__init__.py"
        spec = importlib.util.spec_from_file_location("teapot_rails_test", path)
        rails = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rails)
        old = os.environ.get("AEC_DEMO_ID")
        os.environ["AEC_DEMO_ID"] = "teapot-01"
        try:
            blocked = rails.on_pre_tool_call(
                tool_name="mcp_blender_execute_blender_code",
                args={"code": "raise SystemExit('done')"},
            )
            self.assertEqual(blocked["action"], "block")
            master_save = rails.on_pre_tool_call(
                tool_name="mcp_blender_execute_blender_code",
                args={"code": "bpy.ops.wm.save_as_mainfile(filepath='demos/cliff_house/hero/cliff_house_02_HERO.blend')"},
            )
            self.assertEqual(master_save["action"], "block")
            allowed = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": 'python "$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py"'},
            )
            self.assertIsNone(allowed)
        finally:
            if old is None:
                os.environ.pop("AEC_DEMO_ID", None)
            else:
                os.environ["AEC_DEMO_ID"] = old

    def test_installer_creates_independent_cliff_hero_profile(self):
        installer = (ROOT / "Install-AEC-Demo.ps1").read_text(encoding="utf-8")
        for token in (
            "cliff_hero",
            "Start-Cliff-Hero-Quick.ps1",
            "Cliff_HERO_Quick.bat",
            "cliff-house-hero-runtime-store",
            "project:cliff-house-hero-01",
            "Sync-TeapotExecutionRails",
        ):
            self.assertIn(token, installer)


if __name__ == "__main__":
    unittest.main()
