# Rhino `_New` modal-template failure — validated 2026-07-14

- Project: `project:vp-studio-01`
- Phase: Rhino preflight / site and shell
- Operation: create or replace the active Rhino document
- Approach signature: `rhino-interactive-new-command`
- Validation: `FAILURE_VALIDATED`

## Observed evidence

The agent invoked Rhino's `_New`/new-document command on a workstation without a
configured default Rhino template. Rhino displayed the modal **Open Template
File** window. The MCP `run_command` call blocked for 180 seconds, later
`run_python` calls failed immediately, the agent retried failing calls, and
replacement slot creation failed because the router's Windows Job Object denied
`CreateProcess`. The run consumed 102 API calls and ended without phase progress.

## Root cause

The VP demo lacked an explicit datum-template opening contract. A healthy MCP
router cannot automate through Rhino's interactive template-selection dialog.

## Avoidance rule

Open `source/vp_studio_01_template.3dm` with `mcp_rhino_open_doc`. Never call
`_New`, `_NewSmall`, `New`, close the datum document, spawn a replacement slot,
or use `vp_studio_01_base_model.3dm`. Confirm inches, 0.01-inch tolerance, four
locked `VP00_TEMPLATE_*` layers, reference-only curves/text, and zero design
solids or meshes before modeling.
