# Changelog

All notable changes of the maintenance fork. Versions follow [SemVer](https://semver.org/); the version is defined
only in `Directory.Build.props`. Releases are Git tags `vX.Y.Z`. History of the original up to 18.0.1:
<https://github.com/stephanstapel/ZUGFeRD-csharp/releases>.

## [Unreleased]

### Changed
- Fork of ZUGFeRD-csharp 18.0.1 (Apache-2.0, Stephan Stapel). Assembly names and namespaces unchanged.
- NuGet package IDs `ChriveSolutions.ZUGFeRD` and `ChriveSolutions.ZUGFeRD.PDF` (instead of `ZUGFeRD-csharp` and
  `ZUGFeRD.PDF-csharp`), published to GitHub Packages.
- `ZUGFeRD.PDF` references the fork's core project instead of the original `ZUGFeRD-csharp` package.
- Version, authors and repository URLs centrally in `Directory.Build.props`.
- Test `BasicSaveFileAndEmbedFonts` no longer writes to a fixed path `e:\out.pdf`.

### Added
- `SECURITY.md`, `CONTRIBUTING.md`, `NOTICE`, `CODEOWNERS`, Dependabot configuration.
- CI for pull requests (build, tests, license header); release workflow for GitHub Packages.
- Monthly check agent (`.agent/`, `docs/AGENT.md`): standards and vulnerabilities, one issue per month.

### Removed
- Original workflows `dotnet.yml` and `license-check.yml` (replaced by `ci.yml`), `.licenserc.json`.
