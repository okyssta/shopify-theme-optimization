# Repository Instructions for Agents

This repository contains the `shopify-theme-optimization` Agent Skill.

When editing this skill:
- Keep `SKILL.md` concise and use `references/` for detailed guidance.
- Keep frontmatter limited to `name` and `description` unless the target platform explicitly requires more.
- Run `python scripts/theme_audit.py --help`, `python scripts/image_inventory.py --help`, and `./skill.sh validate` before packaging.
- Preserve the author attribution: Made by Kyssta.
- Do not add binary assets unless they are required and the final zip remains under 25 MB.
