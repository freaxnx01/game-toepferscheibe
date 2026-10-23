# Nasser Glanz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unfired clay shines wet, subtly, where it is being shaped. The shine dries back to matt within a few seconds (#7).

**Architecture:** A per-ring wetness array `this.wet` (length `RINGS`) holds the state. Shaping wets the touched ring and its neighbours, and every frame dries all rings. Because the wheel spins, a whole ring is wet, which matches the real effect. The pure logic lives in `pottery.js`. `index.html` turns wetness into a per-vertex `wet` attribute that a small `onBeforeCompile` patch on the clay material reads to lower roughness locally.

**Tech Stack:** Buildless static page, three.js 0.160 (`MeshStandardMaterial`), node:test, Playwright e2e (Python).

**Spec:** Issue #7 body, plus the decisions the user made in the interview on 2026-10-23:
- **Where:** the shine appears only where the clay is being shaped (finger + water). There are no random spots.
- **Drying:** without touch, a spot goes matt again in about 5–8 s. Shaping wets it again.
- **Strength:** subtle. The clay must still read as clay, not as glaze.
- From the issue: fired or glazed clay never shines wet.

## Global Constraints

- Use Test-Driven Development for every task: write a failing test first, watch it fail, implement minimally to pass, verify green.
- Run e2e under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`. Run a single flow with `FLOW=<name>`.
- Values:
  - `WET_DRY_MS = 6500` (full wet → dry, linear)
  - `WET_RATE = 1 / 250` per ms while shaping, so a ring is fully wet after about 0.25 s of contact
  - neighbour falloff: ring ±1 gets 0.6×, ring ±2 gets 0.25×
  - dry roughness stays `0.95`; fully wet roughness is `0.45` (subtle)
- Wetness is cosmetic state only. It is **not** part of `makeShape`, the gallery, or the undo history.
- Code style: match `pottery.js`, which uses dense one-line arrow functions, and add the new names to `api`.

## Review Focus

- Glazing: on `glaze`/`firing`/`done` screens the wet shine must be gone at once, not drying slowly. Glaze roughness values must not be multiplied by stale wetness.
- New piece / „Weiter töpfern“ / „Ton zurücksetzen“ / undo start dry.
- Gallery snapshot (`saveToGallery`) is taken without wet shine.
- Orbit (dragging off the pot) and the notch tool do not wet anything.
- Performance: drying only touches the GPU attribute while some ring is still > 0. An idle dry pot costs nothing per frame.

---

### Task 1: Wet shine while shaping

**Files:**
- Modify: `pottery.js` (new pure functions + `api`)
- Modify: `index.html` (material patch, `buildGeo` attribute, `flowTick`/`tick`, resets)
- Test: `tests/pottery.test.js`, `tests/e2e/smoke.py` (new flow `wet_shine`)

**Interfaces (pottery.js, all exported via `api`):**
- `WET_DRY_MS`, `WET_RATE`: the constants above.
- `wetStep(wet: number[], idx: number|null, dtMs: number) => boolean`: mutates `wet` in place.
  - First all rings dry by `dtMs / WET_DRY_MS`, clamped at 0.
  - Then, if `idx` is an integer in range, ring `idx` gains `dtMs * WET_RATE`, ring ±1 gains 0.6× of that and ring ±2 gains 0.25×. All values are clamped at 1.
  - Returns `true` if any value changed.
  - With a non-finite or non-positive `dtMs`, it returns `false` and changes nothing.
- `wetRoughness(w: number) => number`: `0.95 - 0.5 * clamp(w, 0, 1)`.
- `outlineRings(profile, height) => number[]`: for each point of `outline(profile, height)`, the ring index it belongs to. Outer wall point i → i. Inner wall point at ring i → i. The axis and floor points → 0. Its length must equal `outline(...).length`.

**index.html:**
- `this.wet = new Array(RINGS).fill(0)`.
- Reset `this.wet` to all 0 (`dryAll()`) in `startNew`, `loadWork`, `resetClay`, undo, and when leaving the wheel screen for glaze (the transition into `screen: 'glaze'`).
- `buildGeo` adds a float attribute `wet`. For each vertex it is `this.wet[rings[j]]`, using `outlineRings` per outline point j and repeated for every segment.
- Add a helper `syncWet()` that rewrites the attribute values in place and sets `needsUpdate`, without rebuilding the geometry.
- Clay material `onBeforeCompile`:
  - declare `attribute float wet; varying float vWet;` and set `vWet = wet;` in the vertex shader
  - in the fragment shader, after `#include <roughnessmap_fragment>`, add `roughnessFactor = mix(roughnessFactor, roughnessFactor * (0.45 / 0.95), vWet);`
  - the result for clay: 0.95 dry, 0.45 fully wet
  - glazed materials only see `vWet = 0`, because wetness is cleared before glazing
- Wetting comes from shaping only:
  - In `flowTick`, while shaping is active (the same guard as now), compute `idx` and call `wetStep(this.wet, idx, dt)`.
  - Otherwise, while any ring is > 0, call `wetStep(this.wet, null, dt)`.
  - Call `syncWet()` only when `wetStep` returns true.
- Expose the maximum wetness for tests as `data-wet` on the mount element, rounded to 2 decimals, and update it only when it changes.

- [ ] **Step 1: Failing unit tests** in `tests/pottery.test.js`:
  - `wetStep` with idx 10 and dt 250 on a zero array → `wet[10] === 1`, `wet[9]` ≈ 0.6 (±0.01), `wet[12]` ≈ 0.25 (±0.01), `wet[13] === 0`, returns true.
  - Drying: a wet[5]=1 array after 3250 ms with idx null → ≈ 0.5. After a further 4000 ms → 0. When already 0, it returns false.
  - Edges: idx 0 and idx RINGS-1 do not throw or write out of range. A dt of 0, NaN or a negative value returns false and leaves the array unchanged.
  - `wetRoughness(0) === 0.95`, `wetRoughness(1)` ≈ 0.45, `wetRoughness(2)` ≈ 0.45.
  - `outlineRings(p, h).length === outline(p, h).length` for the default profile at heights 0.35, 1 and 1.6. Every value is an integer in [0, RINGS-1]. Index 1 → 0 and index RINGS → RINGS-1, because the outer wall points are `pts[1..RINGS]`.
- [ ] **Step 2: Failing e2e** `wet_shine`:
  - Start a piece and read `data-wet` on the mount: it is `0`.
  - Drag on the pot for about 0.5 s: it becomes ≥ 0.8.
  - Wait 8 s without touching: it is `0`.
  - Drag again, then go straight to the glaze screen: it is `0` at once.
  - Pick „Neues Stück beginnen“ / start: it is `0`.
  - No page errors.
  - Reuse the existing drag helpers in `smoke.py`.
- [ ] **Step 3: Implement** (`pottery.js` first, then `index.html`) and get both green.
- [ ] **Step 4:** Run the full suite (unit + all e2e flows) green. Check visually with one Playwright screenshot while dragging and one after drying, saved to the scratchpad and not committed. The wet ring must look subtly shiny, not like glaze.
- [ ] **Step 5: Commit** `feat(ton): nasser Glanz beim Formen, trocknet ab (#7)`, then `docs: CHANGELOG Unreleased (#7)` with an `## [Unreleased]` entry „Nasser Glanz: Der Ton glänzt beim Formen stellenweise nass und trocknet in einigen Sekunden ab (#7).“ Add trailers to both.
