# Träger Ton (#6) — Design

## Why
Tester feedback: "Das Töpfern ist zu schnell für eine alte Frau. Vielleicht sollte es mehr ziehen/drücken brauchen und der Ton sollte träger reagieren." Today `applyAt` moves each ring 50 % (`clayStrength` 0.5) toward the finger **per pointermove event**, so one quick swipe nearly finishes the wall, and the rate depends on how fast/how often the device fires events.

## Decisions (user)
- **Time-based flow:** while a finger rests on the clay, the wall flows toward the finger at a steady, time-based rate — also when the finger holds still, like pressing against a turning wheel. Swipe speed and event rate no longer matter.
- **Tempo ~3 s:** a clear shape change has been fully followed after about 3 seconds.
- **Fixed default:** no new setting/button.

## Behaviour
- Pointer events only record the **target** (height y + radius r, as today: one finger → |x|, two fingers → half the distance, height = midpoint).
- Each animation frame while shaping: every ring in the existing Gaussian window (k = -3..3, w = exp(-k²/4)) moves toward the target by `w * f`, with `f = 1 - exp(-dt / FLOW_TAU)` and **`FLOW_TAU = 1000` ms** (≈ 95 % after 3 s). `dt` is the real frame time, clamped to at most 100 ms so a stalled tab does not jump.
- Releasing the finger(s) stops the flow immediately; the target is cleared. Leaving the wheel screen (gallery, glaze, lump picker, tool mode) also stops it.
- Undo granularity unchanged: one snapshot per stroke (pointerdown).
- Rub sound unchanged (still driven by finger movement speed).
- `clayStrength` editor prop is removed (superseded by FLOW_TAU); `wheelSpeed` stays.
- Tool mode, notches, corners, random shape, lump choice, gallery edit: unaffected.

## Builder's calls (mine)
- FLOW_TAU and the pure step function live in `pottery.js` so they are unit-testable (`flowFactor(dtMs)`, `flowToward(profile, idx, r, f)` or equivalent).
- Height clamp and ring-index mapping identical to today's `applyAt`.

## Non-goals
- Requiring the wheel to spin in order to shape.
- Changing orbit/zoom speed, wheel speed, or tool-mode behaviour.

## Tests
- Unit: flowFactor(0)=0, monotonic, flowFactor(3000) ≥ 0.95, flowFactor(16) small (< 0.02); step moves the centre ring toward target by exactly f, neighbours by w·f, ring 0 untouched, MAXR/0.2 clamp kept.
- e2e: a quick swipe barely changes the wall; holding the finger still for ~3 s changes it nearly fully; existing 12 flows stay green (adjust ones that relied on instant shaping by holding/waiting).
