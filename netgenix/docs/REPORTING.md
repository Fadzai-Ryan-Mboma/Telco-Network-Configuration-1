# NetGenix Reporting Sections

The v2 reporting module is file-first. For now, a person logs into MAE/Evaluation, Telrad, EPC, and subscriber systems, downloads the raw Excel/CSV exports, and uploads those files into NetGenix. NetGenix then performs Brighton's Excel "cooking" steps and generates an Excel workbook plus audit JSON under ignored `runtime/reports/`.

## Current Operating Model

- Human downloads raw Excel/CSV files from the source platforms.
- NetGenix accepts one or more raw files in the Reports tab.
- NetGenix detects column mappings before cooking the report.
- NetGenix converts Evaluation traffic from `Gbit` to `GB` when source columns indicate Gbit.
- NetGenix computes the weekly KPIs, top/bottom site rankings, executive KPI values, exceptions, and audit trail.
- Site exclusions remain operator-provided through the exclusions field.

## Generated Workbook Sections

- `Summary`: run totals, included/excluded site counts, headline traffic/subscriber values.
- `Report Sections`: generated section inventory for audit and operator review.
- `Executive KPI`: weekly executive network health snapshot.
- `GCO Report`: copy-forward section for GCO/GCOO style reporting.
- `GCU Report`: copy-forward section for GCU/GCUO style reporting.
- `General Report`: reusable general weekly KPI section.
- `Site Performance`: per-site metrics.
- `Top 20 Traffic`: top sites by weekly traffic.
- `Bottom 20 Traffic`: bottom sites by weekly traffic.
- `Top 20 PRB`: highest busy-hour PRB weekly averages.
- `Bottom 20 PRB`: lowest busy-hour PRB weekly averages.
- `Top 20 Code Drop`: highest weekly code/drop-rate averages.
- `Bottom 20 Code Drop`: lowest weekly code/drop-rate averages.
- `Exceptions`: excluded/new/non-commercialised sites and missing-site rows.
- `Audit`: input file, generated output, row counts, exclusions, source columns.

## Recognised Input Concepts

The importer currently recognises common column-name variants for:

- Site name
- Traffic in GB or Evaluation-style Gbit
- Busy-hour PRB utilisation
- Code/drop rate
- Radio network availability
- Active subscribers
- Addressable/total subscribers
- Peak throughput Mbps
- Average/total throughput Mbps

## Brighton-Parity Cooking Logic

- Traffic: source `Gbit` values are divided by `8` to produce `GB`.
- Traffic TB: computed from cooked `GB` values using decimal reporting conversion.
- PRB utilisation: weekly average by site.
- Code drop: weekly average by site.
- Top/bottom rankings: top 20 and bottom 20 after operator exclusions.
- Executive values: reused across GCO, GCU, and General workbook sections.

## Testing Still Needed

- Use the built-in sample files from the Reports tab for smoke testing.
- Validate real Evaluation exports and adjust column aliases.
- Validate real Telrad exports and radio availability mapping.
- Validate subscriber extracts and EPC monthly report columns.
- Confirm whether source traffic is already GB or still Gb/bit-based in each export.
- Confirm final GCO/GCU template cell layout before exact cell-population mapping.

## Current UI Features

- Column mapping preview before generation.
- Generated report sections preview after generation.
- Report run history with download links.
- Sample Evaluation, Telrad, and EPC/subscriber CSV downloads.
