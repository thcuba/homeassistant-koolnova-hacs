"""Tests for the Koolnova coordinator.

Home Assistant is not installed in CI, so module-level stubs are registered
before any ``custom_components.koolnova`` import touches ``__init__.py`` or
``coordinator.py`` (both depend on HA symbols).
"""

import importlib.util
import sys
import types
import unittest
import asyncio
from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent


def _install_home_assistant_stubs():
    """Register minimal stubs for every HA symbol that the package init and
    coordinator need, so these tests can run without Home Assistant installed."""
    if "homeassistant.core" in sys.modules:
        return

    # ---- homeassistant.config_entries ----
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = MagicMock

    # ---- homeassistant.core ----
    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = MagicMock

    # ---- homeassistant.exceptions ----
    exceptions = types.ModuleType("homeassistant.exceptions")
    exceptions.ConfigEntryAuthFailed = type("ConfigEntryAuthFailed", (Exception,), {})

    # ---- homeassistant.helpers.update_coordinator ----
    class _DataUpdateCoordinator:
        """Minimal stand-in so KoolnovaDataUpdateCoordinator.__init__ can
        call super().__init__(hass, logger, **kwargs) without going through
        MagicMock's spec machinery."""
        def __init__(self, hass, logger, **kwargs):
            self.hass = hass
            self.update_interval = kwargs.get("update_interval")
            self.data = {}

    uc = types.ModuleType("homeassistant.helpers.update_coordinator")
    uc.DataUpdateCoordinator = _DataUpdateCoordinator
    uc.UpdateFailed = type("UpdateFailed", (Exception,), {})

    # ---- homeassistant.const ----
    ha_const = types.ModuleType("homeassistant.const")
    ha_const.Platform = MagicMock

    # ---- homeassistant.components.climate (same stub as test_const.py) ----
    from enum import StrEnum

    class HVACMode(StrEnum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        HEAT_COOL = "heat_cool"
        AUTO = "auto"
        DRY = "dry"
        FAN_ONLY = "fan_only"

    climate = types.ModuleType("homeassistant.components.climate")
    climate.HVACMode = HVACMode
    climate.FAN_LOW = "low"
    climate.FAN_MEDIUM = "medium"
    climate.FAN_HIGH = "high"
    climate.FAN_AUTO = "auto"

    # ---- Wire the package tree ----
    ha = types.ModuleType("homeassistant")
    ha.const = ha_const
    ha.config_entries = config_entries
    ha.core = core
    ha.exceptions = exceptions

    components = types.ModuleType("homeassistant.components")
    components.climate = climate

    helpers = types.ModuleType("homeassistant.helpers")
    helpers.update_coordinator = uc

    ha.components = components
    ha.helpers = helpers

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.const"] = ha_const
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.exceptions"] = exceptions
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.climate"] = climate
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.update_coordinator"] = uc


_install_home_assistant_stubs()

# ── Add custom_components to sys.path and import via importlib so that    ─
#    relative imports within the koolnova package resolve correctly.
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "custom_components"))

# ├─ Load koolnova_api submodules in dependency order (coordinator depends on
#    them via relative imports).  importlib.import_module sets up __package__
#    and sys.modules properly for dotted names.
for mod_name in [
    "custom_components.koolnova.koolnova_api.exceptions",
    "custom_components.koolnova.koolnova_api.const",
    "custom_components.koolnova.koolnova_api.session",
    "custom_components.koolnova.koolnova_api.client",
]:
    importlib.import_module(mod_name)

# ├─ Load integration const, then coordinator (before __init__.py)
const = importlib.import_module("custom_components.koolnova.const")
coordinator = importlib.import_module("custom_components.koolnova.coordinator")

# ── Symbols used by test methods ──────────────────────────────────────────
KoolnovaDataUpdateCoordinator = coordinator.KoolnovaDataUpdateCoordinator
CONF_UPDATE_INTERVAL = const.CONF_UPDATE_INTERVAL
DEFAULT_UPDATE_INTERVAL = const.DEFAULT_UPDATE_INTERVAL


class TestKoolnovaCoordinator(unittest.TestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.data = {
            "email": "test@example.com",
            "password": "password",
            CONF_UPDATE_INTERVAL: 60,
        }
        self.config_entry.options = {
            CONF_UPDATE_INTERVAL: 70,
        }
        self.config_entry.entry_id = "test_entry_id"

    def test_update_interval_initialization(self):
        """Test that the update interval is initialized from options."""
        coordinator_instance = KoolnovaDataUpdateCoordinator(self.hass, self.config_entry)
        self.assertEqual(coordinator_instance.update_interval, timedelta(seconds=70))

    def test_async_options_updated_changes_interval(self):
        """Test that async_options_updated correctly changes the update interval."""
        coordinator_instance = KoolnovaDataUpdateCoordinator(self.hass, self.config_entry)

        # Change options to a different interval
        self.config_entry.options = {
            CONF_UPDATE_INTERVAL: 80,
            "project_update_frequency": 20,
        }

        # Call async_options_updated using existing event loop
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coordinator_instance.async_options_updated())
        finally:
            loop.close()

        self.assertEqual(coordinator_instance.update_interval, timedelta(seconds=80))
        self.assertEqual(coordinator_instance._project_update_frequency, 20)


if __name__ == "__main__":
    unittest.main()