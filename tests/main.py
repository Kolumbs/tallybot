"""Test tallybot command line call."""

import asyncio
import subprocess

import websockets

from tests import base
from tests.simulators import network, slack


class CommandLine(base.TestCase):
    """Test tallybot commandline."""

    def test(self):
        """Test main module."""
        with subprocess.Popen(
            ["env/bin/python", "tallybot", self.config_file],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        ) as subproc:
            try:
                self.connect()
            except Exception:
                subproc.terminate()
                print(subproc.stdout.read())
                raise
            else:
                subproc.terminate()

    def connect(self):
        """Connect to tallybot slack port."""
        port = self.config["slack"]["port"]
        network.wait_for_connection(port)
        challenge = "1234567890"
        status, headers, body = slack.send_challenge(
            challenge, port, self.config["slack"]["signing_secret"].encode("ascii")
        )
        self.assertEqual(status, 200)
        self.assertEqual(body, challenge.encode("ascii"))

    async def connect_websocket(self, port):
        async with websockets.connect(f"ws://localhost:{port}") as websocket:
            await websocket.send('{"text": "Hello, tallybot!"}')
            recv = await asyncio.wait_for(websocket.recv(), timeout=2)
            self.assertEqual(
                recv,
                '{"author": "tallyBot", "text": "What would you like me to do?"}',
            )
