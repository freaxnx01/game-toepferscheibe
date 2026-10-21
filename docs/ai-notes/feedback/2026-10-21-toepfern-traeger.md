# Feedback 2026-10-21 — Töpfern zu schnell

status: done

| # | Note (normalized, short EN) | Att. | Topic | Kind | Disposition | Rationale / link | Status |
|---|---|---|---|---|---|---|---|
| 01 | Shaping reacts too fast for an elderly player — clay should need more pulling/pushing and respond more sluggishly | | Scheibe | Improvement | Issue | `applyAt` (index.html:352) moves each ring 50 % toward the finger per pointermove (`clayStrength` default 0.5, range 0.2–1) — a single swipe nearly snaps the wall. Making it sluggish touches feel (strength, maybe per-frame easing instead of per-event), undo granularity and the e2e flows; needs a decision on how slow, and whether it's a setting (e.g. „Ton: weich / fest“) or the new default. Not covered by #1–#5 | done — #6 |

## Raw notes

- Das Töpfern ist zu schnell für eine alte Frau. Vielleicht sollte es mehr ziehen/drücken brauchen und der Ton sollte träger reagieren [#01]
