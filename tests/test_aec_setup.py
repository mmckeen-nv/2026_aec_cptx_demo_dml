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
        self.assertIn("demos\\virtual_production_studio", launcher)
        self.assertIn("Test-RTX-Pro-Preflight.ps1", launcher)

    def test_rtx_preflight_requires_mcp_and_isolated_dml(self):
        preflight = (REPO_ROOT / "deployment" / "rtx-pro-profile" / "Test-RTX-Pro-Preflight.ps1").read_text()
        for server in ("rhino", "blender", "daystrom_dml", "cma"):
            self.assertIn(server, preflight)
        self.assertIn("project:vp-studio-01", preflight)
        self.assertIn("vp-studio-01-runtime-store", preflight)
        self.assertIn("cma_mcp_server_vp_studio.cmd", preflight)
        self.assertIn("RHINO_MCP_AUTOSTART_PORT", preflight)
        self.assertIn("Wait-TcpPort $rhinoMcpPort", preflight)
        self.assertIn("Rhino MCP direct-router config", preflight)

    def test_vp_studio_contract_enforces_pipeline_and_agentic_dml(self):
        contract = (REPO_ROOT / "demos" / "virtual_production_studio" / "AGENTS.md").read_text()
        self.assertIn("Rhino 8", contract)
        self.assertIn("Blender", contract)
        self.assertIn("ComfyUI", contract)
        self.assertIn("mcp_daystrom_dml_query", contract)
        self.assertIn("mcp_cma_augment", contract)
        self.assertIn("mcp_cma_reinforce", contract)
        self.assertIn("asset_manifest.yaml", contract)
        self.assertIn("04_comfyui_stylization_contract.md", contract)
        self.assertIn("05_dml_learning_contract.md", contract)
        self.assertIn("FAILURE_PARTIAL_MUTATION", contract)
        self.assertIn("Do not repeat an unchanged approach", contract)
        self.assertIn("127.0.0.1:10500", contract)
        self.assertIn("Do not edit Hermes MCP configuration", contract)
        self.assertIn("06_mcp_operations_contract.md", contract)

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
        operations = (
            REPO_ROOT / "demos" / "virtual_production_studio" / "prompts" / "06_mcp_operations_contract.md"
        ).read_text()
        self.assertIn("127.0.0.1:10500", operations)
        self.assertIn("127.0.0.1:9876", operations)
        self.assertIn("cancel the pending interactive command", operations)

    def test_vp_dml_contract_learns_successes_and_failures(self):
        contract = (
            REPO_ROOT
            / "demos"
            / "virtual_production_studio"
            / "prompts"
            / "05_dml_learning_contract.md"
        ).read_text()
        self.assertIn("approach_signature", contract)
        self.assertIn("SUCCESS_VALIDATED", contract)
        self.assertIn("FAILURE_VALIDATED", contract)
        self.assertIn("FAILURE_PARTIAL_MUTATION", contract)
        self.assertIn("files >= 1", contract)
        self.assertIn("Two failures with the same approach signature", contract)

        knowledge = REPO_ROOT / "demos" / "virtual_production_studio" / "knowledge" / "dml"
        success = (knowledge / "rhino_massing_success_20260713.md").read_text()
        failure = (knowledge / "rhino_to_blender_obj_failure_20260713.md").read_text()
        self.assertIn("outcome: SUCCESS_VALIDATED", success)
        self.assertIn("outcome: FAILURE_PARTIAL_MUTATION", failure)
        self.assertIn("cumulative vertex offsets", failure)

    def test_vp_uses_original_direct_3dm_handoff(self):
        demo = REPO_ROOT / "demos" / "virtual_production_studio"
        contract = (demo / "AGENTS.md").read_text()
        workflow = (demo / "prompts" / "00_workflow_and_dml.md").read_text()
        importer = (REPO_ROOT / "skills" / "import_with_metadata.py").read_text()
        self.assertIn("system_prompts/07_phase_export_blender.md", contract)
        self.assertIn("IncludeRenderMeshes=true", contract)
        self.assertIn("OBJ and FBX are prohibited", workflow)
        self.assertNotIn("ToFloatArray", importer)
        self.assertNotIn("ToIntArray", importer)
        self.assertIn("unit_scale_to_meters", importer)

    def test_comfyui_contract_uses_verified_blender_asset_handoff(self):
        contract = (
            REPO_ROOT
            / "demos"
            / "virtual_production_studio"
            / "prompts"
            / "04_comfyui_stylization_contract.md"
        ).read_text()
        self.assertIn("blender_import_smoke_test.json", contract)
        self.assertIn("ASSET_<ASSET_KEY>", contract)
        self.assertIn("camera_cinema_body_re1monsen", contract)
        self.assertIn("cables_modular_simon_laisne", contract)
        self.assertIn("object-ID or cryptomatte", contract)
        self.assertIn("ComfyUI stylizes approved Blender renders", contract)

    def test_vp_asset_manifest_excludes_restricted_license_classes(self):
        manifest = (REPO_ROOT / "demos" / "virtual_production_studio" / "assets" / "asset_manifest.yaml").read_text()
        self.assertIn("preferred_licenses: [CC0-1.0, CC-BY-4.0]", manifest)
        self.assertIn("NoAI", manifest)
        self.assertNotIn("license: CC-BY-NC", manifest)
        self.assertNotIn("license: CC-BY-SA", manifest)

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

    def test_windows_installer_is_safe_and_portable(self):
        installer = (REPO_ROOT / "Install-AEC-Demo.ps1").read_text()
        self.assertIn("SupportsShouldProcess = $true", installer)
        self.assertIn("AEC_DEMO_ROOT", installer)
        self.assertIn("PortableBundle", installer)
        self.assertIn("OfflineOnly", installer)
        self.assertIn("Sanitized config examples were not copied", installer)
        self.assertIn("Repair-DaystromRetrievalPolicy", installer)
        self.assertIn("Set Daystrom DML retrieval_policy to always", installer)
        self.assertIn("Get-FileSha256", installer)
        self.assertIn("Assert-PortableManifestAssets", installer)
        self.assertIn("Portable manifest asset checksum mismatch", installer)
        self.assertIn('$mountRoot = "/mnt/$drive"', installer)
        self.assertIn("$wslRepo.Distro, '-u', 'root', '-e', 'bash'", installer)
        self.assertIn("integrations\\daystrom-dml\\source", installer)
        self.assertIn("DML_SOURCE_DIR saved for future sessions", installer)
        self.assertIn("Sync-DaystromProfilePlugin", installer)
        self.assertIn("Repair-DaystromStrictPreflight", installer)
        self.assertIn("Read-Utf8Text", installer)
        self.assertIn("Write-Utf8Text", installer)
        self.assertIn("Ollama model store: $current current, $copied copied", installer)
        self.assertIn("Restore-PortableDaystromStores", installer)
        self.assertIn("Preserved existing Daystrom store", installer)
        self.assertIn("Seed-DemoDmlKnowledge", installer)
        self.assertIn("teapot-01-runtime-store", installer)
        self.assertIn("cliff-house-01-runtime-store", installer)
        self.assertNotIn("C:\\Users\\", installer)

        for relative in (
            "deployment/bac-teapot-profile/Start-BAC_Teapot.ps1",
            "deployment/rtx-pro-profile/Start-RTX-Pro.ps1",
            "deployment/aec-cptx-profile/Start-Hermes-AEC-Rhino-DML.ps1",
        ):
            launcher = (REPO_ROOT / relative).read_text()
            self.assertIn("DML_SOURCE_DIR", launcher)
            self.assertIn("integrations\\daystrom-dml\\source", launcher)

    def test_profiles_require_strict_daystrom_preflight(self):
        for relative in (
            "deployment/rtx-pro-profile/config.example.yaml",
            "deployment/bac-teapot-profile/config.example.yaml",
            "deployment/aec-cptx-profile/config.example.yaml",
        ):
            self.assertIn("preflight_strict: true", (REPO_ROOT / relative).read_text(encoding="utf-8"))

    def test_rtx_preflight_checks_dcn_runtime_hook(self):
        preflight = (REPO_ROOT / "deployment/rtx-pro-profile/Test-RTX-Pro-Preflight.ps1").read_text(encoding="utf-8")
        self.assertIn("Daystrom/DCN runtime hook", preflight)
        self.assertIn("load_memory_provider('daystrom_dml')", preflight)

    def test_portable_bundle_builder_exports_only_tracked_source(self):
        builder = (REPO_ROOT / "New-AEC-PortableBundle.ps1").read_text()
        self.assertIn("git -C $info.Path ls-files", builder)
        self.assertIn("docker', 'save'", builder)
        self.assertIn("huggingface-cache.tar", builder)
        self.assertIn("portable-bundle.json", builder)
        self.assertIn("FAT32", builder)
        self.assertIn("Assert-ModelEndpoint 8000", builder)
        self.assertIn("Assert-ModelEndpoint 8001", builder)
        self.assertIn("/tmp/aec-portable-", builder)
        self.assertIn("Get-WslUncPath", builder)
        self.assertIn("Docker archive copy failed", builder)
        self.assertIn("Hugging Face cache archive copy failed", builder)
        self.assertIn('$mountRoot = "/mnt/$drive"', builder)
        self.assertIn("ReuseExistingAssets", builder)
        self.assertIn("Cannot reuse missing or empty runtime archive", builder)
        self.assertIn("SkipDmlStores", builder)
        self.assertIn("offline\\daystrom\\stores", builder)
        self.assertIn("includes_daystrom_stores", builder)
        self.assertIn("Project DML/CMA state is bundled by default", builder)
        self.assertIn("Close all Hermes demo sessions", builder)

    def test_model_scripts_allow_first_download_then_use_offline_cache(self):
        for name in ("run-vllm-qwen36.sh", "run-vllm-nemotron-vision.sh"):
            script = (REPO_ROOT / "deployment" / "wsl-vllm" / name).read_text()
            self.assertIn("OFFLINE_ENV=()", script)
            self.assertIn("No cached snapshot found; first start requires internet access", script)
            self.assertIn('"${OFFLINE_ENV[@]}"', script)
            self.assertIn('alias="${MODEL_CACHE}/blobs/$(basename "${module}")"', script)
            self.assertIn("Container created from the local Hugging Face cache", script)


if __name__ == "__main__":
    unittest.main()
