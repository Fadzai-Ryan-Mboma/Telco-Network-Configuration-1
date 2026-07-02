from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from backend.netgenix.reports import engine
from backend.netgenix.services import database
from backend.netgenix.services.parameter_catalog import TOP_5_PARAMETERS
from backend.netgenix.services.evaluation_ingestion import _extract_csvs
from network import evaluation_exporter
from network.evaluation_exporter import default_daily_rolling_period, default_week_period, validate_period


class EvaluationPeriodTests(unittest.TestCase):
    def test_previous_completed_thursday_to_wednesday(self):
        start, end = default_week_period(date(2026, 6, 29))
        self.assertEqual(start, date(2026, 6, 18))
        self.assertEqual(end, date(2026, 6, 24))

    def test_daily_rolling_period_ends_yesterday(self):
        start, end = default_daily_rolling_period(date(2026, 6, 29))
        self.assertEqual(end, date(2026, 6, 28))
        self.assertEqual(start, date(2026, 6, 22))
        self.assertEqual((end - start).days + 1, 7)

    def test_seven_and_fourteen_day_validation(self):
        self.assertEqual(validate_period(date(2026, 6, 1), date(2026, 6, 7)), 7)
        self.assertEqual(validate_period(date(2026, 6, 1), date(2026, 6, 14)), 14)
        with self.assertRaises(ValueError):
            validate_period(date(2026, 6, 1), date(2026, 6, 8))

    def test_session_key_is_created_with_restricted_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            key_path = Path(temp) / "session.key"
            with patch.object(evaluation_exporter, "SESSION_KEY_PATH", key_path), patch.dict(
                "os.environ", {"EVALUATION_SESSION_KEY": ""}
            ):
                cipher = evaluation_exporter._fernet(create=True)
                token = cipher.encrypt(b"state")
                self.assertEqual(evaluation_exporter._fernet().decrypt(token), b"state")
                self.assertEqual(key_path.stat().st_mode & 0o777, 0o600)

    def test_session_prefers_key_file_over_environment_override(self):
        with tempfile.TemporaryDirectory() as temp:
            key_path = Path(temp) / "session.key"
            session_path = Path(temp) / "session.enc"
            good_key = evaluation_exporter.Fernet.generate_key().decode("ascii")
            bad_key = evaluation_exporter.Fernet.generate_key().decode("ascii")
            key_path.write_text(good_key, encoding="ascii")
            session_path.write_bytes(evaluation_exporter.Fernet(good_key.encode("ascii")).encrypt(b'{"cookies": []}'))

            with patch.object(evaluation_exporter, "SESSION_KEY_PATH", key_path), patch.dict(
                "os.environ", {"EVALUATION_SESSION_KEY": bad_key}
            ):
                payload = evaluation_exporter.load_session(session_path)
                self.assertEqual(payload, {"cookies": []})

    def test_scheduler_uses_harare_daily_and_thursday_windows(self):
        try:
            from collector.scheduler import build_scheduler
        except ModuleNotFoundError as exc:
            if exc.name == "apscheduler":
                self.skipTest("APScheduler is installed in the collector image")
            raise
        scheduler = build_scheduler()
        jobs = {job.id: str(job.trigger) for job in scheduler.get_jobs()}
        self.assertEqual(str(scheduler.timezone), "Africa/Harare")
        self.assertIn("hour='1'", jobs["daily_evaluation"])
        self.assertIn("day_of_week='thu'", jobs["weekly_report"])
        self.assertIn("hour='6'", jobs["weekly_report"])
        self.assertIn("hour='5'", jobs["daily_rolling_report"])


class EvaluationZipTests(unittest.TestCase):
    def test_zip_members_are_flattened_to_safe_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_path = root / "report.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("nested/Cell Level KPIs.csv", "header")
                archive.writestr("../Whole Network Main KPIs.csv", "header")
                archive.writestr("notes.txt", "ignored")
            output = root / "output"
            output.mkdir()
            extracted = _extract_csvs(archive_path, output)
            self.assertEqual(
                {path.name for path in extracted},
                {"Cell Level KPIs.csv", "Whole Network Main KPIs.csv"},
            )
            self.assertTrue(all(path.parent == output for path in extracted))

    def test_mismatched_section_period_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "report.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(
                    "report(Whole Network Main KPIs).csv",
                    "Date,Whole Network\n2025-12-01,Whole Network\n",
                )
                archive.writestr(
                    "report(Cell Level KPIs).csv",
                    "Date,Cell Name\n2026-06-23,CELL-1\n2026-06-29,CELL-1\n",
                )
            with self.assertRaisesRegex(RuntimeError, "Whole Network Main KPIs"):
                evaluation_exporter._validate_downloaded_period(
                    archive_path, date(2026, 6, 23), date(2026, 6, 29)
                )


class EvaluationOnlyReportTests(unittest.TestCase):
    def test_database_report_marks_external_metrics_unavailable(self):
        rows = [
            {
                "Date": "2026-06-02",
                "eNodeB Name": "SITE-001",
                "Total Traffic (Gbit)": 8.0,
                "DL PRB Usage Rate(%)": 40.0,
                "Call Drop Rate (All)(%)": 1.0,
                "Radio Net Availability Rate(%)": 99.9,
            }
        ]
        with tempfile.TemporaryDirectory() as temp, patch.object(engine, "REPORT_ROOT", Path(temp)):
            result = engine.run_report_from_rows(
                rows,
                source_label="test database",
                exclusions=["NOT-THIS-SITE"],
                evaluation_only=True,
            )
            audit = json.loads(Path(result["audit_file"]).read_text(encoding="utf-8"))
            self.assertEqual(audit["executive_kpis"]["active_subscribers"], "N/A")
            self.assertEqual(audit["executive_kpis"]["peak_throughput_mbps"], "N/A")
            self.assertTrue(Path(result["output_file"]).exists())
            self.assertTrue(Path(result["pdf_file"]).exists())


class NetGenixBridgeTests(unittest.TestCase):
    def test_dashboard_parameter_catalog_is_back_to_five_cards(self):
        self.assertEqual(
            [parameter.key for parameter in TOP_5_PARAMETERS],
            [
                "reference_signal_power_pdschcfg",
                "a3_event_offset",
                "t310_timer",
                "p0_nominal_pusch",
                "pdcch_aggregation_level",
            ],
        )

    def test_timescale_summary_is_mapped_to_legacy_kpis(self):
        with patch.object(
            database,
            "_timescale_site_kpis",
            return_value={
                "network_access_success": 98.5,
                "download_speed": 12.4,
                "download_quality": 93.0,
                "upload_speed": 4.1,
                "upload_quality": 91.0,
                "control_channel_load": 37.0,
                "feedback_channel_load": 18.0,
                "timestamp": "2026-06-29T00:00:00+00:00",
            },
        ):
            result = database.get_site_kpis("SITE-001")
        self.assertEqual(result["network_access_success"], 98.5)
        self.assertEqual(result["download_speed"], 12.4)
        self.assertEqual(result["control_channel_load"], 37.0)

    def test_timescale_history_is_used_before_sqlite_fallback(self):
        with patch.object(
            database,
            "_timescale_kpi_history",
            return_value=[("2026-06-23", 96.2), ("2026-06-24", 97.0)],
        ):
            history = database.get_kpi_history("SITE-001", "network_access_success", 7)
        self.assertEqual(history, [("2026-06-23", 96.2), ("2026-06-24", 97.0)])


if __name__ == "__main__":
    unittest.main()
