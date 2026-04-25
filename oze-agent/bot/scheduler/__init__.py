"""Scheduled (non-request-response) jobs for the Telegram bot."""

from bot.scheduler.morning_brief_job import register_morning_brief

__all__ = ["register_morning_brief"]
