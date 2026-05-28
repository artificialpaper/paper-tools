"""Built-in email tools."""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> dict:
    """Send a follow-up email."""
    logger.info("tool.send_email", extra={"to": to, "subject": subject})
    return {"status": "sent", "to": to, "subject": subject, "message_id": f"msg_{hash(to + subject) % 100000}"}
