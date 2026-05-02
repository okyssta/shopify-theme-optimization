---
name: shopify-theme-optimization
description: optimize shopify themes for speed, core web vitals, liquid efficiency, asset loading, javascript/css weight, image delivery, third-party scripts, and conversion-safe storefront performance. use when auditing or modifying shopify theme repositories, theme zip files, liquid templates, sections, snippets, assets, app embeds, lighthouse/page speed issues, lcp/cls/inp problems, slow product/collection/home pages, or requests to make a shopify store faster without changing its visual ui, overlays, merchandising, checkout path, tracking, or conversion behavior unless explicitly approved. trigger on shortcuts such as $shopify-theme-optimization, $shopifyoptimize, /shopifyoptimize, /shopify-optimize, /optimize shopify, shopifyoptimize, shopifyoptimze, shopfityoptimze, and shopify performance audit/fix/diagnose/verify requests.
---

# Shopify Theme Optimization

Made by Kyssta.

## Operating principle

Optimize performance without damaging the storefront's conversion system. Treat layout, merchandising hierarchy, app-driven UI, overlays, cart/checkout flows, tracking, accessibility, and brand presentation as protected unless the user explicitly asks to change them.

## Shortcut commands

Treat these as explicit invocations of this skill:
- `$shopify-theme-optimization [mode] [target]`
- `$shopifyoptimize [mode] [target]`
- `/shopifyoptimize [mode] [target]`
- `/shopify-optimize [mode] [target]`
- `/optimize shopify [mode] [target]`
- `shopifyoptimize [mode] [target]`
- `shopifyoptimze [mode] [target]`
- `shopfityoptimze [mode] [target]`

Modes:
- `audit`: inspect a theme directory, theme zip, repo, URL, or report; produce prioritized findings without editing.
- `diagnose` or `diagnosis`: explain root causes for known Lighthouse/PageSpeed/Core Web Vitals issues and map them to theme files when possible.
- `fix`: implement safe, conversion-preserving patches. Run an audit first if no current baseline exists.
- `verify`: rerun audits/checks, compare before/after evidence, and list remaining risks.
- `report`: format findings and completed work using `references/audit-report-template.md`.
- `inventory`: run image/asset inventory and identify oversized or poorly loaded assets.

If mode is missing, default to `audit`. If target is missing, inspect the current repository when it looks like a Shopify theme; otherwise ask for a theme path, zip, URL, or report.

## Default workflow

1. Identify the input:
   - Theme directory, theme zip, Git repo, or individual Liquid/asset files: inspect files directly.
   - Store URL or Lighthouse/PageSpeed report: use available reports as baseline and request/derive theme changes only when evidence supports them.
   - No files yet: provide an optimization plan/checklist and ask for a theme zip/repo when implementation is needed.
2. Establish a baseline before edits.
   - Run `python scripts/theme_audit.py <theme-path> --format markdown` when theme files are available.
   - Run `python scripts/image_inventory.py <theme-path>` for image-heavy themes.
   - Use Lighthouse, WebPageTest, PageSpeed Insights, browser performance traces, Shopify Theme Check, and real-device checks when available. Do not invent scores.
3. Prioritize fixes by impact and risk:
   - High impact, low risk first: image sizing, eager vs lazy image loading, `defer` scripts, duplicate assets, obvious unused/duplicate third-party scripts, missing dimensions, render-blocking theme assets.
   - Medium risk next: route-specific JS/CSS loading, section-specific script splitting, font strategy, app embed gating, Liquid loop cleanup.
   - High risk only with explicit approval: removing apps, changing popups/overlays, changing checkout/cart UX, deleting tracking pixels, replacing major libraries, altering merchandising layout.
4. Implement minimal patches.
   - Preserve visual output and interaction behavior.
   - Prefer native browser and Shopify primitives over adding libraries.
   - Avoid broad rewrites when targeted fixes solve the measured bottleneck.
5. Verify and report.
   - Summarize changes, expected metric impact, files changed, tests run, and any risks/rollback notes.
   - If actual metrics cannot be measured, label the result as a code-level optimization rather than a proven score improvement.

## References to load when needed

- Performance strategies and prioritization: `references/performance-playbook.md`.
- Shopify Liquid and asset patterns/snippets: `references/shopify-patterns.md`.
- Conversion, UX, analytics, and app safety rules: `references/conversion-safety.md`.
- Known issue library: `references/common-issues.md`.
- Report format: `references/audit-report-template.md`.

## Bundled scripts

Use scripts when files are available and deterministic inspection helps.

```bash
python scripts/theme_audit.py /path/to/theme --format markdown
python scripts/theme_audit.py /path/to/theme.zip --format json --out audit.json
python scripts/image_inventory.py /path/to/theme --format markdown
python scripts/minify_assets.py /path/to/theme          # dry run
python scripts/minify_assets.py /path/to/theme --write  # creates .bak files by default
```

Script rules:
- Treat audit findings as leads, not automatic truth. Confirm context before editing.
- Keep `minify_assets.py` on dry run unless the user asks to write changes or you are already editing the theme.
- Never minify `.liquid` assets with generic minifiers. The script intentionally skips Liquid files.

## Safe optimization checklist

Before finalizing, check that:
- Above-the-fold/LCP images are not lazy loaded and have explicit dimensions or aspect-ratio allocation.
- Below-the-fold images use native lazy loading and responsive `image_url`/`image_tag` patterns where possible.
- Parser-blocking theme scripts are deferred, async, module-based, or loaded on interaction when safe.
- CSS/JS changes do not remove required functionality for variant selection, add-to-cart, cart drawer, subscriptions, reviews, search, personalization, consent, or analytics.
- Third-party scripts are inventoried before removal. Disable/remove only with evidence and user approval.
- CLS risks are handled by reserving space for images, banners, app blocks, announcement bars, dynamic reviews, and fonts.
- Liquid loops do not repeatedly perform expensive operations or render heavyweight snippets unnecessarily.
- The store still feels fast, trustworthy, and purchasable on mobile.

## Default output

Use this structure for audits and completed work:

1. Executive summary: biggest bottlenecks and safest wins.
2. Priority fixes: table with severity, metric affected, files, action, risk, and expected impact.
3. Implemented changes or proposed patch plan.
4. Verification: commands/tests run, measured results if available, and remaining unknowns.
5. Conversion safety notes: what was deliberately preserved and any approval-needed items.
