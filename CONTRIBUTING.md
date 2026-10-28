# Contributing to Koolnova for Home Assistant

Thanks for wanting to help. This is a custom HACS integration that talks to
the Koolnova cloud API — which is undocumented, brittle, and bans your IP if
you push it. Read `docs/API.md` before touching the client.

## Getting started

The integration lives in `custom_components/koolnova/` and must keep the
standard HACS shape: `custom_components/koolnova/`, `hacs.json` and
`README.md` at the repo root, no zips, no `zip_release`.

Run the client tests (stdlib `unittest`, no pytest, no HA install):

```bash
python3 -m unittest discover -s tests -t . -v
```

Every HTTP call is mocked. **Never put real credentials, tokens or hostnames
in the tests** — an earlier tests directory held exploration scripts with a
plaintext password and had to be purged from git history.

## Rules that come from the API

- Koolnova bans your IP when polled more than once every 30 s, and on
  repeated failed logins. `MIN_UPDATE_INTERVAL` is 30 s and there is a 300 s
  cooldown after a failed login — never lower them.
- The API needs browser-like headers on every request (`User-Agent`, `origin`,
  `referer`). Missing them produces 400/404s that look like auth failures.
- `koolnova_api/` is vendored on purpose. Use relative imports
  (`from .koolnova_api.client import ...`); never an absolute
  `import koolnova_api`, and never add the PyPI `koolnova-api` package as a
  dependency.

## Conventions

- Home Assistant-side code follows the HA developer guidelines. Translations
  go in `strings.json` and `translations/` (en, es, it).
- Version changes: bump `"version"` in
  `custom_components/koolnova/manifest.json` and add a matching entry to
  `CHANGELOG.md`. The git tag and the manifest version must match exactly
  (tag `v1.3.2` ↔ version `1.3.2`).
- Update `docs/` (`API.md`, `DEVELOPMENT.md`, `TROUBLESHOOTING.md`) when
  behavior changes.

## Testing changes

The vendored client is covered by the unit tests. The Home Assistant side
(`climate.py`, `coordinator.py`, `config_flow.py`) has no automated tests — it
only means something against a live HA instance and a real Koolnova account.
If you changed it, say what you tested on the PR.

## Issues and discussions

- Bugs → use the bug report template.
- Feature ideas → the feature request template.
- Questions → GitHub Discussions.
- Security problems → report privately via **Security → Report a
  vulnerability** (see [SECURITY.md](SECURITY.md)). Please don't open a public
  issue.
