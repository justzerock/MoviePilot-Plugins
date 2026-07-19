# Yahaha Cover Studio Motion Plans

Plans were audited against commit `dd835ca`.

| # | Plan | Severity | Status |
| --- | --- | --- | --- |
| 001 | Unify Yahaha title type across preview and settings | HIGH | DONE |
| 002 | Bind MoviePilot compact headers to the real scroll root | HIGH | DONE |
| 003 | Refine compact-header motion and reduced-motion behavior | MEDIUM | DONE |
| 004 | Unify history materials, header controls, and form surfaces | HIGH | DONE |

## Recommended order

1. Execute `001-unify-yahaha-title-type.md` first; it changes only display
   typography and establishes the shared title baseline.
2. Execute `002-fix-plugin-compact-header-scroll-root.md` next; it fixes the
   plugin behavior before motion is polished.
3. Execute `003-refine-header-motion-system.md` last; it depends on the compact
   header ownership and behavior from plan 002.
4. Execute `004-unify-history-header-and-form-materials.md`; it builds on the
   shared title and compact-header baseline and synchronizes the remaining
   history, toolbar, rule-card, and dark-theme control surfaces.

No plan adds dependencies or changes cover-generation behavior.
