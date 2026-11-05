"""Local WSGI server that keeps read-only UI endpoints responsive during runs."""

from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """Handle independent HTTP requests concurrently.

    Simulation execution is serialized separately because BioSTEAM relies on
    process-global flowsheet and settings state. Read-only endpoints therefore
    remain responsive while a model run is in progress.
    """

    daemon_threads = True
