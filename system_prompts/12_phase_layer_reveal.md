# Phase — Layer Reveal Animation
### Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Version 1.0 — May 2026*
*Tool chain: Rhino 3D + RhinoMCP (C# scripting)*

---

## Purpose

Progressively reveal the design in Rhino by turning on layers one at a time,
with a user-specified pause between each step. The sequence runs live in the
Rhino viewport and is captured as part of the demo footage.

---

## Pre-Phase

Ask the user:
1. **Pause duration** between each step (e.g. 1s, 2s, 3s)
2. **Reveal order** — default is bottom-up (ground floor first); confirm or adjust

Then audit the live layer tree fresh — never rely on cached indices.

---

## Execution

See skill: `rhino-layer-reveal-sequence`

---

## Post-Phase Checklist

- [ ] Sequence plays through without errors
- [ ] Each step holds for the specified pause duration
- [ ] Final state shows the complete design
- [ ] Sequence re-runs cleanly on "run it again"

---

## ▶ REVIEW GATE

Run the sequence end-to-end. Confirm timing feels right and reveal order
tells the design story clearly. Adjust pause duration or grouping as needed.

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."
