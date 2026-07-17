import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "deployment" / "plugins" / "vp_execution_rails" / "__init__.py"


def load_plugin():
    spec = importlib.util.spec_from_file_location("vp_execution_rails_test", PLUGIN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module._STATE.clear()
    return module


class VpExecutionRailsTests(unittest.TestCase):
    def setUp(self):
        self.rails = load_plugin()
        self.env = patch.dict(
            os.environ,
            {"AEC_DEMO_ID": "vp-studio-01", "AEC_DEMO_RUN_ID": "test-run"},
            clear=False,
        )
        self.env.start()
        self.rails.on_post_tool_call(
            tool_name="mcp_rhino_open_doc",
            args={"path": "source/vp_studio_01_template.3dm"},
            status="ok",
            result={},
        )

    def tearDown(self):
        self.env.stop()

    def test_blocks_python_outside_mcp_but_allows_inline_rhino_python(self):
        blocked = self.rails.on_pre_tool_call(
            tool_name="terminal", args={"command": "python build_shell.py"}
        )
        self.assertEqual("block", blocked["action"])
        allowed = self.rails.on_pre_tool_call(
            tool_name="mcp_rhino_run_python", args={"script": "print('ok')"}
        )
        self.assertIsNone(allowed)
        mutation = self.rails.on_pre_tool_call(
            tool_name="mcp_rhino_run_python",
            args={"script": "doc.Objects.AddBrep(box, attrs)"},
        )
        self.assertEqual("block", mutation["action"])

    def test_blocks_in_agent_application_launches(self):
        for command in (
            r'"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" scene.blend',
            "Rhino.exe /nosplash",
            "comfy launch",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name="terminal", args={"command": command}
            )
            self.assertEqual("block", blocked["action"])

    def test_allows_only_the_checked_in_comfyui_helper(self):
        state = self.rails._STATE["test-run"]
        state["blender_render_ready"] = True
        state["comfy_preflight_ready"] = True
        for command in (
            "python skills/comfyui_vp_stylize.py --dry-run",
            "python3 ./skills/comfyui_vp_stylize.py",
            "python skills/comfyui_vp_stylize.py --denoise 0.20",
        ):
            self.assertIsNone(self.rails.on_pre_tool_call(
                tool_name="terminal", args={"command": command}
            ))

        wrapped = (
            "cd C:/Users/test/2026_aec_cptx_demo_dml/"
            "demos/virtual_production_studio && "
            "python skills/comfyui_vp_stylize.py --dry-run"
        )
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="terminal", args={"command": wrapped}
        ))
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="terminal", args={"cmd": "python skills/comfyui_vp_stylize.py"}
        ))

        for command in (
            "curl http://127.0.0.1:8188/object_info",
            "python build_comfy_workflow.py",
            "comfy launch --background",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name="terminal", args={"command": command}
            )
            self.assertEqual("block", blocked["action"])

    def test_comfy_requires_render_pass_then_dry_run(self):
        state = self.rails._STATE["test-run"]
        dry = "python skills/comfyui_vp_stylize.py --dry-run"
        full = "python skills/comfyui_vp_stylize.py"
        blocked = self.rails.on_pre_tool_call(
            tool_name="terminal", args={"command": dry}
        )
        self.assertIn("VP_RENDER_PASS", blocked["message"])
        state["blender_render_ready"] = True
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="terminal", args={"command": dry}
        ))
        blocked = self.rails.on_pre_tool_call(
            tool_name="terminal", args={"command": full}
        )
        self.assertIn("COMFY_PREFLIGHT_PASS", blocked["message"])
        self.rails.on_post_tool_call(
            tool_name="terminal", args={"command": dry}, status="ok",
            result={"output": "COMFY_PREFLIGHT_PASS"},
        )
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="terminal", args={"command": full}
        ))

    def test_blocks_comfyui_browser_and_workflow_file_improvisation(self):
        blocked = self.rails.on_pre_tool_call(
            tool_name="browser_navigate", args={"url": "http://127.0.0.1:8188"}
        )
        self.assertEqual("block", blocked["action"])
        blocked = self.rails.on_pre_tool_call(
            tool_name="write_file",
            args={"path": "work/vp_studio_workflow.json", "content": "{}"},
        )
        self.assertEqual("block", blocked["action"])

    def test_blocks_nonexistent_memory_prompt_lookup(self):
        for tool in ("mcp_cma_get_prompt", "mcp_daystrom_dml_get_prompt"):
            blocked = self.rails.on_pre_tool_call(
                tool_name=tool, args={"name": "rhino-model-building"}
            )
            self.assertEqual("block", blocked["action"])

    def test_blocks_file_patch_churn_after_modeling_starts(self):
        args = {"script": "doc.Objects.AddBrep(box, attrs)"}
        self.rails.on_post_tool_call(
            tool_name="mcp_rhino_run_python", args=args, status="ok", result={}
        )
        blocked = self.rails.on_pre_tool_call(
            tool_name="patch", args={"path": "build_shell.py"}
        )
        self.assertEqual("block", blocked["action"])
        self.assertIsNone(
            self.rails.on_pre_tool_call(
                tool_name="write_file", args={"path": "work/dml_events/phase.md"}
            )
        )

    def test_blocks_importer_rewrite_even_before_modeling(self):
        for path in (
            "skills/import_with_metadata.py",
            "demos/virtual_production_studio/skills/import_with_metadata.py",
            r"C:\demo\skills\import_with_metadata.py",
            "skills/blender_vp_production.py",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name="write_file", args={"path": path, "content": "invented parser"}
            )
            self.assertEqual("block", blocked["action"])

    def test_blocks_all_new_python_and_csharp_files(self):
        for path in (
            "work/build_shell_phase1.py",
            "work/retry.cs",
            "work/retry.csx",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name="write_file", args={"path": path, "content": "probe"}
            )
            self.assertEqual("block", blocked["action"])

    def test_blocks_camera_diagnostic_loop_after_two_attempts(self):
        blocked = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": "# CAMERA FIX v1\nbpy.ops.mesh.primitive_cube_add(); # test_cube"},
        )
        self.assertEqual("block", blocked["action"])

    def test_only_allows_atomic_manifest_camera_helper_without_preconsuming_retries(self):
        direct = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": "cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()"},
        )
        self.assertEqual("block", direct["action"])
        approved = (
            "skill='skills/blender_vp_production.py'; "
            "vp.apply_required_set_dressing(root); "
            "vp.render_beauty_preview(root)"
        )
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": approved}
        ))
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": approved}
        ))
        third = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": approved}
        )
        self.assertIsNone(third)
        self.assertEqual(0, self.rails._STATE["test-run"]["blender_camera_retries"])

    def test_limits_blender_visual_reviews(self):
        for _ in range(3):
            self.assertIsNone(self.rails.on_pre_tool_call(
                tool_name="mcp_blender_get_viewport_screenshot", args={}
            ))
        blocked = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_get_viewport_screenshot", args={}
        )
        self.assertEqual("block", blocked["action"])

    def test_rhino_traceback_does_not_consume_mutation_budget(self):
        mutation = {"script": "doc.Objects.AddBrep(box, attrs)"}
        traceback = {
            "stdout": (
                "Traceback (most recent call last):\n"
                "AttributeError: 'LayerTable' object has no attribute 'FindByName'"
            ),
            "error": None,
        }
        for _ in range(8):
            self.assertIsNone(
                self.rails.on_pre_tool_call(
                    tool_name="mcp_rhino_run_csharp", args=mutation
                )
            )
            self.rails.on_post_tool_call(
                tool_name="mcp_rhino_run_csharp",
                args=mutation,
                status="ok",
                result=traceback,
            )
        state = self.rails._STATE["test-run"]
        self.assertEqual(0, state["total_mutations"])
        self.assertEqual(0, state["phase_mutations"])

    def test_explicit_rhino_error_does_not_consume_mutation_budget(self):
        mutation = {"script": "doc.Objects.AddBrep(box, attrs)"}
        self.rails.on_post_tool_call(
            tool_name="mcp_rhino_run_csharp",
            args=mutation,
            status="ok",
            result={"stdout": "", "error": "script failed"},
        )
        self.assertEqual(0, self.rails._STATE["test-run"]["total_mutations"])

    def test_numeric_and_vision_sequence_is_advisory_not_blocking(self):
        mutation = {"script": "doc.Objects.AddBrep(box, attrs)"}
        self.rails.on_post_tool_call(
            tool_name="mcp_rhino_run_csharp", args=mutation, status="ok", result={}
        )
        self.assertIsNone(
            self.rails.on_pre_tool_call(
                tool_name="mcp_rhino_get_viewport_image", args={}
            )
        )
        self.assertIsNone(
            self.rails.on_pre_tool_call(tool_name="mcp_rhino_save_doc", args={})
        )

        validator = {"script": "print('bounds')"}
        self.rails.on_post_tool_call(
            tool_name="mcp_rhino_run_python",
            args=validator,
            status="ok",
            result={"stdout": "NUMERIC_PASS"},
        )
        self.assertIsNone(
            self.rails.on_pre_tool_call(tool_name="mcp_rhino_get_viewport_image", args={})
        )
        self.rails.on_post_tool_call(
            tool_name="mcp_rhino_get_viewport_image", args={}, status="ok", result={}
        )
        self.assertIsNone(
            self.rails.on_pre_tool_call(tool_name="mcp_rhino_save_doc", args={})
        )

    def test_blocks_external_script_replay_inside_mcp(self):
        blocked = self.rails.on_pre_tool_call(
            tool_name="mcp_rhino_run_python",
            args={"script": "exec(compile(open('phase.py').read(), 'phase.py', 'exec'))"},
        )
        self.assertEqual("block", blocked["action"])

    def test_blocks_blender_obj_and_addon_fallbacks(self):
        for code in (
            "bpy.ops.import_scene.obj(filepath='bad.obj')",
            "bpy.ops.wm.obj_import(filepath='bad.obj')",
            "bpy.ops.preferences.addon_enable(module='io_import_3dm')",
            "if line.startswith('v'): objects_data[name] = []",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name="mcp_blender_execute_blender_code", args={"code": code}
            )
            self.assertEqual("block", blocked["action"])

        wrong_directory = (
            "cd C:/Users/test/Desktop && "
            "python skills/comfyui_vp_stylize.py --dry-run"
        )
        blocked = self.rails.on_pre_tool_call(
            tool_name="terminal", args={"command": wrong_directory}
        )
        self.assertEqual("block", blocked["action"])
        blocked = self.rails.on_pre_tool_call(
            tool_name="execute_code", args={"code": "python skills/comfyui_vp_stylize.py"}
        )
        self.assertEqual("block", blocked["action"])

    def test_blocks_blender_host_termination(self):
        for code in (
            "raise SystemExit('diagnostic failed')",
            "import sys; sys.exit('no tripod')",
            "quit()",
            "exit('done')",
            "bpy.ops.wm.quit_blender()",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name="mcp_blender_execute_blender_code", args={"code": code}
            )
            self.assertEqual("block", blocked["action"])
            self.assertIn("never terminate the Blender host", blocked["message"])

    def test_allows_checked_in_blender_3dm_importer(self):
        allowed = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": "skill='skills/import_with_metadata.py'; mod.import_3dm(handoff)"},
        )
        self.assertIsNone(allowed)

    def test_blocks_direct_blend_open_and_save(self):
        for code in (
            "bpy.ops.wm.open_mainfile(filepath='old.blend')",
            "bpy.ops.wm.save_as_mainfile(filepath='wrong.blend')",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name="mcp_blender_execute_blender_code", args={"code": code}
            )
            self.assertEqual("block", blocked["action"])

    def test_verified_handoff_resets_blender_review_budgets(self):
        state = self.rails._STATE["test-run"]
        state["blender_camera_retries"] = 2
        state["blender_visual_reviews"] = 3
        code = "skill='skills/blender_vp_production.py'; vp.import_current_handoff(root, reset_scene=True)"
        self.rails.on_post_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": code},
            status="ok",
            result={"result": "VP_HANDOFF_PASS imported=174"},
        )
        self.assertTrue(state["blender_handoff_ready"])
        self.assertEqual(0, state["blender_camera_retries"])
        self.assertEqual(0, state["blender_visual_reviews"])
        self.assertEqual("blender", state["workflow_phase"])
        self.assertFalse(state["blender_set_dressing_ready"])

    def test_requires_set_dressing_receipt_before_camera_and_render(self):
        approved_camera = (
            "skill='skills/blender_vp_production.py'; "
            "vp.render_beauty_preview(root)"
        )
        blocked = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": approved_camera},
        )
        self.assertEqual("block", blocked["action"])
        self.assertIn("VP_SET_DRESSING_PASS", blocked["message"])

        dressing = (
            "skill='skills/blender_vp_production.py'; "
            "vp.apply_required_set_dressing(root)"
        )
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": dressing}
        ))
        self.rails.on_post_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": dressing}, status="ok",
            result={"result": "VP_SET_DRESSING_PASS categories=6 placements=27"},
        )
        self.assertTrue(self.rails._STATE["test-run"]["blender_set_dressing_ready"])
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": approved_camera},
        ))

    def test_verified_handoff_permanently_closes_rhino(self):
        code = "skill='skills/blender_vp_production.py'; vp.import_current_handoff(root, reset_scene=True)"
        self.rails.on_post_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": code}, status="ok",
            result={"result": "VP_HANDOFF_PASS imported=265"},
        )
        for tool in (
            "mcp_rhino_list_slots",
            "mcp_rhino_run_python",
            "mcp_rhino_run_csharp",
            "mcp_rhino_get_viewport_image",
            "mcp_rhino_save_doc",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name=tool, args={"script": "print('x')"}
            )
            self.assertEqual("block", blocked["action"])
            self.assertIn("permanently closed", blocked["message"])

    def test_requires_fixed_asset_placement_helper(self):
        for code in (
            "vp.fit_to_proxy(imported, proxy)",
            "vp.import_cached_asset(root, key)",
            "obj.scale = (0.01, 0.01, 0.01)",
        ):
            blocked = self.rails.on_pre_tool_call(
                tool_name="mcp_blender_execute_blender_code", args={"code": code}
            )
            self.assertEqual("block", blocked["action"])
            # Keep this test focused on the individual prohibition; retry
            # exhaustion is covered by test_stops_repeated_unapproved_asset_retries.
            self.rails._STATE["test-run"]["blender_asset_retry_count"] = 0
            self.rails._STATE["test-run"]["blender_asset_deployment_blocked"] = False

        approved = (
            "skill='skills/blender_vp_production.py'; "
            "vp.place_cached_asset(root, 'roadcase_thomas_kole', 'ROAD_CASE_01')"
        )
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": approved}
        ))

        bare_stand = (
            "skill='skills/blender_vp_production.py'; "
            "vp.place_cached_asset(root, 'grip_c_stand_kilianpohl', 'FLOOR_LIGHT_01')"
        )
        blocked = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": bare_stand}
        )
        self.assertEqual("block", blocked["action"])
        self.assertIn("bare C-stand", blocked["message"])

    def test_stops_repeated_unapproved_asset_retries(self):
        code = "obj.scale = (0.01, 0.01, 0.01)"
        first = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": code}
        )
        self.assertEqual("block", first["action"])
        second = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": code}
        )
        self.assertEqual("block", second["action"])
        self.assertIn("retry budget exhausted", second["message"])
        approved = (
            "skill='skills/blender_vp_production.py'; "
            "vp.place_cached_asset(root, 'roadcase_thomas_kole', 'ROAD_CASE_01')"
        )
        blocked = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": approved}
        )
        self.assertEqual("block", blocked["action"])
        self.assertIn("asset deployment is blocked", blocked["message"])

    def test_stops_retries_after_fixed_placement_failure_receipt(self):
        code = (
            "skill='skills/blender_vp_production.py'; "
            "vp.apply_required_set_dressing(root)"
        )
        self.assertIsNone(self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": code}
        ))
        self.rails.on_post_tool_call(
            tool_name="mcp_blender_execute_blender_code",
            args={"code": code},
            status="ok",
            result={"error": "fixed placement size verification failed for camera_tripod_silver_key"},
        )
        blocked = self.rails.on_pre_tool_call(
            tool_name="mcp_blender_execute_blender_code", args={"code": code}
        )
        self.assertEqual("block", blocked["action"])
        self.assertIn("asset deployment is blocked", blocked["message"])

    def test_requires_template_open_and_resets_mutation_state(self):
        self.rails._STATE.clear()
        mutation = {"script": "doc.Objects.AddBrep(box, attrs)"}
        blocked = self.rails.on_pre_tool_call(
            tool_name="mcp_rhino_run_csharp", args=mutation
        )
        self.assertEqual("block", blocked["action"])
        self.rails.on_post_tool_call(
            tool_name="mcp_rhino_open_doc",
            args={"path": "source/vp_studio_01_template.3dm"},
            status="ok",
            result={},
        )
        self.assertIsNone(
            self.rails.on_pre_tool_call(
                tool_name="mcp_rhino_run_csharp", args=mutation
            )
        )

    def test_does_not_impose_turn_based_mutation_limits(self):
        mutation = {"script": "doc.Objects.AddBrep(box, attrs)"}
        for _ in range(30):
            self.assertIsNone(
                self.rails.on_pre_tool_call(
                    tool_name="mcp_rhino_run_csharp", args=mutation
                )
            )
            self.rails.on_post_tool_call(
                tool_name="mcp_rhino_run_csharp", args=mutation, status="ok", result={}
            )
        self.assertIsNone(
            self.rails.on_pre_tool_call(
                tool_name="mcp_rhino_run_csharp", args=mutation
            )
        )

        validator = {"script": "print('NUMERIC_PASS')"}
        self.rails.on_post_tool_call(
            tool_name="mcp_rhino_run_python",
            args=validator,
            status="ok",
            result={"stdout": "NUMERIC_PASS"},
        )
        for _ in range(10):
            self.assertIsNone(
                self.rails.on_pre_tool_call(
                    tool_name="mcp_rhino_run_csharp", args=mutation
                )
            )
            self.rails.on_post_tool_call(
                tool_name="mcp_rhino_run_csharp", args=mutation, status="ok", result={}
            )
        self.assertIsNone(
            self.rails.on_pre_tool_call(
                tool_name="mcp_rhino_run_csharp", args=mutation
            )
        )


if __name__ == "__main__":
    unittest.main()
