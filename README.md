> [!IMPORTANT]
> **Maintenance fork.** This repository is a fork of [ZUGFeRD-csharp](https://github.com/stephanstapel/ZUGFeRD-csharp)
> by Stephan Stapel (Apache-2.0), maintained by chrive-solutions e.U. **for its own products**. The original's
> maintenance ends on 30 November 2026; this fork keeps the library usable (bug fixes, security fixes, checks
> against the standards).
>
> - **No commitments to third parties:** no support, no response times, no roadmap.
> - **Issues are welcome.** Pull requests are reviewed, but without a response deadline (see `CONTRIBUTING.md`).
> - **Security reports** only privately, see `SECURITY.md`.
> - Packages: `ChriveSolutions.ZUGFeRD` and `ChriveSolutions.ZUGFeRD.PDF` on GitHub Packages. Assembly names and
>   namespaces (`s2industries.ZUGFeRD`) are unchanged. Only `ZUGFeRD` and `ZUGFeRD.PDF` are maintained.
> - Credits: original work Copyright 2013-2026 Stephan Stapel / STwo Industries GmbH, see `NOTICE` and `LICENSE.txt`.
>
> The original author's text follows unchanged.

## Maintenance ends on November 30, 2026

ZUGFeRD-csharp is entering its final maintenance phase. My maintenance of this project will end on November 30, 2026.

Until that date, maintenance will be limited to selected significant bug fixes and the review of reported security issues. No new features or support for new versions of invoicing standards are planned. There are no guaranteed response or resolution times.

From December 1, 2026, the NuGet packages will be marked as deprecated (Legacy), and this repository will be archived.

Existing releases and source code will remain available under their existing open-source license. You may continue using them or maintain an independent fork. This does not imply compatibility with future standards, validators, or runtime versions.

Active development, support for evolving standards, and commercial support continue in FactoorSharp, the commercial successor:

https://www.factoorsharp.de

Migration guide:
https://www.factoorsharp.de/en/Home/GettingStarted

Thank you to everyone who has contributed code, reported issues, sponsored development, or supported this project since 2013.

## FactoorSharp — the commercial successor

FactoorSharp builds on the experience gained from ZUGFeRD-csharp since 2013 and continues its active development as a commercial .NET SDK.

For new projects and existing applications that need ongoing updates, support for evolving standards, and professional support, we recommend FactoorSharp.

### Why choose FactoorSharp?

- **Current and evolving invoicing standards**  
  Create and read ZUGFeRD, Factur-X, XRechnung, and Peppol BIS Billing 3.0 documents in CII and UBL format. Receive updates for supported standards during your active subscription.

- **Advanced validation**  
  Check electronic invoices and PDF documents using validation tools such as Mustang, Valitool, and veraPDF, with actionable results to help identify issues early.

- **PDF processing and invoice visualization**  
  Embed invoice XML into PDF/A-3 documents and generate human-readable invoice representations from structured invoice data.

- **Analysis tools and online services**  
  Inspect XML and PDF invoices for profiles, embedded invoice data, structure, and common sources of errors.

- **Professional support**  
  Get assistance with integration, migration, and technical questions during your active subscription.

### Migrating from ZUGFeRD-csharp

FactoorSharp uses a familiar invoice model and an intentionally similar API to help you reuse existing application logic.

Start with the migration information and test your application's invoice output against the requirements relevant to your use case:

https://www.factoorsharp.de/en/Home/GettingStarted

### Try FactoorSharp

Register for a free 30-day trial with the full feature set. No payment details are required.

https://www.factoorsharp.de/en/Account/SignUp

### Resources

- Website and licensing: https://www.factoorsharp.de
- Core NuGet package: https://www.nuget.org/packages/FactoorSharp.FacturX
- PDF NuGet package: https://www.nuget.org/packages/FactoorSharp.FacturX.PDF
- Issues and support information: https://github.com/S2-Industries/FactoorSharp.FacturX

FactoorSharp requires a separate commercial license. Existing open-source releases of ZUGFeRD-csharp remain usable under their existing license.
