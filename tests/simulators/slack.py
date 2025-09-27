"""Slack related functions.

`send_slack_event` sends a slack event to the server.
`send_challenge` sends a slack challenge to the server.
"""

import hmac
import json
import time
import urllib.request


def get_slack_signature(secret: bytes, body: bytes, timestamp: bytes) -> str:
    """Return slack signature.

    :param secret: Slack signing secret.
    :param body: Request body.
    :param timestamp: Request timestamp in seconds from epoch.
    """
    stamp = b"v0:" + timestamp + b":" + body
    hasher = hmac.new(secret, stamp, digestmod="sha256")
    return "v0=" + hasher.hexdigest()


def send_event(port: int, body: dict, secret: bytes):
    """Send slack event.

    :param port: Port to send slack event to.
    :param body: Slack event body.
    """
    payload = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    timestamp = str(int(time.time()))
    headers["X-Slack-Request-Timestamp"] = timestamp
    headers["X-Slack-Signature"] = get_slack_signature(
        secret, payload, timestamp.encode("ascii")
    )
    request = urllib.request.Request(
        f"http://localhost:{port}",
        headers=headers,
        data=payload,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            length = int(response.headers.get("Content-Length", 0))
            return response.status, response.headers, response.read(length)
    except TimeoutError:
        raise AssertionError(f"Request to {request.full_url} timed out")


def send_challenge(challenge: str, port: int, secret: bytes):
    """Send slack challenge."""
    body = {"type": "url_verification", "challenge": challenge}
    return send_event(port, body, secret)
