"""Apply the AEC consumed-visual history compaction patch to Hermes."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


HELPER = r'''

_VISUAL_TOOL_NAME_MARKERS = (
    "get_viewport_image",
    "get_screenshot",
    "take_screenshot",
    "capture_viewport",
    "capture_image",
)
_ENCODED_IMAGE_MARKERS = (
    "data:image/",
    '"mimeType":"image/',
    '"mime_type":"image/',
    '"type":"image"',
)


def compact_consumed_visual_tool_results(
    messages: list,
    *,
    min_payload_chars: int = 16_000,
) -> int:
    """Replace already-consumed encoded visual tool results with receipts."""
    compacted = 0
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "tool":
            continue
        content = msg.get("content")
        if not isinstance(content, str) or len(content) < min_payload_chars:
            continue
        tool_name = str(msg.get("name") or "").lower()
        prefix = content[:4096].lower()
        is_visual_tool = any(marker in tool_name for marker in _VISUAL_TOOL_NAME_MARKERS)
        has_encoded_image = any(marker.lower() in prefix for marker in _ENCODED_IMAGE_MARKERS)
        if not (is_visual_tool or has_encoded_image):
            continue
        original_chars = len(content)
        msg["content"] = (
            "[visual payload consumed and removed from replay history] "
            f"tool={tool_name or 'unknown'} original_chars={original_chars}. "
            "Use the assistant response immediately following the original "
            "tool result as the retained visual interpretation."
        )
        compacted += 1
    return compacted
'''

HOOK = r'''

            # The response above has consumed all existing tool results.
            # Remove giant serialized viewport/screenshot payloads now so
            # they are not replayed on every later API call.
            _visual_results_compacted = compact_consumed_visual_tool_results(messages)
            if _visual_results_compacted:
                logger.info(
                    "%sCompacted %d consumed visual tool payload(s) from replay history",
                    agent.log_prefix,
                    _visual_results_compacted,
                )
'''


def _backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = path.with_name(f"{path.name}.bak-aec-visual-history-{stamp}")
    shutil.copy2(path, backup)
    return backup


def patch(hermes_root: Path) -> list[str]:
    agent_dir = hermes_root / "agent"
    sanitization = agent_dir / "message_sanitization.py"
    loop = agent_dir / "conversation_loop.py"
    for path in (sanitization, loop):
        if not path.is_file():
            raise FileNotFoundError(f"Hermes source file not found: {path}")

    changed: list[str] = []
    text = sanitization.read_text(encoding="utf-8")
    updated = text
    if "def compact_consumed_visual_tool_results(" not in updated:
        anchor = "\ndef _sanitize_structure_non_ascii("
        if anchor not in updated:
            raise RuntimeError("Unrecognized Hermes message_sanitization.py layout")
        updated = updated.replace(anchor, HELPER + anchor, 1)
    export_anchor = '    "_strip_images_from_messages",\n'
    if '"compact_consumed_visual_tool_results"' not in updated:
        if export_anchor not in updated:
            raise RuntimeError("Hermes message_sanitization.py export anchor missing")
        updated = updated.replace(
            export_anchor,
            export_anchor + '    "compact_consumed_visual_tool_results",\n',
            1,
        )
    if updated != text:
        _backup(sanitization)
        sanitization.write_text(updated, encoding="utf-8", newline="\n")
        changed.append(str(sanitization))

    text = loop.read_text(encoding="utf-8")
    updated = text
    import_anchor = "from agent.message_sanitization import (\n"
    if "    compact_consumed_visual_tool_results,\n" not in updated:
        if import_anchor not in updated:
            raise RuntimeError("Hermes conversation_loop.py import anchor missing")
        updated = updated.replace(
            import_anchor,
            import_anchor + "    compact_consumed_visual_tool_results,\n",
            1,
        )
    if "Compacted %d consumed visual tool payload(s)" not in updated:
        hook_anchor = (
            "                else:\n"
            "                    assistant_message.content = str(raw)\n"
            "\n"
            "            try:\n"
            "                from hermes_cli.plugins import (\n"
        )
        if hook_anchor not in updated:
            raise RuntimeError("Hermes conversation_loop.py response hook anchor missing")
        replacement = hook_anchor.replace(
            "\n            try:\n",
            HOOK + "\n            try:\n",
            1,
        )
        updated = updated.replace(hook_anchor, replacement, 1)
    if updated != text:
        _backup(loop)
        loop.write_text(updated, encoding="utf-8", newline="\n")
        changed.append(str(loop))

    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes-agent-root", required=True, type=Path)
    args = parser.parse_args()
    changed = patch(args.hermes_agent_root.resolve())
    if changed:
        print("HERMES_VISUAL_HISTORY_PATCH_PASS changed=" + ",".join(changed))
    else:
        print("HERMES_VISUAL_HISTORY_PATCH_PASS current=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
