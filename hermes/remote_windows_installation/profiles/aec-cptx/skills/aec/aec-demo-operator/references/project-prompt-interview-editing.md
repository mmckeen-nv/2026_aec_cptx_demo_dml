# Safe editing of project_prompt.md during design interview

## Problem

project_prompt.md contains ~20 identical lines:
```
Your answer:  [FILL IN]
```
A global sed replace corrupts the entire file. There is no git history to restore from.

## Safe single-field update

```bash
# Step 1: Find the line number
grep -n "FILL IN" /path/to/project_prompt.md | head -20

# Step 2: Confirm context around the target line
sed -n '90,96p' /path/to/project_prompt.md

# Step 3: Replace by exact line number only
sed -i '95s/Your answer:  \[FILL IN\]/Your answer:  Coastal bluff/' /path/to/project_prompt.md

# Step 4: Verify
grep -n "Your answer:" /path/to/project_prompt.md | grep -v "FILL IN" | grep -v "Example"
```

## Recovery after accidental global replace

If all [FILL IN] entries were replaced with the same text:

```bash
# Revert all bad entries back to [FILL IN]
python -c "
path = '//wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md'
with open(path, 'r') as f:
    content = f.read()
content = content.replace('Your answer:  BAD_TEXT', 'Your answer:  [FILL IN]')
with open(path, 'w') as f:
    f.write(content)
"
```

Then re-apply each previously filled answer one at a time using line-targeted sed.

Note: python3 is not available on this Windows host; use `python` (3.11.15).

## Section line-number reference (cliff_house_02, as of June 2026)

These are approximate — always verify with grep before editing:

- Section 1 "who is this for": ~line 73
- Section 2 landscape: ~line 95
- Section 2 view direction: ~line 105
- Section 2 ground cover: ~line 116
- Section 2 building pad: ~line 128
- Section 2 retaining walls: ~line 141
- Section 2 patio: ~line 153
- Section 2 driveway: ~line 163

Line numbers shift as content is filled in (answers can be longer than "[FILL IN]"). Always re-grep.
