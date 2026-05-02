# Shopify Theme Optimization Skill

A portable Agent Skill for optimizing Shopify themes for speed, Core Web Vitals, asset loading, image delivery, script strategy, Liquid efficiency, and conversion-safe UX.

- Name: `shopify-theme-optimization`
- Author: Kyssta

## What it helps agents do

- Audit Shopify theme folders or theme zip files.
- Identify common performance issues in Liquid, JS, CSS, images, and app/third-party scripts.
- Apply safe fixes without changing the store's visible UI, overlay behavior, cart/checkout flow, analytics, or conversion logic unless explicitly requested.
- Produce clear implementation plans and post-change verification summaries.

## Agent shortcuts

Use any of these in an agent chat after installing the skill:

```text
$shopify-theme-optimization audit ./theme
$shopifyoptimize fix ./theme
/shopifyoptimize audit ./theme
/shopifyoptimize fix ./theme
/shopifyoptimize diagnose ./lighthouse-report.json
/shopifyoptimize verify ./theme
/optimize shopify inventory ./theme.zip
shopifyoptimize report ./theme
```

Typo aliases such as `shopifyoptimze` and `shopfityoptimze` are included so the skill still triggers.

## Install

```bash
npx skills add https://github.com/kyssta-exe/shopify-theme-optimization --skill shopify-theme-optimization -a codex
npx skills add https://github.com/kyssta-exe/shopify-theme-optimization --skill shopify-theme-optimization -a claude-code -a cursor
```

## Bundled tools

```bash
python scripts/theme_audit.py /path/to/theme --format markdown
python scripts/image_inventory.py /path/to/theme --format markdown
python scripts/minify_assets.py /path/to/theme
```
