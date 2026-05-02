# Common Shopify Theme Performance Issues

## Issue library

| Issue | Symptoms | Safe fix | Watch-outs |
|---|---|---|---|
| Hero/LCP image lazy loaded | High LCP, blank hero on load | Make first visible hero/product image eager, consider one preload/fetchpriority high | Do not eager-load all carousel slides |
| Missing image width/height | CLS, lazy loading behaves badly | Use `image_tag` or explicit dimensions/aspect-ratio | Ensure CSS remains responsive |
| Desktop image downloaded on mobile | High transfer size, slow LCP | Use `image_url`, `image_tag`, `widths`, `sizes` | Verify art direction/crop requirements |
| Parser-blocking theme script | Delayed FCP/LCP | Add `defer` to non-critical scripts | Preserve dependency order and globals |
| Product code loaded everywhere | JS/CSS bloat on home/collection pages | Gate by `template.name` or section presence | Do not break quick-add or predictive search |
| Duplicate libraries | High JS parse/execute | Remove duplicate jQuery/sliders/lazy libraries after approval | Apps may expect globals |
| Legacy lazyload library | Extra JS, incorrect LCP priority | Replace with native `loading` and Shopify filters | Test older custom components |
| Too many preloads | Network contention, worse LCP | Keep one or two critical preloads per template | More preloads are not automatically better |
| Heavy reviews/chat/heatmap scripts | Long tasks, INP/TBT issues | Defer to idle/interaction/visibility where allowed | Revenue and support impact may be real |
| Fonts block rendering | FCP/LCP delay, CLS | Reduce variants, use swap/system font, preload one critical font | Brand requirements |
| Hidden carousel renders everything | Large DOM/assets | Lazy load non-visible slides and avoid hidden heavy snippets | First slide must remain fast and accessible |
| `render` inside large loops | Slow server render/large HTML | Simplify cards, move logic outside loops, paginate | Visual parity with product cards |
| Huge JSON in Liquid | Large HTML and parse cost | Scope JSON to component and only required fields | App or JS may depend on data shape |
| CSS purge too aggressive | Broken dynamic states/apps | Safelist dynamic classes and visually test | Shopify settings can generate class names |
| App leftovers | Extra requests and errors | Remove old snippets/assets after confirming app is unused | Ask merchant before deleting |

## Red flags in files

Search for:
- `| script_tag` for scripts that could be parser blocking.
- `lazyload`, `data-src`, `data-bgset`, `lazysizes` for old lazy-loading libraries.
- `<img` without `width`, `height`, or `loading` attributes.
- `loading: 'lazy'` in hero, slideshow, image-banner, product media, or first section code.
- External `<script src="https://...">` in theme layout, snippets, or sections.
- `all_products[` inside loops.
- Very large `.js`, `.css`, `.json`, or image files in `assets/`.
- Repeated app snippets in `theme.liquid` plus app embeds performing similar work.

## Do not optimize blindly

Bad optimizations that often hurt stores:
- Lazy loading the LCP image.
- Removing reviews, popups, chat, subscriptions, or pixels just because they are heavy.
- Deferring variant/product-form JS until after user interaction.
- Purging CSS without safelisting dynamic app/theme classes.
- Replacing Shopify CDN image filters with static image URLs.
- Adding another optimization library to fix excessive JavaScript.
