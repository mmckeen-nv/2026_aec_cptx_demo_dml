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

    def unlock_memory(self):
        self.post("mcp_daystrom_dml_stats")
        self.post("mcp_daystrom_dml_query")
        self.post("mcp_cma_augment")

    def mutation(self, suffix=""):
        return {"script": f"doc.Objects.AddBrep(brep{suffix})"}

    def test_mutation_requires_memory_sequence(self):
        blocked = self.pre("mcp_rhino_run_python", self.mutation())
        self.assertIn("DML stats", blocked["message"])
        self.unlock_memory()
        self.assertIsNone(self.pre("mcp_rhino_run_python", self.mutation()))

    def test_missing_required_script_is_blocked(self):
        blocked = self.pre("mcp_rhino_run_python", {})
        self.assertIn("non-empty 'script'", blocked["message"])

    def test_three_mutations_require_object_and_viewport_inspection(self):
        self.unlock_memory()
        for index in range(3):
            args = self.mutation(str(index))
            self.assertIsNone(self.pre("mcp_rhino_run_python", args))
            self.post("mcp_rhino_run_python", args)
        self.assertIn("three Rhino mutations", self.pre("mcp_rhino_run_python", self.mutation("x"))["message"])
        self.post("mcp_rhino_list_objects")
        self.assertIsNotNone(self.pre("mcp_rhino_run_python", self.mutation("x")))
        self.post("mcp_rhino_get_viewport_image")
        self.assertIsNone(self.pre("mcp_rhino_run_python", self.mutation("x")))

    def test_identical_failure_twice_forces_changed_approach(self):
        args = {"script": "print('probe')"}
        for _ in range(2):
            self.post("mcp_rhino_run_python", args, status="error", error_message="boom")
        blocked = self.pre("mcp_rhino_run_python", args)
        self.assertIn("failed twice", blocked["message"])

    def test_reopen_spawn_and_blender_fallback_are_blocked(self):
        path = {"path": "C:/demo/source/vp_studio_01_template.3dm"}
        self.assertIsNone(self.pre("mcp_rhino_open_doc", path))
        self.post("mcp_rhino_open_doc", path)
        self.assertIn("opened only once", self.pre("mcp_rhino_open_doc", path)["message"])
        self.assertIn("prohibited", self.pre("mcp_rhino_spawn_slot", {})["message"])
        self.assertIn("Blender is locked", self.pre("mcp_blender_get_scene_info", {})["message"])

    def test_controller_is_inert_outside_target_demo(self):
        with mock.patch.dict(os.environ, {"AEC_DEMO_ID": "cliff-house-01"}, clear=False):
            self.assertIsNone(self.pre("mcp_rhino_spawn_slot", {}))


if __name__ == "__main__":
    unittest.main()

