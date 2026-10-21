# Galerie bearbeiten, Klang, Ausgangsklumpen, Werkzeuge — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement issues #1 (Galerie-Werke weiter töpfern), #3 (natürlicherer Klang), #4 (Ausgangsklumpen) and #2 (Kerben + eckig machen) in the buildless Töpferwerkstatt.

**Architecture:** Pure logic moves into a new classic script `pottery.js` (global `Pottery`, plus `module.exports` under Node) that `index.html` loads before `support.js`; it is unit-tested with `node --test`. `index.html`'s `Component` keeps all three.js/WebAudio/UI wiring and calls into `Pottery`. UI flows are covered by a Playwright (Python) smoke script that asserts on DOM text and `localStorage`, not pixels.

**Tech Stack:** Plain JS (no build), three.js 0.160 from unpkg, WebAudio, Node 24 `node:test`, Python Playwright (already installed) for e2e.

**Spec:** `docs/superpowers/specs/2026-10-20-galerie-klang-werkzeuge-design.md`

## Global Constraints

- Use Test-Driven Development for every task: write a failing test first, watch it fail, implement minimally to pass, verify green.
- Buildless: no bundler, no npm dependencies, no `package.json` needed. `pottery.js` is loaded with `<script src="./pottery.js"></script>` directly before `<script src="./support.js"></script>` (index.html line 8).
- Touch targets ≥ 64 px high, German copy in Sie-form, matching the existing inline-style button look (`#F4ECDF` / `#B9A58A` secondary, `#B45E3A` primary).
- Every new action is undoable via „Rückgängig“ (shape, notch, corners, lump choice, random shape).
- localStorage key `toepfern.galerie` unchanged; max 30 entries; old entries (no `id`/`shape`) must still render and be removable.
- Shape limits unchanged for all lump sizes: radius `MINR 0.15`…`MAXR 1.6` (pull clamps to 0.2), height 0.35…1.6.
- Commit messages reference the issue (`(#1)`, `(#3)`, `(#4)`, `(#2)`).
- Run any Playwright script under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`; serve with `python3 -m http.server 8799 --directory <worktree>`; launch Chromium with `--use-gl=swiftshader --enable-unsafe-swiftshader` and `set_default_timeout(120000)` (the box is slow under swiftshader).

## Review Focus

- Leaving for the Galerie while the kiln is firing: the fire timer must not yank the screen to „Fertig“; „Zurück zu meinem Stück“ then lands on „Fertig“. (Task 3 e2e)
- Old gallery entries without `id`/`shape`: still shown, no „Weiter töpfern“, „Entfernen“ removes exactly that card. (Task 2 e2e seeds one)
- Original removed while being edited: saving then adds a new entry instead of replacing or crashing. (Task 1 unit)
- „Neuer Tonklumpen“ while editing, then „Rückgängig“: edit link is back and saving replaces the original (no duplicate). (Task 2 e2e)
- Notch taps on the same spot / many taps / at the 0↔2π seam combined with corners: no duplicates within 0.25 rad, max 8 notches, no NaN vertices. (Task 6 unit)

---

### Task 1: `pottery.js` foundation + gallery data model (#1)

**Files:**
- Create: `pottery.js`
- Create: `tests/pottery.test.js`
- Modify: `index.html:8` (add script tag), `index.html` constants block (`RINGS`, `MINR`, `MAXR`, `defaultProfile` now come from `Pottery`)

**Interfaces:**
- Produces (all on `Pottery`):
  - `RINGS = 28`, `MINR = 0.15`, `MAXR = 1.6`, `HMIN = 0.35`, `HMAX = 1.6`, `MAX_WORKS = 30`
  - `defaultProfile(): number[]` (moved verbatim from index.html)
  - `newId(): string` — unique, e.g. time + random base36
  - `makeShape({profile, height, notches = [], corners = 'rund', lump = {size:'mittel', form:'kegel'}}): Shape` → `{version: 1, profile: number[], height, notches: number[], corners, lump}` (deep copies)
  - `canEdit(entry): boolean` — true iff `entry.id` and `entry.shape?.version >= 1` and `entry.shape.profile.length === RINGS`
  - `upsertEntry(gallery: Entry[], entry: Entry, editId: string|null): Entry[]` — new array; if an element has `id === editId` replace it at the same index, else prepend; cap at `MAX_WORKS`
  - Entry shape: `{id, img, glaze, date, shape}`

- [ ] **Step 1: Write failing tests** in `tests/pottery.test.js` (`const P = require('../pottery.js')`, `node:test`, `node:assert/strict`):
  - `defaultProfile` has length 28, first ≈0.95, last ≈0.60.
  - `makeShape` returns `version 1`, copies arrays (mutating input afterwards doesn't change result).
  - `canEdit`: false for `{img, glaze, date}` (old entry), false without `id`, true for `{id:'a', shape: makeShape({profile: defaultProfile(), height:1})}`.
  - `upsertEntry` with matching `editId` keeps length and position (replace middle of 3 → index 1 has new img).
  - `upsertEntry` with `editId` not present (original removed) → prepends, length +1.
  - `upsertEntry` with 30 entries and no editId → length stays 30, new one first.
  - `newId` twice → different strings.
- [ ] **Step 2: Run** `node --test tests/` → FAIL (`Cannot find module '../pottery.js'`).
- [ ] **Step 3: Implement `pottery.js`** as an IIFE that builds the object, assigns `window.Pottery` when `window` exists and `module.exports` when `module` exists. Add the script tag in `index.html`; replace the local `RINGS/MINR/MAXR/defaultProfile` definitions with `const { RINGS, MINR, MAXR, defaultProfile } = Pottery;` (keep `CLAY` local).
- [ ] **Step 4: Run** `node --test tests/` → all pass. Load the page once in Playwright (start screen shows „Ton auf die Scheibe legen“, no `pageerror`).
- [ ] **Step 5: Commit** `feat(galerie): add pottery.js with gallery data model (#1)`

### Task 2: „Weiter töpfern“ — edit and replace gallery works (#1)

**Files:**
- Modify: `index.html` (Component state/fields, `snapshot`/`undo`, `startNew`, `resetClay`, `saveToGallery`, `goGlaze`, gallery card markup)
- Create: `tests/e2e/smoke.py` (Playwright; one function per flow, `main()` runs all, exits non-zero on failure, prints `PASS <name>` per flow)

**Interfaces:**
- Consumes: `Pottery.makeShape`, `canEdit`, `upsertEntry`, `newId`.
- Produces (Component, used by Tasks 3/5/6/7):
  - fields `profile`, `height`, `notches: number[]`, `corners: string`, `lump: {size, form}`, `editId: string|null`, `preferredGlaze: string|null`
  - `snapshot()` pushes `{p, h, n, c, l, e}` (profile, height, notches, corners, lump, editId — all copied); `undo` restores all six and calls `refresh()` + `forceUpdate()`
  - `currentShape(): Shape` → `Pottery.makeShape({...})` from those fields
  - `loadWork(entry)` — sets fields from `entry.shape`, `editId = entry.id`, `preferredGlaze = entry.glaze`, `history = []`, resets material, `screen: 'wheel'`, `glaze: null`, `fired: false`, `spinning: true`
  - gallery item view-model gains `canEdit: boolean` and `edit: () => this.loadWork(entry)`

- [ ] **Step 1: Write failing e2e flows** in `tests/e2e/smoke.py`:
  - `edit_replaces`: start → „Fertig – Glasieren →“ → pick „Kobalt“ → „In den Ofen →“ → wait for „In die Galerie stellen“ → click; assert 1 card. Click „Weiter töpfern“; assert step label „An der Scheibe“. Click „▲ Höher ziehen“, go glaze; assert „Kobalt“ button has the selected border color `rgb(180, 94, 58)`. Fire, save; assert still 1 card and `JSON.parse(localStorage['toepfern.galerie'])[0].shape.height > 1`.
  - `old_entry`: seed `localStorage['toepfern.galerie']` with one old-style entry `{img:'data:,', glaze:'Honig', date:'1. Januar 2026'}` plus one new entry, reload, open gallery; old card has no „Weiter töpfern“, „Entfernen“ on it leaves exactly the new one.
  - `undo_keeps_link`: from an edited work click „Neuer Tonklumpen“, then „↶ Rückgängig“, glaze, fire, save → card count unchanged.
- [ ] **Step 2: Run** `python3 tests/e2e/smoke.py` (server + memory cap per Global Constraints) → FAIL (no „Weiter töpfern“).
- [ ] **Step 3: Implement** the Interfaces above. Card markup: „Weiter töpfern“ primary-style button above „Entfernen“, wrapped in `<sc-if value="{{ w.canEdit }}">`. `saveToGallery` builds `{id: Pottery.newId(), img, glaze, date, shape: this.currentShape()}`, stores `Pottery.upsertEntry(s.gallery, w, this.editId)`, then `editId = w.id`. `startNew` and `resetClay` set `editId = null`, `notches = []`, `corners = 'rund'` (`resetClay` snapshots first, so undo restores the link). `goGlaze` preselects `preferredGlaze` via `setGlaze` if no glaze is chosen. Keep the existing quota `try/catch`.
- [ ] **Step 4: Run** `node --test tests/` and the smoke script → all PASS.
- [ ] **Step 5: Commit** `feat(galerie): continue editing gallery works (#1)`

### Task 3: „← Zurück zu meinem Stück“ (#1)

**Files:**
- Modify: `index.html` (state `returnScreen`, `goGallery`, `startFire` timer end, gallery header markup)
- Modify: `tests/e2e/smoke.py`

**Interfaces:**
- Consumes: Task 2 fields.
- Produces: state `returnScreen: null | 'wheel' | 'glaze' | 'firing' | 'done'`; handler `backToWork()`.

- [ ] **Step 1: Write failing e2e flows:**
  - `back_from_wheel`: start → „▲ Höher ziehen“ → header „Galerie“ → assert „← Zurück zu meinem Stück“ visible → click → step label „An der Scheibe“; glaze, fire, save → stored `shape.height > 1` (the change survived the detour).
  - `back_during_firing`: start fire → immediately header „Galerie“ → wait 8 s → assert still on gallery (heading „Meine Werke“) → click back → step label „Fertig“.
  - `no_back_after_save`: save a work → gallery shows no back button.
- [ ] **Step 2: Run** smoke → FAIL.
- [ ] **Step 3: Implement:** `goGallery` sets `returnScreen` to the current screen when it is one of the four work screens. Save, `startNew` and `loadWork` set `returnScreen: null`. Fire timer end: if `screen === 'firing'` go to `'done'` as today, else set `fired: true` and `returnScreen: 'done'`. Back button (`min-height:72px`, secondary style) at the top of the gallery header row, shown via `<sc-if value="{{ hasReturn }}">`.
- [ ] **Step 4: Run** smoke + unit → PASS.
- [ ] **Step 5: Commit** `feat(galerie): return to the unsaved piece from the gallery (#1)`

### Task 4: Natürlicherer Klang (#3)

**Files:**
- Modify: `pottery.js`, `tests/pottery.test.js`
- Modify: `index.html` (`startSound`, `stopSound`, `pointermove`, `toggleSpin`)

**Interfaces:**
- Produces: `Pottery.rubGain(speed: number /* px per second */): number` — 0 for speed ≤ 20, monotonic non-decreasing, saturates at exactly `0.12` for speed ≥ 1200; `Pottery.MOTOR_GAIN = 0.045`.
- Component: `startSound()` builds the graph once; `setRub(speed)`; `setMotor(on)`; `stopSound()` fades both to 0 (time constant 0.3 s), no hard cut.

- [ ] **Step 1: Write failing unit tests** for `rubGain`: `rubGain(0) === 0`, `rubGain(20) === 0`, `rubGain(300) > 0`, `rubGain(300) <= rubGain(600)`, `rubGain(5000) === 0.12`, never NaN for negative input (→0).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `rubGain` (smoothstep between 20 and 1200 scaled to 0.12). Audio graph (one shared looping 2 s white-noise buffer):
  - Motor: noise → bandpass 140 Hz, Q 0.8 → gain (`MOTOR_GAIN` when spinning) → amplitude wobble: a 0.115 Hz sine LFO with depth 0.25 × MOTOR_GAIN added to the gain param → destination. Plus a very quiet 50 Hz triangle → lowpass 120 Hz → gain 0.012 when spinning. Spin on/off ramps with time constant 0.6 s.
  - Rub: noise → bandpass 900 Hz, Q 0.6 → lowpass 2500 Hz → gain; a 0.7 Hz sine LFO (depth 0.3 × current target) for the „wet“ flutter. In `pointermove` (shape mode) compute speed from the move delta and time delta; `setRub(speed)` does `cancelScheduledValues(t)`, `setTargetAtTime(rubGain(speed), t, 0.05)`, then `setTargetAtTime(0, t + 0.12, 0.2)` so holding still fades out. Pointer up → `setRub(0)`.
  - Default still off; „Klang an/aus“ toggles unchanged.
- [ ] **Step 4: Run** unit → PASS; page loads without `pageerror`; toggling „Klang an“ with a drag raises no console error (Playwright). Final sound judgement is the user's on the iPad.
- [ ] **Step 5: Commit** `feat(klang): softer motor hum and speed-dependent clay rub (#3)`

### Task 5: Ausgangsklumpen wählen (#4)

**Files:**
- Modify: `pottery.js`, `tests/pottery.test.js`
- Modify: `index.html` (start screen markup, wheel panel, `startNew`, `resetClay`, state `lumpSize`, `lumpForm`, `pickingLump`)
- Modify: `tests/e2e/smoke.py`

**Interfaces:**
- Produces: `Pottery.lumpShape(size: 'klein'|'mittel'|'gross', form: 'kugel'|'kegel'): {profile: number[], height: number}`
  - `('mittel','kegel')` equals `{profile: defaultProfile(), height: 1}`
  - size scales radii by `klein 0.75 / mittel 1 / gross 1.25` and height `0.7 / 1 / 1.3`
  - `kegel` is monotonically non-increasing bottom→top; `kugel` has its widest ring at an index in 8…20 and top radius ≥ 0.35
  - all radii within `[0.2, MAXR]`, height within `[HMIN, HMAX]`
- Component: `startNew(size, form)` and the lump picker set `this.lump = {size, form}`.

- [ ] **Step 1: Write failing unit tests** for the `lumpShape` rules above (all 6 combinations for the range checks).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `lumpShape`. UI:
  - Start screen: above „Ton auf die Scheibe legen“ two rows of big toggle buttons — „Klein · Mittel · Gross“ and „Kugel · Kegel“ (selected = `#B45E3A` 3 px border), defaults Mittel + Kegel; the main button starts with the selection.
  - Wheel panel: „Neuer Tonklumpen“ sets `pickingLump: true`, which swaps the panel content for the same two rows plus „Ton auflegen“ (snapshot, apply lump, `editId = null`, notches/corners reset, `pickingLump: false`) and „Abbrechen“.
  - Gallery „Neues Stück beginnen“ and „Fertig“'s new-piece button go to the start screen so the lump can be chosen.
- [ ] **Step 4: Run** unit → PASS; add e2e flow `lump_choice` (choose Gross + Kugel → wheel; „Neuer Tonklumpen“ → Klein → „Ton auflegen“ → „Rückgängig“ works without error) and run smoke → PASS. Update Task 2/3 flows if their entry path changed.
- [ ] **Step 5: Commit** `feat(scheibe): choose the starting clay lump (#4)`

### Task 6: Mesh with corners and notches (#2)

**Files:**
- Modify: `pottery.js`, `tests/pottery.test.js`
- Modify: `index.html` (`buildGeo` uses `Pottery.buildMesh`)

**Interfaces:**
- Produces on `Pottery`:
  - `CORNERS = ['rund','oval','dreieckig','viereckig']`, `NOTCH_DEPTH = 0.18`, `NOTCH_HALF_WIDTH = 0.22` (rad), `NOTCH_MIN_GAP = 0.25` (rad), `MAX_NOTCHES = 8`
  - `cornerFactor(mode: string, angle: number): number` — `rund` → 1; `oval` → `1 + 0.18*cos(2θ)`; `dreieckig`/`viereckig` → blend `0.4 + 0.6 * polygon(n)` where `polygon(n)(θ) = cos(π/n) / cos(((θ mod 2π/n) − π/n))`, normalised so the mean over a full turn is 1 ± 0.02
  - `rimDrop(notches: number[], angle: number): number` — max over notches of `NOTCH_DEPTH * (1 + cos(π·d/NOTCH_HALF_WIDTH))/2` for angular distance `d < NOTCH_HALF_WIDTH` (distance wraps at 2π), else 0
  - `addNotch(notches: number[], angle: number): number[]` — new array; angle normalised to [0, 2π); unchanged if within `NOTCH_MIN_GAP` of an existing one or already `MAX_NOTCHES`
  - `angleOf(x: number, z: number): number` — `atan2(x, z)` normalised to [0, 2π) (mesh uses `x = r·sin θ`, `z = r·cos θ`, like `LatheGeometry`)
  - `outline(profile, height): [r, y][]` — the exact point list today's `buildGeo` feeds to `LatheGeometry` (outer wall up, inner wall down, floor)
  - `buildMesh(shape: Shape, segments = 72): {positions: Float32Array, uvs: Float32Array, indices: number[]}` — for each of `segments+1` angles and each outline point: radius `r·cornerFactor(corners, θ)`; height remapped inside the top band `band = 0.35`: if `y > H − band` then `y' = (H − band) + (y − (H − band))·(band − drop)/band` with `H = 2·height`, `drop = rimDrop(notches, θ)`. UVs as LatheGeometry (`u = i/segments`, `v = j/(points−1)`); index layout as LatheGeometry.
- Component: `buildGeo()` → `BufferGeometry` from `buildMesh(this.currentShape())`, then `computeVertexNormals()`.

- [ ] **Step 1: Write failing unit tests:**
  - `cornerFactor('rund', any) === 1`; mean of each mode over 720 samples within 0.02 of 1; `viereckig` has 4 local maxima over a turn, `dreieckig` 3.
  - `rimDrop([], θ) === 0`; `rimDrop([1], 1) ≈ NOTCH_DEPTH`; `rimDrop([0.05], 2π − 0.05) > 0` (seam).
  - `addNotch` dedupe within 0.25 rad, max 8, normalises `-0.5` to `2π − 0.5`.
  - `angleOf(1, 0) ≈ π/2`, `angleOf(0, 1) === 0`, `angleOf(0, -1) ≈ π`.
  - `buildMesh(makeShape({profile: defaultProfile(), height: 1}))`: positions length `= (73 · outline.length) · 3`, no NaN; max y = 2. With `notches: [0]`: max y of vertices at θ = 0 is `2 − NOTCH_DEPTH` (± 1e-6) while at θ = π it is 2. With `corners: 'viereckig'` plus `notches: [0, 6.2]`: no NaN.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** the functions; switch `buildGeo` to the new mesh. With `rund` and no notches the pot must look the same as before.
- [ ] **Step 4: Run** unit → PASS; Playwright screenshot of the wheel matches today's look (visual check), no `pageerror`.
- [ ] **Step 5: Commit** `feat(werkzeuge): build pot mesh with corners and rim notches (#2)`

### Task 7: Werkzeug mode UI (#2)

**Files:**
- Modify: `index.html` (wheel panel markup, `pointerdown`, state `tool: false`, `spinBeforeTool`, hint text)
- Modify: `tests/e2e/smoke.py`, `README.md` (Controls section)

**Interfaces:**
- Consumes: `Pottery.addNotch`, `angleOf`, `CORNERS`, Task 2 `snapshot`/`currentShape`.
- Produces: handlers `setToolMode(on: boolean)`, `setCorners(mode: string)`, `notchAt(event)`.

- [ ] **Step 1: Write failing e2e flow** `tools`: on the wheel click „Werkzeug“ → assert spin label reads „▶ Scheibe drehen“ (wheel stopped) and the four buttons „Rund“, „Oval“, „Dreieckig“, „Viereckig“ exist; click „Viereckig“; click on the pot's rim (canvas point at the top edge of the pot in the default camera — compute from a `getBoundingClientRect` of the canvas, upper-middle area); click „Formen“ → spin label back to „⏸ Scheibe anhalten“; glaze, fire, save; assert stored `shape.corners === 'viereckig'` and `shape.notches.length === 1`; „Weiter töpfern“ → „Rückgängig“ is harmless; then in Werkzeug mode „Rückgängig“ after a corner change restores `'rund'` (assert by saving again and reading storage).
- [ ] **Step 2: Run** smoke → FAIL.
- [ ] **Step 3: Implement:**
  - Panel top: two big toggle buttons „Formen“ | „Werkzeug“ (selected = primary color). In Werkzeug mode the shaping buttons (Höher/Niedriger/Zufällige Form) are replaced by the four corner buttons (2×2 grid, selected border) and a hint „Tippen Sie auf den Rand, um eine Kerbe zu machen.“; „Rückgängig“ stays visible in both modes.
  - Entering Werkzeug: remember `spinning`, set `spinning: false`; leaving restores it.
  - `pointerdown` in Werkzeug mode: raycast the pot; hit with local `y > 2·height − 0.5` → `snapshot()`, `notches = addNotch(notches, angleOf(local.x, local.z))`, `refresh()`; otherwise orbit as today. Local point via `this.pot.worldToLocal(hit.point.clone())`.
  - `setCorners(mode)`: `snapshot()`, set, `refresh()`.
  - README Controls: add „Werkzeug“ mode (tap rim = notch; corner buttons) and the lump choice.
- [ ] **Step 4: Run** unit + full smoke → PASS; Playwright screenshot of a square pot with two notches, glazed — check it visually.
- [ ] **Step 5: Commit** `feat(werkzeuge): tool mode with rim notches and corner shapes (#2)`
