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
- [ ] Secret `ANTHROPIC_API_KEY` und erster Lauf per `workflow_dispatch` (Maintainer, #10)
- [x] Erstes Release `v18.1.0` (2026-11-20, GitHub Packages, #13)

## Fixes (je mit Test)

- [x] XML-Leser: DTD verbieten (`DtdProcessing.Prohibit`, `XmlResolver = null`) — #4, 18.1.0
- [x] XML-Leser: Speicherbedarf beim Erkennen der Version (50 MB: 1,29 GB → 334 MB) — #5, 18.1.0
- [x] Ohne Lieferangaben fehlt `ApplicableHeaderTradeDelivery` (CII D16B verlangt ihn) — #6, 18.1.0
- [x] UBL-Lesen erfindet bei Kopf-Abschlägen Grundcode 41 / Basis 0,00, leeres Projekt — #7, 18.1.0
- [ ] UBL-Lesen, Rest aus #7: Zahlungsempfänger (BR-17), Steuervertreter (BR-18/56), Typcode 916, Adresszeilen
- [ ] Eingehende ZUGFeRD 2.4/2.5(.2)-XML lesen: Muster beschaffen und testen
- [ ] Warnungen CS1591/CS1570 (440, aus dem Original) abbauen, danach `TreatWarningsAsErrors`
