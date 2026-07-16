from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROFILE_CONFIGS = (
    ROOT / "deployment" / "rtx-pro-profile" / "config.example.yaml",
    ROOT / "deployment" / "bac-teapot-profile" / "config.example.yaml",
    ROOT / "deployment" / "aec-cptx-profile" / "config.example.yaml",
)


def test_demo_profiles_use_bounded_non_reasoning_nemotron_vision():
    for path in PROFILE_CONFIGS:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        vision = config["auxiliary"]["vision"]
        assert "Nemotron-3-Nano-Omni" in vision["model"]
        assert vision["max_tokens"] == 512
        assert vision["temperature"] == 0.2
        assert vision["extra_body"]["top_k"] == 1
        assert vision["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False


def test_demo_profiles_keep_dml_retrieval_compact_and_advisory():
    for path in PROFILE_CONFIGS:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        dml = config["memory"]["daystrom_dml"]
        assert dml["retrieval_policy"] == "always"
        assert dml["top_k"] == 8
        assert dml["max_context_chars"] == 3200
        assert dml["dcn"]["mode"] == "active_read"
