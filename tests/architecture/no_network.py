"""pytest plugin: make any outbound connection during the run an error.

The architecture gate must hold on a bare checkout, so it may read source and
in-process types but never reach a database or the network (AC-04).
"""

import socket


class NetworkAccessDuringArchitectureGate(AssertionError):
    pass


def _blocked(*args, **kwargs):
    raise NetworkAccessDuringArchitectureGate(
        "the architecture gate opened a connection; it must run on source and types alone"
    )


def pytest_configure(config):
    socket.socket.connect = _blocked
    socket.socket.connect_ex = _blocked
    socket.create_connection = _blocked
