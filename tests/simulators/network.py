"""Network related requests."""

import socket
import time


def wait_for_connection(port, timeout=2):
    """Open socket and wait for connection."""
    start = time.time()
    while start + timeout > time.time():
        sock = socket.socket()
        try:
            sock.connect(("localhost", port))
        except ConnectionRefusedError:
            time.sleep(0.01)
        else:
            sock.shutdown(socket.SHUT_RDWR)
            return
        finally:
            sock.close()
    raise AssertionError("Did not establish connection within timeout")
