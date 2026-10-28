# Tests

Tests for the vendored `koolnova_api` client. They run on the standard library alone
(`unittest` + `unittest.mock`) and need neither pytest nor a Home Assistant install:

```bash
python3 -m unittest discover -s tests -v
```

**Every HTTP call is mocked. Never put real credentials, tokens or hostnames in here** — an earlier
`tests/` directory held API exploration scripts with a plaintext password and had to be purged from
git history in v1.2.6.

These cover the parts that have actually broken in production:

| File | Guards against |
|---|---|
| `test_session.py` | the login payload field (`email`, not `username`) and the browser headers, i.e. the v1.3.0 → v1.3.1 regression and issue #4 |
| `test_client.py` | HTTP verbs and paths per endpoint (`PUT` for sensors, `PATCH` for topics), response parsing, and the auth-failure cooldown that prevents IP bans |
| `test_const.py` | the mode/status/fan code tables and their auto-generated inverses |
| `test_no_committed_secrets.py` | a credential or a real email address committed anywhere in the tree |

The Home Assistant side (`climate.py`, `coordinator.py`, `config_flow.py`) is not covered: it needs
a running Home Assistant to be meaningful. See [../docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md).
