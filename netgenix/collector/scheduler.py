"""
NetGenix Collector — APScheduler daemon.

Schedule
--------
  Hourly  : :05 every hour  → mae_collector.run_collection("hourly")
  Weekly  : Sunday 01:00    → mae_collector.run_collection("weekly")

Run:
  python collector/scheduler.py
"""

import logging
import sys
import time
from pathlib import Path

# make sure repo root is on sys.path when run directly inside the container
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from network.mae_collector import run_collection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("collector.scheduler")


def job_hourly():
    log.info("=== Hourly collection triggered ===")
    try:
        run_collection(mode="hourly", headless=True)
    except Exception as exc:
        log.exception("Hourly collection failed: %s", exc)


def job_weekly():
    log.info("=== Weekly collection triggered ===")
    try:
        run_collection(mode="weekly", headless=True)
    except Exception as exc:
        log.exception("Weekly collection failed: %s", exc)


def main():
    scheduler = BlockingScheduler(timezone="Africa/Harare")

    # Every hour at :05 (gives MAE time to close the previous hour's counters)
    scheduler.add_job(job_hourly, CronTrigger(minute=5), id="hourly_kpi")

    # Every Sunday at 01:00 local time
    scheduler.add_job(job_weekly, CronTrigger(day_of_week="sun", hour=1, minute=0), id="weekly_kpi")

    log.info("Scheduler started — hourly(:05) + weekly(Sun 01:00 CAT)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped")


if __name__ == "__main__":
    main()
