# Feedback 2026-10-21 — Aussehen des Tons

status: done

| # | Note (normalized, short EN) | Att. | Topic | Kind | Disposition | Rationale / link | Status |
|---|---|---|---|---|---|---|---|
| 01 | Clay should be one even colour, no speckle/grain | | Ton-Material | Improvement | Immediate | `clayTexture()` (index.html:265) paints 2600 dark/light speckles + 18 vertical streaks into the `map` of the clay material (l.244). Drop the map → uniform colour. Side effect: the map also stays on under glazes (`setGlaze` only changes colour), so glazes become smooth/even too | done |
| 02 | Clay colour should be more earthy / loam-like | | Ton-Material | Improvement | Immediate | One constant: `CLAY = '#A86B48'` (l.198, reddish terracotta) → a muted ochre-grey loam brown (proposal `#9C7B5E`) | done |
| 03 | Clay should glisten wet in places (water is used while throwing) | | Ton-Material | New feature | Issue | Material is fully matte (roughness 0.95, l.244/464). Patchy shine needs a roughness map or wetness that follows where the fingers touched, plus deciding whether it dries out and what happens at glazing/firing (fired clay must not shine) | done — #7 |
| 04 | Add hollowing out (opening the lump) as the first phase of throwing | | Scheibe | New feature | Issue | The pot is always hollow already: `outline()` (pottery.js:38) derives the inside from the outer profile with a fixed wall (0.13) and floor (0.14). An opening phase needs a solid-lump state, a press-into-centre gesture that sets inner depth/width (and so wall/floor thickness), a phase step before shaping, and fits the gallery/undo data model | done — #8 |

## Raw notes

- ton soll keine maserung aufweisen sondern gleichfarbig sein. [#01] die farbe sollte mehr erdfarben/lehmartiger sein. [#02] es wird beim töpfern ja wasser verwendet. daher sollte es stellenweise glänzen [#03]
- könnten wir als erste phase auch das aushöhlen im spiel abbilden? [#04]
