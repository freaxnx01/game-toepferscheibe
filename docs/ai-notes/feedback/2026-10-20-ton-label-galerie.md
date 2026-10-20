# Feedback 2026-10-20 — Ton-Labels & Galerie bearbeiten

status: done

| # | Note (normalized, short EN) | Att. | Topic | Kind | Disposition | Rationale / link | Status |
|---|---|---|---|---|---|---|---|
| 01 | "Neuer Ton" (new clay) vs. "Ton an/aus" (sound) — "Ton" means both clay and sound; toggle label shows state, not action | | Werkbank-Bedienleiste | Improvement | Immediate | Label-only edit in `index.html` (button l.74, `soundLabel` l.383): "Neuer Ton" → "Neuer Tonklumpen", sound → "🔊 Klang an" / "🔇 Klang aus" | done — labels changed |
| 02 | Gallery works should be re-openable and editable | | Galerie | New feature | Issue | Gallery entries store only a JPEG + glaze name + date (`saveToGallery`, l.400) — no profile/height, so needs data-model change (store shape, glaze, fired state), "Bearbeiten" button, screen flow; old entries can't be edited | done — #1 |

## Raw notes

- 'Neuer Ton' und 'Ton an/aus' ist verwirrend [#01]
- Werke aus Galerie soll man weiter bearbeiten können [#02]
