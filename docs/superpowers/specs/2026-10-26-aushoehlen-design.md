# Aushöhlen als erste Phase (#8) — Design

## Why

A tester asked: „könnten wir als erste phase auch das aushöhlen im spiel abbilden?“

On a real wheel the potter first opens the centred lump:
1. The thumb presses down into the middle. This sets the depth, and with it the floor.
2. The opening is pulled outward. This sets the width, and with it the wall.
3. Only then are the walls pulled up.

Today the game skips this. A piece is always already hollow: `outline()` in `pottery.js` derives the inside from the outer profile with a fixed wall of 0.13 and a fixed floor height of 0.14.

The players are older people on an iPad. The interaction must be calm, forgiving and never a dead end (see #6, slow clay).

## Decisions (user, 2026-10-26)

- **Gesture: press, then pull.**
  - Holding a finger in the middle of the turning lump slowly deepens the hole. It stops at a minimum floor.
  - Dragging from the hole outward widens the opening and thins the wall. It stops at a minimum wall.
  - Both use the time-based, slow flow of #6 (`FLOW_TAU`), not instant jumps.
- **Own phase before shaping.**
  - After a new lump comes the step „Aushöhlen“, with a button „Weiter zum Formen →“.
  - The shaping step gets „← Zurück zum Aushöhlen“.
  - Undo (Rückgängig) covers hollowing strokes too.
- **Skippable.** A button „Für mich aushöhlen“ hollows with today's default values (wall 0.13, floor 0.14) and goes straight on to shaping. Nobody is ever stuck.
- **Effect: wall and floor thickness.**
  - Hollowing fixes two numbers per piece: `wall` (thickness) and `floor` (height of the inside floor). They stay constant while shaping and are saved with the work.
  - Old gallery works without these fields keep 0.13 / 0.14.

## Behaviour

**Starting state.** A new lump starts **solid**: no inner surface, the top is closed. This applies to „Ton auf die Scheibe legen“ and to „Neuer Tonklumpen“ / Neu anfangen. The game then opens the „Aushöhlen“ step. The header step label reads „Aushöhlen“.

**Aushöhlen step (panel on the right, same style as the shaping panel):**
- **Short hint:** „Halten Sie den Finger in die Mitte – das Loch wird tiefer. Ziehen Sie dann nach aussen – die Öffnung wird weiter.“
- **Buttons:**
  - „Weiter zum Formen →“ (primary). It is enabled once there is a hole at all.
  - „Für mich aushöhlen“ (secondary).
  - „↶ Rückgängig“, as in shaping.
- **Unchanged from shaping:** the wheel keeps turning and the motor/spin toggle is available. Orbit and pinch-zoom still work with a drag that does not start on the clay.
- **Not available here:** the lump picker, „🎲 Zufällige Form“, the notch tool, the corner shape and height changes. All of these belong to shaping.

**Press (depth).**
- **Trigger:** a finger on the clay near the axis, i.e. inside the current opening plus a small margin, or anywhere near the centre while the lump is still solid.
- **Effect:** the floor moves down over time while the finger stays there. It starts at the top of the lump.
- **Stop:** `FLOOR_MIN`.
- **Hole width:** while pressing, the hole is narrow, about a thumb.

**Pull (width).**
- **Trigger:** a finger that starts in or at the opening and moves outward.
- **Effect:** the opening widens toward the finger's radius, the time-based flow of #6, and the wall gets thinner.
- **Stop:** `WALL_MIN`. The opening never cuts through the outside.

**„Für mich aushöhlen“.** Sets `wall = 0.13` and `floor = 0.14`, which is exactly today's look, and takes one undo snapshot. It goes to shaping.

**„Weiter zum Formen →“.** Keeps the hollowed `wall` and `floor` and goes to shaping.

**Shaping.**
- Behaves as today, except that the inside is derived from the piece's own `wall` and `floor` instead of the constants.
- „← Zurück zum Aushöhlen“ returns to the hollowing step. The hollow can then be refined further with the same gestures; it is not reset.

**Undo.**
- Snapshots include `wall` and `floor`.
- One snapshot per hollowing stroke (pointerdown), as for shaping.
- Undo does not switch the phase.

**„🎲 Zufällige Form“.** Keeps the current `wall` and `floor`.

**Gallery.**
- Saved shapes carry `wall` and `floor`.
- „Weiter töpfern“ on a saved work goes straight to **shaping**, because the piece is already hollow. It uses the work's `wall` and `floor`, or 0.13 / 0.14 when missing.
- Thumbnails and the 3D view (#13) render with the work's own values.

**Home / Galerie / back paths.** The new step behaves like the shaping step for „Start“, the header „Galerie“ and „← Zurück zu meinem Stück“. Every list of "work screens" that today names `'wheel'` must also name the new step.

## Constraints

- **Pure geometry stays in `pottery.js` and is unit-tested:**
  - `outline`, `outlineRings` and `buildMesh` take the wall and floor values (with defaults 0.13 / 0.14).
  - `makeShape` stores them.
  - A solid outline exists for "not hollowed yet".
- **Old saved works must render exactly as before.** Default values must give a byte-identical `outline()` to today's.
- **UI conventions:**
  - German copy addresses the player as „Sie“ and uses real umlauts.
  - Buttons are at least 64px high and text at least 20px.
  - Use the existing colours and inline styles.
- **Wet shine (#7)** must keep working. `outlineRings` must match `outline` in point count for every wall/floor, including the solid case.
- **Use Test-Driven Development** for every task.

## Builder's calls (mine)

- **The step is a new screen** `'hollow'` with label „Aushöhlen“, rather than a sub-state of `'wheel'`. That follows the existing per-screen pattern for labels, `canvasDisplay`, `syncWheel` and the back paths.
- **Solid representation:** "not hollowed" is `floor` at or above the top (`2*height`), with `wall` irrelevant. `outline` then closes the top at the centre. Any equivalent encoding is fine, provided `outline`, `outlineRings` and `buildMesh` handle it.
- **Ranges** (tune if it looks wrong):
  - `WALL_MIN = 0.08`. There is no small upper cap, because a thumb hole in a big lump can mean a wall of about 1.0. Clamp the stored `wall` to at most 1.2 as a sanity bound.
  - `FLOOR_MIN = 0.08`.
  - When rendering, the floor is clamped to at most `2*height - 0.2`. Shrinking the height while shaping then never inverts the inside, while the stored value stays as it was.
- **One model for the inside, no third saved field.**
  - The inner radius at each ring is `max(0.03, profile[i] - wall)`, as today, in the hollowing step and when shaping.
  - During hollowing, the game works with an **opening radius at the rim**, `holeR`, and converts with `wall = profile[top] - holeR`. `top` is the top ring.
  - So the opening at the rim is exactly `holeR`, and below it the inside follows the outer form. There is no funnel that pinches shut on a cone or a ball.
  - Pressing starts with `holeR = 0.15`, a thumb.
  - Going back from shaping to hollowing recomputes `holeR` from the stored `wall`.
- **Gesture: the finger's position decides, no mode switch.**
  - **Mapping:** one finger. Its horizontal distance from the axis is mapped to the radius `r` exactly as shaping maps it (|x| to radius). Height does not matter in this step.
  - **Pressing:** if `r ≤ holeR + 0.1`, or the lump is still solid, the floor sinks over time.
  - **Pulling:** if `r > holeR + 0.1`, `holeR` flows toward `r` over time and the floor stays put. It is limited so that `wall ≥ WALL_MIN`.
  - **Flow:** both use the #6 flow factor (`FLOW_TAU`) on real frame time.
  - **Off the clay:** a drag that starts off the clay orbits, as everywhere.
  - **For the player:** the middle makes it deeper, further out makes it wider.
- **Recovery:** the hole can only get deeper or wider, as with real clay. There are three ways back:
  - „↶ Rückgängig“, one stroke at a time;
  - „Für mich aushöhlen“, which sets the default values;
  - „Neuer Tonklumpen“.
- **A solid piece can never reach glazing, firing or the gallery.** The way there only leads through shaping, and shaping is only reachable once a hole exists, either via „Weiter zum Formen →“ or via „Für mich aushöhlen“.
  - The header „Galerie“ from the hollowing step only navigates, with `returnScreen = 'hollow'`. It does not save anything.
- **Wet shine while hollowing:** applies at the touched ring, using the same `wetStep` as in shaping. This is optional polish.
- **Analytics:** unchanged. No new event.

## Non-goals

- Centring the lump as a separate step.
- A variable wall thickness along the height.
- Trimming the foot or a ring foot.
- Changing how shaping, notches, corners, glazing or firing work.
- Converting old works.

## Tests

**Unit:**
- `outline`/`outlineRings` with default values are identical to today's output.
- Custom wall/floor values move the inner points.
- The solid case has no inner points and a closed top.
- Point counts of `outline` and `outlineRings` match in all cases.
- `makeShape` round-trips `wall`/`floor`, and missing values give the defaults.
- Pure hollowing step functions (press/pull with dt), if extracted: they clamp at `FLOOR_MIN`/`WALL_MIN` and are time-based.

**e2e:**
- „Ton auf die Scheibe legen“ shows „Aushöhlen“.
- Holding a finger in the middle deepens the hole, readable via a test hook such as a `data-floor` attribute, like `data-wet`.
- Dragging outward thins the wall.
- „Weiter zum Formen →“ reaches shaping.
- „← Zurück zum Aushöhlen“ works.
- „Für mich aushöhlen“ gives 0.13/0.14.
- Saving and reopening via „Weiter töpfern“ keeps wall/floor and lands in shaping.
- An old gallery entry without the fields still opens and renders.
- The existing flows that click „Ton auf die Scheibe legen“ and then shape must pass through hollowing, most simply via „Für mich aushöhlen“.
