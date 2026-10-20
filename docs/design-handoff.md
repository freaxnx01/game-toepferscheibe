# Handoff: Virtuelle Töpferscheibe (iPad)

## Overview
A calm, accessible pottery-wheel app for an 84-year-old user in a senior residence. She shapes clay on a slowly turning 3D wheel with one or two fingers, picks a glaze, "fires" the piece in a kiln, and keeps it in a personal gallery. Priorities: very large type, high contrast, no time pressure, undo at any time, optional soft wheel sound, slow wheel.

Target device: iPad, landscape and portrait (layout reflows). Also usable with a mouse on desktop.

## About the Design Files
`Toepferscheibe.dc.html` (+ `support.js` runtime) is a **design reference built in HTML** — a working prototype showing intended look and behavior, not production code. Recreate it in the target codebase's environment (e.g. SwiftUI + SceneKit/RealityKit for a native iPad app, or React + three.js for a web/PWA). If no codebase exists, a React + three.js PWA installed to the home screen is the simplest path; a native SwiftUI/SceneKit app is the most robust for touch and offline use.

## Fidelity
**High-fidelity.** Colors, typography, sizes, copy, and interaction rules are final. Recreate 1:1 using the codebase's component patterns.

## Screens / Views

Shared shell: full-height column; background `#F4ECDF`; text `#35261B`.

**Header** (all screens): `#FBF6EC`, bottom border `2px #D9C9B2`, padding `18px 28px`, flex space-between.
- Title "Töpferwerkstatt" — Lora 600, 30px, letter-spacing −0.01em.
- Step label (22px, 500, `#6E5A4A`): "An der Scheibe" / "Glasieren" / "Brennen" / "Fertig" / "Galerie"; empty on Start.
- Right: "Galerie (N)" outline button (hidden on Start and Gallery) — 60px min-height, 22px/700, border `2px #35261B`, radius 14, bg `#FBF6EC`, hover `#F0E4D0`.

### 1. Start
Centered column, gap 28, padding 48/28, text centered.
- Clay disc: 140px circle, radial gradient `#C98A63 → #8A5A3A (70%) → #5E3A24`, shadow `0 12px 30px rgba(53,38,27,.25)`.
- H1 "Schön, dass Sie da sind." — Lora 600, 48px, line-height 1.15, max-width 720.
- Paragraph (26px, lh 1.5, `#4D3B2D`, max-width 640): "Die Scheibe dreht sich langsam. Legen Sie zwei Finger links und rechts an den Ton und ziehen Sie sie auseinander oder zusammen – ganz ohne Eile. Am PC ziehen Sie einfach mit der Maus am Rand des Tons."
- Primary button "Ton auf die Scheibe legen" (see Primary button token).
- If gallery non-empty: outline button "Meine Werke ansehen" (64px, 24px/700).

### 2. Wheel / Glaze / Firing / Done (shared two-pane layout)
Flex row, wraps. Left 3D pane `flex:1 1 560px; min-height:72vh`, background gradient `#EFE3CF → #E2D2B9`. Right aside `flex:0 1 320px; min-width:280px`, bg `#FBF6EC`, left border `2px #D9C9B2`, padding 20, column gap 14. In portrait the aside wraps below the 3D pane.

3D pane overlays:
- Top-right button "⟲ Ansicht zurücksetzen" — 56px, 20px/700, bg `rgba(251,246,236,.92)`, border `2px #B9A58A`, radius 14.
- Wheel screen only: bottom-centered hint pill — bg `rgba(251,246,236,.92)`, border `2px #D9C9B2`, radius 14, padding 12/20, 22px `#4D3B2D`, max-width 600. Text: "Am Ton ziehen formt ihn. Neben dem Ton ziehen dreht die Ansicht; zwei Finger neben dem Ton zoomen."
- Firing screen only: full-pane kiln glow overlay, `radial-gradient(ellipse at 50% 70%, rgba(255,140,40,.75), rgba(180,60,10,.35) 55%, rgba(40,10,0,.6))`, opacity pulsing .55↔.9 over 2.4s ease-in-out.

**Aside — Wheel ("Formen", H2 Lora 600 30px)**
Secondary buttons in 2-col grids, gap 12, 72px min-height, 24px/700:
"▲ Höher ziehen" | "▼ Niedriger"; "↶ Rückgängig" | "Neuer Ton"; then 64px/22px: "⏸ Scheibe anhalten"/"▶ Scheibe drehen" | "🔊 Ton an"/"🔇 Ton aus". Spacer. Primary "Fertig – Glasieren →" (84px, 28px).

**Aside — Glaze ("Glasur wählen")**
Intro 22px `#6E5A4A`: "Tippen Sie auf eine Farbe. Sie können jederzeit wechseln." Single-column list, gap 10: buttons 68px, flex row gap 16, padding 0 16, 22px/700, bg `#F4ECDF`, border `3px` — `#D9C9B2` default, `#B45E3A` when selected. 40px round swatch with `inset 0 -6px 10px rgba(0,0,0,.2), 0 1px 2px rgba(0,0,0,.25)`.
Glazes (name / color / roughness): Honig `#C8893A` .30 · Seladon `#9FB8A3` .35 · Himmelblau `#6B8FB0` .30 · Milchweiß `#EFE7D8` .40 · Ochsenblut `#7A1F1F` .25 · Tenmoku `#2B1A14` .20.
Bottom: secondary "← Zurück zur Scheibe" (64px), primary "In den Ofen →".

**Aside — Firing ("Im Brennofen")**
Text 24px: "Der Ofen heizt langsam auf. Die Glasur schmilzt und wird glänzend." (<60 %) then "Der Ofen kühlt ab. Gleich können Sie Ihr Stück herausnehmen." Progress bar 22px high, track `#E6D9C3`, border `2px #D9C9B2`, fill `linear-gradient(90deg,#C8893A,#B45E3A)`. Temperature readout 26px/700 "NNN °C".

**Aside — Done ("Fertig gebrannt")**
"Ihr Stück in **{Glasur}** ist abgekühlt. Schauen Sie es sich in Ruhe an." Primary "In die Galerie stellen"; secondary "Neues Stück beginnen".

### 3. Gallery ("Meine Werke", H1 Lora 40px)
Padding 32/28. Header row with primary "Neues Stück beginnen" (72px, 26px). Empty state 26px `#6E5A4A`: "Noch ist das Regal leer – das erste Stück wartet auf Sie." Grid `repeat(auto-fill, minmax(260px,1fr))`, gap 24. Card: bg `#FBF6EC`, border `2px #D9C9B2`, radius 18; square thumbnail (cover, bg `#E2D2B9`); glaze name 24px/700; date 20px `#6E5A4A` (de-DE long format); "Entfernen" outline button 56px, 20px, `#6E5A4A`.

## 3D Scene
- Camera: perspective FOV 32, orbit around target `(0, 0.9·height, 0)`; default θ=0, φ=1.25 rad, distance 5.4; φ clamped 0.35–1.55, distance 3–9.
- Lights: hemisphere `#fff4e0`/`#8a6a4a` 0.9; key directional white 1.6 at (3,6,4) with shadows; fill `#ffe8d0` 0.5 at (−4,3,−2). Shadow catcher plane opacity .25.
- Wheel head: cylinder r 2.2/2.3, h 0.18, texture `#6b4a33` with concentric dark rings, 12 light spokes and a light marker dot (so rotation is visible); dark torus rim r 2.25.
- Clay: lathe geometry from a radial profile of 28 rings (default radius 0.95 at base → 0.60 at top), height = 2·heightFactor (factor 0.35–1.6, default 1.0). Hollow: outer wall up, inner wall down (thickness 0.13, min inner r 0.03) to floor at y 0.14. Material: `#A86B48`, roughness .95, DoubleSide, speckle texture.
- Wheel + clay rotate together, 0.012 rad/frame × speed (speed tweakable 0.3–2).
- Glaze: set material color/roughness, metalness .05. Firing: emissive `#ff6a1a`, intensity ramps 0→.45 (first 60 %) →0.

## Interactions & Behavior
- **Shape (wheel screen)**: pointer down that hits the clay (raycast on mesh, or within profile radius + 0.3 in the camera-facing plane) enters shape mode. One pointer: ring at pointer height gets radius = |x| of pointer. Two pointers: ring at mean height gets radius = half their horizontal distance. Each move blends 7 neighbouring rings with gaussian falloff `exp(−k²/4)` × strength (0.5 default, tweakable 0.2–1). Radius clamped 0.2–1.6.
- **Orbit**: pointer down beside the clay (any screen except Start/Gallery) → drag rotates θ (−0.006 rad/px) and φ (0.005 rad/px); two-finger pinch zooms (0.01/px). Mouse wheel: height on wheel screen; with Ctrl/Shift (or on other screens) zoom.
- **Undo**: snapshot of profile + height pushed on every pointer-down and height change; max 60; "Rückgängig" pops.
- **Height buttons**: ±0.08; wheel ±0.04.
- **Neuer Ton**: snapshot, reset profile/height.
- **Spin toggle**, **sound toggle** (default off). Sound: low-pass (320 Hz) white noise, gain .02 idle / .12 while touching; 55 Hz sine hum .05 while spinning. Create AudioContext only on first user gesture.
- **Firing**: 2 %/120 ms → ~6 s; then Done.
- **Save to gallery**: render current frame, center-crop square 480×480 JPEG (q .8) onto `#E8DAC2`, store `{img, glaze, date}`; newest first; cap 30; persist (localStorage key `toepfern.galerie` in prototype — use app storage natively).
- No timers that expire, no modal confirmations; every destructive step is one tap with undo or an obvious "Neuer Ton".
- Responsive: flex-wrap; aside goes below 3D pane when width < ~880px.

## State
`screen: start|wheel|glaze|firing|done|gallery`, `profile[28]`, `height`, `history[]`, `spinning`, `sound`, `glaze|null`, `firePct`, `gallery[]`, camera `{theta, phi, dist}`.

## Design Tokens
Colors: bg `#F4ECDF`, surface `#FBF6EC`, surface-hover `#F0E4D0` / `#EBDFCB`, line `#D9C9B2`, line-strong `#B9A58A`, ink `#35261B`, ink-2 `#4D3B2D`, ink-muted `#6E5A4A`, accent `#B45E3A`, accent-hover `#9B4D2E`, accent-shadow `#8A4428`, clay `#A86B48`, pane gradient `#EFE3CF→#E2D2B9`.
Type: headings Lora 600 (48/40/30); UI Nunito Sans 500/700 (30/28/26/24/22/20). Nothing below 20px.
Radii: 18 (primary/cards), 14 (buttons), 12 (small), 11 (progress).
Primary button: bg accent, text `#FBF6EC`, no border, radius 18, shadow `0 6px 0 #8A4428`, active translateY 4px + shadow 2px. Secondary: bg `#F4ECDF`/`#FBF6EC`, border `2px #B9A58A`, radius 14.
Touch targets ≥ 56px; primary actions 84px.

## Assets
Fonts: Lora, Nunito Sans (Google Fonts). All textures generated procedurally (canvas) — no image assets.

## Files
- `Toepferscheibe.dc.html` — full prototype (template + logic).
- `support.js` — prototype runtime (needed only to open the HTML; not part of the design).
