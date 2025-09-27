"""Email sending facility."""

import email.message
from smtplib import LMTP


def send(msg: email.message.Message, port: int, host: str = "localhost"):
    """Send email message."""
    with LMTP(host=host, port=port) as lmtp:
        lmtp.send_message(msg, msg["from"], msg["to"])
