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
- **Neuer Tonklumpen** — choose size (Klein/Mittel/Gross) and form (Kugel/Kegel) of the starting lump
- **Tonklumpen wählen** — schon auf dem Startbildschirm (Grösse Klein/Mittel/Gross, Form Kugel/Kegel) und
  später an der Scheibe über „Neuer Tonklumpen“ (dann „Ton auflegen“)
- **Weiter töpfern** — in der Galerie öffnet es ein Stück zum Weiterarbeiten; beim erneuten Speichern
  ersetzt es das Original (kein Duplikat)
- **← Zurück zu meinem Stück** — in der Galerie und auf dem Startbildschirm, solange ein Stück in Arbeit ist
- **Klang** („Klang aus“/„Klang an“, standardmässig aus) — leises Motorbrummen, solange sich die Scheibe dreht,
  und ein Reibegeräusch beim Formen, das der Fingergeschwindigkeit folgt

## Stack

Buildless static page. `index.html` is a Claude Design (`dc`) document hydrated
by the generic `support.js` runtime; the 3D scene uses three.js from unpkg. No
build step — GitHub Pages serves the repo root as-is. The gallery is stored in
the browser's `localStorage` (key `toepfern.galerie`).

The full design reference is in [`docs/design-handoff.md`](docs/design-handoff.md).

## Versioning

The git tag `vX.Y.Z` is the source of truth; `version.js` mirrors it for the
in-page badge. See [`CHANGELOG.md`](CHANGELOG.md).
