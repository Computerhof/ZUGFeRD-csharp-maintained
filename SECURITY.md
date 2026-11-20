# Security policy

## Reporting a vulnerability

Please report vulnerabilities **privately** via GitHub:
**Security → Report a vulnerability** in this repository
(<https://github.com/Computerhof/ZUGFeRD-csharp-maintained/security/advisories/new>).

Do not open a public issue for security problems. There is no e-mail address for reports.

Helpful: affected version or commit, a minimal input that shows the problem (invented data, never real invoices),
and the observed effect.

## Scope

Maintained are the libraries `ZUGFeRD` (package `ChriveSolutions.ZUGFeRD`) and `ZUGFeRD.PDF`
(package `ChriveSolutions.ZUGFeRD.PDF`). `ZUGFeRD.Excel`, `ZUGFeRD.Render` and the demo projects are kept as
received from the original and are not maintained.

## What to expect

This is a maintenance fork for our own products. Reports are read and assessed, but there is **no guaranteed
response or fix time**. Fixed issues are listed in `CHANGELOG.md` and, where appropriate, published as a
GitHub security advisory.

## Known hardening topics

Since 18.1.0, `InvoiceDescriptor.Load` and `GetVersion` reject documents with a `<!DOCTYPE` (`XmlException`; no
entity expansion, no external resources) and detect the version by streaming instead of copying the document once per
reader. Loading still builds the whole document in memory (`XmlDocument`, a few times the input size), so callers that
process XML from unknown senders should still limit the input size. Versions up to 18.0.1 (including the original
package `ZUGFeRD-csharp`) resolve internal entities and use about 26 times the input size in memory.
