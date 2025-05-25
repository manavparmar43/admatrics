import asyncio
from datetime import datetime
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configure logging
logging.basicConfig(
    filename="cron_job.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,  
)


logger = logging.getLogger()
scheduler = AsyncIOScheduler()
for handler in logger.handlers:
    handler.setLevel(logging.INFO)
    handler.flush = lambda: handler.stream.flush()


async def log_timestamp():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Logging timestamp: {timestamp}")
    logging.info(f"Timestamp: {timestamp}")


def setup_scheduler():
    scheduler.add_job(log_timestamp, "interval", hours=6, replace_existing=True,id='log_timestamp_job')
    scheduler.start()
