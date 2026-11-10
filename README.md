# Northstar Acquisitions + Alternative Data Aggregator

A zero-cost, browser-based real-estate acquisition workspace with a separate Python alternative-data research pipeline.

## Current application

The GitHub Pages application is a self-contained dashboard. It supports local lead, buyer, and deal records; property underwriting; buyer matching; draft document generation; an operating checklist; and JSON/CSV exports. Records are stored in the current browser's local storage unless exported. There is no hosted database, account system, paid API, automatic seller contact, or automatic contract execution.

## Deploy

GitHub Actions publishes the repository root to GitHub Pages. In GitHub, enable **Settings → Pages → Build and deployment → GitHub Actions**. The workflow deploys on pushes to `main`.

## Alternative-data pipeline

The Python pipeline is a distinct research component. Planned sources are SEC company filings, EPA CAMPD, and Illinois WARN notices. These sources provide company, emissions, and labor-market context; they do **not** identify motivated residential sellers or establish property ownership. The pipeline uses SQLite and records source timestamps and provenance. Source endpoint validation is required before relying on live data.

## Legal and operational limits

This software is an organizational and calculation aid, not a brokerage, title, valuation, legal, or tax service. Do not market, negotiate, contract, or accept compensation unless the activity is permitted under applicable law and licensing requirements. Illinois wholesaling and brokerage rules require review by an Illinois-licensed real-estate attorney and, where applicable, a sponsoring brokerage. Document outputs are unexecuted drafts with conspicuous review warnings; they are not state-approved forms and are not legal advice.

Never enter sensitive personal information that you do not need. Do not store Social Security numbers, bank credentials, payment-card data, or identity documents in this browser app. Local browser storage is not encrypted or backed up. Export backups and protect the device.

## Files

- `index.html` — self-contained browser application.
- `docs/OPERATING_GUIDE.md` — concise operating sequence and limitations.
- `docs/ILLINOIS_COMPLIANCE.md` — legal review checklist, not legal advice.
- `aggregator/` — separate Python source-ingestion and signal pipeline.
- `.github/workflows/pages.yml` — GitHub Pages deployment.
