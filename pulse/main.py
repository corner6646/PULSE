"""PULSE 主入口：全流程编排 + 定时调度。"""
import argparse
import logging
import sys
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from pulse.storage.db import init_db, mark_paper_processed
from pulse.ingestion.arxiv_fetcher import fetch
from pulse.llm.summarizer import batch_summarize
from pulse.delivery.notifier import send_papers


def _setup_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-5s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("pulse.log", encoding="utf-8"),
        ],
    )


def run_once() -> None:
    """执行一次完整的论文拉取 → 摘要 → 推送流程。"""
    logger = logging.getLogger("pulse.main")
    logger.info("=== PULSE pipeline start ===")

    # 1. 拉取
    try:
        papers = fetch()
    except Exception as e:
        logger.exception("Ingestion failed: %s", e)
        return

    if not papers:
        logger.info("No new papers found, pipeline ends")
        return

    # 2. 摘要
    try:
        results = batch_summarize(papers)
    except Exception as e:
        logger.exception("LLM processing failed: %s", e)
        return

    # 3. 标记已处理
    for paper, _ in results:
        mark_paper_processed(paper)

    # 4. 推送
    try:
        send_papers(results)
    except Exception as e:
        logger.exception("Delivery failed: %s", e)

    logger.info("=== PULSE pipeline done (%d papers sent) ===", len(results))


def start_scheduler() -> None:
    """启动 APScheduler 定时任务。"""
    hour, minute = settings.SCHEDULE_TIME.split(":")
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_once,
        trigger="cron",
        hour=int(hour),
        minute=int(minute),
        id="pulse_daily",
        name="PULSE Daily Paper Digest",
    )
    scheduler.start()
    logging.getLogger("pulse.main").info(
        "Scheduler started, will run daily at %s", settings.SCHEDULE_TIME
    )

    # 保持主线程存活
    try:
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logging.getLogger("pulse.main").info("Scheduler stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="PULSE - Paper Update & LLM Summarization Engine")
    parser.add_argument("--once", action="store_true", help="Run once immediately and exit")
    args = parser.parse_args()

    _setup_logging()
    init_db()

    if args.once:
        run_once()
    else:
        run_once()  # 启动时立即跑一次
        start_scheduler()


if __name__ == "__main__":
    main()
