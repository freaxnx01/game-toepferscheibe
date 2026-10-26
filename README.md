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
  tap the rim for a notch (up to 16); the corner buttons make the pot Rund, Oval,
  Dreieckig or Viereckig. „Rückgängig“ undoes both. „Formen“ switches back.
- **Choosing the lump** — on the start screen pick size (Klein/Mittel/Gross) and form
  (Kugel/Kegel); at the wheel, „Neuer Tonklumpen“ opens the same choice („Ton auflegen“ places it)
- **Weiter töpfern** (gallery) — reopens a piece at the wheel; saving it again replaces the original
- **← Zurück zu meinem Stück** — shown in the gallery and on the start screen while a piece is unsaved
- **Klang an/aus** (off by default) — soft motor hum while the wheel turns, plus a clay rub
  sound that follows how fast your finger moves

## Datenschutz / Privacy

**Deutsch.** Dieses Spiel zählt Besuche und Spielstarts mit **Umami**, selbst gehostet auf
einem Server in **Deutschland** (`stats.freaxnx01.ch`). Es werden keine Cookies gesetzt und
keine personenbezogenen Daten gespeichert. Die IP-Adresse wird nicht gespeichert, sondern
nur kurzzeitig für die Bestimmung von Land und Region verwendet. Die Galerie bleibt im
Browser (`localStorage`) und wird nicht übertragen. Wird das Skript blockiert (z. B. durch
einen Adblocker), läuft das Spiel unverändert weiter.

**Speicherung.** Die Werke bleiben nur in diesem Browser. Safari kann Daten von Seiten löschen,
die länger nicht besucht wurden; das Spiel bittet den Browser deshalb um dauerhaften Speicher
und zeigt auf iPad/iPhone einmalig den Tipp, es auf den Home-Bildschirm zu legen.

**English.** This game counts visits and game starts with **Umami**, self-hosted on a server
in **Germany** (`stats.freaxnx01.ch`). No cookies are set and no personal data is stored. The
IP address is not stored; it is used only transiently to look up country and region. The
gallery stays in the browser (`localStorage`) and is never sent. If the script is blocked
(e.g. by an ad blocker), the game runs exactly as before.

**Storage.** Works stay only in this browser. Safari may purge data of sites not visited for a
while, so the game asks the browser for persistent storage and, on iPad/iPhone, shows a
one-time tip to add it to the Home Screen.

## Stack

Buildless static page. `index.html` is a Claude Design (`dc`) document hydrated
by the generic `support.js` runtime; the 3D scene uses three.js from unpkg. No
build step — GitHub Pages serves the repo root as-is. The gallery is stored in
the browser's `localStorage` (key `toepfern.galerie`).

The full design reference is in [`docs/design-handoff.md`](docs/design-handoff.md).

## Versioning

The git tag `vX.Y.Z` is the source of truth; `version.js` mirrors it for the
in-page badge. See [`CHANGELOG.md`](CHANGELOG.md).
