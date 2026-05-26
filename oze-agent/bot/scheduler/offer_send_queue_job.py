"""PTB JobQueue wrapper for durable offer-send attempts."""

import logging

from telegram.ext import Application, ContextTypes

from bot.config import Config
from shared.offers.queue_worker import process_offer_send_queue_once

logger = logging.getLogger(__name__)

JOB_NAME = "offer_send_queue"


async def _offer_send_queue_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    processed = await process_offer_send_queue_once(
        context.bot,
        limit=Config.OFFER_SEND_QUEUE_BATCH_SIZE,
    )
    if processed:
        logger.info("offer_send_queue.run processed=%d", processed)


def register_offer_send_queue(app: Application) -> None:
    if not Config.OFFER_SEND_QUEUE_ENABLED:
        logger.info("offer_send_queue: disabled")
        return
    job_queue = app.job_queue
    if job_queue is None:
        logger.warning(
            "offer_send_queue: JobQueue unavailable on Application — "
            "offer sends will not be processed in this bot process"
        )
        return
    job_queue.run_repeating(
        _offer_send_queue_callback,
        interval=Config.OFFER_SEND_QUEUE_INTERVAL_SECONDS,
        first=5,
        name=JOB_NAME,
    )
    logger.info(
        "offer_send_queue: scheduled every %ss batch_size=%s",
        Config.OFFER_SEND_QUEUE_INTERVAL_SECONDS,
        Config.OFFER_SEND_QUEUE_BATCH_SIZE,
    )
