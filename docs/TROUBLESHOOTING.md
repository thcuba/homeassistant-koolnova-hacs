# Troubleshooting

Common problems when using the integration. If you are going to touch the code, read
[DEVELOPMENT.md](DEVELOPMENT.md) and [API.md](API.md) first.

## First of all: do not retry in a loop

Koolnova **bans your IP automatically** if their API receives more than one request every
30 seconds, or if it detects repeated failed logins. When something fails, do not reload the
integration over and over and do not lower the update interval: wait a few minutes between
attempts. A ban shows up as connection errors that persist even though the credentials are correct.

## The integration cannot connect / 404 errors in the logs

A `404` from this API almost never means the route does not exist: it means the request did not
look like it came from a browser. The API requires a modern Chrome `User-Agent` and the
`sec-ch-ua*` / `sec-fetch-*` headers (see `koolnova_api/const.py`).

If it starts failing out of nowhere without any change on your side, Koolnova has most likely
tightened that filter again — it happened in May 2026 (issue #4). Please open an issue.

## "Authentication failed" during setup

- Check your username and password by signing in to the official Koolnova app.
- Login uses the `email` field; if you modified the client to send `username`, the API answers
  `400 "Unable to log in with provided credentials"` (see [API.md](API.md#authentication)).
- After a failed login the integration waits 5 minutes before retrying, on purpose. It is not
  stuck.

## "No projects found"

The account has no active project. Create one in the Koolnova app first.

## Entities show as "unavailable"

In order of likelihood:

1. The project is offline (`is_online: false`) — check it in the official app.
2. The coordinator cannot update: check the logs.
3. Authentication problem or expired token; restart Home Assistant.

If it persists, delete the integration from the UI, restart HA and add it again.

## Changes are not applied

- **Temperature out of range**: adjust `min_temp` / `max_temp` in the integration options.
- The state HA shows comes from the last cached read; with a 30 s interval it can lag behind a
  change made from the official app.

## HACS: "No content to download"

The release tag and the `"version"` field in `manifest.json` do not match. That is a packaging
mistake, not something you did: please report it.

## Collecting information for an issue

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.koolnova: debug
```

Restart HA, reproduce the problem, and attach your Home Assistant version, the integration version
and the relevant logs to the
[issue](https://github.com/thcuba/homeassistant-koolnova/issues).

> Debug logs no longer include your password or token as of v1.3.0, but they **do** include your
> project and zone names. Review them before posting.

## Support
- **Issues** ? https://github.com/thcuba/homeassistant-koolnova/issues
- Include relevant logs.
- Specify HA & integration versions.