# Feedback 2026-10-22 — Träger Ton, Kerben, Brenntexte

status: done

| # | Note (normalized, short EN) | Att. | Topic | Kind | Disposition | Rationale / link | Status |
|---|---|---|---|---|---|---|---|
| 01 | Sluggish clay (#6) feels much better | | Scheibe | — | No action | Confirmation of #6 (closed, live since fae8be8) | done |
| 02 | Notches work at first; after letting the wheel spin and stopping it, further notches suddenly can't be made | | Werkzeuge | Improvement (bug) | Issue | Not reproduced headless: 2 notches → spin 4 s → stop → 3 more notches all landed (5 visible). Likely causes: silent cap `MAX_NOTCHES = 8` (pottery.js:23, `addNotch` returns unchanged, no hint) and/or silent min-gap rejection (0.25 rad) next to an existing notch that rotated to the front; on iPad possibly a lost pointerup leaving `this.pointers` non-empty, which blocks `notchAt` (index.html:361 requires `!this.pointers.size`) | done — #9 (user: eher viele Kerben, 7–8+) |
| 03 | Firing texts disappear too fast — keep all texts visible | | Brennen | Improvement | Issue | Firing runs 50 steps × 120 ms = 6 s total (index.html:446-452); text 1 („heizt auf“) shows ~3.6 s, text 2 („kühlt ab“) ~2.4 s, then the screen switches to „done“. Needs a decision: show both stages as a list (current one highlighted) and/or slow down / end firing only on a button | done — #10 (Entscheid: Liste + Knopf) |

## Raw notes

- viel besser [#01]
- wenn ich kerben mache geht das zuerst ganz gut. dann lass ich scheiben weiter drehen, stoppe und will weitere kerben machen. Das geht dann plötzlich nicht mehr. [#02]
- die texte beim brennen verschwinden zu schnell wieder. kann man nicht alle texte sichtbar lassen? [#03]
