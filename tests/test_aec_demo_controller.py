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

    def post(self, tool, args=None, status="ok", error_message=None):
        controller.on_post_tool_call(
            **self.kw,
            tool_name=tool,
            args=args or {},
            result="ok",
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

    def test_mutation_is_not_quota_gated_but_phase_transitions_need_visual_evidence(self):
        for index in range(12):
            args = self.mutation(str(index))
            self.assertIsNone(self.pre("mcp_rhino_run_python", args))
            self.post("mcp_rhino_run_python", args)
        blocked = self.pre("mcp_rhino_save_doc", {"path": "C:/demo/work/checkpoint.3dm"})
        self.assertIn("completed vision_analyze", blocked["message"])
        self.post("mcp_rhino_list_objects", {})
        self.post("mcp_rhino_get_viewport_image", {})
        blocked = self.pre("mcp_rhino_save_doc", {"path": "C:/demo/work/checkpoint.3dm"})
        self.assertIn("completed vision_analyze", blocked["message"])
        vision = {"image_url": "C:/demo/work/viewport.png", "question": "Check massing and collisions"}
        self.assertIsNone(self.pre("vision_analyze", vision))
        self.post("vision_analyze", vision)
        save_args = {"path": "C:/demo/work/checkpoint.3dm"}
        self.assertIsNone(self.pre("mcp_rhino_save_doc", save_args))
        self.post("mcp_rhino_save_doc", save_args)
        self.assertIsNone(self.pre("mcp_blender_get_scene_info", {}))
        self.assertIsNone(self.pre("mcp_blender_execute_blender_code", {"code": "print('import')"}))
        self.assertIsNone(self.pre("mcp_cma_reinforce", {"evidence": "passed"}))

    def test_reinforce_and_blender_import_blocked_before_gated_save(self):
        args = self.mutation()
        self.post("mcp_rhino_run_python", args)
        self.post("mcp_rhino_list_objects", {})
        self.post("mcp_rhino_get_viewport_image", {})
        vision = {"image_url": "C:/demo/work/viewport.png", "question": "Check the phase"}
        self.post("vision_analyze", vision)
        self.assertIn("successful gated save", self.pre("mcp_cma_reinforce", {})["message"])
        self.assertIn("successfully saved Rhino handoff", self.pre("mcp_blender_execute_blender_code", {"code": "x"})["message"])

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

    def test_viewport_capture_without_vision_is_not_validation(self):
        args = self.mutation()
        self.post("mcp_rhino_run_python", args)
        self.post("mcp_rhino_list_objects", {})
        self.post("mcp_rhino_get_viewport_image", {})
        blocked = self.pre("mcp_rhino_save_doc", {"path": "C:/demo/work/checkpoint.3dm"})
        self.assertIn("completed vision_analyze", blocked["message"])

    def test_vision_requires_fresh_viewport_and_complete_arguments(self):
        self.assertIn("image_url", self.pre("vision_analyze", {})["message"])
        self.assertIn(
            "fresh Rhino viewport",
            self.pre("vision_analyze", {"image_url": "x.png", "question": "inspect"})["message"],
        )

    def test_vision_rejects_invented_remote_rhino_url(self):
        self.post("mcp_rhino_get_viewport_image", {})
        blocked = self.pre(
            "vision_analyze",
            {"image_url": "https://viewer.example/fake.jpg", "question": "Any defects?"},
        )
        self.assertIn("CaptureToBitmap", blocked["message"])

    def test_browser_and_blender_lifecycle_recovery_are_blocked(self):
        self.assertIn("browser fallback", self.pre("browser_snapshot", {})["message"])
        blocked = self.pre("terminal", {"command": 'Blender.exe --python-expr "bpy.ops.blendermcp.start_server()"'})
        self.assertIn("do not launch, configure, patch, or repair Blender", blocked["message"])

    def test_shell_rhino_python_and_live_config_repair_are_blocked(self):
        blocked = self.pre("terminal", {"command": 'Rhino.exe /runscript="_-RunPythonScript C:/demo/build.py"'})
        self.assertIn("shell/UI recovery", blocked["message"])
        blocked = self.pre(
            "terminal",
            {"command": "hermes config set mcp_servers.rhino.args '[--default-version, 8]'"},
        )
        self.assertIn("may not modify Hermes configuration", blocked["message"])

    def test_normal_terminal_inspection_remains_available(self):
        self.assertIsNone(self.pre("terminal", {"command": "git status --short"}))

    def test_controller_is_inert_outside_target_demo(self):
        with mock.patch.dict(os.environ, {"AEC_DEMO_ID": "cliff-house-01"}, clear=False):
            self.assertIsNone(self.pre("mcp_rhino_spawn_slot", {}))


if __name__ == "__main__":
    unittest.main()
