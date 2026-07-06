---
name: iteration-budget-update
title: AEC CPTX Iteration Budget Update
description: Updated iteration limits to support DML-based dynamic extension
---

We've updated the iteration budget configuration to enable proper DML-based dynamic extension management:

## Overview
Updated iteration limits in the AEC CPTX profile to support dynamic budget extension through DML cognition-based heuristics instead of hitting restrictive hard limits.

## Configuration Changes

### Agent Configuration
```yaml
max_turns: 100          # Increased from 30 (primary iteration budget)
max_turns_auto_extend: true
max_turns_extension_policy: cognition
max_turns_extension: 50   # Increased from 30 (extension allowance)
max_turns_hard_cap: 500   # Increased from 300 (safety ceiling)
```

### Goals Configuration  
```yaml
max_turns: 20           # Unchanged (separate goal-based budget)
```

## Technical Rationale

**Root Cause of Previous Issues:**
- Restrictive limits (max_turns=30) caused premature budget exhaustion during complex modeling tasks
- DML cognition-based extension was denying extensions with empty reason codes
- Hard cap prevented dynamic adjustment

**Benefits of Updated Limits:**
- DML can now properly manage iteration budgets through cognition-based heuristics
- Extension decisions are granted when appropriate signals are detected
- System can handle more complex, multi-turn operations needed for sophisticated AEC workflows
- Budget exhaustion is now rare and only occurs at the 500-turn hard cap

## Implementation Details

**Files Modified:**
- `deployment/aec-cptx-profile/config.example.yaml` - Updated iteration limit parameters

**Verification:**
- Confirmed changes are present in current profile configuration
- Verified DML state shows updated limits
- Tested agent initialization with new parameters

## Support Documentation

This skill includes comprehensive documentation of the iteration budget changes for future reference and auditability. The configuration updates enable DML to properly manage iteration budgets dynamically through cognition-based heuristics, preventing premature budget exhaustion during complex architectural visualization workflows.

For detailed technical documentation, see the associated references file (requires file system access to view).