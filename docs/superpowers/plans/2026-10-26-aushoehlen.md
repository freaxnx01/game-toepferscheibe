# Aushöhlen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new lump starts solid and is first hollowed out in its own step „Aushöhlen“ (#8). Pressing in the middle deepens the hole and pulling outward widens it. The resulting `wall`/`floor` are kept per piece.

**Architecture:**
- **Pure geometry and hollowing math** (`pottery.js`): `outline`, `outlineRings`, `buildMesh` and `makeShape` gain `wall` and `floor`. `floor === null` means solid. New pure helpers do the time-based press/pull step.
- **UI** (`index.html`): a new screen `'hollow'` placed before `'wheel'`. It reuses the existing raycast `toLocal`, the pointer handling and the #6 flow factor.

**Tech Stack:** Buildless static page (dc document), three.js 0.160, node:test, Playwright e2e (Python).

**Spec:** `docs/superpowers/specs/2026-10-26-aushoehlen-design.md`. Read it; it is binding.

## Global Constraints

- **TDD:** Use Test-Driven Development for every task: write a failing test first, watch it fail, implement minimally to pass, verify green.
- **Running e2e:**
  - Always run e2e under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`.
  - Run a single flow with `FLOW=<name>`.
  - Unit tests: `node --test tests/pottery.test.js`.
- **Old saved works must render exactly as before.** `outline(p, h)` and `outline(p, h, 0.13, 0.14)` must be deep-equal to today's output.
- **German copy** uses „Sie“ and real umlauts.
- **Tap targets:** buttons at least 64px high, text at least 20px.
- **Existing style:**
  - Inline styles and dense one-line methods.
  - Colours `#B45E3A` / `#FBF6EC` / `#D9C9B2` / `#35261B`.
  - Secondary buttons look like „🎲 Zufällige Form“.
- **Exact copy:**
  - Step label: „Aushöhlen“.
  - Buttons: „Weiter zum Formen →“, „Für mich aushöhlen“, „← Zurück zum Aushöhlen“. Undo uses the existing „↶ Rückgängig“ label/style.
  - Hint: „Halten Sie den Finger in die Mitte – das Loch wird tiefer. Ziehen Sie dann nach aussen – die Öffnung wird weiter.“

## Review Focus

- **Old gallery entries** without `wall`/`floor`:
  - They render, and „Weiter töpfern“ opens them in shaping with 0.13/0.14.
  - Thumbnails and the 3D view (#13) are unchanged.
- **Wet shine (#7):** `outlineRings` length equals `outline` length for the solid case, for custom values, and for the floor clamped by a low height.
- **No dead ends:**
  - From `'hollow'`, the header „Galerie“ and Start can always be left and returned to with „← Zurück zu meinem Stück“.
  - A solid piece can never reach glaze, firing or saving.
- **Undo across strokes** restores `wall`/`floor`, including a hollow-step undo after „← Zurück zum Aushöhlen“.
- **The view (#13) and „Weiter töpfern“** never land in `'hollow'`.

---

### Task 1: Geometry and hollowing math (`pottery.js`)

**Files:**
- Modify: `pottery.js`. Touches `outline` (~l.38), `outlineRings`, `buildMesh`, `makeShape` and the `api` export.
- Test: `tests/pottery.test.js`

**Interfaces (Produces):**
- **Constants:** `WALL_DEFAULT = 0.13`, `FLOOR_DEFAULT = 0.14`, `WALL_MIN = 0.08`, `WALL_MAX = 1.2`, `FLOOR_MIN = 0.08`, `HOLE_THUMB = 0.15`, `PRESS_MARGIN = 0.1`.
- **`outline(profile, height, wall = 0.13, floor = 0.14) => [r, y][]`**
  - `floor === null` means **solid**: `[[0,0], ...outer rings, [0, 2*height]]`, with no inner points.
  - Otherwise the inner side is as today, using `wall`, with the effective floor `min(floor, 2*height - 0.2)`.
- **`outlineRings(profile, height, wall = 0.13, floor = 0.14) => number[]`**
  - It mirrors `outline` point for point.
  - For the solid case its last entry is `RINGS - 1` (the top cap belongs to the rim).
- **`buildMesh(shape, segments)`** uses `shape.wall ?? 0.13`. The floor is `shape.floor === undefined ? 0.14 : shape.floor`, so `null` stays solid.
- **`makeShape({ ..., wall = 0.13, floor = 0.14 })`** stores both fields. `version` stays 1, so `canEdit` is unchanged.
- **`wallFor(profile, holeR) => number`** is `profile[RINGS-1] - holeR`, clamped to `[WALL_MIN, WALL_MAX]`.
- **`holeFor(profile, wall) => number`** is `profile[RINGS-1] - wall`, clamped to at least `0.03`.
- **`hollowStep({ floor, holeR }, profile, height, r, f) => { floor, holeR }`** is pure and returns a new object.
  - **Press** happens when `floor === null` or `r <= holeR + PRESS_MARGIN`.
    - `floor` starts from `2*height` if it is null.
    - `holeR` becomes `HOLE_THUMB` if it is not yet set.
    - Then `floor += (FLOOR_MIN - floor) * f`.
  - **Pull** happens otherwise. `holeR += (min(r, profile[RINGS-1] - WALL_MIN) - holeR) * f`, and `holeR` never shrinks.
  - The floor never rises and never goes below `FLOOR_MIN`.
  - `f = 0` returns an unchanged copy, except that a solid input stays solid.

- [ ] **Step 1: Failing unit tests**, added to `tests/pottery.test.js`:
  - `outline defaults unchanged`: compare `outline(p,h)` and `outline(p,h,0.13,0.14)` deep-equal to a copy of today's algorithm inlined in the test, for `defaultProfile()` at h = 1 and h = 0.35.
  - `outline custom wall/floor`: with wall 0.3, inner radii are `max(profile[i]-0.3, 0.03)`. The floor point y is 0.5.
  - `outline floor clamped`: with h = 0.4 and floor 0.7, the floor y is `0.6` (2h - 0.2).
  - `outline solid`: `outline(p,1,0.13,null)` has length `RINGS + 2`. The last point is `[0, 2]`.
  - `outlineRings mirrors outline`: lengths are equal for the default, custom, clamped and solid cases.
  - `buildMesh solid vs default`: vertex counts follow `outline` length. A shape with `floor: null` builds without NaN.
  - `makeShape wall/floor`: the values round-trip. Missing values give 0.13/0.14.
  - `wallFor/holeFor`: they are inverse within bounds and clamp at `WALL_MIN`/`WALL_MAX`/0.03.
  - `hollowStep press`:
    - from solid with r = 0 and f = 0.5, floor = `2h + (0.08 - 2h)*0.5` and holeR = 0.15;
    - repeated steps approach but never go below 0.08;
    - f = 0 leaves the floor unchanged.
  - `hollowStep pull`:
    - with floor 0.5, holeR 0.15, r = 0.6 and f = 0.5, holeR = 0.375 and the floor is unchanged;
    - r beyond the rim clamps so that `wallFor(...) === WALL_MIN`;
    - a smaller r does not shrink holeR.
- [ ] **Step 2: Run them and see them fail**: `node --test tests/pottery.test.js`.
- [ ] **Step 3: Implement** to the interfaces above and export everything new on `api`.
- [ ] **Step 4: Unit tests green.** Run the e2e flows `wet_shine` and `gallery_view` to prove nothing changed for existing shapes.
- [ ] **Step 5: Commit** `feat(scheibe): Wand- und Bodendicke in der Geometrie (#8)`.

### Task 2: Step „Aushöhlen“: screen, buttons, paths, saving (`index.html`)

**Files:**
- Modify: `index.html`. Touches:
  - instance fields (~l.247): `wall`, `floor`, `holeR`
  - `snapshot`/`undo`, `applyLump`, `currentShape`, `loadWork`, `startNew`, `resetClay`, `randomShape`
  - `labels`, `canvasDisplay`, `syncWheel`, `goStart`/`goGallery` return lists
  - a new aside panel `isHollow`
- Modify: `tests/e2e/smoke.py`. Adds the helper `start_clay(page)` and new flows `hollow_steps`, `hollow_old_entry`.

**Interfaces:**
- **Consumes** from Task 1: `outline`/`outlineRings`/`makeShape` with `wall`/`floor`, plus `wallFor`, `holeFor`, `WALL_DEFAULT`, `FLOOR_DEFAULT`.
- **Produces** for Task 3:
  - `this.floor` (number or `null`) and `this.holeR`, with `this.wall` kept consistent as `wallFor(profile, holeR)` whenever there is a hole.
  - The screen name `'hollow'`.
  - The mount element attributes `data-floor` and `data-wall`, written like `data-wet` (only on change, `toFixed(3)`, `'solid'` for null). They are the e2e hooks.
- **Producing geometry:** `buildGeo()` must pass `this.wall` and `this.floor` to `outlineRings`, and `currentShape()` must include them.

**Behaviour** (spec „Behaviour“ section):
- **Entering `'hollow'`:** „Ton auf die Scheibe legen“ (`startNew`) and „Neuer Tonklumpen“ (`resetClay`) set `floor = null`, `holeR = null`, `wall = 0.13` and go to `'hollow'`.
- **The hollow panel** shows:
  - the hint;
  - „Weiter zum Formen →“, disabled while `floor === null`;
  - „Für mich aushöhlen“, which snapshots, sets wall 0.13 and floor 0.14, sets `holeR = holeFor(...)`, refreshes and goes to `'wheel'`;
  - „↶ Rückgängig“.
- **Not in the hollow step:** the lump picker, the tool, random shape and height changes. Neither the mouse wheel nor the height buttons change the height there.
- **Shaping:** the panel gets „← Zurück zum Aushöhlen“ (secondary). It sets `holeR = holeFor(profile, wall)` and goes to `'hollow'`.
- **`loadWork`** (gallery „Weiter töpfern“, also from the view) sets wall/floor from the shape, falling back to 0.13/0.14, and lands in `'wheel'`.
- **`randomShape`** keeps wall/floor.
- **`goStart`/`goGallery`** treat `'hollow'` like `'wheel'` for `returnScreen`.
- **The turntable** is visible in `'hollow'` and the canvas is shown. The step label is „Aushöhlen“.
- **Snapshots and undo** carry `wall`, `floor` and `holeR`.

- [ ] **Step 1: Failing e2e.**
  - Add `start_clay(page)`: click „Ton auf die Scheibe legen“, wait for „Aushöhlen“, click „Für mich aushöhlen“, wait for „An der Scheibe“.
  - Replace every existing „click 'Ton auf die Scheibe legen' then shape/glaze“ with `start_clay`. That includes `make_work` and flows that click „Neues Stück beginnen“ then „Ton auf die Scheibe legen“. Keep flows that only assert the start screen as they are.
  - `lump_choice`: after „Neuer Tonklumpen“ it must show „Aushöhlen“. Adapt it.
  - New `hollow_steps`:
    - Start shows the label „Aushöhlen“ and `data-floor == 'solid'`.
    - „Weiter zum Formen →“ is disabled.
    - „Für mich aushöhlen“ leads to „An der Scheibe“ with `data-floor == '0.140'` and `data-wall == '0.130'`.
    - „← Zurück zum Aushöhlen“ shows „Aushöhlen“ with the values unchanged.
    - Header „Galerie“ then „← Zurück zu meinem Stück“ returns to „Aushöhlen“.
    - Glaze, fire and save, then „Weiter töpfern“ on that work, lands in „An der Scheibe“ with 0.140/0.130.
    - There are no page errors.
  - New `hollow_old_entry`:
    - Seed an entry whose `shape` has no `wall`/`floor`.
    - „Weiter töpfern“ lands in „An der Scheibe“ with `data-wall == '0.130'` and `data-floor == '0.140'`.
    - „In 3D anschauen“ opens without errors.
  - Run them; the new flows FAIL.
- [ ] **Step 2: Implement** as described above.
- [ ] **Step 3:** The new flows are green, then the full suite is green. Report any flow that only times out in the full run.
- [ ] **Step 4: Commit** `feat(scheibe): Schritt „Aushöhlen“ vor dem Formen (#8)`.

### Task 3: Press and pull gesture (`index.html`)

**Files:**
- Modify: `index.html`. Touches `bindPointer` pointerdown mode selection, `flowTick`, and `undo` snapshots per stroke.
- Modify: `tests/e2e/smoke.py`. New flow `hollow_gesture`.
- Modify: `CHANGELOG.md` `[Unreleased]` and `README.md`, if it lists the game steps.

**Interfaces:**
- **Consumes:** `hollowStep`, `wallFor`, `flowFactor` and `wetStep` (Task 1 / existing), and `this.floor`, `this.holeR`, `this.wall`, `'hollow'` and `data-floor`/`data-wall` (Task 2).
- **Pointer mode:**
  - In `'hollow'`, a primary pointerdown that `hitsPot` sets `mode = 'hollow'`, takes one `snapshot()` and starts the rub sound like shaping.
  - Anything else orbits, as today.
  - Pinch-zoom with two fingers still works when the stroke started off the clay.
- **Target:** a `'hollow'` stroke uses `toLocal` of the first pointer. `r = |x|`; y is ignored.
- **`flowTick`**, while `mode === 'hollow'` with a pointer down on screen `'hollow'`:
  - `({floor, holeR} = hollowStep({floor, holeR}, profile, height, r, flowFactor(dt)))`, then `wall = wallFor(profile, holeR)`.
  - It calls `refresh()` when the floor or `holeR` changed by more than 1e-4.
  - Optional: `wetStep` at the top ring.
  - The step is time-based, like shaping, so holding still keeps working.
- **„Weiter zum Formen →“** becomes enabled as soon as `floor !== null`. That needs a re-render when it flips; `forceUpdate` is fine.

- [ ] **Step 1: Failing e2e `hollow_gesture`.**
  - **Setup:** start, so the screen is „Aushöhlen“. The canvas centre-top of the lump is at `rim_point`-style coordinates. Add a helper `top_center(page)` that computes the screen point of `(0, 2h - 0.05, 0)` with the same camera maths as `rim_point`.
  - **Press:** mouse down at `top_center` and hold for 2.5 s with small moves (±1px every 100 ms). Then:
    - `data-floor` is not `'solid'` and is below `2h - 0.6`;
    - „Weiter zum Formen →“ is enabled.
  - **Pull:** a new stroke at `top_center`, moving horizontally outward to the screen x of `rim_point(page)` over about 0.5 s, then held for 2.5 s. Then:
    - `data-wall` is lower than right after the press;
    - `data-wall` is at least `0.080`;
    - `data-floor` is unchanged by the pull, within 0.005.
  - **Undo:** „↶ Rückgängig“ once restores the press-only `data-wall`.
  - **Continue:** „Weiter zum Formen →“ reaches „An der Scheibe“ with the same `data-wall`/`data-floor`.
  - **Errors:** there are no page errors.
  - Run it; it FAILS.
- [ ] **Step 2: Implement** as described above.
- [ ] **Step 3:** `hollow_gesture` is green and the full suite is green. Save a screenshot of the hollowed lump to `$E2E_SHOT_DIR`, if it is set, for the controller.
- [ ] **Step 4: CHANGELOG** `[Unreleased]`: „Aushöhlen als erster Schritt: in der Mitte drücken macht das Loch tiefer, nach aussen ziehen macht es weiter (#8).“ Update the README if it describes the steps.
- [ ] **Step 5: Commit** `feat(scheibe): Aushöhlen mit dem Finger (#8)`.
