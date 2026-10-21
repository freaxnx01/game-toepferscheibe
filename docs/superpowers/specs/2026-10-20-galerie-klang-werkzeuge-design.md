# Design: Galerie bearbeiten, Klang, Werkzeuge, Ausgangsklumpen

Datum: 2026-10-20 · Issues: #1, #3, #2, #4

## Intent

Die Töpferwerkstatt ist ein ruhiges Töpferspiel für eine 84-jährige Tante auf dem
iPad: grosse Schrift, hoher Kontrast, keine Zeitnot, jederzeit rückgängig. Tester-
Feedback verlangt vier Erweiterungen, die das Spiel reicher machen, ohne diese
Ruhe zu brechen:

1. **#1** Werke aus der Galerie weiter bearbeiten.
2. **#3** Ein natürlicherer Klang beim Töpfern.
3. **#2** Werkzeuge: Kerben in den Rand (z.B. Aschenbecher) und Gefäss eckig machen.
4. **#4** Ausgangsklumpen wählen (Grösse, Grundform).

Reihenfolge der Umsetzung: #1 → #3 → #4 → #2 (klein nach gross; #2 baut auf dem
Datenmodell aus #1 auf).

## Globale Constraints

- **Buildless bleibt buildless.** Statische Seite, `index.html` als `dc`-Dokument,
  `support.js`-Runtime, three.js von unpkg. Kein Bundler, keine npm-Dependencies
  für die Seite selbst.
- **Zielgruppe:** sehr grosse Touch-Ziele (≥ 64 px Höhe wie bestehende Knöpfe),
  deutsche Texte in Sie-Form wie bestehende Hinweistexte, keine überladenen Panels.
- **Rückgängig** muss jede neue Aktion zurücknehmen können (Form, Kerbe, Ecken,
  Klumpenwahl, Zufallsform).
- **localStorage**-Key `toepfern.galerie` bleibt; max. 30 Werke. Alte Einträge
  (ohne Formdaten) dürfen nicht kaputtgehen.
- **Tests:** Test-Driven Development für reine Logik. Dafür wird die reine Logik
  (Profil-/Form-Erzeugung, Verformung, Serialisierung, Klang-Parameter-Berechnung)
  in eine eigene Datei `pottery.js` ausgelagert (klassisches Script, setzt ein
  Global `Pottery` und exportiert zusätzlich via `module.exports`, wenn vorhanden),
  die `index.html` per `<script>` lädt und `node --test` direkt testen kann —
  ohne npm-Dependencies. UI/3D/Audio-Verkabelung wird per Playwright-Screenshot
  bzw. manuell auf dem iPad geprüft.

## #1 Galerie-Werke weiterbearbeiten

Entschieden (mit dem Auftraggeber):

- Jede Galerie-Karte bekommt einen Knopf **„Weiter töpfern“** neben „Entfernen“.
  Er öffnet das Werk an der Scheibe (Screen `wheel`) mit gespeicherter Form.
- Ablauf danach wie gewohnt (formen → glasieren → brennen → „In die Galerie
  stellen“). Speichern **ersetzt** den Originaleintrag **an derselben Stelle**
  (gleiche Position im Array, neues Vorschaubild, neues Datum).
- Beim Glasieren ist die bisherige Glasur **vorausgewählt**, aber änderbar. An der
  Scheibe erscheint das Werk wieder als ungebrannter Ton (wie heute).
- „Neuer Tonklumpen“ oder Neustart über den Start-Screen verlässt den
  Bearbeitungsmodus; das nächste Speichern legt ein **neues** Werk an.
- Alte Werke ohne Formdaten: Knopf ausgeblendet; ansehen und entfernen geht weiter.
- **Angefangene Arbeit geht nicht still verloren** (Entscheid des Auftraggebers):
  Solange ein ungespeichertes Stück existiert (an der Scheibe, beim Glasieren, Brennen
  oder auf „Fertig“), zeigt die Galerie oben einen grossen Knopf **„← Zurück zu meinem
  Stück“**, der genau dorthin zurückführt, wo man war. Erst „Weiter töpfern“ auf einem
  anderen Werk oder ein Neustart verwirft das angefangene Stück. Keine
  Bestätigungsdialoge.

Datenmodell (Builder-Entscheid im Detail): jeder neue Galerie-Eintrag speichert
zusätzlich ein `shape`-Objekt, das alles enthält, was zum Wiederherstellen nötig
ist — mindestens `profile` (28 Radien), `height`, Glasurname, und ab #2/#4 auch
Kerben, Ecken-Modus und Klumpen. Eine `version`-Zahl im `shape` erlaubt spätere
Erweiterung. Identität eines Eintrags über eine stabile `id` (nicht über den
Array-Index, da „Entfernen“ Indizes verschiebt).

Undo-Verlauf: beim Öffnen eines Werks startet der Verlauf leer.

Rückgängig und Bearbeitungsmodus (Claudes Entscheid): Der Bezug „bearbeite Werk X“
ist **Teil jedes Undo-Snapshots**, zusammen mit Profil, Höhe, Kerben, Ecken-Modus und
Klumpenwahl. „Neuer Tonklumpen“ setzt all das zurück (inkl. Kerben und Ecken) und löst
den Bezug; drückt man danach „Rückgängig“, ist der Bezug wieder da, und Speichern
ersetzt wieder das Original. Wird das Originalwerk inzwischen aus der Galerie entfernt,
legt Speichern ein neues Werk an.

## #3 Natürlicherer Klang

Entscheid: Claude wählt; Auftraggeber hat zugestimmt. Weiterhin **synthetisch per
WebAudio**, keine Audiodateien.

- **Scheibe:** gedämpftes Rauschen wie ein leiser Motor unter dem Tisch, ersetzt den
  reinen 55-Hz-Sinus. Leichte Schwankung im Takt der Drehung. Beim Anhalten sanftes
  Ausklingen (statt hartem Abschalten).
- **Ton anfassen:** weiches, feuchtes Schlurfen. Lautstärke abhängig von der
  **Geschwindigkeit der Fingerbewegung** (stillhalten → leise), nicht konstant beim
  Berühren. Langsames Zufallsflattern gegen gleichförmiges Zischen.
- Bleibt: standardmässig aus, „Klang an/aus“-Knopf, insgesamt leise.
- Die genaue Klangabstimmung (Filterfrequenzen, Pegel) ist Sache des Builders;
  Abnahme erfolgt durch Anhören auf dem iPad.

## #4 Ausgangsklumpen

Entschieden:

- Beim Start („Ton auf die Scheibe legen“) und bei „Neuer Tonklumpen“ wählt man
  **Grösse** (klein / mittel / gross) und **Grundform** (Kugel / flacher Kegel).
- Grösse bestimmt Startbreite und -höhe; Grundform bestimmt das Startprofil.
- „Mittel + Kegel“ entspricht ungefähr dem heutigen Startprofil.
- Kein eckiger Klumpen: echter Ton wird rund zentriert; Eckiges entsteht über #2.

Grösse ist **nur ein Startpunkt**, keine Grenze (Claudes Entscheid): danach gelten
die heutigen Grenzen (Radius 0.2–1.6, Höhe 0.35–1.6) für alle Grössen; „gross“ bleibt
innerhalb dieser Grenzen. Kein Volumenmodell.

Offen für den Builder: ob die Auswahl ein eigener kleiner Screen/Dialog oder eine
Zeile Knöpfe im Panel ist — solange grosse Touch-Ziele und höchstens ein Extra-Schritt.

## #2 Werkzeuge: Kerbe und Eckig machen

Entschieden:

- An der Scheibe zwei Modi: **„Formen“** (wie heute) und **„Werkzeug“**. Im
  Werkzeug-Modus hält die Scheibe an, damit man eine Stelle treffen kann; beim
  Zurück zu „Formen“ dreht sie wieder (sofern sie vorher drehte).
- **Kerbe:** Tippen auf den **Rand** setzt dort eine runde Kerbe fester Grösse
  (Zigarettenablage). Mehrfach möglich. Rückgängig nimmt die letzte zurück.
- **Eckig machen:** grosse Knöpfe **Rund · Oval · Dreieckig · Viereckig**; die
  Seiten werden gleichmässig flachgedrückt (kein freies Drücken mit dem Finger).
- **Reihenfolge frei:** Nach Kerben/Ecken darf man wieder formen; Kerben und Ecken
  bleiben erhalten und folgen der neuen Form. Deshalb werden sie als **Parameter**
  gespeichert (Kerben: Winkel um die Achse; Ecken: Modus) und bei jedem Neuaufbau
  auf das Rotationsprofil angewendet — nicht als einmalige Mesh-Verformung.
- Kerben und Ecken werden in der Galerie mitgespeichert (#1).

Technik: Das Gefäss wird nicht mehr nur per `LatheGeometry` aus einem Profil
gedreht, sondern als Gitter (Ringe × Segmente) erzeugt, dessen Radius pro Punkt
= Profilradius × Eckenfaktor(Winkel) und dessen Randhöhe an Kerbenwinkeln abgesenkt
wird. Innen- und Aussenwand, Rand und Boden müssen weiter geschlossen wirken.
Formen (Ziehen am Ton) arbeitet weiter auf dem Rotationsprofil.
Der Profilradius entspricht ungefähr dem **mittleren** Radius der eckigen Form
(Ecken etwas weiter aussen, flache Seiten etwas weiter innen), damit das Ziehen mit
dem Finger grob dort greift, wo die Oberfläche sichtbar ist (Claudes Entscheid).

Treffererkennung „Rand“ für die Kerbe: Builder-Entscheid (z.B. Raycast aufs Mesh,
Treffer im oberen Bereich → Winkel aus Trefferpunkt).

## Nicht-Ziele

- Keine Audiodateien/Samples.
- Kein freies Modellieren mit Fingerdruck an beliebiger Stelle, keine Muster/Ritzungen,
  keine Löcher.
- Kein eckiger Ausgangsklumpen.
- Kein Cloud-Sync der Galerie.

## Anti-Ziele (wäre ein Fehlschlag, selbst wenn es technisch läuft)

- Bedienung wird für die Tante unübersichtlich (zu viele kleine Knöpfe, Modi, die man
  versehentlich wechselt, ohne zu merken, in welchem man ist).
- Bestehende Galerie-Werke verschwinden oder lassen sich nicht mehr anzeigen.
- Die Seite ruckelt auf dem iPad, weil der Neuaufbau des Gefässes zu teuer wird.
