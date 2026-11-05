"""Run the GreenHub WSGI API with Python's development server."""

from __future__ import annotations

import os
from wsgiref.simple_server import make_server

from .app import application
from .server import ThreadingWSGIServer


def main() -> None:
    host = os.environ.get("GREENHUB_API_HOST", "127.0.0.1")
    port = int(os.environ.get("GREENHUB_API_PORT", "8000"))
    print(f"GreenHub API listening on http://{host}:{port}/api/v1/health")
    print("HTTP requests are concurrent; BioSTEAM simulations are serialized for global-state safety.")
    with make_server(host, port, application, server_class=ThreadingWSGIServer) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
