# Shopify Theme Optimization Skill

A portable Agent Skill for optimizing Shopify themes for speed, Core Web Vitals, asset loading, image delivery, script strategy, Liquid efficiency, and conversion-safe UX.

- Name: `shopify-theme-optimization`
- Author: Kyssta
- Entry point: `SKILL.md`
- Compatible format: OpenAI/ChatGPT/Codex skills, Claude Code skills, and skills.sh-style `SKILL.md` skill directories.

## What it helps agents do

- Audit Shopify theme folders or theme zip files.
- Identify common performance issues in Liquid, JS, CSS, images, and app/third-party scripts.
- Apply safe fixes without changing the store's visible UI, overlay behavior, cart/checkout flow, analytics, or conversion logic unless explicitly requested.
- Produce clear implementation plans and post-change verification summaries.

## Useful commands

```bash
python scripts/theme_audit.py /path/to/theme --format markdown
python scripts/image_inventory.py /path/to/theme --format markdown
python scripts/minify_assets.py /path/to/theme
./skill.sh validate
```

## Install

With the skills.sh CLI:

```bash
npx skills add https://github.com/<owner>/shopify-theme-optimization --skill shopify-theme-optimization -a codex
npx skills add https://github.com/<owner>/shopify-theme-optimization --skill shopify-theme-optimization -a claude-code -a cursor
```

From a local clone:

```bash
./skill.sh install --project --agent codex
./skill.sh install --global --agent claude-code
./skill.sh install --project --agent all
./skill.sh package .
```

For ChatGPT/OpenAI products, upload `skill.zip` where custom skills are supported. For skills.sh, publish this folder in a Git repository; the CLI discovers repositories and directories that contain a valid `SKILL.md`.
