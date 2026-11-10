# Northstar operating guide

## First-run sequence

1. Open the GitHub Pages site after the Pages deployment workflow succeeds.
2. Complete the legal checklist before any seller or investor solicitation. Obtain written guidance from an Illinois real-estate attorney and any required sponsoring broker.
3. Add seller leads only where the source and contact method are lawful and permission-based. Distinguish seller-stated facts from estimates.
4. Add investors with their target geography, property type, price range, strategy, and funding-verification status. Self-attestation is not proof of funds.
5. Underwrite using recent comparable closed sales, inspections, and documented repair estimates. The calculator performs arithmetic only.
6. Track deal stages and export a JSON backup regularly.
7. Generate a document discussion draft only for attorney review. It is not a binding or state-approved contract.

## Limits

- No server, login, encrypted storage, shared CRM, or cloud backup.
- No automatic lead discovery, cold calls, unsolicited texts, email campaigns, or restricted-site scraping.
- No valuation, title, lien, identity, proof-of-funds, or contract verification.
- No automatic assignment recommendation or execution.
- Do not store sensitive identifiers, bank details, credentials, or identity documents.

## Alternative-data workflow

The separate Python pipeline is run manually from GitHub Actions. Configure repository secrets SEC_USER_AGENT (descriptive app name plus monitored contact email) and EPA_API_KEY (free api.data.gov key). Then run the workflow named Run official-source research pipeline from the Actions tab. The SQLite database is uploaded as a short-lived workflow artifact, not committed to the public repository. SEC, EPA CAMPD, and Illinois WARN are contextual sources, not residential seller leads.
