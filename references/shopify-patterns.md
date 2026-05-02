# Shopify Liquid and Asset Patterns

## Responsive image pattern

Use Shopify image filters instead of hard-coded CDN URLs where possible.

```liquid
{% assign loading = 'lazy' %}
{% assign fetch_priority = 'auto' %}

{{ product.featured_image
  | image_url: width: 1800
  | image_tag:
    widths: '360, 533, 720, 940, 1066, 1200, 1600, 1800',
    sizes: '(min-width: 990px) 50vw, 100vw',
    loading: loading,
    fetchpriority: fetch_priority,
    class: 'product-card__image'
}}
```

## Above-the-fold hero image

Avoid lazy loading the first visible hero/LCP image. Use one high-priority candidate, not every image.

```liquid
{% assign hero_loading = 'lazy' %}
{% assign hero_fetch_priority = 'auto' %}
{% assign hero_preload = false %}

{% if section.index == 1 and section.location == 'template' %}
  {% assign hero_loading = 'eager' %}
  {% assign hero_fetch_priority = 'high' %}
  {% assign hero_preload = true %}
{% endif %}

{{ section.settings.image
  | image_url: width: 2400
  | image_tag:
    widths: '375, 550, 750, 1100, 1500, 1780, 2000, 2400',
    sizes: '100vw',
    loading: hero_loading,
    fetchpriority: hero_fetch_priority,
    preload: hero_preload,
    class: 'hero__image'
}}
```

## Defer theme scripts

Avoid output that creates parser-blocking scripts for non-critical theme assets.

```liquid
<!-- Avoid for non-critical JS because it emits a plain script tag. -->
{{ 'theme.js' | asset_url | script_tag }}

<!-- Prefer when execution can wait until document parsing is complete. -->
<script src="{{ 'theme.js' | asset_url }}" defer="defer"></script>
```

Keep dependency order intact. If `theme.js` depends on `vendor.js`, both can be deferred, but `vendor.js` must appear first.

## Route-specific loading

Do not load product-only code on every page.

```liquid
{% if template.name == 'product' %}
  <script src="{{ 'product-form.js' | asset_url }}" defer="defer"></script>
{% endif %}
```

For sections, prefer loading the section asset only when the section is rendered.

## Interaction-based loading

Use this only for non-critical optional UI, not for core purchase flow.

```html
<button type="button" data-load-size-guide>Size guide</button>
<script>
(() => {
  let loaded = false;
  function loadSizeGuide() {
    if (loaded) return;
    loaded = true;
    const script = document.createElement('script');
    script.src = "{{ 'size-guide.js' | asset_url }}";
    script.defer = true;
    document.head.appendChild(script);
  }
  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-load-size-guide]')) loadSizeGuide();
  }, { passive: true });
})();
</script>
```

## CSS loading

Use normal stylesheet loading for required theme CSS. Consider preloading only a critical stylesheet.

```liquid
{{ 'base.css' | asset_url | stylesheet_tag: preload: true }}
{{ 'product.css' | asset_url | stylesheet_tag }}
```

Do not preload many files. Competing preloads can delay the LCP image.

## CLS prevention

Prefer explicit dimensions from `image_tag`. For custom markup, reserve space.

```liquid
<div class="media" style="aspect-ratio: {{ image.aspect_ratio }};">
  {{ image | image_url: width: 1200 | image_tag: loading: 'lazy' }}
</div>
```

For app widgets and review blocks, reserve a minimum height if they hydrate late.

## Liquid loop cleanup

Avoid expensive work inside loops.

```liquid
<!-- Risky: sorting or product lookups inside loops -->
{% for block in section.blocks %}
  {% assign product = all_products[block.settings.product] %}
  {% render 'heavy-card', product: product %}
{% endfor %}
```

Safer options:
- Limit block count.
- Render lighter cards for offscreen content.
- Use settings with direct product objects when possible.
- Avoid hidden full renders for carousel slides that are not initially visible.
