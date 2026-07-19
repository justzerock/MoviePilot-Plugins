# 004 — Unify history materials, header controls, and form surfaces

- **Status**: DONE
- **Commit**: dd835ca
- **Severity**: HIGH
- **Category**: Visual hierarchy, motion consistency, dark-theme accessibility
- **Estimated scope**: 9 source files plus mirrored regression tests

## Problem

The Docker and MoviePilot frontends now share the same title typography and
compact-header behavior, but four high-visibility surfaces still diverge:

1. Expanded history groups inherit a primary-blue selected fill. Because the
   expansion layer is teleported, some local surface variables are unavailable,
   making the blue field more prominent than intended in both the time-machine
   and library views.
2. Preview and settings headers mix several button systems. Run, settings,
   preview, and close controls differ in material, border, radius, and pressed
   feedback. Compact headers also lack the leading identity used by the large
   header.
3. Media-library scheme rules are visually flat, while their add action and
   default selector occupy separate rows with uneven vertical rhythm.
4. The reusable multiselect popover is teleported outside the settings shell.
   Dark-theme colors that depend on shell-scoped variables therefore fall back
   to light surfaces or low-contrast text.

The existing history expansion transition also uses a large scale delta and a
generic `ease`, which makes the material feel like a new modal layer instead of
the existing cover stack opening in place.

## Target

Implement the same component semantics in both frontends:

- Expanded history surfaces use explicit neutral Apple-like material tokens in
  light and dark themes. Selection is communicated by a fine primary border,
  check state, and at most a 4–6% primary tint, never a solid blue field.
- History expansion uses a 220–260ms strong ease-out transition based on
  opacity and a restrained `scale(.94)`/translation delta. Closing is slightly
  faster. Reduced motion uses opacity only.
- All header action controls use one shared material contract: equal control
  height, radius, border, background, icon color, focus ring, pressed scale,
  and dark-theme values. Running state may keep the primary progress fill.
- The preview compact header shows the current avatar before its title. The
  settings large and compact headers show a settings glyph before the Chinese
  title. These leading controls do not change the existing action bindings.
- The default scheme selector and `新增规则` action share one aligned row with
  equal top and bottom spacing. Each user rule is a quiet bordered surface with
  its delete action aligned to the rule fields.
- Multiselect triggers, chips, menus, options, selected states, placeholders,
  and checkboxes have explicit dark-theme values that remain valid after
  Teleport.
- Switch labels and neighboring form controls remain vertically centered on
  mobile; long descriptions wrap below without moving the switch track.

## Motion specification

Use the existing shared motion tokens when available. Otherwise use these exact
values without adding a dependency:

```css
--yh-motion-enter: cubic-bezier(0.23, 1, 0.32, 1);
--yh-motion-move: cubic-bezier(0.77, 0, 0.175, 1);
--yh-motion-fast: 140ms;
--yh-motion-standard: 220ms;
```

History expansion:

```css
.yh-history-expansion-enter-active {
  transition: opacity 180ms var(--yh-motion-enter);
}
.yh-history-expansion-enter-active .yh-history-expansion__panel {
  transition: transform 240ms var(--yh-motion-enter), opacity 180ms ease-out;
}
.yh-history-expansion-enter-from .yh-history-expansion__panel {
  opacity: 0;
  transform: translate3d(var(--yh-history-origin-x), var(--yh-history-origin-y), 0)
    scale(.94);
}
```

Header controls and rule cards:

```css
transition:
  background-color 180ms ease,
  border-color 180ms ease,
  color 180ms ease,
  transform 140ms var(--yh-motion-enter);
```

Pressed controls use `transform: scale(.97)`. Do not animate layout properties,
use `transition: all`, add bounce, or add decorative glow. Under
`prefers-reduced-motion: reduce`, remove transform transitions and preserve a
short opacity/color response.

## Implementation scope

Mirror behavior and styling across these paired files:

- `docker-app/frontend/src/components/HistoryExpansionLayer.vue`
- `mcg_frontend/src/components/HistoryExpansionLayer.vue`
- `docker-app/frontend/src/components/Page.vue`
- `mcg_frontend/src/components/Page.vue`
- `docker-app/frontend/src/components/Config.vue`
- `mcg_frontend/src/components/Config.vue`
- `docker-app/frontend/src/components/BlueprintSelect.vue`
- `mcg_frontend/src/components/BlueprintSelect.vue`
- `docker-app/frontend/src/styles/applePolish.css` (shared baseline imported by
  both applications; confirm the plugin import before editing)
- each frontend's `tests/ui-regression.test.mjs`

Preserve all existing button events, history selection state, scheme rule data,
server/library IDs, configuration keys, and generation behavior.

## Verification

1. Run both frontend regression suites and builds.
2. In Docker light and dark themes, open time-machine and library history,
   expand a stack, select a card, and confirm no large blue background appears.
3. Repeat the history check in the MoviePilot plugin window.
4. Confirm large and compact preview headers show the avatar, and large and
   compact settings headers show the settings glyph.
5. Compare run/settings/preview/close controls in normal, hover, focus, pressed,
   disabled, and running states in both themes.
6. Confirm default scheme and add-rule controls remain on one row at desktop and
   mobile widths; added rules have a distinct quiet surface and aligned delete
   action.
7. Open every server/library and custom-style multiselect in dark mode. Verify
   trigger, chips, popover, options, selected states, and placeholder contrast.
8. Check 320px, 375px, 390px, and 430px widths for switch/control alignment and
   horizontal overflow.
9. Enable reduced motion and confirm expansion becomes a short crossfade with no
   scale travel.

## Acceptance criteria

- No blue expansion field remains in either history view or frontend.
- Header controls form one recognizable system in both themes.
- Leading avatar/settings identity is visible in compact headers without
  reducing action hit areas below 40px.
- Rule controls are aligned and rules read as individual, non-nested surfaces.
- All multiselect content is legible in dark mode, including teleported menus.
- No new console errors, horizontal scrolling, broken bindings, or generation
  changes are introduced.
