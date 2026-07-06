# DML PolicyRouter Config Key Mismatch — FIXED June 30 2026

Originally discovered 2026-06-29. Confirmed by direct Python probe. **Patched in-place 2026-06-30.**

## The bug

`dml_adapter.py` (in `dml_core/daystrom_dml/`) reads config keys with dot-notation:

```python
# Line 222
self.agentic_mode_enabled = bool(self.config.get("dml.agentic_mode.enabled", False))

# Line 226
router_enabled = bool(self.config.get("dml.router.enabled", False))
```

But `self.config` is built from `self.settings.as_dict()` which calls Pydantic's `model_dump()`. The YAML config has nested structure:

```yaml
agentic_mode:
  enabled: true
  schema_validation: true
  promotion_pipeline: true
  scratch_to_durable_threshold: 0.7
```

`model_dump()` produces a nested dict:
```python
{"agentic_mode": {"enabled": True, ...}}
```

There is NO flat key `"dml.agentic_mode.enabled"` in the dict. `dict.get("dml.agentic_mode.enabled", False)` always returns `False`.

## Proof (ran in DML venv)

```python
from dml_core.daystrom_dml.config import load_config
settings = load_config('aec-cptx-portable.yaml')
cfg = settings.as_dict()

cfg.get("dml.agentic_mode.enabled", False)  # → False (BUG)
cfg.get("dml.router.enabled", False)         # → False (BUG)
cfg["agentic_mode"]["enabled"]               # → True  (correct)
```

## Impact

1. `self.agentic_mode_enabled` is always `False`
2. `self.agentic_router` is always `None`
3. The `PolicyRouter` (policy_router.py) never runs
4. The `PromotionPipeline` is never initialized (line 239)
5. All retrieve_context calls skip the router branch (line 1793)

The PolicyRouter implements iteration-flexible budgets:
- 4 task profiles: devops (budget 400), coding (500), research (600), chat (300)
- 5 phase modifiers: plan (top_k 12), build, execute, debug (top_k 4), reflect
- State adaptations: token_pressure >0.8 reduces budget by 20%, stuckness raises similarity threshold
- This entire system is dead code.

The static `_apply_token_budgets()` at line 2809 still runs with the FIXED token_budget=800 from config, applying 70/20/10 semantic/literal/free splits. But no per-iteration adaptation occurs.

## Fix applied (June 30 2026)

Option A was implemented directly in `dml_adapter.py`. Three changes:

### Change 1: agentic_mode_enabled (line 222)

```python
# BEFORE (broken):
self.agentic_mode_enabled = bool(self.config.get("dml.agentic_mode.enabled", False))

# AFTER (fixed):
_agentic_cfg = self.config.get("agentic_mode", {})
if isinstance(_agentic_cfg, dict):
    self.agentic_mode_enabled = bool(_agentic_cfg.get("enabled", False))
else:
    self.agentic_mode_enabled = bool(self.config.get("dml.agentic_mode.enabled", False))
```

### Change 2: router config (lines 226-228)

```python
# BEFORE (broken):
router_enabled = bool(self.config.get("dml.router.enabled", False))
router_profile = self.config.get("dml.router.profile")
router_log = self.config.get("dml.router.log_level", "info")

# AFTER (fixed — defaults router_enabled=True when agentic_mode is on):
_router_cfg = self.config.get("router", {})
if not isinstance(_router_cfg, dict):
    _router_cfg = {}
router_enabled = bool(_router_cfg.get("enabled", True))
router_profile = _router_cfg.get("profile")
router_log = _router_cfg.get("log_level", "info")
```

No separate `router:` YAML section needed — defaults to enabled when agentic_mode is active.

### Change 3: commitment_threshold (line 249)

```python
# BEFORE (broken — "dml." prefix doesn't exist as a flat key):
commitment_threshold=float(self.config.get("dml.commitment_threshold", 0.75)),

# AFTER (fixed):
commitment_threshold=float(self.config.get("commitment_threshold", 0.75)),
```

### Verification (ran against live store)

```
DMLAdapter initialized with:
  agentic_mode_enabled: True
  PolicyRouter: initialized, enabled=True
  PromotionPipeline: initialized
  Ollama backend: llama3:8b connected
  Embedder: qwen3-embedding:0.6b on CUDA
  DML health: status=ok, 94 records, latency 27ms
```

## Fix options (historical — Option A was chosen)

### Option A: Fix config access (minimal, correct)

```python
# Line 222 — change from:
self.agentic_mode_enabled = bool(self.config.get("dml.agentic_mode.enabled", False))
# to:
_am = self.config.get("agentic_mode") or {}
self.agentic_mode_enabled = bool(_am.get("enabled", False) if isinstance(_am, dict) else False)

# Line 226 — same pattern for router:
# But note: there is no "router" section in aec-cptx-portable.yaml at all.
# Adding it would also be needed:
```

### Option B: Add dot-notation flattening to as_dict()

Add a helper that flattens `{"agentic_mode": {"enabled": True}}` to `{"dml.agentic_mode.enabled": True, ...}` after `model_dump()`.

### Option C: Add flat keys to YAML (ugly, fragile)

Add explicit `dml.agentic_mode.enabled: true` and `dml.router.enabled: true` as top-level flat keys in the YAML. Works because `DMLSettings` has `extra="allow"`. But defeats the purpose of nested structure.

## Related: router section missing from config

Even after fixing the config access, the router itself checks `dml.router.enabled` which has no corresponding YAML section. To fully activate the PolicyRouter:

1. Fix the nested dict access in dml_adapter.py
2. Add a `router:` section to aec-cptx-portable.yaml:
```yaml
router:
  enabled: true
  profile: null   # auto-detect from task type
  log_level: info
```

## Files involved

- `source/dml_core/daystrom_dml/dml_adapter.py` — lines 222, 226-228
- `source/dml_core/daystrom_dml/policy_router.py` — PolicyRouter class
- `source/dml_core/daystrom_dml/settings.py` — DMLSettings (extra="allow")
- `source/dml_core/daystrom_dml/config.py` — load_config, _validate_settings
- `config/aec-cptx-portable.yaml` — runtime config
