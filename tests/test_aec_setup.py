from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "aec_setup.py"
REPO_ROOT = MODULE_PATH.parents[1]
SPEC = importlib.util.spec_from_file_location("aec_setup", MODULE_PATH)
aec_setup = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = aec_setup
SPEC.loader.exec_module(aec_setup)


class SetupTests(unittest.TestCase):
    def test_load_env_preserves_explicit_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.env"
            path.write_text("COMFYUI_URL=http://example:8188\nNEW_VALUE=hello\n")
            with mock.patch.dict(os.environ, {"COMFYUI_URL": "http://explicit:8188"}, clear=False):
                os.environ.pop("NEW_VALUE", None)
                aec_setup.load_env(path)
                self.assertEqual(os.environ["COMFYUI_URL"], "http://explicit:8188")
                self.assertEqual(os.environ["NEW_VALUE"], "hello")
                os.environ.pop("NEW_VALUE", None)

    def test_every_tier_has_python_and_blender(self):
        for components in aec_setup.TIERS.values():
            self.assertIn("python", components)
            self.assertIn("blender", components)

    def test_windows_install_commands_use_exact_package_ids(self):
        with mock.patch("platform.system", return_value="Windows"):
            self.assertIn("BlenderFoundation.Blender", aec_setup.install_command("blender"))
            self.assertIn("astral-sh.uv", aec_setup.install_command("uvx"))

    def test_all_demo_profiles_have_isolated_dml_and_mcp_contracts(self):
        demos = {
            "virtual_production_studio": "project:vp-studio-01",
            "cliff_house": "project:cliff-house-01",
            "teapot": "project:teapot-01",
        }
        for demo, project_id in demos.items():
            contract = (REPO_ROOT / "demos" / demo / "AGENTS.md").read_text()
            self.assertIn(project_id, contract)
            self.assertIn("mcp_daystrom_dml", contract)
            self.assertIn("mcp_cma_augment", contract)
            self.assertIn("mcp_cma_reinforce", contract)

    def test_installer_carries_and_preserves_daystrom_state(self):
        installer = (REPO_ROOT / "Install-AEC-Demo.ps1").read_text()
        builder = (REPO_ROOT / "New-AEC-PortableBundle.ps1").read_text()
        self.assertIn("Restore-PortableDaystromStores", installer)
        self.assertIn("Preserved existing Daystrom store", installer)
        self.assertIn("Seed-DemoDmlKnowledge", installer)
        self.assertIn("SkipDmlStores", builder)
        self.assertIn("offline\\daystrom\\stores", builder)
        self.assertIn("includes_daystrom_stores", builder)
        self.assertIn("Project DML/CMA state is bundled by default", builder)
        self.assertIn("Close all Hermes demo sessions", builder)


if __name__ == "__main__":
    unittest.main()
