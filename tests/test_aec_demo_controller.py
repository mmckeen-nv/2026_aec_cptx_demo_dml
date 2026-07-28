from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "deployment" / "plugins" / "aec_demo_controller" / "__init__.py"
SPEC = importlib.util.spec_from_file_location("aec_demo_controller_test", MODULE_PATH)
controller = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(controller)


class AecDemoControllerTests(unittest.TestCase):
    def setUp(self):
        controller._STATES.clear()
        self.env = mock.patch.dict(
            os.environ,
            {"AEC_DEMO_ID": "vp-studio-01", "AEC_DEMO_CONTROLLER_LOG_DIR": tempfile.gettempdir()},
            clear=False,
        )
        self.env.start()
        self.kw = {"session_id": "test-session", "task_id": "test-task"}

    def tearDown(self):
        self.env.stop()

    def post(self, tool, args=None, status="ok", error_message=None, result=None):
        if result is None:
            result = "PASS: required visible elements are present" if tool == "vision_analyze" else "ok"
        controller.on_post_tool_call(
            **self.kw,
            tool_name=tool,
            args=args or {},
            result=result,
            status=status,
            error_message=error_message,
        )

    def pre(self, tool, args=None):
        return controller.on_pre_tool_call(**self.kw, tool_name=tool, args=args or {})

    def mutation(self, suffix=""):
        return {"script": f"doc.Objects.AddBrep(brep{suffix})"}

    def test_mutation_does_not_require_memory_ceremony(self):
        self.assertIsNone(self.pre("mcp_rhino_run_python", self.mutation()))

    def test_missing_required_script_is_blocked(self):
        blocked = self.pre("mcp_rhino_run_python", {})
        self.assertIn("non-empty 'script'", blocked["message"])

    def test_mutation_save_and_phase_transition_are_not_ceremony_gated(self):
        for index in range(12):
            args = self.mutation(str(index))
            self.assertIsNone(self.pre("mcp_rhino_run_python", args))
            self.post("mcp_rhino_run_python", args)
        save_args = {"path": "C:/demo/work/checkpoint.3dm"}
        self.assertIsNone(self.pre("mcp_rhino_save_doc", save_args))
        self.post("mcp_rhino_save_doc", save_args)
        self.assertIsNone(self.pre("mcp_blender_get_scene_info", {}))
        self.assertIsNone(self.pre("mcp_blender_execute_blender_code", {"code": "print('import')"}))
        self.assertIsNone(self.pre("mcp_cma_reinforce", {"evidence": "passed"}))

    def test_reinforce_is_advisory_while_blender_requires_a_save(self):
        args = self.mutation()
        self.post("mcp_rhino_run_python", args)
        self.assertIsNone(self.pre("mcp_cma_reinforce", {}))
        self.assertIn("saved Rhino .3dm", self.pre("mcp_blender_execute_blender_code", {"code": "x"})["message"])

    def test_python_and_csharp_both_use_script_argument(self):
        for tool in ("mcp_rhino_run_python", "mcp_rhino_run_csharp"):
            self.assertIn("non-empty 'script'", self.pre(tool, {})["message"])
            self.assertIsNone(self.pre(tool, {"script": "print('ok')"}))

    def test_reopen_and_slot_lifecycle_are_blocked(self):
        path = {"path": "C:/demo/source/vp_studio_01_template.3dm"}
        self.assertIsNone(self.pre("mcp_rhino_open_doc", path))
        self.post("mcp_rhino_open_doc", path)
        self.assertIn("opened only once", self.pre("mcp_rhino_open_doc", path)["message"])
        self.assertIn("prohibited", self.pre("mcp_rhino_spawn_slot", {})["message"])
        self.assertIn("prohibited", self.pre("mcp_rhino_close_doc", {})["message"])

    def test_all_rhino_command_macros_are_blocked(self):
        for command in ("_New", "_SaveAs", "_Export", "_ZoomExtents", "_SetView _World _Top"):
            blocked = self.pre("mcp_rhino_run_command", {"command": command})
            self.assertIn("Rhino command macros are prohibited", blocked["message"])

    def test_save_is_allowed_when_vision_is_temporarily_unavailable(self):
        args = self.mutation()
        self.post("mcp_rhino_run_python", args)
        self.post("mcp_rhino_list_objects", {})
        self.assertIsNone(self.pre("mcp_rhino_save_doc", {"path": "C:/demo/work/checkpoint.3dm"}))

    def test_vision_requires_complete_arguments_but_not_controller_bookkeeping(self):
        self.assertIn("image_url", self.pre("vision_analyze", {})["message"])
        self.assertIsNone(self.pre("vision_analyze", {"image_url": "x.png", "question": "inspect"}))

    def test_vision_rejects_invented_remote_rhino_url(self):
        blocked = self.pre(
            "vision_analyze",
            {"image_url": "https://viewer.example/fake.jpg", "question": "Any defects?"},
        )
        self.assertIn("CaptureToBitmap", blocked["message"])

    def test_large_inline_viewport_tool_is_redirected_to_local_png(self):
        blocked = self.pre("mcp_rhino_get_viewport_image", {})
        self.assertIn("local-PNG", blocked["message"])

    def test_capture_to_bitmap_is_viewport_evidence_not_a_mutation(self):
        mutation = self.mutation()
        self.post("mcp_rhino_run_python", mutation)
        self.post("mcp_rhino_list_objects", {})
        capture = {
            "script": "view.ActiveViewport.CaptureToBitmap(System.Drawing.Size(960,540)).Save('C:/demo/work/rhino_phase.png')"
        }
        self.post("mcp_rhino_run_python", capture)
        state = controller._STATES["test-task"]
        self.assertEqual(1, state["mutations"])
        self.assertTrue(state["viewport_since_mutation"])
        self.assertEqual("C:/demo/work/rhino_phase.png", state["rhino_last_viewport_path"])
        vision = {"image_url": state["rhino_last_viewport_path"], "question": "Check the LED curve"}
        self.assertIsNone(self.pre("vision_analyze", vision))

    def test_blender_validation_does_not_invalidate_rhino_handoff(self):
        mutation = self.mutation()
        self.post("mcp_rhino_run_python", mutation)
        self.post("mcp_rhino_list_objects", {})
        self.post("mcp_rhino_run_python", {"script": "view.ActiveViewport.CaptureToBitmap(size).Save('C:/demo/work/rhino.png')"})
        rhino_vision = {"image_url": "C:/demo/work/rhino.png", "question": "Check layout"}
        self.post("vision_analyze", rhino_vision)
        self.post("mcp_rhino_save_doc", {"path": "C:/demo/work/handoff.3dm"})
        self.post("mcp_blender_execute_blender_code", {"code": "import bpy"})
        state = controller._STATES["test-task"]
        self.assertTrue(state["rhino_handoff_ready"])
        self.assertTrue(state["vision_since_viewport"])
        self.assertFalse(state["blender_vision_since_viewport"])
        self.post("mcp_blender_get_viewport_screenshot", {"path": "C:/demo/work/blender.png"})
        blender_vision = {"image_url": "C:/demo/work/blender.png", "question": "Check imported geometry"}
        self.assertIsNone(self.pre("vision_analyze", blender_vision))
        self.post("vision_analyze", blender_vision)
        self.assertTrue(state["blender_vision_since_viewport"])

    def test_revise_vision_verdict_is_recorded_but_does_not_destroy_checkpointing(self):
        mutation = self.mutation()
        self.post("mcp_rhino_run_python", mutation)
        self.post("mcp_rhino_list_objects", {})
        capture = {"script": "view.ActiveViewport.CaptureToBitmap(size).Save('C:/demo/work/rhino.png')"}
        self.post("mcp_rhino_run_python", capture)
        vision = {"image_url": "C:/demo/work/rhino.png", "question": "Check geometry quality"}
        self.post("vision_analyze", vision, result="REVISE: LED wall is visibly faceted")
        state = controller._STATES["test-task"]
        self.assertFalse(state["vision_since_viewport"])
        self.assertIsNone(self.pre("mcp_rhino_save_doc", {"path": "C:/demo/work/handoff.3dm"}))

    def test_dml_runtime_directory_is_precreated(self):
        with tempfile.TemporaryDirectory() as root:
            with mock.patch.dict(os.environ, {"AEC_DEMO_ROOT": root}, clear=False):
                controller.on_session_start(**self.kw)
                self.assertTrue((Path(root) / "work" / "dml_events").is_dir())

    def test_comfyui_is_not_controller_gated_by_visual_bookkeeping(self):
        request = {"command": "Invoke-RestMethod http://127.0.0.1:8188/prompt"}
        self.assertIsNone(self.pre("terminal", request))

    def test_dml_query_does_not_require_stats_first(self):
        self.post("mcp_daystrom_dml_query", {"query": "prior stage lesson"})
        self.assertTrue(controller._STATES["test-task"]["query"])

    def test_cliff_automatic_starts_in_rhino_and_blocks_discovery(self):
        with mock.patch.dict(
            os.environ,
            {"AEC_DEMO_ID": "cliff-house-01", "AEC_DEMO_ACTION": "automatic"},
            clear=False,
        ):
            self.assertIn(
                "must begin",
                self.pre("mcp_blender_get_scene_info", {})["message"],
            )
            self.assertIn(
                "self-contained",
                self.pre("read_file", {"path": "hermes/DEMO_RULES.md"})["message"],
            )
            self.assertIsNone(
                self.pre(
                    "mcp_rhino_run_csharp",
                    {"script": "doc.Objects.AddBrep(brep)"},
                )
            )

    def test_cliff_automatic_normalizes_native_mcp_tool_names(self):
        with mock.patch.dict(
            os.environ,
            {"AEC_DEMO_ID": "cliff-house-01", "AEC_DEMO_ACTION": "automatic"},
            clear=False,
        ):
            self.assertIsNone(
                self.pre(
                    "mcp__rhino__run_csharp",
                    {"script": "doc.Objects.AddBrep(brep)"},
                )
            )
            blocked = self.pre("mcp__blender__get_scene_info", {})
            self.assertIn("must begin", blocked["message"])

    def test_cliff_automatic_handoff_unlocks_host_and_blender_tools(self):
        with mock.patch.dict(
            os.environ,
            {"AEC_DEMO_ID": "cliff-house-01", "AEC_DEMO_ACTION": "automatic"},
            clear=False,
        ):
            mutation = {"script": "doc.Objects.AddBrep(brep)"}
            self.post("mcp_rhino_run_csharp", mutation)
            self.assertIn(
                "before the fresh Rhino handoff",
                self.pre("terminal", {"command": "python scripts/build_mesh_bridge.py"})["message"],
            )
            self.assertIn(
                "before the fresh Rhino handoff",
                self.pre("mcp_blender_get_scene_info", {})["message"],
            )
            self.post("mcp_rhino_save_doc", {"path": "C:/demo/base_model.3dm"})
            self.assertIsNone(
                self.pre("terminal", {"command": "python scripts/build_mesh_bridge.py"})
            )
            self.assertIsNone(self.pre("mcp_blender_get_scene_info", {}))

    def test_cliff_automatic_disables_rhino_viewport_calls(self):
        with mock.patch.dict(
            os.environ,
            {"AEC_DEMO_ID": "cliff-house-01", "AEC_DEMO_ACTION": "automatic"},
            clear=False,
        ):
            mutation = {"script": "doc.Objects.AddBrep(brep)"}
            self.post("mcp_rhino_run_csharp", mutation)
            blocked = self.pre("mcp_rhino_get_viewport_image", {})
            self.assertIn("viewport calls are disabled", blocked["message"])

    def test_browser_and_blender_lifecycle_recovery_are_blocked(self):
        self.assertIn("browser fallback", self.pre("browser_snapshot", {})["message"])
        blocked = self.pre("terminal", {"command": 'Blender.exe --python-expr "bpy.ops.blendermcp.start_server()"'})
        self.assertIn("do not launch, configure, patch, or repair Blender", blocked["message"])

    def test_legitimate_rhino_to_blender_pipeline_paths_are_not_recovery(self):
        commands = (
            'python scripts/build_mesh_bridge.py --source "run/rhino_assets/base_model.3dm" --output "run/blender_assets/fresh.mesh.json"',
            'python scripts/comfyui_flux2_direct.py --source "run/renders/single_frame/comfy_source/frame_0000.png" --output "run/renders/single_frame/flux2_enhanced/frame_0000.png"',
        )
        for command in commands:
            self.assertIsNone(self.pre("terminal", {"command": command}))

    def test_shell_rhino_python_and_live_config_repair_are_blocked(self):
        blocked = self.pre("terminal", {"command": 'Rhino.exe /runscript="_-RunPythonScript C:/demo/build.py"'})
        self.assertIn("shell/UI recovery", blocked["message"])
        blocked = self.pre(
            "terminal",
            {"command": "hermes config set mcp_servers.rhino.args '[--default-version, 8]'"},
        )
        self.assertIn("may not modify Hermes configuration", blocked["message"])

    def test_generated_application_scripts_can_be_written_but_not_shell_launched(self):
        generated = {
            "path": "work/generated_scripts/build_stage.py",
            "content": "import Rhino\ndoc.Objects.AddBrep(stage)",
        }
        self.assertIsNone(self.pre("write_file", generated))
        blocked = self.pre(
            "terminal",
            {"command": 'Rhino.exe /runscript="_-RunPythonScript work/generated_scripts/build_stage.py"'},
        )
        self.assertIn("shell/UI recovery", blocked["message"])

    def test_external_rhino_script_execution_is_counted_as_mutation(self):
        args = {
            "script": "path=r'C:/demo/work/generated_scripts/build_stage.py'; exec(compile(open(path).read(), path, 'exec'))"
        }
        self.assertIsNone(self.pre("mcp_rhino_run_python", args))
        self.post("mcp_rhino_run_python", args)
        state = controller._STATES["test-task"]
        self.assertEqual(1, state["mutations"])
        self.assertFalse(state["viewport_since_mutation"])

    def test_normal_terminal_inspection_remains_available(self):
        self.assertIsNone(self.pre("terminal", {"command": "git status --short"}))

    def test_context_rollover_metrics_measure_compaction_savings(self):
        first = {**self.kw, "session_id": "raw-1", "approx_input_tokens": 150000, "message_count": 200}
        controller.on_pre_api_request(**first)
        controller.on_post_api_request(**first, usage={"input_tokens": 150000, "output_tokens": 100})
        second = {**self.kw, "session_id": "raw-2", "approx_input_tokens": 30000, "message_count": 8}
        controller.on_pre_api_request(**second)
        controller.on_post_api_request(**second, usage={"input_tokens": 30000, "output_tokens": 50})
        state = controller._STATES["test-task"]
        self.assertEqual(1, state["compression_rotations"])
        self.assertEqual(30000, state["compaction_retained_tokens"])
        self.assertEqual(120000, state["compaction_reclaimed_tokens"])
        self.assertLess(state["compaction_retained_pct"], 12)

    def test_cliff_house_gets_only_lifecycle_guardrails(self):
        with mock.patch.dict(os.environ, {"AEC_DEMO_ID": "cliff-house-01"}, clear=False):
            self.assertIn("prohibited", self.pre("mcp_rhino_spawn_slot", {})["message"])
            self.assertIn("command macros", self.pre("mcp_rhino_run_command", {"command": "_Save"})["message"])
            self.assertIsNone(self.pre("mcp_rhino_open_doc", {"path": "C:/demo/base_model.3dm"}))
            self.assertIsNone(self.pre("mcp_rhino_save_doc", {"path": "C:/demo/work/checkpoint.3dm"}))

    def test_controller_is_inert_outside_supported_demos(self):
        with mock.patch.dict(os.environ, {"AEC_DEMO_ID": "unrelated-demo"}, clear=False):
            self.assertIsNone(self.pre("mcp_rhino_spawn_slot", {}))


if __name__ == "__main__":
    unittest.main()
