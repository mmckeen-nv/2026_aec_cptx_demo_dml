import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "demos" / "virtual_production_studio" / "skills" / "comfyui_vp_stylize.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("comfyui_vp_stylize_test", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_flux_graph_uses_sdxl_result_as_reference_conditioning():
    helper = load_helper()
    graph = helper.flux_workflow(
        "vp_studio/vp_studio_sdxl.png",
        helper.DEFAULT_FLUX_MODEL,
        helper.DEFAULT_FLUX_CLIP,
        helper.DEFAULT_FLUX_VAE,
        960,
        512,
        42,
        20,
        5.0,
        "studio prompt",
    )
    assert graph["106"]["inputs"]["image"] == "vp_studio/vp_studio_sdxl.png"
    assert graph["108"]["inputs"]["pixels"] == ["107", 0]
    assert graph["109"]["inputs"]["latent"] == ["108", 0]
    assert graph["110"]["inputs"]["latent"] == ["108", 0]
    assert graph["116"]["inputs"]["latent_image"] == ["111", 0]
    assert graph["118"]["inputs"]["images"] == ["117", 0]


def test_flux_graph_uses_locked_dimensions_and_models():
    helper = load_helper()
    graph = helper.flux_workflow("image.png", "flux.safetensors", "qwen.safetensors", "vae.safetensors",
                                 960, 512, 7, 20, 5.0)
    assert graph["101"]["inputs"]["unet_name"] == "flux.safetensors"
    assert graph["102"]["inputs"] == {
        "clip_name": "qwen.safetensors", "type": "flux2", "device": "default"
    }
    assert graph["103"]["inputs"]["vae_name"] == "vae.safetensors"
    assert graph["111"]["inputs"]["width"] == 960
    assert graph["111"]["inputs"]["height"] == 512
    assert graph["115"]["inputs"]["steps"] == 20
    prompt = graph["104"]["inputs"]["text"]
    assert "primary modeled subject" in prompt
    assert "curved LED wall" not in prompt


def test_top_level_demo_prompts_require_two_stage_receipts():
    demo = ROOT / "demos" / "virtual_production_studio"
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            demo / "AGENTS.md",
            demo / "skills" / "INDEX.md",
            demo / "system_prompts" / "00_session_startup.md",
            demo / "prompts" / "00_workflow_and_dml.md",
            demo / "prompts" / "04_comfyui_stylization_contract.md",
        )
    )
    assert "COMFY_SDXL_OUTPUT_PASS" in text
    assert "COMFY_FLUX_OUTPUT_PASS" in text
    assert "COMFY_OUTPUT_PASS stage=sdxl+flux" in text
    assert "FLUX.2 Klein" in text
