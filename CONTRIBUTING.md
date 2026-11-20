# Contributing

This is a maintenance fork of ZUGFeRD-csharp, kept alive for our own products after the original's maintenance
ended on 30 November 2026. Issues are welcome. Pull requests are reviewed, but without a response deadline and
without a promise to merge.

## Rules for pull requests

- **Small and focused.** One topic per pull request, with tests. Larger changes: open an issue first.
- **No binary files** (DLLs, PDFs, images, archives). Test inputs as text (XML) with invented data only —
  never real invoices, real company names, tax IDs or bank details.
- **No new dependencies** without a reason in the pull request. Each dependency is a long-term risk here.
- **No changes to `.github/` or `.agent/`** (workflows, agent, settings) by outside contributors. Such pull
  requests are closed.
- **Human review is mandatory.** Every pull request needs the code owner's approval; nothing is merged
  automatically. Workflows of first-time and outside contributors run only after manual approval and never
  with secrets.
- **Keep the API stable.** Assembly names and namespaces (`s2industries.ZUGFeRD`) stay as in the original so
  existing code keeps compiling. Breaking changes need an issue and a major version.
- **License.** Contributions are accepted under Apache-2.0. Keep the license header in source files.

## Note on automation

A monthly check agent reads release notes, package metadata and advisory databases and writes one issue per run.
It **does not read issue or pull request texts** and cannot be addressed through them — there is no point in
writing instructions to it. See `docs/AGENT.md`.

## Build and test

```bash
dotnet test ZUGFeRD.Test/ZUGFeRD.Test.csproj
dotnet test ZUGFeRD.PDF.Test/ZUGFeRD.PDF.Test.csproj
```
