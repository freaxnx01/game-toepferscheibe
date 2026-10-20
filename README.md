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

## Stack

Buildless static page. `index.html` is a Claude Design (`dc`) document hydrated
by the generic `support.js` runtime; the 3D scene uses three.js from unpkg. No
build step — GitHub Pages serves the repo root as-is. The gallery is stored in
the browser's `localStorage` (key `toepfern.galerie`).

The full design reference is in [`docs/design-handoff.md`](docs/design-handoff.md).

## Versioning

The git tag `vX.Y.Z` is the source of truth; `version.js` mirrors it for the
in-page badge. See [`CHANGELOG.md`](CHANGELOG.md).
