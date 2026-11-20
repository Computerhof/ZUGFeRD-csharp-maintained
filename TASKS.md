# Aufgaben

## Einrichtung (2026-11-20)

- [x] Fork `Computerhof/ZUGFeRD-csharp-maintained` angelegt, Branch `main`
- [x] Secret Scanning + Push Protection, Dependabot-Alerts und -Sicherheitsupdates, Private Vulnerability Reporting
- [x] Ruleset `main-schutz`: PR + 1 Code-Owner-Review, veraltete Reviews verwerfen, kein Force-Push/Löschen,
      Ausnahme nur für Admin über Pull Request
- [x] Workflow-Token standardmäßig lesend, Freigabe für Workflows externer Beitragender
- [x] Paket-IDs `ChriveSolutions.ZUGFeRD` / `.PDF`, PDF per Projektreferenz, Version in `Directory.Build.props`
- [x] SECURITY, CONTRIBUTING, NOTICE, CODEOWNERS, CHANGELOG, Dependabot, CI, Release nach GitHub Packages
- [x] Prüfagent (`.agent/`, `docs/AGENT.md`) mit Baseline
- [x] CI auf Windows (PDF-Tests brauchen Arial; `core.longpaths` wegen `documentation/`)
- [x] CodeQL-Standardeinrichtung (C#, Actions) eingeschaltet, erster Lauf ohne Befund
- [x] Actions: nur GitHub-eigene, SHA-Pins Pflicht (`sha_pinning_required`)
- [x] Tag-Ruleset `release-tags` für `v*` (kein Löschen/Überschreiben); `main` verlangt den Check `build-test`
- [x] Monatsprüfung meldet neuere Modelle derselben Linie und Abkündigung (kein `opus-latest` in der API)
- [ ] Secret `ANTHROPIC_API_KEY` (Chris) und erster Lauf per `workflow_dispatch` (Freigabe Chris)
- [ ] Erstes Release `v18.1.0` nach den ersten Fixes; Prozessor stellt danach die Paketreferenz um

## Fixes (je mit Test)

- [ ] XML-Leser: DTD verbieten (`DtdProcessing.Prohibit`, `XmlResolver = null`)
- [ ] XML-Leser: Speicherbedarf beim Erkennen der Version (`ReadToEnd().Replace` je Leser, ~26-fach der Eingabe)
- [ ] Ohne Lieferangaben fehlt `ApplicableHeaderTradeDelivery` (CII D16B verlangt ihn)
- [ ] UBL-Lesen erfindet bei Kopf-Abschlägen Grundcode 41 / Basis 0,00
- [ ] Eingehende ZUGFeRD 2.4/2.5(.2)-XML lesen: Muster beschaffen und testen
- [ ] Warnungen CS1591/CS1570 (440, aus dem Original) abbauen, danach `TreatWarningsAsErrors`
