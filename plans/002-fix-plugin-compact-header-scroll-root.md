# 002 — Bind MoviePilot compact headers to the real scroll root

- **Status**: DONE
- **Commit**: dd835ca
- **Severity**: HIGH
- **Category**: Interruptibility & spatial consistency
- **Estimated scope**: 4 files, focused composable extraction and tests

## Problem

The plugin compact header is teleported and `position: fixed`, but its visibility
is calculated only against the browser viewport. MoviePilot scrolls plugin
content inside a host scroll container, so the header's relationship to that
container is not encoded in the trigger condition.

```ts
// mcg_frontend/src/components/Page.vue:2159-2173 — current
function updateCompactHeader() {
  if (typeof window === 'undefined' || !pageHeroEl.value || !pageShellEl.value) return
  const heroRect = pageHeroEl.value.getBoundingClientRect()
  const shellRect = pageShellEl.value.getBoundingClientRect()
  const visible = heroRect.bottom <= 8
  compactHeaderVisible.value = visible
  // fixed header position uses shellRect
}
```

```ts
// mcg_frontend/src/components/Page.vue:4249-4255 — current
window.addEventListener('scroll', updateHistoryFloatingActionsPosition, true)
window.addEventListener('scroll', updateCompactHeader, true)
```

`SettingsAnchorNav.vue:78-223` already contains the correct repository pattern:
find the actual scrollable ancestor and bind a passive listener directly to it.

## Target

Resolve the current scroll root once, observe it for scrolling and size changes,
and calculate visibility relative to its visible top edge. Use the same behavior
for preview and configuration compact headers in both applications.

```ts
// target visibility calculation
const rootRect = scrollRoot?.getBoundingClientRect()
const topEdge = rootRect ? rootRect.top : 0
compactHeaderVisible.value = heroRect.bottom <= topEdge + 8
```

The fixed toolbar remains visually aligned to the shell, clamped to the browser
viewport:

```ts
const left = clamp(shellRect.left, 8, window.innerWidth - 8)
const width = Math.max(0, Math.min(shellRect.width, window.innerWidth - left - 8))
```

Every scroll update is batched in one `requestAnimationFrame`; user scroll,
resize, shell resize, and root resize all feed that batch. No timers or forced
page scrolls are allowed.

## Repo conventions to follow

- Copy the root-discovery rule from
  `mcg_frontend/src/components/SettingsAnchorNav.vue:78-97`:
  `(auto|scroll|overlay)` plus `scrollHeight > clientHeight + 2`.
- The existing compact surface is correctly teleported in
  `mcg_frontend/src/components/Page.vue:1148-1155` and
  `mcg_frontend/src/components/Config.vue:666-673`; keep Teleport.
- The same components exist under `docker-app/frontend/src/components/`.

## Steps

1. Add a small `useCompactHeaderScrollRoot.ts` composable in both frontend
   projects (or a mirrored source module) with `resolveScrollRoot()`, a
   requestAnimationFrame scheduler, `bind()`, and `dispose()`.
2. Resolve from `pageHeroEl` / `configTopbarEl` after mount and whenever the
   shell's `ResizeObserver` fires. Directly listen to the resolved root with
   `{ passive: true }`; use `window` only as fallback.
3. Replace capture-phase global scroll listeners for compact header updates in
   both `Page.vue` and `Config.vue` with the composable binding. Leave unrelated
   history listeners untouched.
4. Compute visibility relative to the root rectangle as shown above. Recompute
   `left` and `width` on every scheduled update; never add `scrollY` to a
   `getBoundingClientRect()` coordinate.
5. Clean up the root listener, `ResizeObserver`, and pending animation frame on
   component unmount.
6. Add focused tests with a fake internal root: scroll it past the header,
   assert visibility becomes true; scroll back, assert false; resize it and
   assert the fixed geometry remains clamped.

## Boundaries

- Do NOT change MoviePilot host layout, parent overflow rules, or page scroll
  position.
- Do NOT replace the compact header with a regular sticky element; it must keep
  working when the host has nested scrolling.
- Do NOT use `setTimeout`, `scrollIntoView()`, or an absolute hard-coded left
  position.
- Do NOT alter Docker-only controls or plugin close/config events.

## Verification

- **Mechanical**:
  - Run both frontend test suites and builds.
  - Verify the compact header source has no `window.addEventListener('scroll',
    updateCompactHeader, true)` left behind.
- **Feel check**:
  - In MoviePilot at desktop and narrow plugin-window widths, scroll the actual
    host content until the large header leaves the visible content area.
  - Confirm the compact bar appears once, remains fixed, contains title and
    actions, and disappears immediately when the large header returns.
  - Scroll rapidly in both directions and resize the host sidebar/window; the
    bar must not flicker, jump to page origin, or leave the visible plugin area.
  - With reduced motion enabled, confirm the visibility change is opacity-only.
- **Done when**: the plugin preview and configuration headers remain reachable
  during any host-container scroll without duplicate bars or viewport escapes.

## Implementation record

- Added mirrored `compactHeaderScrollRoot` controllers which resolve the real
  scrollable ancestor, batch updates with `requestAnimationFrame`, observe
  target/root size changes, and clean up listeners on unmount.
- Both preview and settings headers now compare their source header against the
  resolved root's visible top edge instead of browser-window scroll state.
- Verified with regression assertions plus both production builds; the plugin
  bundle was deployed to the MoviePilot host without a container restart.
