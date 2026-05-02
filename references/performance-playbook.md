# Shopify Performance Playbook

## Prioritization model

Rank work by impact, confidence, and conversion risk.

1. Fix LCP first: hero media, first product image, render-blocking CSS/JS, font blocking, server-rendered above-the-fold markup.
2. Fix CLS: missing width/height, dynamic banners, app blocks, review widgets, fonts, media galleries.
3. Fix INP/TBT: large JS bundles, duplicate libraries, heavy third-party scripts, expensive event handlers, synchronous app snippets.
4. Reduce transfer and parsing cost: unused CSS/JS, overlarge theme images, old lazy-loading libraries, polyfills, repeated app assets.
5. Clean Liquid render paths: expensive loops, repeated snippet renders, unnecessary `all_products` lookups, large JSON blobs.

## Images and LCP

Safe wins:
- Use Shopify CDN transformations through `image_url` and render with `image_tag` when possible.
- Use responsive `widths` and `sizes` so mobile does not download desktop-sized media.
- Do not lazy load above-the-fold hero/product images. Use `loading: 'eager'` and optionally `fetchpriority: 'high'` for the one likely LCP image.
- Use `preload: true` sparingly for the single critical image when helpful.
- Set explicit width/height or reserve aspect ratio to prevent CLS.
- Keep below-the-fold and hidden carousel images lazy loaded.
- Avoid JavaScript lazy-loading libraries unless the theme has a specific unsupported browser need.

Review carefully:
- Background images used for hero banners. Convert to real images when possible for responsive sizing, alt text, priority hints, and dimensions.
- Sliders that preload every slide. Only the first visible slide should be eager; later slides should lazy load.
- Product media galleries that load every zoom image on initial page load.

## JavaScript

Safe wins:
- Replace parser-blocking theme asset tags with deferred scripts where execution order permits.
- Keep critical inline bootstrap small; move non-critical code into deferred assets.
- Load code on interaction for modals, size guides, video players, maps, reviews tabs, chat, and other optional features.
- Use event delegation and passive listeners for scroll/touch where possible.
- Remove duplicate libraries and old app leftovers after approval.

Avoid:
- Defering scripts required to render the first visible UI when it causes flashes, broken menus, broken variants, or add-to-cart failures.
- Replacing working app code without confirming the merchant still needs the app.
- Adding large optimization libraries to solve what native browser features already handle.

## CSS and render blocking

Safe wins:
- Remove unused legacy CSS after confirming no template uses it.
- Split route-specific CSS when the theme has large page-only styles.
- Inline only tiny critical CSS when it is stable and maintainable.
- Preload at most the truly critical stylesheet(s); too many preloads compete with images and scripts.
- Avoid `@import` chains in CSS.

Risky:
- Broad CSS purging can remove dynamic classes used by Liquid settings, apps, and JavaScript state. Use safelists and visual QA.

## Fonts

Safe wins:
- Prefer system font stacks when brand allows.
- Use `font-display: swap` or equivalent.
- Limit families, weights, and variants.
- Preload only the main above-the-fold font file if custom fonts are required.
- Reserve line-height and avoid late font swaps that create CLS.

## Liquid and theme rendering

Safe wins:
- Move sorting/filtering outside loops.
- Avoid rendering heavy snippets inside large loops unless the output is required.
- Avoid repeated `all_products[...]` lookups inside loops.
- Paginate large collections and avoid rendering excessive hidden products.
- Keep JSON blobs small and scoped to the component that needs them.
- Prefer `render` over old `include` for snippet isolation and clarity.

## Third-party scripts and apps

Safe wins:
- Inventory every external script and classify as revenue-critical, deferrable, or removal candidate.
- Remove duplicate or dead pixels only after approval.
- Load non-critical widgets after idle, interaction, or visibility.
- Ensure consent requirements remain intact.

High-risk actions needing approval:
- Removing chat, reviews, subscriptions, personalization, analytics, consent, popups, or upsell apps.
- Changing the order of scripts that depend on globals from other scripts.

## Verification strategy

For each optimization, verify:
- Same visual output on mobile and desktop.
- Same purchase path behavior.
- Improved or neutral Lighthouse/Core Web Vitals signals.
- No console errors from missing globals or late-loaded apps.
- No broken app widgets caused by delayed initialization.
