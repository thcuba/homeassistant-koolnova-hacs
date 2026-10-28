# Where the Koolnova API is documented

The Koolnova cloud API is **not public and not officially documented**. Everything known about it was
reverse-engineered from the `app.koolnova.com` webapp and verified against the client in this repo.
That makes this repository the most complete description of the API in existence, and it makes it easy
to lose track of which document holds what.

This page is the index: for any question about the API, here is the one file that answers it.

## Start here

| Question | File |
|---|---|
| What are the endpoints, headers, payloads and error codes? | [`API.md`](API.md) |
| Which endpoints exist and which do not? | [`../tests/API_METHODS_DISCOVERY.md`](../tests/API_METHODS_DISCOVERY.md) |
| How is the API actually called, in code? | [`../custom_components/koolnova/koolnova_api/client.py`](../custom_components/koolnova/koolnova_api/client.py) |
| Why does a request return `404`? | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |
| What are the rate limits I must not cross? | [`DEVELOPMENT.md`](DEVELOPMENT.md) (`Limits imposed by Koolnova`) and `API.md` |

## The reference

**[`docs/API.md`](API.md)** — the normative document. Base URL, the mandatory browser-like headers, the
login contract (`email`, never `username`), every endpoint with its verb and payload, the code tables
for project mode / zone status / fan speed, and the error-code table. If you change the client, update
this file in the same commit: it is the only description that exists.

The four rules that break everything when ignored are at the top of it, and they are worth repeating:

1. browser-like headers on **every** request — without them the API answers `404`, not `401`;
2. a trailing slash on **every** path;
3. at most one request every **30 s**, or your IP is banned;
4. a **50 s** minimum request timeout.

## Endpoint coverage

**[`tests/API_METHODS_DISCOVERY.md`](../tests/API_METHODS_DISCOVERY.md)** — the discovery record: which
endpoints were probed, which answered, and the negative result that matters just as much (the ~50 that
do not exist: `schedules/`, `planning/`, `history/`, `measurements/`, `diagnostics/`, `stats/`,
`analytics/`, `alerts/`, `energy/`, …). It also compares the surface against a typical HVAC API, which
is useful before proposing a feature: scheduling, historical data and energy management are **not**
available from the cloud.

**[`tests/specific_endpoints_results.json`](../tests/specific_endpoints_results.json)** — the raw
outcome of probing the administrative surface (`admin/`, `topics/reboot`, `projects/restart`, …):
`302`, `403` and `404`, i.e. a Django admin that redirects to a login and nothing callable.

## The living specification: the client

The documents can lag; the code cannot. These are the executable truth:

| File | Holds |
|---|---|
| `koolnova_api/const.py` | the base URL, the auth URL, `COMMON_HEADERS`, `PATCH_HEADERS` |
| `koolnova_api/session.py` | login, the 50-minute token renewal, the 300 s auth-failure cooldown |
| `koolnova_api/client.py` | one method per endpoint, the verbs, the parsing |
| `const.py` (component root) | the mode / status / speed code tables |
| `coordinator.py` | the polling cycle, and therefore the request budget |

The unit tests pin the contracts that have actually broken in production:
`tests/test_session.py` (the `email` field and the browser headers — the v1.3.0 → v1.3.1 regression),
`tests/test_client.py` (`PUT` for sensors, `PATCH` for topics, the cooldown), `tests/test_const.py`
(the code tables).

## Discovery methodology

If the API has to be re-probed (a new field, a new endpoint, Koolnova changing something), the
approach that produced the documents above is in
`tests/explore_api_deep.py`, `tests/explore_api_comprehensive.py` and `tests/diag_*.py`.

> These scripts must read credentials from the environment. Do not put an account in them —
> see [`../tests/README.md`](../tests/README.md).

## When the cloud is not enough: the local path

Two things are unavailable through the cloud API on most accounts, and both are reachable locally:

- **Humidity** — the cloud reports `sensor.topic_info.humidity` as the boolean `false` (see
  [`API.md`](API.md) under `GET /devices/`);
- **The full register surface** — the controller exposes more than the cloud relays.

The community integration
[`sinseman44/koolnova-BMS-Integration`](https://github.com/sinseman44/koolnova-BMS-Integration)
documents **Modbus RTU over RS485** for the `100-CPNR00` / `100-CPND00` controllers: an RS485-USB
dongle or an RS485/WiFi bridge (Elfin EW11), the Modbus toggle `INT 49` on the master radio thermostat,
per-area target (15-35 °C) and throughput (0-15), the global mode options including floor modules
`100-MSR002`, and the diagnostic entities. Its README carries the wiring schematics and the register
behaviour.

Two caveats from that project: the Modbus communication must be **enabled on the controller** (`INT 49`),
and **Koolnova 2.0 changed the register table** — that integration documents v1.0 only.

## Related

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — how the integration is put together (coordinator, platforms, vendored client)
- [`DEVELOPMENT.md`](DEVELOPMENT.md) — polling rates, the two cycles, the vendor-import rule
- [`DEV_ENV.md`](DEV_ENV.md) — the developer environment and the import rule
- [`DASHBOARDS.md`](DASHBOARDS.md) — Lovelace examples for the entities this API feeds
- [`RELEASE.md`](RELEASE.md) — versioning and the release process
