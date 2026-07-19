# 001 — Unify Yahaha title type across preview and settings

- **Status**: DONE
- **Commit**: dd835ca
- **Severity**: HIGH
- **Category**: Cohesion & typography
- **Estimated scope**: 6 files, small focused changes plus frontend tests

## Problem

The preview and settings headers request `app_impact` for the English wordmark,
while the Chinese title requests `app_chaohei`. This contradicts the desired
single Wordart-style title face and leaves the English title visually too heavy.
The settings title also has a separate, smaller geometry, so the two screens do
not form one application identity.

```ts
// mcg_frontend/src/components/Page.vue:2112-2134 — current
return {
  '--yh-brand-zh-font': `"${getTemplateFontFaceName('app_chaohei')}"`,
  '--yh-brand-en-font': `"${getTemplateFontFaceName('app_impact')}"`,
}
// ...
fontFamily: `"${getTemplateFontFaceName('app_impact')}", Impact, "Arial Narrow", sans-serif`,
```

```ts
// mcg_frontend/src/components/Config.vue:745-764 — current
return {
  '--yh-settings-zh-font': `"${getTemplateFontFaceName('app_chaohei')}"`,
  '--yh-settings-en-font': `"${getTemplateFontFaceName('app_impact')}"`,
}
// ...
fontFamily: `"${getTemplateFontFaceName('app_impact')}", Impact, "Arial Narrow", sans-serif`,
```

```css
/* mcg_frontend/src/components/Config.vue:4996-5024 — current */
.mcr-config-shell .yh-settings-title-wrap { min-height: 70px; }
.mcr-config-shell .yh-settings-en { font-size: clamp(32px, 3.6vw, 54px); }
.mcr-config-shell .yh-settings-zh { font-size: clamp(28px, 3vw, 46px); }
```

## Target

Use the loaded `app_chaohei` face for both Chinese and English decorative title
layers on both screens. The English layer remains a quiet background wordmark,
not a competing headline.

```ts
// target font binding in both Page.vue and Config.vue
'--yh-*-zh-font': `"${getTemplateFontFaceName('app_chaohei')}"`,
'--yh-*-en-font': `"${getTemplateFontFaceName('app_chaohei')}"`,
```

```css
/* target desktop geometry, shared by preview and settings */
.yh-*-title-wrap { min-height: 86px; }
.yh-*-en {
  color: rgba(83, 125, 198, 0.11);
  font-size: clamp(34px, 4vw, 64px);
  font-weight: 400;
  letter-spacing: -0.02em;
  line-height: 0.98;
}
.yh-*-zh {
  font-size: clamp(28px, 3vw, 48px);
  font-weight: 400;
  line-height: 1.05;
  opacity: .8;
}
[data-mcr-theme="dark"] .yh-*-en { color: rgba(244, 247, 251, 0.10); }
```

On mobile retain the existing no-overlap constraints from `2.2.8`: normal
kerning, `line-height: 1.04`, and the `clamp(52px, 14vw, 72px)` wordmark size.

## Repo conventions to follow

- Dynamic header font faces are loaded through `getTemplateFontFaceName()` and
  `loadPreviewFontFaces()` in `mcg_frontend/src/components/Page.vue:2112-2155`.
- Docker has the same components under `docker-app/frontend/src/components/`;
  edits must preserve identical semantics.
- Use CSS variables and `[data-mcr-theme="dark"]`, matching
  `docker-app/frontend/src/styles/applePolish.css:6-71`.

## Steps

1. In both `Page.vue` files, change the English CSS variable and inline style
   from `app_impact` to `app_chaohei`; retain `fontWeight: '400'`.
2. In both `Config.vue` files, make the identical font binding change.
3. Align the settings title metrics with the preview metrics: `min-height: 86px`,
   English `clamp(34px, 4vw, 64px)`, Chinese `clamp(28px, 3vw, 48px)`.
4. Lower the English opacity/color to the target values above in light and dark
   themes. Do not change the Chinese title opacity.
5. Keep the compact headers Chinese-only; do not introduce English text into
   the collapsed toolbar.
6. Extend each `ui-regression.test.mjs` with assertions that both header font
   bindings resolve to `app_chaohei`, the settings metrics match preview, and
   the English background layer has the lower opacity.

## Boundaries

- Do NOT alter canvas text-layer fonts, user-configured fonts, or font API
  payloads.
- Do NOT remove `app_impact`; it remains available for user templates.
- Do NOT change title copy, page layout, or header action bindings.
- Do NOT add dependencies.

## Verification

- **Mechanical**:
  - `cd docker-app/frontend && npm test && npm run build`
  - `cd mcg_frontend && npm test && npm run build`
  - Confirm `rg 'app_impact'` no longer finds header title bindings.
- **Feel check**:
  - Open preview and settings in light and dark mode at desktop width.
  - Confirm English title is legible as a pale, same-family background layer;
    Chinese remains the visual foreground.
  - At 390px and 375px widths, wait for the font request to finish and confirm
    the English wordmark does not overlap itself or the Chinese foreground.
- **Done when**: preview and settings title pairs use the same font, scale, and
  hierarchy in both Docker and MoviePilot builds.

## Implementation record

- Completed in Docker and MoviePilot frontends with the same `app_chaohei`
  dynamic font binding for Chinese and English decorative title layers.
- Preserved the mobile wordmark safeguards while reducing the desktop English
  layer to a low-contrast background treatment.
- Verified with both frontend regression suites and production builds.
