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

    def test_rtx_launcher_selects_rtx_pro_profile(self):
        launcher = (REPO_ROOT / "deployment" / "rtx-pro-profile" / "Start-RTX-Pro.ps1").read_text()
        self.assertIn("$env:HERMES_PROFILE = 'rtx_pro'", launcher)
        self.assertIn("-p rtx_pro chat", launcher)

    def test_vllm_launcher_repairs_network_and_waits_noninteractively(self):
        launcher = (REPO_ROOT / "deployment" / "wsl-vllm" / "start_vllm.bat").read_text()
        self.assertIn("docker network connect bridge", launcher)
        self.assertIn("--no-pause", launcher)
        self.assertIn("ping.exe -n 6", launcher)
        self.assertNotIn("timeout /t 5", launcher)

    def test_bac_launcher_starts_vllm_when_endpoints_are_down(self):
        launcher = (REPO_ROOT / "deployment" / "bac-teapot-profile" / "Start-BAC_Teapot.ps1").read_text()
        self.assertIn("Test-LocalModel 8000", launcher)
        self.assertIn("start_vllm.bat", launcher)
        self.assertIn("--no-pause", launcher)


if __name__ == "__main__":
    unittest.main()
