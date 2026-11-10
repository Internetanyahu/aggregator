# Data source registry and limitations

## SEC EDGAR

- Company submissions: https://data.sec.gov/submissions/CIK##########.json
- Company tickers: https://www.sec.gov/files/company_tickers.json
- Access is public and does not require an API key. Automated access must use an accurate descriptive User-Agent and follow SEC fair-access guidance.
- SEC records describe filer disclosures, not the ownership or availability of any particular real estate asset.

## EPA CAMPD

- Official portal: https://www.epa.gov/power-sector/cam-api-portal
- Example endpoint: https://api.epa.gov/easey/streaming-services/emissions/apportioned/hourly
- Requires a free api.data.gov key in EPA's published examples. Configure EPA_API_KEY in the environment; never commit the key.
- Hourly endpoint requests are restricted here to a maximum 31-day window. EPA documents a default 1,000 requests/hour and a 500-row page limit for paginated endpoints.
- Emissions observations are environmental / industrial context, not residential property condition data.

## Illinois WARN

- Official state context: https://dceo.illinois.gov/workforcedevelopment/warn.html
- Official monthly reports archive: https://www.illinoisworknet.com/LayoffRecovery/Pages/ArchivedWARNReports.aspx
- Reports are published as monthly downloadable files; current implementation discovers XLSX links from the official archive and parses them with openpyxl.
- Some older archive periods are PDF-only and are not ingested by this initial XLSX adapter. The official state warns that notices do not capture all layoff activity and are not a proxy for employment or job-loss data.
- WARN notices do not establish seller motivation, financial distress, property ownership, or availability.

## Research controls

Every stored observation includes source, source identifier, source URL, publication date when available, and retrieval timestamp. Signals are deliberately descriptive and assigned a neutral score until a validated research methodology exists. Do not use these observations as a substitute for title records, county property records, comparable sales, inspections, or direct seller authorization.
