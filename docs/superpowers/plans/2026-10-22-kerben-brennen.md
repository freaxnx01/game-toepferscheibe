# Kerben-Hinweis & Brenn-Schritte Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make rejected notch taps visible and raise the notch limit (#9); keep all firing steps on screen and continue only by button (#10).

**Architecture:** Pure logic lives in `pottery.js` (exported via `api`, tested with `node --test`); `index.html` wires it into the dc component (`setState` / `renderVals`). e2e flows in `tests/e2e/smoke.py` drive the real page.

**Tech Stack:** Buildless static page, three.js 0.160, node:test, Playwright (Python).

**Spec:** Issues #9 and #10 (bodies are the spec). Decisions made in session (controller's calls, recorded here):
- `MAX_NOTCHES` 8 → **16** (rim fits ~25 at 0.25 rad gap; 16 keeps room between notches).
- Rejection hint texts (game copy uses „Sie“): full → **„Mehr Kerben passen nicht auf den Rand.“**; too close → **„Zu nah an einer Kerbe – tippen Sie etwas daneben.“** Shown in the existing bottom hint box for **3 s**, then the normal tool hint returns.
- Lost `pointerup` safety: also treat `lostpointercapture` like `pointerup`.
- Firing: steps list, no auto-switch; button **„Stück herausnehmen →“** appears at 100 % and goes to `done`.

## Global Constraints

- Use Test-Driven Development for every task: write a failing test first, watch it fail, implement minimally to pass, verify green.
- Heavy jobs (e2e) run under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`.
- Match surrounding code style: dense one-liners, inline styles, colours from the existing palette (`#B45E3A`, `#4D3B2D`, `#6E5A4A`, `#D9C9B2`, `#FBF6EC`).
- German UI copy with real umlauts, polite „Sie“ like the existing game text.
- Never use `git stash`.

## Review Focus

- Tapping the rim when 16 notches exist → hint „Mehr Kerben passen nicht …“, no snapshot pushed to undo history.
- Tap within 0.25 rad of an existing notch after spinning → „Zu nah …“ hint, not silence.
- Leaving the firing screen (gallery / start) mid-firing and returning after it finished → lands on the firing screen showing all steps done plus the button, not stuck and not auto-jumped.
- Kiln glow overlay must stop once firing is complete (screen stays `firing`).
- Undo after a rejected notch tap must not undo an earlier real notch twice (no stray snapshot).

---

### Task 1: Notch limit 16 + visible rejection hint (#9)

**Files:**
- Modify: `pottery.js` (constants l.23, `addNotch` l.28–33, `api` l.66)
- Modify: `index.html` (`notchAt` ~l.288, pointer binding ~l.358–381, `renderVals` hint ~l.471)
- Test: `tests/pottery.test.js`, `tests/e2e/smoke.py` (`tools` flow or a new `notch_hint` flow)

**Interfaces:**
- Produces: `Pottery.notchBlock(notches: number[], a: number) => 'full' | 'near' | null` — why a notch at angle `a` would be refused (`'full'` checked first). `addNotch` uses it; behaviour otherwise unchanged. `MAX_NOTCHES === 16`.

- [ ] **Step 1: Failing unit tests** — in `tests/pottery.test.js`:
  - `assert.equal(P.MAX_NOTCHES, 16)`; the existing `addNotch` loop test fills 0.5 rad steps — extend it to 20 iterations so it still hits the cap (12 × 0.5 < 2π gives only 12 slots: use `i * 0.3` for 30 iterations and assert length 16).
  - `notchBlock([1], 1.1) === 'near'`, `notchBlock([1], 2) === null`, a 16-entry list → `'full'` even for a far angle, `notchBlock([], 0) === null`, wrap-around: `notchBlock([0.1], TAU - 0.05) === 'near'`.
- [ ] **Step 2:** `node --test` → the new assertions FAIL.
- [ ] **Step 3: Implement** `notchBlock` in `pottery.js`, export it, set `MAX_NOTCHES = 16`, make `addNotch` return `[...notches]` iff `notchBlock` is non-null.
- [ ] **Step 4:** `node --test` → all pass.
- [ ] **Step 5: UI** — in `notchAt`, after the rim hit check, call `Pottery.notchBlock`; if non-null set a transient hint (state field e.g. `notchMsg`, cleared by a `setTimeout` of 3000 ms that is cleared/replaced on each new message and on unmount) and return without `snapshot()`. In `renderVals`, when `s.tool && s.notchMsg` show `notchMsg` instead of the tool hint. Clear `notchMsg` when leaving tool mode. Add `el.addEventListener('lostpointercapture', up)` next to `pointerup`/`pointercancel`.
- [ ] **Step 6: e2e first-red then green** — add flow `notch_hint` to `tests/e2e/smoke.py` (and to `FLOWS`): place a notch at `rim_point(page, 0.0)`, tap the same spot again, `wait_text(page, 'Zu nah an einer Kerbe')`. Run it red against the unmodified `index.html` if feasible (or note that the text cannot appear before Step 5), then green: `FLOW=notch_hint systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 python3 tests/e2e/smoke.py`. Also run `FLOW=tools`.
- [ ] **Step 7: Commit** `fix(werkzeuge): Kerben-Limit 16 und Hinweis bei abgelehnter Kerbe (#9)`.

### Task 2: Firing steps as a list, continue by button (#10)

**Files:**
- Modify: `pottery.js` (add + export `fireSteps`)
- Modify: `index.html` (firing panel l.125–134, kiln overlay l.57, `startFire` ~l.444–455, `renderVals` ~l.465–495)
- Test: `tests/pottery.test.js`, `tests/e2e/smoke.py` (`glaze_fire_save`, `edit_replaces`, `done_then_start`, `back_during_firing`)

**Interfaces:**
- Produces: `Pottery.fireSteps(pct: number) => Array<{ text: string, state: 'done' | 'active' | 'todo' }>` with exactly two steps:
  1. „Der Ofen heizt langsam auf. Die Glasur schmilzt und wird glänzend.“ — `active` for pct < 60, else `done`.
  2. „Der Ofen kühlt ab. Gleich können Sie Ihr Stück herausnehmen.“ — `todo` for pct < 60, `active` for 60 ≤ pct < 100, `done` at ≥ 100.

- [ ] **Step 1: Failing unit test** `fireSteps`: states at pct 0, 59, 60, 99, 100 as above; texts equal the two strings above.
- [ ] **Step 2:** `node --test` → FAIL (`fireSteps` undefined).
- [ ] **Step 3: Implement** `fireSteps` in `pottery.js`, export it. `node --test` → pass.
- [ ] **Step 4: UI** —
  - Firing panel: replace the single `{{ fireText }}` paragraph with an `sc-for` over the steps: each row shows a marker (`✓` done, `●` active, `○` todo) and the text; active bold `#4D3B2D`, done `#6E5A4A`, todo muted. Keep progress bar and temperature. At 100 % show a third line „Ihr Stück ist abgekühlt.“ is NOT needed — instead show the primary button „Stück herausnehmen →“ (same style as „In den Ofen →“) only when `firePct >= 100`.
  - `startFire` completion: no screen switch; just `clearInterval`, emissive 0, `setState({ fired: true })`. Remove the `returnScreen: 'done'` branch (returning goes back to `firing`, which now shows the finished list + button).
  - Button handler `takeOut: () => this.setState({ screen: 'done' })`.
  - Kiln overlay (l.57): show only while firing is in progress (`screen === 'firing' && firePct < 100`).
  - Remove `fireText` from `renderVals` if unused.
- [ ] **Step 5: e2e** — update helpers/flows so that after „In den Ofen →“ they `click(page, 'Stück herausnehmen →')` before waiting for „In die Galerie stellen“ / „Fertig gebrannt“ (`glaze_fire_save`, `edit_replaces`, `done_then_start`, `back_during_firing`). In `back_during_firing` additionally assert that after BACK the firing screen shows „Stück herausnehmen →“ and both step texts are visible. Run red before Step 4 is wired if feasible, then green: the full suite `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 python3 tests/e2e/smoke.py` (~10+ min; run in background).
- [ ] **Step 6: Commit** `feat(brennen): alle Brenn-Schritte sichtbar, weiter per Knopf (#10)`.
