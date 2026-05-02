# Conversion Safety Rules

## Protected storefront behavior

Do not change these unless the user explicitly approves:
- Header/navigation structure, mega menus, search behavior, announcement bars, product media/gallery, variant selection, add-to-cart, dynamic checkout buttons, cart drawer, checkout link behavior, subscription widgets, review widgets, upsells, cross-sells, bundles, loyalty/referral widgets, consent banners, exit-intent or discount popups, sticky add-to-cart, and localization/currency selectors.
- Analytics and marketing pixels, including consent mode, attribution, customer events, and server/client pixel coordination.
- Accessibility affordances such as focus states, reduced motion behavior, keyboard navigation, labels, and ARIA state.
- SEO-critical content, structured data, canonical tags, hreflang tags, and product schema.

## Safe defaults

- Preserve UI markup and CSS classes whenever possible.
- Move scripts later only when functionality still initializes before the user needs it.
- Keep first meaningful product interactions responsive: variant picker, add-to-cart, sticky cart, cart drawer, and search.
- Use feature flags or small reversible patches for risky changes.
- Prefer delaying non-critical marketing/chat/reviews code until idle, interaction, or below-fold visibility instead of removing it.

## App and third-party script policy

Inventory before touching. Classify each script as:
1. Revenue critical: payments, subscriptions, reviews/social proof, product options, bundles, personalization, analytics attribution, consent.
2. Potentially deferrable: chat, heatmaps, surveys, social embeds, low-priority recommendation widgets.
3. Candidate for removal: duplicate tags, abandoned app snippets, old pixels, unused libraries, repeated CDN imports.

For removal or disabling, require evidence and approval. Provide a rollback path.

## QA scenarios after edits

Minimum mobile QA:
- Home page loads, hero looks unchanged, menu opens, search works.
- Product page variant changes update price/media/availability.
- Add to cart works, cart drawer/page opens, quantity updates, checkout link works.
- Discount/popup/overlay behavior remains as intended.
- Reviews/subscription/bundle widgets still load where expected.
- Consent and analytics scripts still honor merchant requirements.
- No major layout shifts on first load or during app widget hydration.
