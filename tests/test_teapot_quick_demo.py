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
        self.assertIn("COMFY_SDXL_OUTPUT_PASS", cookbook)
        self.assertIn("COMFY_FLUX_OUTPUT_PASS", cookbook)
        self.assertIn("stage=sdxl+flux", cookbook)
        self.assertIn("comfyui_vp_stylize.py", wrapper)
        self.assertIn("comfy_style_prompt.txt", wrapper)
        self.assertIn("cliff_house_sdxl.png", wrapper)

    def test_teapot_lane_has_deterministic_hero_transition(self):
        transition = (TEAPOT / "system_prompts" / "05_phase_comfyui.md").read_text(encoding="utf-8")
        interaction = (TEAPOT / "prompts" / "04_phase_material_interactions.md").read_text(encoding="utf-8")
        plugin = (ROOT / "deployment" / "plugins" / "teapot_execution_rails" / "__init__.py").read_text(encoding="utf-8")
        for text in (transition, interaction, plugin):
            self.assertIn("demos/teapot/hero/BAC_TEAPOT_HERO.blend", text)
        self.assertIn("hero.open_verified_hero(root)", transition)
        self.assertIn("ComfyUI never runs inside Blender MCP", transition)
        self.assertIn("comfyui_bac_hero.py", transition)
        self.assertIn("COMFY_FLUX_OUTPUT_PASS", transition)
        self.assertIn("Never substitute the", plugin)
        self.assertIn("standalone Cliff House or VP Studio HERO", plugin)

        bac_master = TEAPOT / "hero" / "BAC_TEAPOT_HERO.blend"
        self.assertEqual(bac_master.stat().st_size, 1548410063)
        bac_helper = (TEAPOT / "skills" / "blender_bac_hero.py").read_text(encoding="utf-8")
        for token in (
            'EXPECTED = {"objects": 506, "meshes": 257, "cameras": 6, "lights": 1}',
            "350e19eb3db88cf5c98c98ba76f5d9f2017ed168b5fcf7e276a2c3bb13c7b882",
            "BAC_TEAPOT_HERO_working.blend",
            "Camera_day",
            "BAC_HERO_OPEN_PASS",
            "BAC_HERO_RENDER_PASS",
        ):
            self.assertIn(token, bac_helper)
        bac_wrapper = (TEAPOT / "skills" / "comfyui_bac_hero.py").read_text(encoding="utf-8")
        self.assertIn("bac_teapot_hero_sdxl.png", bac_wrapper)
        self.assertIn("bac_teapot_hero_stylized.png", bac_wrapper)
        self.assertIn("COMFY_SOURCE_PASS lane=bac_hero", bac_wrapper)
        self.assertIn("render_root not in source.parents", bac_wrapper)
        self.assertIn('marker_lines[1].strip()', bac_wrapper)
        self.assertIn('"--denoise", "0.18"', bac_wrapper)
        self.assertIn('"--flux-cfg", "3.5"', bac_wrapper)
        self.assertIn('"--seed", "126"', bac_wrapper)
        hero_prompt = (TEAPOT / "hero" / "user_prompts" / "comfy_style_prompt.txt").read_text(encoding="utf-8")
        self.assertIn("circular magenta float", hero_prompt)
        self.assertIn("ring with a clearly open center", hero_prompt)
        self.assertIn("flamingo float", hero_prompt)
        self.assertIn("rugged coastal cliff", hero_prompt)
        self.assertIn("No empty void, studio backdrop, beige cyclorama", hero_prompt)
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("/demos/teapot/hero/BAC_TEAPOT_HERO.blend filter=lfs", attributes)

        teapot_wrapper = (TEAPOT / "skills" / "comfyui_teapot.py").read_text(encoding="utf-8")
        self.assertIn("comfyui_vp_stylize.py", teapot_wrapper)
        self.assertIn("teapot_sdxl.png", teapot_wrapper)
        self.assertIn("teapot_stylized.png", teapot_wrapper)
        self.assertTrue((TEAPOT / "user_prompts" / "comfy_style_prompt.txt").is_file())

    def test_teapot_rails_block_blender_host_exit_but_allow_comfy_wrapper(self):
        import importlib.util
        import os
        import tempfile
        path = ROOT / "deployment" / "plugins" / "teapot_execution_rails" / "__init__.py"
        spec = importlib.util.spec_from_file_location("teapot_rails_test", path)
        rails = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rails)
        old = os.environ.get("AEC_DEMO_ID")
        old_root = os.environ.get("AEC_DEMO_ROOT")
        os.environ["AEC_DEMO_ID"] = "teapot-01"
        temp = tempfile.TemporaryDirectory()
        os.environ["AEC_DEMO_ROOT"] = temp.name
        try:
            blocked = rails.on_pre_tool_call(
                tool_name="mcp_blender_execute_blender_code",
                args={"code": "raise SystemExit('done')"},
            )
            self.assertEqual(blocked["action"], "block")
            master_save = rails.on_pre_tool_call(
                tool_name="mcp_blender_execute_blender_code",
                args={"code": "bpy.ops.wm.save_as_mainfile(filepath='demos/teapot/hero/BAC_TEAPOT_HERO.blend')"},
            )
            self.assertEqual(master_save["action"], "block")
            allowed = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": 'python "$AEC_DEMO_ROOT/demos/teapot/skills/comfyui_bac_hero.py"'},
            )
            self.assertIsNone(allowed)
            teapot_allowed = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": 'python "$AEC_DEMO_ROOT/demos/teapot/skills/comfyui_teapot.py"'},
            )
            self.assertIsNone(teapot_allowed)
            native_root = str(Path(temp.name).resolve())
            msys_root = "/" + native_root.replace("\\", "/")[0].lower() + native_root.replace("\\", "/")[2:]
            msys_allowed = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": f"python {msys_root}/demos/teapot/skills/comfyui_bac_hero.py --dry-run"},
            )
            self.assertIsNone(msys_allowed)
            marker = Path(temp.name) / "demos" / "teapot" / "work" / "active_render_lane.txt"
            marker.parent.mkdir(parents=True)
            marker.write_text("bac_hero\n", encoding="utf-8")
            wrong_lane = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": 'python "$AEC_DEMO_ROOT/demos/teapot/skills/comfyui_teapot.py"'},
            )
            right_lane = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": 'python "$AEC_DEMO_ROOT/demos/teapot/skills/comfyui_bac_hero.py"'},
            )
            self.assertEqual(wrong_lane["action"], "block")
            self.assertIsNone(right_lane)
            marker.unlink()
            temp_demo = Path(temp.name) / "demos" / "teapot"
            cd_allowed = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": f'cd "{temp_demo}" && python skills/comfyui_teapot.py --dry-run'},
            )
            self.assertIsNone(cd_allowed)
            env_allowed = rails.on_pre_tool_call(
                tool_name="terminal",
                args={
                    "command": f'AEC_DEMO_ROOT="{temp.name}" python skills/comfyui_teapot.py 2>&1',
                    "background": True,
                },
            )
            self.assertIsNone(env_allowed)
            browser_blocked = rails.on_pre_tool_call(
                tool_name="browser_navigate", args={"url": "http://127.0.0.1:8188"}
            )
            self.assertEqual(browser_blocked["action"], "block")
            execute_code = rails.on_pre_tool_call(
                tool_name="execute_code", args={"code": "import hashlib"}
            )
            self.assertEqual(execute_code["action"], "block")
            curl_probe = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": "curl -s http://127.0.0.1:8188/system_stats"},
            )
            self.assertEqual(curl_probe["action"], "block")
            invented = rails.on_pre_tool_call(
                tool_name="terminal", args={"command": "python skills/comfy_stylize.py"}
            )
            self.assertEqual(invented["action"], "block")
            execute_code = rails.on_pre_tool_call(
                tool_name="execute_code",
                args={"code": "import comfyui_teapot; comfyui_teapot.main()"},
            )
            self.assertEqual(execute_code["action"], "block")
        finally:
            temp.cleanup()
            if old is None:
                os.environ.pop("AEC_DEMO_ID", None)
            else:
                os.environ["AEC_DEMO_ID"] = old
            if old_root is None:
                os.environ.pop("AEC_DEMO_ROOT", None)
            else:
                os.environ["AEC_DEMO_ROOT"] = old_root

    def test_bac_hero_pool_assets_are_locked_to_measured_zones(self):
        helper = (TEAPOT / "skills" / "blender_bac_hero.py").read_text(encoding="utf-8")
        prompt = (TEAPOT / "system_prompts" / "05_phase_comfyui.md").read_text(encoding="utf-8")
        phase = (TEAPOT / "prompts" / "05_phase_pool_assets.md").read_text(encoding="utf-8")
        rails = (ROOT / "deployment" / "plugins" / "teapot_execution_rails" / "__init__.py").read_text(
            encoding="utf-8"
        )
        for token in (
            "def add_pool_assets",
            'POOL_COLLECTION = "BAC_POOL_ASSETS"',
            'POOL_WATER_OBJECT = "water_surface_new"',
            "POOL_SCENE_SCALE = 0.001",
            "BAC_POOL_ASSETS_PASS floats=2 chairs=3 furniture=1",
            '"category": "float"',
            '"category": "chair"',
            '"category": "furniture"',
            "chair intersects water",
            "furniture not on north patio",
        ):
            self.assertIn(token, helper)
        for text in (prompt, phase, rails):
            self.assertIn("add_pool_assets(root, reset=True)", text)
            self.assertIn("BAC_POOL_ASSETS_PASS", text)
            self.assertIn("Cam_Shot_A", text)
        self.assertIn("Let's add the pool assets to the pool area", prompt)
        self.assertIn("1:1000", prompt)
        self.assertEqual(helper.count('"rotation": math.radians(270.0)'), 3)

        expected = {
            "beach_chair_v1.blend": "7c27fe5b19bd211a6736342636876993fb04d91690feba0c3d49993d9adc1f9e",
            "beach_chair_v2.blend": "cbd8b8bef53865f6528859515ef55afeffd83e4dbfc6b5474686604f853db509",
            "beach_chair_v3.blend": "560e94ffe989f5b0eec97163e99d4de7b1182c8f7e3fc35351d651f0b7438792",
            "float_ring.blend": "04333a1b08d114412e591e89725cc660e29a6dda042be52ca5ccad7e21a06344",
            "OutdoorFurniture1.blend": "11388046766d5fd5d39337d1a3cd9213d3ffccc84498ec308db2efcdbbbf935a",
            "pool_flamingo.blend": "40e58bd288c8154345b5ee490f09d2fcefd027c3a04d7edeb3ded5ea43af9f37",
        }
        asset_dir = TEAPOT / "hero" / "assets" / "pool"
        for name, digest in expected.items():
            path = asset_dir / name
            self.assertTrue(path.is_file(), name)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("/demos/teapot/hero/assets/pool/*.blend filter=lfs", attributes)

    def test_installer_creates_independent_cliff_hero_profile(self):
        installer = (ROOT / "Install-AEC-Demo.ps1").read_text(encoding="utf-8")
        for token in (
            "cliff_hero",
            "Start-Cliff-Hero-Quick.ps1",
            "Cliff_HERO_Quick.bat",
            "cliff-house-hero-runtime-store",
            "project:cliff-house-hero-01",
            "Sync-TeapotExecutionRails",
            "Sync-CliffHeroExecutionRails",
        ):
            self.assertIn(token, installer)

        dml = (ROOT / "deployment" / "cliff-hero-profile" / "dml_mcp_server_cliff_hero.cmd").read_text(encoding="utf-8")
        cma = (ROOT / "deployment" / "cliff-hero-profile" / "cma_mcp_server_cliff_hero.cmd").read_text(encoding="utf-8")
        config = (ROOT / "deployment" / "cliff-hero-profile" / "config.example.yaml").read_text(encoding="utf-8")
        launcher = (ROOT / "deployment" / "cliff-hero-profile" / "Start-Cliff-Hero-Quick.ps1").read_text(encoding="utf-8")
        self.assertIn(".venv-dml\\Scripts\\python.exe", dml)
        self.assertIn("-m dml_mcp.dml_mcp_server", dml)
        self.assertIn("-m cma.mcp_server", cma)
        self.assertNotIn("  rhino:", config)
        self.assertIn("cliff_hero_execution_rails", config)
        self.assertIn("-SkipRhino", launcher)

    def test_cliff_hero_rails_keep_the_quick_lane_bounded(self):
        import importlib.util
        import os
        path = ROOT / "deployment" / "plugins" / "cliff_hero_execution_rails" / "__init__.py"
        spec = importlib.util.spec_from_file_location("cliff_hero_rails_test", path)
        rails = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rails)
        old_id = os.environ.get("AEC_DEMO_ID")
        old_root = os.environ.get("AEC_DEMO_ROOT")
        os.environ["AEC_DEMO_ID"] = "cliff-house-hero-01"
        os.environ["AEC_DEMO_ROOT"] = str(ROOT)
        try:
            allowed = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": 'python "$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py" --dry-run'},
            )
            self.assertIsNone(allowed)
            cd_allowed = rails.on_pre_tool_call(
                tool_name="terminal",
                args={"command": f'cd "{HERO}" && python skills/comfyui_cliff_hero.py'},
            )
            self.assertIsNone(cd_allowed)
            self.assertEqual(rails.on_pre_tool_call(tool_name="mcp_rhino_get_document_info", args={})["action"], "block")
            self.assertEqual(rails.on_pre_tool_call(tool_name="browser_navigate", args={"url": "http://127.0.0.1:8188"})["action"], "block")
            self.assertEqual(rails.on_pre_tool_call(tool_name="terminal", args={"command": "python skills/comfy_stylize.py"})["action"], "block")
        finally:
            if old_id is None:
                os.environ.pop("AEC_DEMO_ID", None)
            else:
                os.environ["AEC_DEMO_ID"] = old_id
            if old_root is None:
                os.environ.pop("AEC_DEMO_ROOT", None)
            else:
                os.environ["AEC_DEMO_ROOT"] = old_root

    def test_other_demo_launchers_preflight_comfyui(self):
        launchers = (
            ROOT / "deployment" / "aec-cptx-profile" / "Start-Hermes-AEC-Rhino-DML.ps1",
            ROOT / "deployment" / "bac-teapot-profile" / "Start-BAC_Teapot.ps1",
            ROOT / "deployment" / "cliff-hero-profile" / "Start-Cliff-Hero-Quick.ps1",
        )
        for launcher in launchers:
            text = launcher.read_text(encoding="utf-8")
            self.assertNotIn("-SkipComfyUI", text)

    def test_bac_launcher_rejects_missing_lfs_hero_payload(self):
        launcher = (ROOT / "deployment" / "bac-teapot-profile" / "Start-BAC_Teapot.ps1").read_text(encoding="utf-8")
        self.assertIn("BAC_TEAPOT_HERO.blend", launcher)
        self.assertIn("1548410063", launcher)
        self.assertIn("git lfs pull", launcher)

    def test_original_cliff_animation_is_two_stage(self):
        phase7 = (ROOT / "scripts" / "comfyui_phase7.py").read_text(encoding="utf-8")
        for token in (
            "load_flux_builder",
            "flux-2-klein-base-4b-fp8.safetensors",
            "qwen_3_4b.safetensors",
            "flux2-vae.safetensors",
            "sdxl_enhanced",
            "ocean_view_ai_flux.mp4",
            "COMFY_OUTPUT_PASS stage=sdxl+flux",
            "--prompt-file",
        ):
            self.assertIn(token, phase7)


if __name__ == "__main__":
    unittest.main()
