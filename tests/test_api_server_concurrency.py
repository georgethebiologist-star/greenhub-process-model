from concurrent.futures import ThreadPoolExecutor
from threading import Event, Thread
from urllib.request import urlopen
from wsgiref.simple_server import make_server

from api.server import ThreadingWSGIServer


def test_health_like_http_request_is_served_while_another_request_is_waiting():
    slow_started = Event()
    release_slow = Event()

    def app(environ, start_response):
        if environ.get("PATH_INFO") == "/slow":
            slow_started.set()
            release_slow.wait(timeout=3)
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]

    server = make_server("127.0.0.1", 0, app, server_class=ThreadingWSGIServer)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            slow_request = pool.submit(lambda: urlopen(f"{base_url}/slow", timeout=2).read())
            assert slow_started.wait(timeout=1)
            with urlopen(f"{base_url}/health", timeout=1) as response:
                assert response.status == 200
                assert response.read() == b"ok"
            release_slow.set()
            assert slow_request.result(timeout=2) == b"ok"
    finally:
        release_slow.set()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
