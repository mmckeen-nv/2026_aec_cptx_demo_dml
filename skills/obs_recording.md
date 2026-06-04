# OBS Recording -- Protocol and Verification
# skills/obs_recording.md
# Last updated: May 2026

---

## Architecture

The recording system is a tray app + stage file. Claude does not control OBS directly.

```
Claude                          Tray App (tools/obs_recorder.py)
  |                                 |
  | writes current_stage.json       | reads current_stage.json on every click
  |                                 | -> builds filename NNN-phase_app
  |                                 | -> verifies source is live (sourceHeight > 0)
  |                                 | -> stops current clip if recording
  |                                 | -> switches OBS source
  |                                 | -> starts new clip
  v                                 v
tools/current_stage.json        OBS WebSocket (port 4455)
```

---

## Claude's responsibilities (OBS)

**One action only:** write `tools/current_stage.json` at the start of each phase.

```python
import json
stage = {"project": project_name, "phase": phase_name}
with open(r"{ROOT}\tools\current_stage.json", "w") as f:
    json.dump(stage, f, indent=2)
```

Phase short names (use exactly):
  `site_prep`  `massing`  `detailing`  `export`  `materials`  `lighting`  `camera`  `render`  `session`

When switching applications, announce it in chat:
  -> Rhino:   "Switching to Rhino -- click Record Rhino in the tray when ready."
  -> Blender: "Switching to Blender -- click Record Blender in the tray."
  -> Back:    "Back to Claude -- click Record Claude if you want this captured."

Claude NEVER calls: obs-start-record, obs-stop-record, obs-set-current-scene,
obs-set-scene-item-enabled, or any other OBS recording management tool.

---

## OBS setup (single scene, four sources)

Scene: `Claude-rhino_capture`

| Source name    | sceneItemId | Captures         |
|----------------|-------------|------------------|
| claude_window  | 1           | Claude Desktop   |
| Rhino_window   | 2           | Rhinoceros 3D    |
| blender_window | 3           | Blender          |
| Display Capture| 4           | Full monitor     |

Config file: `tools/obs_recorder_config.json`

---

## Source health check (MANDATORY)

The tray app runs this automatically before every recording. If it fires,
the tray icon turns amber and recording does NOT start.

Condition: `sceneItemTransform.sourceHeight == 0`
Meaning: source is black / window handle lost
Fix: right-click the source in OBS -> Properties -> reselect the application window

This happens after system restarts, application updates, or virtual desktop switches.
It is silent -- OBS shows no error. The tray catches it before any footage is lost.

---

## Filename format

`NNN-phase_app.mp4`

NNN  = sequential number, max existing in capture folder + 1, zero-padded to 3 digits
phase = value from current_stage.json (e.g. site_prep)
app  = rhino | claude | blender | display

Examples:
  001-session_claude.mp4
  002-site_prep_rhino.mp4
  003-site_prep_claude.mp4
  004-massing_rhino.mp4

---

## Output folder

Auto: `aa_demo_versions/[project]/demo_captures/`
Override: set `capture_root` in `tools/obs_recorder_config.json`

---

## Tray app controls

Right-click the tray icon (system tray, bottom-right):
  Record Rhino    -- switches to Rhino source, starts clip
  Record Claude   -- switches to Claude source, starts clip
  Record Blender  -- switches to Blender source, starts clip
  Record Display  -- switches to Display Capture, starts clip
  Stop            -- stops current clip, returns to Claude source
  Open Folder     -- opens current project's demo_captures folder
  Settings...     -- change output resolution, capture folder, preview next filename

Switching source while recording: tray auto-stops the current clip first,
then verifies the new source, then starts a new clip.

---

## Settings dialog

Access: tray -> Settings...

  Current stage:     reads current_stage.json (read-only, written by Claude)
  Output resolution: dropdown, current value pre-selected, applied immediately on Save
  Capture folder:    override path (blank = auto from project)
  Next filename:     live preview of what the next clip will be named

---

## Launch the tray

  tools/launch_obs_recorder.bat

Or manually:
  pythonw.exe tools/obs_recorder.py

---

## Known failure modes

| Symptom                              | Cause                                      | Fix                                           |
|--------------------------------------|--------------------------------------------|-----------------------------------------------|
| Tray icon turns amber, no recording  | videoActive = False, app not open or window handle lost | Open the app first, or OBS -> right-click source -> Properties -> reselect window |
| Wrong project in filename            | current_stage.json not updated             | Claude: write stage file before phase starts  |
| Clip not in expected folder          | capture_root override set in config        | Tray -> Settings -> clear capture folder      |
| OBS MCP drops mid-session            | obs-mcp process exited                     | Auto-restart via obs_mcp_wrapper.ps1 (wired in claude_desktop_config.json) |
| Duplicate NNN prefix                 | Files from a different project in folder   | Move old files out of demo_captures first     |
