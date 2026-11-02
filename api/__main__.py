"""Run the GreenHub WSGI API with Python's development server."""

from __future__ import annotations

import os
from wsgiref.simple_server import make_server

from .app import application


def main() -> None:
    host = os.environ.get("GREENHUB_API_HOST", "127.0.0.1")
    port = int(os.environ.get("GREENHUB_API_PORT", "8000"))
    print(f"GreenHub API listening on http://{host}:{port}/api/v1/health")
    print("This development server executes simulations synchronously.")
    with make_server(host, port, application) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
