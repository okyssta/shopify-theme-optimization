# Audit Report Template

Use this format for Shopify theme audits or optimization completion reports.

## Executive summary

State the main bottlenecks, safest wins, and whether actual performance metrics were measured or inferred from code inspection.

## Baseline

| Source | Page/template | Metric or signal | Value | Notes |
|---|---|---:|---:|---|
| Lighthouse/PageSpeed/trace/theme audit | home/product/collection/cart | LCP/CLS/INP/requests/asset weight | value | limitations |

If metrics are unavailable, say: "No live performance trace was available; findings are based on static theme inspection."

## Priority fixes

| Priority | Issue | Metric affected | Files | Recommended action | Conversion risk | Expected impact |
|---:|---|---|---|---|---|---|
| 1 | Example: hero image lazy loaded | LCP | `sections/image-banner.liquid` | eager load/preload first section image | Low | High |

## Proposed or implemented changes

Group by category:
- Images and LCP
- JavaScript and INP/TBT
- CSS and render blocking
- Liquid/render time
- Third-party apps/scripts
- CLS and visual stability
- Fonts

For each change include:
- What changed
- Why it helps
- What was deliberately preserved
- How to roll back

## Verification

| Check | Command/source | Result |
|---|---|---|
| Static audit | `python scripts/theme_audit.py ...` | pass/fail/notes |
| Theme lint | `shopify theme check` | pass/fail/not available |
| Lighthouse | report URL or command | before/after |
| Manual QA | mobile product page add-to-cart, variant switch, cart drawer, checkout link | pass/fail |

## Approval-needed items

List any performance opportunities that require owner approval, such as removing apps, changing popups, delaying analytics, disabling chat widgets, or altering above-the-fold layout.
