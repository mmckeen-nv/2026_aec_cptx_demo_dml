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
        self.assertIn("AEC_DEMO_ID = 'vp-studio-01'", launcher)
        self.assertNotIn("-SkipComfyUI", launcher)
        self.assertIn("SDXL depth -> FLUX.2 Klein", launcher)

    def test_rtx_preflight_requires_mcp_and_isolated_dml(self):
        preflight = (REPO_ROOT / "deployment" / "rtx-pro-profile" / "Test-RTX-Pro-Preflight.ps1").read_text()
        for server in ("rhino", "blender", "daystrom_dml", "cma"):
            self.assertIn(server, preflight)
        self.assertIn("ProjectId = 'vp-studio-01'", preflight)
        self.assertIn("vp-studio-01-runtime-store", preflight)
        self.assertIn("cma_mcp_server_vp_studio.cmd", preflight)
        self.assertIn("RHINO_MCP_AUTOSTART_PORT", preflight)
        self.assertIn("Wait-TcpPort $rhinoMcpPort", preflight)
        self.assertIn("Rhino MCP direct-router config", preflight)
        self.assertIn("ProfileName = 'rtx_pro'", preflight)
        self.assertIn("DmlStoreName = 'vp-studio-01-runtime-store'", preflight)
        self.assertIn("RhinoTemplatePath", preflight)
        self.assertIn("ComfyUI SDXL + FLUX.2 model set", preflight)
        self.assertIn("flux-2-klein-base-4b-fp8.safetensors", preflight)
        self.assertIn("qwen_3_4b.safetensors", preflight)
        self.assertIn("flux2-vae.safetensors", preflight)

    def test_vp_studio_uses_datum_template_without_interactive_new(self):
        demo = REPO_ROOT / "demos" / "virtual_production_studio"
        contract = "\n".join(
            (demo / path).read_text()
            for path in (
                "AGENTS.md",
                "system_prompts/00_session_startup.md",
                "prompts/02_rhino_modeling_contract.md",
            )
        )
        launcher = (REPO_ROOT / "deployment" / "rtx-pro-profile" / "Start-RTX-Pro.ps1").read_text()
        generator = (REPO_ROOT / "tools" / "create_vp_studio_template.py").read_text()
        template = (
            REPO_ROOT
            / "demos"
            / "virtual_production_studio"
            / "source"
            / "vp_studio_01_template.3dm"
        )
        self.assertTrue(template.is_file())
        self.assertIn("mcp_rhino_open_doc", contract)
        self.assertIn("invoke `_New`", contract)
        self.assertIn("vp_studio_01_template.3dm", contract)
        self.assertIn("vp_studio_01_template.3dm", launcher)
        self.assertIn("-RhinoTemplatePath $rhinoTemplate", launcher)
        self.assertIn("UnitSystem.Inches", generator)
        self.assertNotIn("AddBrep", generator)
        self.assertNotIn("AddMesh", generator)
        self.assertNotIn("AddExtrusion", generator)

    def test_all_launchers_run_profile_scoped_preflight_without_killing_apps(self):
        launchers = {
            "aec-cptx-profile/Start-Hermes-AEC-Rhino-DML.ps1": ("aec-cptx", "cliff-house-01"),
            "bac-teapot-profile/Start-BAC_Teapot.ps1": ("bac_teapot", "teapot-01"),
            "rtx-pro-profile/Start-RTX-Pro.ps1": ("rtx_pro", "Test-RTX-Pro-Preflight.ps1"),
        }
        deployment = REPO_ROOT / "deployment"
        for relative, required in launchers.items():
            text = (deployment / relative).read_text()
            self.assertIn(required[0], text)
            self.assertIn(required[1], text)
            self.assertIn("preflight", text.lower())
            self.assertNotIn("Stop-Process", text)

    def test_vp_studio_contract_enforces_pipeline_and_agentic_dml(self):
        demo = REPO_ROOT / "demos" / "virtual_production_studio"
        active_files = [demo / "AGENTS.md", demo / "system_prompts" / "00_session_startup.md"]
        active_files.extend(sorted((demo / "prompts").glob("*.md")))
        active_files.extend(sorted((demo / "skills").glob("*.md")))
        contract = "\n".join(path.read_text() for path in active_files)
        self.assertIn("Hermes designs and models the studio in Rhino", contract)
        self.assertIn("Blender", contract)
        self.assertIn("ComfyUI", contract)
        self.assertIn("Automatic active-read", contract)
        self.assertIn("never control or gate", contract)
        self.assertIn("asset_manifest.yaml", contract)
        self.assertIn("04_comfyui_stylization_contract.md", contract)
        self.assertIn("there is no checked-in geometry", contract)
        self.assertIn("No generic tool named `run`", contract)
        self.assertIn("../../skills/import_with_metadata.py", contract)
        self.assertNotIn("build_rhino_massing.py", contract)
        self.assertIn("same visible, phase-driven cadence as the pristine", contract)
        self.assertIn("one coherent manifest-defined assembly", contract)
        self.assertIn("Do not write a whole-studio builder", contract)
        self.assertIn("read only the current numbered phase prompt", contract)

    def test_vp_uses_agent_led_workflow_with_controller_disabled(self):
        plugin = REPO_ROOT / "deployment" / "plugins" / "aec_demo_controller"
        controller = (plugin / "__init__.py").read_text()
        installer = (REPO_ROOT / "Install-AEC-Demo.ps1").read_text()
        config = (REPO_ROOT / "deployment" / "rtx-pro-profile" / "config.example.yaml").read_text()
        self.assertTrue((plugin / "plugin.yaml").is_file())
        self.assertIn('ctx.register_hook("pre_tool_call"', controller)
        self.assertIn('ctx.register_hook("post_tool_call"', controller)
        self.assertIn("Disable-HermesProfilePlugin", installer)
        self.assertNotIn("Sync-AecDemoControllerPlugin", installer)
        self.assertNotIn("aec_demo_controller", config)
        self.assertIn("threshold: 0.5", config)
        self.assertIn("target_ratio: 0.2", config)
        self.assertIn("protect_last_n: 4", config)
        self.assertIn("dml_first: true", config)
        self.assertIn("dml_first_tail_ratio: 0.02", config)
        self.assertIn("Repair-HermesDmlContinuation", installer)
        self.assertIn("Continue from the Daystrom DML checkpoint. First inspect", installer)
        self.assertIn("No user query found in messages", installer)

    def test_installer_syncs_neutral_soul_and_cliff_style_runtime(self):
        installer = (REPO_ROOT / "Install-AEC-Demo.ps1").read_text()
        self.assertIn("Sync-CliffStyleProfileFiles", installer)
        self.assertIn("Repair-CliffStyleProfileRuntime", installer)
        self.assertIn("'${1}0.5'", installer)
        self.assertIn("'${1}0.2'", installer)
        for profile in ("aec-cptx-profile", "bac-teapot-profile", "rtx-pro-profile"):
            soul = (REPO_ROOT / "deployment" / profile / "SOUL.md").read_text()
            self.assertIn("Keep this persona layer neutral", soul)
            self.assertNotIn("one coherent", soul)

        launcher = (
            REPO_ROOT / "deployment" / "aec-cptx-profile" / "Start-Hermes-AEC-Rhino-DML.ps1"
        ).read_text()
        self.assertIn("Set-Location $projectRoot", launcher)
        self.assertNotIn("Set-Location $demoRoot", launcher)

    def test_all_demo_profiles_have_isolated_dml_and_mcp_contracts(self):
        demos = {
            "virtual_production_studio": "project:vp-studio-01",
            "cliff_house": "project:cliff-house-01",
            "teapot": "project:teapot-01",
        }
        for demo, project_id in demos.items():
            demo_root = REPO_ROOT / "demos" / demo
            contract = (demo_root / "AGENTS.md").read_text()
            self.assertIn(project_id, contract)
            self.assertIn("DML", contract)
            if demo != "cliff_house":
                self.assertTrue((demo_root / "system_prompts" / "00_session_startup.md").is_file())
                self.assertTrue((demo_root / "skills" / "INDEX.md").is_file())
                self.assertTrue((demo_root / "skills" / "session_state.md").is_file())
                self.assertTrue((demo_root / "user_prompts" / "project_prompt.md").is_file())
        operations = (
            REPO_ROOT / "demos" / "virtual_production_studio" / "prompts" / "06_mcp_operations_contract.md"
        ).read_text()
        self.assertIn("127.0.0.1:10500", operations)
        self.assertIn("127.0.0.1:9876", operations)
        self.assertIn("Never call `mcp_rhino_run_command`", operations)
        self.assertIn("mcp_rhino_get_viewport_image", operations)
        self.assertIn("Hermes routes that fresh image", operations)
        self.assertIn("CaptureToBitmap", operations)
        self.assertIn("never by opening", operations)
        self.assertIn("capped at 1,200 characters", operations)
        self.assertIn("Ask for concrete current-phase defects", operations)

    def test_teapot_reference_builder_enforces_visual_acceptance_geometry(self):
        builder = (REPO_ROOT / "demos" / "teapot" / "build_teapot_demo.py").read_text()
        self.assertIn("forward_axis='NEGATIVE_Y', up_axis='Z'", builder)
        self.assertIn("teapot.location.z -= min_z", builder)
        self.assertIn("point_at(cam", builder)
        self.assertIn("TeapotKey", builder)
        self.assertIn("BLENDER_EEVEE", builder)
        self.assertIn("resolve_demo_path", builder)

    def test_vp_dml_contract_learns_successes_and_failures(self):
        contract = (
            REPO_ROOT
            / "demos"
            / "virtual_production_studio"
            / "prompts"
            / "05_dml_learning_contract.md"
        ).read_text()
        self.assertIn("does not control the modeling loop", contract)
        self.assertIn("automatic active-read", contract)
        self.assertIn("Never require stats, query, augmentation, ingestion, or reinforcement", contract)
        self.assertIn("objective evidence and artifact paths", contract)
        self.assertIn("Failures remain retrieval knowledge", contract)

        knowledge = REPO_ROOT / "demos" / "virtual_production_studio" / "knowledge" / "dml"
        success = (knowledge / "rhino_massing_success_20260713.md").read_text()
        failure = (knowledge / "rhino_to_blender_obj_failure_20260713.md").read_text()
        self.assertIn("outcome: SUCCESS_VALIDATED", success)
        self.assertIn("outcome: FAILURE_PARTIAL_MUTATION", failure)
        self.assertIn("cumulative vertex offsets", failure)

    def test_vp_uses_original_direct_3dm_handoff(self):
        demo = REPO_ROOT / "demos" / "virtual_production_studio"
        workflow = (demo / "prompts" / "00_workflow_and_dml.md").read_text()
        importer = (REPO_ROOT / "skills" / "import_with_metadata.py").read_text()
        self.assertIn("OBJ and FBX are prohibited", workflow)
        handoff = (demo / "prompts" / "07_phase_export_blender.md").read_text()
        self.assertIn("direct metadata-preserving `.3dm` handoff", workflow)
        self.assertIn("mcp_blender_execute_blender_code", handoff)
        self.assertIn("No tool named `run` exists", handoff)
        self.assertIn("../../skills/import_with_metadata.py", handoff)
        self.assertIn("never use", handoff.lower())
        self.assertIn("only `parts[0]`", handoff)
        self.assertNotIn("ToFloatArray", importer)
        self.assertNotIn("ToIntArray", importer)
        self.assertIn("unit_scale_to_meters", importer)

        validator = (REPO_ROOT / "skills" / "validate_blender_scene.py").read_text()
        detector = (REPO_ROOT / "skills" / "coplanar_detector.py").read_text()
        self.assertIn("require_material_slots=False", validator)
        self.assertIn("objects_missing_material_metadata", validator)
        self.assertIn("opposed_contact", detector)
        self.assertIn("same_facing", detector)

    def test_comfyui_contract_uses_verified_blender_asset_handoff(self):
        contract = (
            REPO_ROOT
            / "demos"
            / "virtual_production_studio"
            / "prompts"
            / "04_comfyui_stylization_contract.md"
        ).read_text()
        self.assertIn("approved Blender render", contract)
        self.assertIn("COMFY_PREFLIGHT_PASS", contract)
        self.assertIn("seed `42`, denoise `0.28`", contract)
        self.assertIn("geometry-preservation", contract)
        self.assertIn("skills/comfyui_vp_stylize.py", contract)
        self.assertIn("skills/COMFYUI_COOKBOOK.md", contract)
        self.assertIn("COMFY_SOURCE_FAIL", contract)
        self.assertIn("user_prompts/comfy_style_prompt.txt", contract)

        skill = (
            REPO_ROOT
            / "demos"
            / "virtual_production_studio"
            / "skills"
            / "comfyui"
            / "comfyui-cookbook"
            / "SKILL.md"
        ).read_text()
        installer = (REPO_ROOT / "Install-AEC-Demo.ps1").read_text()
        self.assertIn("name: comfyui-cookbook", skill)
        self.assertIn("python skills/comfyui_vp_stylize.py --dry-run", skill)
        self.assertIn("COMFY_OUTPUT_PASS", skill)
        self.assertIn("user_prompts/comfy_style_prompt.txt", skill)
        self.assertIn("skills\\comfyui\\comfyui-cookbook", installer)

        helper = (
            REPO_ROOT
            / "demos"
            / "virtual_production_studio"
            / "skills"
            / "comfyui_vp_stylize.py"
        ).read_text()
        self.assertIn("def source_quality", helper)
        self.assertIn("foreground_fraction < 0.03", helper)
        self.assertIn('"--prompt-file"', helper)
        self.assertIn('"--prompt"', helper)
        self.assertIn("prompt_sha256", helper)
        prompt_file = (
            REPO_ROOT
            / "demos"
            / "virtual_production_studio"
            / "user_prompts"
            / "comfy_style_prompt.txt"
        )
        self.assertTrue(prompt_file.is_file())
        self.assertGreater(len(prompt_file.read_text().strip()), 40)

    def test_vp_stage_dressing_is_locked_into_rhino_and_blender_phases(self):
        demo = REPO_ROOT / "demos" / "virtual_production_studio"
        manifest = (demo / "prompts" / "01a_locked_scene_manifest.md").read_text()
        rhino_phase = (demo / "prompts" / "02d_phase_rigging_cameras.md").read_text()
        blender_phase = (demo / "prompts" / "07_phase_export_blender.md").read_text()
        for name in (
            "STAGE_DIRECTOR_CHAIR_01",
            "HERO_ROAD_CASE_01",
            "FLOOR_LIGHT_01",
            "SERVER_RACK_01",
        ):
            self.assertIn(name, manifest)
            self.assertIn(name, rhino_phase)
        self.assertIn("apply_required_set_dressing(root)", blender_phase)
        self.assertIn("VP_SET_DRESSING_PASS categories=6 placements=27", blender_phase)
        self.assertIn("bare C-stand is prohibited", blender_phase)

    def test_vp_asset_manifest_excludes_restricted_license_classes(self):
        manifest = (REPO_ROOT / "demos" / "virtual_production_studio" / "assets" / "asset_manifest.yaml").read_text()
        self.assertIn("preferred_licenses: [CC0-1.0, CC-BY-4.0]", manifest)
        self.assertIn("NoAI", manifest)
        self.assertNotIn("license: CC-BY-NC", manifest)
        self.assertNotIn("license: CC-BY-SA", manifest)

    def test_vllm_launcher_repairs_network_and_waits_noninteractively(self):
        launcher = (REPO_ROOT / "deployment" / "wsl-vllm" / "start_vllm.bat").read_text()
        self.assertIn("docker network connect bridge", launcher)
        self.assertIn("docker update --restart no", launcher)
        self.assertIn("call :start_model vllm-qwen36 8000 chat", launcher)
        self.assertIn("call :start_model vllm-nemotron-vision 8001 vision", launcher)
        self.assertLess(
            launcher.index("call :start_model vllm-qwen36 8000 chat"),
            launcher.index("call :start_model vllm-nemotron-vision 8001 vision"),
        )
        self.assertIn("exited while loading", launcher)
        self.assertIn("--no-pause", launcher)
        self.assertIn("ping.exe -n 6", launcher)
        self.assertNotIn("timeout /t 5", launcher)

        for script_name in ("run-vllm-qwen36.sh", "run-vllm-nemotron-vision.sh"):
            model_script = (REPO_ROOT / "deployment" / "wsl-vllm" / script_name).read_text()
            self.assertIn("--restart no", model_script)
            self.assertIn('docker update --restart no "$NAME"', model_script)

    def test_bac_launcher_starts_vllm_when_endpoints_are_down(self):
        launcher = (REPO_ROOT / "deployment" / "bac-teapot-profile" / "Start-BAC_Teapot.ps1").read_text()
        self.assertIn("Test-LocalModel 8000", launcher)
        self.assertIn("start_vllm.bat", launcher)
        self.assertIn("--no-pause", launcher)

    def test_windows_installer_is_safe_and_portable(self):
        installer = (REPO_ROOT / "Install-AEC-Demo.ps1").read_text()
        rtx_preflight = (REPO_ROOT / "deployment" / "rtx-pro-profile" / "Test-RTX-Pro-Preflight.ps1").read_text()
        self.assertIn("SupportsShouldProcess = $true", installer)
        self.assertIn("AEC_DEMO_ROOT", installer)
        self.assertIn("PortableBundle", installer)
        self.assertIn("OfflineOnly", installer)
        self.assertIn("Sanitized config examples were not copied", installer)
        self.assertIn("Repair-DaystromRetrievalPolicy", installer)
        self.assertIn("Repair-DemoApplicationMcps", installer)
        self.assertIn("Repair demo-specific Blender/Rhino MCP registrations", installer)
        self.assertIn("BLENDER_PORT", installer)
        self.assertIn("DISABLE_TELEMETRY", installer)
        self.assertIn("Blender MCP environment values are strings", rtx_preflight)
        self.assertIn("Demo background review forks disabled", rtx_preflight)
        self.assertIn("Stale OBS MCP absent", rtx_preflight)
        self.assertIn("Disable background review forks and stale OBS MCP for RTX Pro", installer)
        self.assertIn("Set Daystrom DML retrieval_policy to always", installer)
        self.assertIn("Get-FileSha256", installer)
        self.assertIn("Assert-PortableManifestAssets", installer)
        self.assertIn("Portable manifest asset checksum mismatch", installer)
        self.assertIn('$mountRoot = "/mnt/$drive"', installer)
        self.assertIn("$provisionArgs = @('-d', $wslRepo.Distro, '-u', 'root', '-e')", installer)
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
        self.assertIn("--tenant-id aec-cptx", installer)
        self.assertIn("--project-id $ProjectId", installer)
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

    def test_one_click_windows_bootstrap_owns_wsl_and_reboot_boundary(self):
        bootstrap = (REPO_ROOT / "Bootstrap-AEC-Windows.ps1").read_text(encoding="utf-8")
        launcher = (REPO_ROOT / "Setup-AEC-Demo.cmd").read_text(encoding="utf-8")
        offline = (REPO_ROOT / "Setup-AEC-Demo-Offline.cmd").read_text(encoding="utf-8")
        installer = (REPO_ROOT / "Install-AEC-Demo.ps1").read_text(encoding="utf-8")

        self.assertIn("Bootstrap-AEC-Windows.ps1", launcher)
        self.assertIn("-OfflineOnly", offline)
        for token in (
            "Start-Process powershell.exe -Verb RunAs",
            "Microsoft-Windows-Subsystem-Linux",
            "VirtualMachinePlatform",
            "AEC-CPTX-Setup-Resume",
            "Request-Reboot",
            "--set-default-version",
            "--install', '--distribution'",
            "--set-version",
            "nvidia-smi --query-gpu=index,name,memory.total",
            "requires two visible NVIDIA GPUs",
            "Docker/NVIDIA Container Toolkit",
            "Install-AEC-Demo.ps1",
            "-ProvisionVllm",
            "-StartVllm",
            "ProgramData",
        ):
            self.assertIn(token, bootstrap)
        self.assertIn("shutdown.exe /r /t 30", bootstrap)
        self.assertIn("-NoRestart", bootstrap)
        self.assertIn("$provisionArgs = @('-d', $wslRepo.Distro, '-u', 'root', '-e')", installer)
        self.assertIn("AEC_SKIP_VLLM_PULL=1", installer)
        self.assertLess(
            installer.index("Provision WSL2 Docker and NVIDIA Container Toolkit"),
            installer.index("Restore available portable runtime assets"),
        )

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

    def test_dml_seed_knowledge_is_profile_retrievable(self):
        seed = (REPO_ROOT / "scripts/seed_demo_dml.py").read_text(encoding="utf-8")
        for required in ("tenant_id", "client_id", "project_id", '"kind": "note"', '"no_merge": True'):
            self.assertIn(required, seed)

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
        self.assertIn("Removed retired bundle file", builder)
        self.assertIn("Cannot reuse missing or empty runtime archive", builder)
        self.assertIn("SkipDmlStores", builder)
        self.assertIn("offline\\daystrom\\stores", builder)
        self.assertIn("includes_daystrom_stores", builder)
        self.assertIn("cliff-house-hero-runtime-store", builder)
        self.assertIn("cma-cliff-house-hero-01", builder)
        self.assertIn("includes_vp_asset_cache", builder)
        self.assertIn(".sketchfab_cookies", builder)
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
