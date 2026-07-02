# Evaluation Report Automation

## Initial connection

From the `netgenix` directory, run:

```bash
python scripts/generate_report.py connect-evaluation
```

Complete the Evaluation login and CAPTCHA in the browser, then return to the terminal and press Enter. NetGenix encrypts the resulting browser session in `data/evaluation-session.enc`; the encryption key and session files are excluded from Git.

## Operation

- **Refresh & Generate** downloads both Evaluation report sections, correctively upserts TimescaleDB, and generates Excel and PDF artifacts.
- **Generate from Latest** uses the selected seven-day period already held in TimescaleDB.
- Daily refresh runs at 01:00 CAT. The completed Thursday-Wednesday report runs Thursday at 06:00 CAT.
- If Evaluation login expires, refresh stops and the dashboard reports that re-authentication is required. It never silently generates from stale data.

The exporter also accepts a 14-day period for validation or backfill:

```bash
python scripts/generate_report.py export --start 2026-06-01 --end 2026-06-14
```
