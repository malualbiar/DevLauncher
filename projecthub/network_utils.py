"""Small networking helpers used to detect whether a server is up."""

import socket


def is_port_available(host: str, port: int) -> bool:
    """Return True if nothing is currently listening on host:port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.settimeout(0.5)
        result = sock.connect_ex((host, port))
        return result != 0

    except OSError:
        return False

    finally:
        sock.close()
