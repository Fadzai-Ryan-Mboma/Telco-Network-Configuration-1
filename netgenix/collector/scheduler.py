"""NetGenix Evaluation collector and report scheduler."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.netgenix.services.report_automation import create_job
from backend.netgenix.services.huawei_parameter_snapshots import (
    collect_all_site_huawei_parameter_snapshots,
)
from network.evaluation_exporter import default_daily_rolling_period, default_week_period
from network.mae_collector import run_collection


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("collector.scheduler")


def job_hourly_parameters() -> None:
    try:
        log.info(
            "Hourly Huawei parameter refresh complete: %s",
            collect_all_site_huawei_parameter_snapshots(),
        )
    except Exception as exc:
        log.exception("Hourly Huawei parameter refresh failed: %s", exc)


def job_daily() -> None:
    log.info("Daily Evaluation refresh started")
    try:
        log.info("Daily Evaluation refresh complete: %s", run_collection("daily", headless=True))
    except Exception as exc:
        log.exception("Daily Evaluation refresh failed: %s", exc)


def job_weekly() -> None:
    log.info("Weekly Evaluation report started")
    try:
        start, end = default_week_period()
        job = create_job(start, end, refresh=True)
        log.info("Weekly report queued: %s", job["job_id"])
    except Exception as exc:
        log.exception("Weekly report queueing failed: %s", exc)


def job_daily_rolling_report() -> None:
    log.info("Daily rolling report started")
    try:
        start, end = default_daily_rolling_period()
        job = create_job(start, end, refresh=True)
        log.info("Daily rolling report queued: %s", job["job_id"])
    except Exception as exc:
        log.exception("Daily rolling report queueing failed: %s", exc)


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone="Africa/Harare")
    scheduler.add_job(
        job_hourly_parameters,
        CronTrigger(minute=5),
        id="hourly_huawei_parameters",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        job_daily,
        CronTrigger(hour=1, minute=0),
        id="daily_evaluation",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        job_weekly,
        CronTrigger(day_of_week="thu", hour=6, minute=0),
        id="weekly_report",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        job_daily_rolling_report,
        CronTrigger(hour=5, minute=0),
        id="daily_rolling_report",
        max_instances=1,
        coalesce=True,
    )
    return scheduler


def main() -> None:
    scheduler = build_scheduler()
    log.info(
        "Scheduler started - hourly parameters, daily ingest 01:00, "
        "daily rolling report 05:00, Thursday report 06:00 CAT"
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped")


if __name__ == "__main__":
    main()
