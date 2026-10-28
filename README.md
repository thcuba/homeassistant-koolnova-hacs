# Koolnova Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom integration for Home Assistant that lets you control Koolnova HVAC systems via the Koolnova REST API.

Requires Home Assistant 2025.12.0 or newer and a Koolnova app account.

## Credits

**Original Creator:** [@luisgsluis](https://github.com/luisgsluis)  
**Current Maintainer:** [@thcuba](https://github.com/thcuba)

## Full Documentation

For developers and advanced users, see the detailed docs:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** � Architecture and import rules
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** � Common problems and solutions
- **[DEV_ENV.md](docs/DEV_ENV.md)** � Development environment setup
- **[API-INDEX.md](docs/API-INDEX.md)** — Where each part of the Koolnova API is documented
- **[API.md](docs/API.md)** � Koolnova API reference
- **[RELEASE.md](docs/RELEASE.md)** � Release history and process

### Features

- HVAC modes per zone and globally (COOL / HEAT / AUTO / OFF)
- Per-zone temperature control
- Fan-speed control (LOW / MEDIUM / HIGH / AUTO)
- Global project control
- Hub control on legacy accounts (ON/OFF + behavior mode)
- Connectivity binary sensor per project (online/offline)
- Per-zone on/off switch
- Smart polling (sensor updates every 3 minutes, cached projects)
- Advanced UI configuration
- ?? Translations: English, Spanish, Italian

### Entities

| Entity | Domain | Purpose |
|---|---|---|
| `climate.koolnova_*` (project) | climate | Global control: target temperature (median of zones), project HVAC mode, ECO/stop attributes |
| `climate.koolnova_*` (zone) | climate | One per room: temperature, setpoint, HVAC mode, fan speed |
| `climate.koolnova_hub_*` | climate | Legacy hub, one per hub: ON/OFF + manual / auto / planning |
| `switch.koolnova_<room>_power` | switch | One per room: power on/off toggle |
| `binary_sensor.koolnova_connectivity_status` | binary_sensor | Online/offline per project, ready for automations |

### Installation

#### HACS (recommended)
1. Add this repository as a custom integration in HACS.
2. Search for "Koolnova" in the store.
3. Install it and restart Home Assistant.

#### Manual
1. Copy `custom_components/koolnova/` into your Home Assistant configuration directory.
2. Restart Home Assistant.
3. Configure the integration via the UI.

### Configuration

1. Open **Configuration ? Devices & Services ? Add Integration**.
2. Search for "Koolnova".
3. Enter your Koolnova app credentials.
4. (Optional) Adjust advanced options.

#### Available Options

| Option | Default | Range |
|---|---|---|
| Update interval | 60 s | 30-3600 s |
| Project refresh frequency | every 10 cycles | 1-300 |
| Project HVAC modes | COOL, HEAT | COOL / HEAT / OFF / AUTO |
| Zone HVAC modes | OFF, AUTO | COOL / HEAT / OFF / AUTO |
| Temperature range | 21-27 C | 15-35 C |
| Temperature precision | 0.5 C | 0.5 or 1 C |
| API request timeout | 60 s | 50–300 s |

### Support

- **Issues**: [GitHub Issues](https://github.com/thcuba/homeassistant-koolnova/issues)
- **Documentation**: the `docs/` folder
- **License**: MIT

### Disclaimer

Unofficial project, not affiliated with Koolnova. It relies on an undocumented API that the
manufacturer may change or shut down at any time.
