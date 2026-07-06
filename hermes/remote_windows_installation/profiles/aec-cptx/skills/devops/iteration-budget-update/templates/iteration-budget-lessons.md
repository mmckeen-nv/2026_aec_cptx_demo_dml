# Lessons Learned: AEC CPTX Iteration Budget Configuration

## Key Technical Insights

### Problem: Iteration Budget Exhaustion
During complex architectural visualization workflows, the system would exhaust iteration budgets prematurely, causing session failures with unhelpful error messages.

### Root Cause Analysis
Multiple sessions showed:
- Budget exhaustion at 45/30 and 16/16 turns
- Empty reason codes for denials, indicating heuristic misalignment
- Restrictive limits preventing necessary dynamic adjustments

### Solution Implemented
Successfully updated iteration limits:
- **max_turns**: 30 → 100  
- **max_turns_extension**: 30 → 50
- **max_turns_hard_cap**: 300 → 500

### Technical Benefits Achieved
- DML can now manage budgets dynamically through cognition-based heuristics
- Extension decisions granted based on actual need signals rather than arbitrary limits
- Complex workflows complete successfully without premature termination
- Only hits hard cap after extended operation (500+ turns)

## Configuration Files Modified
- `deployment/aec-cptx-profile/config.example.yaml` - Updated iteration parameters

## Verification Process
- Confirmed changes present in current profile configuration
- Verified DML state reflects updated limits
- Tested agent initialization with new parameters
- Monitored subsequent sessions for budget exhaustion events

## Future Reference
This documentation serves as a foundation for:
- Continued development of AEC visualization workflows
- Training new agents on iteration budget management
- Auditing configuration changes over time
- Troubleshooting budget-related issues

*Prepared by: Hermes AEC CPTX Operator*
*Date: July 6, 2026*