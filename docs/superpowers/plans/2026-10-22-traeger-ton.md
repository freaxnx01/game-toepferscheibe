# Träger Ton (#6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clay flows toward the finger at a steady time-based rate (≈95 % in 3 s) instead of jumping 50 % per pointer event.

**Architecture:** Pure math (`FLOW_TAU`, `flowFactor`, `flowStep`) in `pottery.js`, unit-tested with `node --test`. `index.html` pointer handlers only record a target; the existing rAF `tick` applies `flowStep` each frame while shaping.

**Tech Stack:** Buildless static page (dc document), three.js 0.160, `pottery.js` UMD-style module (`Pottery` global / `require`), Node test runner, Playwright (Python) e2e.

**Spec:** docs/superpowers/specs/2026-10-22-traeger-ton-design.md

## Global Constraints

- Use Test-Driven Development for every task: write a failing test first, watch it fail, implement minimally to pass, verify green.
- `FLOW_TAU = 1000` ms; per-frame `dt` clamped to at most 100 ms.
- Gaussian window unchanged: k = -3..3, w = exp(-k²/4); ring 0 and indices ≥ RINGS untouched; target radius clamped to [0.2, MAXR].
- Undo: one snapshot per stroke (pointerdown), as today.
- No new UI. Remove the `clayStrength` prop (from `data-props` and all uses). `wheelSpeed` stays.
- Every commit references #6 and ends with:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01XGbh4Q7kL37T591fox7aK3`
- e2e must run under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 python3 tests/e2e/smoke.py` (single flow: `FLOW=<name>`). Never pkill broadly; kill leftover http.server/chrome by PID only.

## Review Focus

1. Finger held still on the clay → wall keeps moving toward it (the core new behaviour) — e2e `sluggish` covers it.
2. Fast swipe → small change only — e2e `sluggish`.
3. Releasing / switching screen (gallery, glaze, lump picker, tool mode) mid-stroke → flow stops, no further change — the `tools` flow's "drag in tool mode must not shape" / picker asserts must stay green.
4. Background tab / long frame → no jump (dt clamp) — unit test on `flowFactor(100)` vs clamp in caller.
5. Two-finger shaping still works (target = midpoint height, half distance).

---

### Task 1: Pure flow math in pottery.js

**Files:**
- Modify: `pottery.js` (add to the module and to `api`)
- Test: `tests/pottery.test.js`

**Interfaces:**
- Produces: `FLOW_TAU` (number, 1000); `flowFactor(dtMs: number) -> number` = `1 - exp(-dtMs / FLOW_TAU)`, returns 0 for dt ≤ 0 or non-finite; `flowStep(profile: number[], idx: number, radius: number, f: number) -> void` mutates `profile` in place: clamps `radius` to [0.2, MAXR], for k in -3..3, j = idx + k, skip j < 1 or j ≥ RINGS, `profile[j] += (r - profile[j]) * exp(-k*k/4) * f`. No-op if idx < 1 or idx ≥ RINGS.

- [ ] **Step 1: failing tests** `test('flowFactor', …)`: `flowFactor(0) === 0`, `flowFactor(-5) === 0`, `flowFactor(NaN) === 0`, `flowFactor(16) < 0.02`, `flowFactor(3000) >= 0.95`, `flowFactor(500) < flowFactor(1000)`, `FLOW_TAU === 1000`. `test('flowStep', …)`: on `defaultProfile()` with idx 10, radius 1.5, f 0.5 → `p[10]` moved exactly half-way (`old + (1.5-old)*0.5`), `p[11]` by `exp(-1/4)*0.5`, `p[14]` unchanged, `p[0]` unchanged for idx 1; radius 99 clamps to MAXR; idx 0 and idx RINGS are no-ops; f 0 leaves profile identical.
- [ ] **Step 2:** `node --test` → new tests FAIL (not a function).
- [ ] **Step 3:** implement in `pottery.js`, export via `api`.
- [ ] **Step 4:** `node --test` → all pass.
- [ ] **Step 5:** commit `feat(scheibe): zeitbasierte Fliess-Mathematik für trägen Ton (#6)`.

### Task 2: Wire the flow into index.html + e2e

**Files:**
- Modify: `index.html` (`applyAt` ~l.349–354, pointer handlers ~l.356–378, `tick` ~l.251, `data-props` l.181)
- Test: `tests/e2e/smoke.py` (new flow `sluggish`, add to `FLOWS`)

**Interfaces:**
- Consumes: `Pottery.FLOW_TAU`, `Pottery.flowFactor`, `Pottery.flowStep` (Task 1).
- Produces: `this.shapeTarget = { y, r } | null`; `applyAt(y, radius)` now only sets `shapeTarget`; new `flowTick(dtMs)` called from `tick` with real frame dt clamped to 100 ms — when `this.mode === 'shape'`, pointers held, `shapeTarget` set and screen is the wheel without picker/tool, maps y → idx exactly like today's `applyAt`, calls `flowStep(this.profile, idx, r, flowFactor(dt))`, then `this.refresh()`. `shapeTarget` cleared in the pointerup/cancel handler when no pointers remain and on pointerdown.

- [ ] **Step 1: failing e2e** `sluggish(b, url)`: lay clay; quick swipe outward on the pot (≈150 ms, a few moves) then release; finish (glaze/fire/save via existing helpers) and read `gallery(page)[0]['shape']['profile']`; max |Δ| vs `Pottery.lumpShape('mittel','kegel').profile` is **> 0 and < 0.25 of** the Δ reached by the hold. Then „Weiter töpfern“, press at the same point and **hold still 3.5 s** (`page.wait_for_timeout`) before releasing, save again: max |Δ| clearly larger (≥ 0.15 world units). Exact point/threshold tuning is the implementer's call; keep it deterministic.
- [ ] **Step 2:** `FLOW=sluggish …smoke.py` → FAIL (hold adds nothing today / swipe changes too much).
- [ ] **Step 3:** implement as in Interfaces; remove `clayStrength` from `data-props` and code.
- [ ] **Step 4:** full suite (13 flows) green + `node --test` green.
- [ ] **Step 5:** commit `feat(scheibe): Ton fliesst träge zum Finger statt zu springen (#6)` and README controls line if it describes shaping speed (English).
