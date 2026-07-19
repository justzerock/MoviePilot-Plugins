# 003 — Refine compact-header motion and reduced-motion behavior

- **Status**: DONE
- **Commit**: dd835ca
- **Severity**: MEDIUM
- **Category**: Easing, performance & accessibility
- **Estimated scope**: 6 files, CSS-only motion refinement and regression tests

## Problem

Compact headers currently use hand-written curves that drift from the shared
Apple motion tokens, and the preview compact header lacks its own reduced-motion
override. The main action button animates `width`, `min-width`, and
`border-radius` while its state changes, creating avoidable layout work inside a
high-visibility control.

```css
/* mcg_frontend/src/components/Page.vue:10885-10900 — current */
.yh-compact-header-enter-active,
.yh-compact-header-leave-active {
  transition: opacity 160ms ease, transform 180ms cubic-bezier(.2, .8, .2, 1);
}
```

```css
/* mcg_frontend/src/components/Page.vue:10785-10790 — current */
transition:
  width 220ms cubic-bezier(.2, .8, .2, 1),
  min-width 220ms cubic-bezier(.2, .8, .2, 1),
  border-radius 220ms cubic-bezier(.2, .8, .2, 1),
  background-color 180ms ease,
  transform 140ms ease !important;
```

The shared layer already defines a token location in
`docker-app/frontend/src/styles/applePolish.css:6-28`, but only provides
`--yh-apple-ease`, which does not express the product's enter/exit distinction.

## Target

Add shared motion tokens and use transform/opacity for header entry and exit.
Use an ease-out curve for entering/exiting and preserve a short, explicit press
response. Respect reduced motion without removing opacity feedback.

```css
/* target tokens */
--yh-motion-enter: cubic-bezier(0.23, 1, 0.32, 1);
--yh-motion-move: cubic-bezier(0.77, 0, 0.175, 1);
--yh-motion-fast: 140ms;
--yh-motion-standard: 220ms;

/* target compact header */
.yh-compact-header-enter-active,
.yh-compact-header-leave-active {
  transition:
    opacity var(--yh-motion-fast) var(--yh-motion-enter),
    transform var(--yh-motion-standard) var(--yh-motion-enter);
  will-change: transform, opacity;
}
.yh-compact-header-enter-from,
.yh-compact-header-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
@media (prefers-reduced-motion: reduce) {
  .yh-compact-header-enter-active,
  .yh-compact-header-leave-active { transition: opacity 140ms ease; }
  .yh-compact-header-enter-from,
  .yh-compact-header-leave-to { transform: none; }
}
```

For the run control, retain its required icon-to-stop affordance but avoid a
layout-affecting animation whenever the compact toolbar is present. Use a fixed
compact-button footprint and animate the inner label with opacity/transform;
keep the wider regular button only where sufficient header space exists.

## Repo conventions to follow

- Define shared tokens only in
  `docker-app/frontend/src/styles/applePolish.css`; plugin imports this file via
  `mcg_frontend/src/styles/applePolish.css:1-4`.
- Existing press feedback in `applePolish.css:107-136` uses a controlled
  `scale(0.97)` and should remain the interaction baseline.
- Mirror component-scoped changes in both frontend trees.

## Steps

1. Add the exact target motion tokens to `applePolish.css`; do not create a
   second token file in the plugin frontend.
2. Replace compact header transition values in both `Page.vue` and `Config.vue`
   trees with the tokens. Add the same reduced-motion override to preview that
   configuration already approximates.
3. Keep transform origin at the top edge of the fixed header so it materializes
   from the viewport edge rather than scaling from its center.
4. Refactor only the compact run button's expanding label so its container has a
   stable maximum footprint; fade/translate the count within it instead of
   repeatedly animating parent width. Do not change the generation state logic.
5. Add tests asserting the shared tokens, compact reduced-motion override, and
   absence of `transition: all` or animation of `width`/`min-width` on the
   compact run button.

## Boundaries

- Do NOT introduce a motion library, JavaScript animation loop, or new
  dependency.
- Do NOT add bouncing or perpetual decorative motion to the headers.
- Do NOT change the existing loading-title opacity-only behavior.
- Do NOT change general canvas, image, or generation algorithms.

## Verification

- **Mechanical**:
  - Run both frontend test suites and builds.
  - Confirm compact-header CSS only animates `opacity` and `transform`.
- **Feel check**:
  - Trigger compact header while scrolling at normal speed: it should arrive
    immediately from the top edge, settle without bounce, and remain responsive
    if the user reverses direction before it completes.
  - Start and stop generation repeatedly: compact toolbar geometry must not
    push nearby actions or visibly relayout.
  - In DevTools Rendering, enable `prefers-reduced-motion`; header state changes
    should cross-fade with no vertical travel.
- **Done when**: both builds have one coherent, restrained header motion system
  with no layout-jank on the compact action control.

## Implementation record

- Added shared enter/move/duration tokens to the shared Apple polish layer.
- Compact headers now enter through transform and opacity, respect reduced
  motion through opacity-only crossfades, and materialize from their top edge.
- Compact generation controls retain a stable action footprint while state,
  progress, and content transition inside it.
- Verified with both frontend regression suites and production builds.
