# Galerie: 3D-Ansicht und Speicherschutz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the player open a gallery piece large and in 3D (#13), and protect the gallery against Safari's 7-day storage wipe (#5).

**Architecture:**
- **3D view (#13):** a new screen `'view'` reuses the existing renderer and canvas. A second mesh, `this.viewPot` with its own material, is added to `this.group` and shows the selected work. `this.pot`, the work in progress, is hidden but never touched, so going back to the gallery, and from there back to the piece, still works.
- **Storage protection (#5):** a quiet `navigator.storage.persist()` request. A dismissible tip on the start screen, shown only in iOS/iPadOS Safari outside home-screen mode.

**Tech Stack:** Buildless static page (dc document), three.js 0.160, node:test, Playwright e2e (Python).

**Spec:** Issues #13 and #5 plus the user's decisions of 2026-10-24:
- **#13:**
  - Tapping a gallery piece opens it large and glazed. It rotates slowly by itself.
  - The finger can rotate and zoom the view. There is no turntable.
  - Buttons: „← Zurück zur Galerie“ and the existing „Weiter töpfern“.
- **#5:**
  - Request `navigator.storage.persist()`.
  - Show the tip „Zum Home-Bildschirm hinzufügen“ once and make it dismissible. It appears only in Safari when the game is not already running as a home-screen app.
  - No export or import.

## Global Constraints

- Use Test-Driven Development for every task: write a failing test first, watch it fail, implement minimally to pass, verify green.
- Run e2e under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`. Run a single flow with `FLOW=<name>`.
- German UI copy uses real umlauts and addresses the player as „Sie“, like the existing UI. Use large tap targets: buttons ≥ 64px high, text ≥ 20px.
- Match the existing style: inline styles, colours `#B45E3A` / `#FBF6EC` / `#D9C9B2` / `#35261B`, and dense one-line methods.

## Review Focus

- Viewing must never change the work in progress. `profile`, `height`, `notches`, `corners`, `history`, `editId` and the clay material all stay exactly as they were. After „Zurück zur Galerie“ → „← Zurück zu meinem Stück“, the piece and its glaze, firing and wet state are unchanged.
- The view screen never shapes, wets or notches the clay. A drag always orbits.
- Old gallery entries without `shape` (`Pottery.canEdit` false) cannot be opened in 3D. They keep showing only the image, with no broken button.
- When leaving the view, the view geometry is disposed, and the turntable and `this.pot` become visible again.
- The home-screen tip never appears outside iOS/iPadOS Safari or in standalone mode. Once closed, it stays closed. A storage error (private mode) does not break the start screen.

---

### Task 1: 3D-Ansicht eines Galerie-Stücks (#13)

**Files:**
- Modify: `index.html`. Touches:
  - the gallery card (~l.175–188)
  - a new aside panel for `isView`
  - `canvasDisplay`, `syncWheel`, the tick rotation and `goGallery`
- Test: `tests/e2e/smoke.py`, new flow `gallery_view`

**Design:**
- State: `screen: 'view'`, `viewing: <gallery entry>`.
- On open: `openView(w)`.
  - Build the geometry with `Pottery.buildMesh(w.shape)`. Use the same normal-seam fix as `buildGeo`, by extracting a shared helper `geoFrom(shape)` that `buildGeo` also uses.
  - Set the colour and roughness of `this.viewMat` from `GLAZES.find(g => g.name === w.glaze)`. If none matches, as with „Unglasiert“, use `CLAY` with roughness 0.95.
  - Hide `this.pot` and show `this.viewPot`.
  - Reset the camera, turn the motor off, and hide the turntable.
- On close: `closeView()` disposes the view geometry, shows `this.pot` again and lets `syncWheel()` decide about the turntable.
  - It runs on „← Zurück zur Galerie“, and on every other exit from `'view'`: header „Galerie“, „Weiter töpfern“, and start.
  - Simplest: call it in `componentDidUpdate` when the screen changed away from `'view'`.
- Auto-rotation: in `tick`, the group also rotates when `screen === 'view'`, whatever `state.spinning` says.
- `canvasDisplay` includes `'view'`. The `wheel` hint box is not shown.
- `goGallery` from `'view'` keeps the existing `returnScreen`, so „← Zurück zu meinem Stück“ still appears afterwards.
- Gallery card:
  - When `canEdit`, the thumbnail becomes a `<button>` with `aria-label="In 3D anschauen"` and a visible badge „In 3D anschauen“. The badge is at least 20px and sits over the bottom of the image.
  - Without `canEdit`, the image stays as it is.
- Aside panel `isView`:
  - glaze name (heading) and date
  - „← Zurück zur Galerie“ (secondary style)
  - „Weiter töpfern“ (primary, same action `loadWork`, only when `canEdit`)
  - a short hint: „Mit dem Finger ziehen dreht das Stück, mit zwei Fingern zoomen Sie.“

- [ ] **Step 1: Failing e2e `gallery_view`.**
  - Seed two gallery entries via localStorage, the same way `old_entry`/`edit_replaces` do: one entry with `shape` and glaze „Kobalt“, and one old entry without `shape`.
  - Assert:
    - The old card has no „In 3D anschauen“ button. The new card has one.
    - Clicking it shows the heading „Kobalt“ and the button „← Zurück zur Galerie“, and the canvas is visible.
    - A drag on the canvas leaves the gallery in localStorage unchanged and produces no page errors.
    - „← Zurück zur Galerie“ shows „Meine Werke“ again.
    - With a piece in progress: Start → shape → header „Galerie“ → open 3D → back → „← Zurück zu meinem Stück“. The wheel screen shows again and the shape is unchanged. Compare `outline` length or a profile sample exposed the same way existing flows read state. If none exists, compare a canvas screenshot hash before and after, with the motor off.
    - „Weiter töpfern“ in the view opens the wheel screen.
  - Run it and see it FAIL.
- [ ] **Step 2: Implement** as designed above.
- [ ] **Step 3:** The flow is green. Take a screenshot of the view screen into the scratchpad for the controller. Run the full suite green.
- [ ] **Step 4: Commit** `feat(galerie): Stück in 3D anschauen (#13)`.

### Task 2: Speicherschutz (#5)

**Files:**
- Modify: `pottery.js`, which gets a pure helper.
- Modify: `index.html`, for the start screen tip, the persist request and the dismiss storage.
- Test: `tests/pottery.test.js`, `tests/e2e/smoke.py` (new flow `home_hint`)

**Interfaces:**
- `Pottery.needsHomeHint({ ua, maxTouchPoints, standalone, displayStandalone }) => boolean`.
  - It returns true only when all of the following hold:
    - The device is iOS/iPadOS: `/iPhone|iPad|iPod/` in `ua`, or `/Macintosh/` with `maxTouchPoints > 1`, which is how iPadOS appears.
    - The browser is Safari: `/Safari/` in `ua` and none of `/CriOS|FxiOS|EdgiOS/`.
    - `standalone` is not true and `displayStandalone` is not true.

**index.html:**
- Request persistent storage once on mount: `try { navigator.storage && navigator.storage.persist && navigator.storage.persist().catch(() => {}); } catch (e) {}`.
- Start screen:
  - When `needsHomeHint(...)` and `localStorage['toepfern.homehint'] !== 'aus'`, show a calm box. Its text: „Tipp: Damit Ihre Werke sicher gespeichert bleiben, legen Sie das Spiel auf den Home-Bildschirm: Tippen Sie in Safari auf das Teilen-Symbol und dann auf „Zum Home-Bildschirm“.“
  - The box has a button „Verstanden“ (≥ 64px). It sets the key to `'aus'`, with try/catch, and hides the box.
  - Inputs for `needsHomeHint`: `navigator.userAgent`, `navigator.maxTouchPoints`, `navigator.standalone`, `matchMedia('(display-mode: standalone)').matches`.

- [ ] **Step 1: Failing unit tests** for `needsHomeHint`:
  - an iPad Safari UA → true
  - a Mac UA with maxTouchPoints 5 → true
  - a Mac UA with 0 → false
  - an iPhone CriOS UA → false
  - iPad Safari with `standalone: true` → false
  - with `displayStandalone: true` → false
  - a desktop Chrome UA → false
- [ ] **Step 2: Failing e2e `home_hint`.**
  - Use a context with an iPad Safari user agent, `has_touch`, and an init script that sets `maxTouchPoints`.
  - The start screen shows „Tipp:“ and „Verstanden“. Click it, and the tip is gone. After a reload it stays gone.
  - The default (desktop) context never shows „Tipp:“. Check this in the existing start-screen flow or the same flow.
- [ ] **Step 3: Implement**, then the tests are green and the full suite is green.
- [ ] **Step 4:** Add to the README section on Datenschutz/storage, or a short „Speicherung“ note: the works stay only in this browser, and the home-screen tip exists. Add a CHANGELOG `[Unreleased]` entry for #13 and #5.
- [ ] **Step 5: Commit** `feat(galerie): Werke vor Safari-Speicherlöschung schützen (#5)` and `docs: CHANGELOG/README (#13, #5)`.
