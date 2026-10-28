"""Integration tests: the real client + session over real HTTP to a local server.

Home Assistant itself cannot be exercised here (no live Koolnova account, no HA), so
"integration" means the full client->session->requests stack against a real socket,
with the URL constants pointed at a local http.server instead of api.koolnova.com.
Every HTTP call goes through the unmodified requests library: no requests.Session mock.

No real Koolnova credentials are used anywhere (see CLAUDE.md: credentials must never
appear in tests).
"""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from requests.exceptions import HTTPError

import koolnova_api.session as session_module
from koolnova_api.client import KoolnovaAPIRestClient

PROJECTS = {
    "data": [
        {
            "name": "Home",
            "topic": {
                "id": 42,
                "name": "Main topic",
                "mode": "1",
                "is_stop": False,
                "is_online": True,
                "eco": False,
                "last_sync": "2026-07-01T10:00:00Z",
            },
        }
    ]
}


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # silence the default per-request log
        pass

    def _dispatch(self):
        path = self.path.split("?", 1)[0]
        plan = self.server.plan.get(path)
        if not plan:
            self._reply(404, {"detail": f"no plan for {path}"})
            return
        status, payload, headers = plan.pop(0)
        self._reply(status, payload, headers)

    def _reply(self, status, payload, headers):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _record(self, method):
        # Reading the body keeps HTTP/1.1 keep-alive clean across requests.
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        payload = json.loads(body) if body else None
        path = self.path.split("?", 1)[0]
        self.server.hits.append(f"{method} {path}")
        if payload is not None:
            self.server.posts.append((path, payload))

    def do_GET(self):
        self._record("GET")
        self._dispatch()

    def do_POST(self):
        self._record("POST")
        self._dispatch()


class IntegrationTestCase(unittest.TestCase):
    """Base class: local HTTP server + the client pointed at it."""

    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.server.plan = {}
        self.server.hits = []
        self.server.posts = []
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

        base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self._patches = [
            patch.object(session_module, "KOOLNOVA_API_URL", base),
            patch.object(session_module, "KOOLNOVA_AUTH_URL", base + "/auth/v2/login/"),
            patch.object(session_module.KoolnovaClientSession, "host", base),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self.server.shutdown()
        self.server.server_close()

    def _plan(self, path, responses):
        self.server.plan[path] = responses

    def _authenticated_client(self):
        """Client whose login is pre-answered by the local server."""
        self._plan("/auth/v2/login/", [(200, {"access_token": "tok"}, None)])
        return KoolnovaAPIRestClient("user@example.com", "secret")


class AuthIntegrationTest(IntegrationTestCase):
    def test_login_sends_the_email_field_over_real_http(self):
        """Regression guard for v1.3.0: 'username' makes the API answer 400."""
        self._plan("/auth/v2/login/", [(200, {"access_token": "tok"}, None)])
        client = KoolnovaAPIRestClient("user@example.com", "secret")
        client._get_session()  # auth is lazy: it runs on the first request

        self.assertEqual(
            self.server.posts,
            [("/auth/v2/login/", {"email": "user@example.com", "password": "secret"})],
        )

    def test_login_returns_a_token_and_projects_are_fetched(self):
        self._plan("/projects/", [(200, PROJECTS, None)])

        client = self._authenticated_client()
        projects = client.get_project()

        self.assertEqual(projects[0]["Topic_id"], 42)
        self.assertEqual(self.server.hits.count("POST /auth/v2/login/"), 1)
        self.assertEqual(self.server.hits.count("GET /projects/"), 1)


class RetryIntegrationTest(IntegrationTestCase):
    def test_a_401_refreshes_the_token_and_retries(self):
        # Two login responses: the initial one and the refresh triggered by the 401.
        # (Not via _authenticated_client: it would overwrite this plan.)
        self._plan("/auth/v2/login/", [(200, {"access_token": "tok"}, None), (200, {"access_token": "tok2"}, None)])
        self._plan("/projects/", [(401, {"detail": "expired"}, None), (200, PROJECTS, None)])

        client = KoolnovaAPIRestClient("user@example.com", "secret")
        projects = client.get_project()

        self.assertEqual(projects[0]["Topic_id"], 42)
        # login, projects(401), refreshed login, projects(200)
        self.assertEqual(self.server.hits.count("POST /auth/v2/login/"), 2)
        self.assertEqual(self.server.hits.count("GET /projects/"), 2)

    def test_a_rate_limit_is_retried_and_honours_retry_after(self):
        self._plan("/projects/", [(429, {"detail": "slow down"}, {"Retry-After": "0"}), (200, PROJECTS, None)])

        client = self._authenticated_client()
        projects = client.get_project()

        self.assertEqual(projects[0]["Topic_id"], 42)
        self.assertEqual(self.server.hits.count("GET /projects/"), 2)

    def test_a_server_error_is_retried(self):
        self._plan("/projects/", [(500, {"detail": "boom"}, None), (200, PROJECTS, None)])

        client = self._authenticated_client()
        projects = client.get_project()

        self.assertEqual(projects[0]["Topic_id"], 42)
        self.assertEqual(self.server.hits.count("GET /projects/"), 2)

    def test_a_persistent_server_error_is_surfaced(self):
        # default max_retries=3 -> 4 attempts, all failing
        self._plan("/projects/", [(500, {"detail": "boom"}, None)] * 4)

        client = self._authenticated_client()
        with self.assertRaises(HTTPError):
            client.get_project()

        self.assertEqual(self.server.hits.count("GET /projects/"), 4)


class HubIntegrationTest(IntegrationTestCase):
    def test_hub_discovery_and_state_over_real_http(self):
        self._plan("/modules/", [(200, [{"Serial": "HB1", "ModuleType_Id": 2}], None)])
        self._plan("/hub/HB1/state", [(200, {"stateEquipment": True, "behavior": "auto"}, None)])

        client = self._authenticated_client()

        self.assertEqual(client.search_all_ids(), {"koolnova": [], "hub": ["HB1"]})
        self.assertEqual(client.get_hub_state("HB1"), {"state": True, "mode": "auto"})


if __name__ == "__main__":
    unittest.main()
