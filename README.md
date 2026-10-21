# Töpferwerkstatt

A calm virtual pottery wheel, made for an 84-year-old aunt on her iPad: shape
clay on a slowly turning 3D wheel with one or two fingers, pick a glaze, fire
the piece in the kiln and keep it in a personal gallery. Very large type, high
contrast, no time pressure, undo at any time.

Play it: <https://github.freaxnx01.ch/game-toepferscheibe/>

## Controls

- **Drag on the clay** (one or two fingers, or the mouse) — shape it
- **Drag beside the clay** — rotate the view; pinch beside it to zoom
- **Mouse wheel** — raise/lower the clay; with Ctrl/Shift, zoom
- **Werkzeug** (toggle at the top of the side panel, next to „Formen“) — stops the wheel;
  tap the rim for a notch (up to 8); the corner buttons make the pot Rund, Oval,
  Dreieckig or Viereckig. „Rückgängig“ undoes both. „Formen“ switches back.
- **Choosing the lump** — on the start screen pick size (Klein/Mittel/Gross) and form
  (Kugel/Kegel); at the wheel, „Neuer Tonklumpen“ opens the same choice („Ton auflegen“ places it)
- **Weiter töpfern** (gallery) — reopens a piece at the wheel; saving it again replaces the original
- **← Zurück zu meinem Stück** — shown in the gallery and on the start screen while a piece is unsaved
- **Klang an/aus** (off by default) — soft motor hum while the wheel turns, plus a clay rub
  sound that follows how fast your finger moves

## Stack

Buildless static page. `index.html` is a Claude Design (`dc`) document hydrated
by the generic `support.js` runtime; the 3D scene uses three.js from unpkg. No
build step — GitHub Pages serves the repo root as-is. The gallery is stored in
the browser's `localStorage` (key `toepfern.galerie`).

The full design reference is in [`docs/design-handoff.md`](docs/design-handoff.md).

## Versioning

The git tag `vX.Y.Z` is the source of truth; `version.js` mirrors it for the
in-page badge. See [`CHANGELOG.md`](CHANGELOG.md).
