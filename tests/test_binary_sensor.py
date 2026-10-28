"""Tests for Koolnova binary sensor entities."""

import sys
import os
import types
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure project root and custom_components are in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _install_home_assistant_stubs():
    """Register minimal stubs for HA modules required by binary_sensor.py if HA is not installed."""
    if "homeassistant.core" in sys.modules:
        return

    from enum import StrEnum

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

    # ---- homeassistant.components.climate ----
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

    # ---- homeassistant.components.binary_sensor ----
    class BinarySensorDeviceClass(StrEnum):
        CONNECTIVITY = "connectivity"

    class BinarySensorEntity:
        """Minimal stub for BinarySensorEntity."""

        _attr_has_entity_name = False
        _attr_translation_key = None
        _attr_device_class = None
        _attr_should_poll = True

        async def async_added_to_hass(self):
            pass

        def async_on_remove(self, func):
            pass

        def async_write_ha_state(self):
            pass

    binary_sensor_mod = types.ModuleType("homeassistant.components.binary_sensor")
    binary_sensor_mod.BinarySensorDeviceClass = BinarySensorDeviceClass
    binary_sensor_mod.BinarySensorEntity = BinarySensorEntity

    # ---- homeassistant.helpers.entity ----
    def DeviceInfo(**kwargs):
        return kwargs

    entity_mod = types.ModuleType("homeassistant.helpers.entity")
    entity_mod.DeviceInfo = DeviceInfo

    # ---- Wire the package tree ----
    ha = types.ModuleType("homeassistant")
    ha.const = ha_const
    ha.config_entries = config_entries
    ha.core = core
    ha.exceptions = exceptions

    components = types.ModuleType("homeassistant.components")
    components.climate = climate
    components.binary_sensor = binary_sensor_mod

    helpers = types.ModuleType("homeassistant.helpers")
    helpers.update_coordinator = uc
    helpers.entity = entity_mod

    ha.components = components
    ha.helpers = helpers

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.const"] = ha_const
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.exceptions"] = exceptions
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.climate"] = climate
    sys.modules["homeassistant.components.binary_sensor"] = binary_sensor_mod
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.update_coordinator"] = uc
    sys.modules["homeassistant.helpers.entity"] = entity_mod


_install_home_assistant_stubs()

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from custom_components.koolnova.binary_sensor import (
    async_setup_entry,
    KoolnovaConnectivitySensor,
)
from custom_components.koolnova.const import DOMAIN


class TestAsyncSetupEntry(unittest.IsolatedAsyncioTestCase):
    """Test suite for Koolnova binary_sensor async_setup_entry."""

    async def test_async_setup_entry_with_projects(self):
        """Test entity creation when coordinator data contains projects."""
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.entry_id = "entry_123"

        coordinator = MagicMock()
        coordinator.data = {
            "projects": [
                {"Topic_id": 1, "Project_Name": "House 1"},
                {"Topic_id": 2, "Project_Name": "House 2"},
            ]
        }
        hass.data = {DOMAIN: {config_entry.entry_id: coordinator}}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        (entities,) = async_add_entities.call_args[0]
        update_before_add = async_add_entities.call_args.kwargs.get("update_before_add")
        self.assertFalse(update_before_add)
        self.assertEqual(len(entities), 2)
        self.assertIsInstance(entities[0], KoolnovaConnectivitySensor)
        self.assertEqual(entities[0]._attr_unique_id, "entry_123_connectivity_1")
        self.assertEqual(entities[1]._attr_unique_id, "entry_123_connectivity_2")

    async def test_async_setup_entry_no_projects(self):
        """Test fallback entity creation when coordinator data has no projects."""
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.entry_id = "entry_456"

        coordinator = MagicMock()
        coordinator.data = {"projects": []}
        hass.data = {DOMAIN: {config_entry.entry_id: coordinator}}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        (entities,) = async_add_entities.call_args[0]
        update_before_add = async_add_entities.call_args.kwargs.get("update_before_add")
        self.assertFalse(update_before_add)
        self.assertEqual(len(entities), 1)
        self.assertIsInstance(entities[0], KoolnovaConnectivitySensor)
        self.assertEqual(entities[0]._attr_unique_id, "entry_456_connectivity_global")


class TestKoolnovaConnectivitySensor(unittest.IsolatedAsyncioTestCase):
    """Test suite for KoolnovaConnectivitySensor entity methods and attributes."""

    def setUp(self):
        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_id"
        self.coordinator = MagicMock()

    def test_init_attributes_with_project(self):
        """Test sensor initialization with explicit project data."""
        project = {"Topic_id": 42, "Project_Name": "Main Home"}
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry, project)

        self.assertTrue(sensor._attr_has_entity_name)
        self.assertEqual(sensor._attr_translation_key, "connectivity_status")
        self.assertEqual(sensor._attr_device_class, BinarySensorDeviceClass.CONNECTIVITY)
        self.assertFalse(sensor._attr_should_poll)
        self.assertEqual(sensor._attr_unique_id, "test_entry_id_connectivity_42")
        self.assertEqual(
            sensor._attr_device_info["identifiers"],
            {(DOMAIN, "test_entry_id_42")}
        )
        self.assertEqual(sensor._attr_device_info["name"], "Koolnova Main Home")
        self.assertEqual(sensor._attr_device_info["manufacturer"], "Koolnova")
        self.assertEqual(sensor._attr_device_info["model"], "REST API Gateway")

    def test_init_attributes_without_project(self):
        """Test sensor initialization without project data (fallback)."""
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry, project=None)

        self.assertEqual(sensor._attr_unique_id, "test_entry_id_connectivity_global")
        self.assertEqual(
            sensor._attr_device_info["identifiers"],
            {(DOMAIN, "test_entry_id_global")}
        )
        self.assertEqual(sensor._attr_device_info["name"], "Koolnova System")

    async def test_async_added_to_hass(self):
        """Test that sensor registers listener with coordinator on add."""
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry)
        sensor.async_on_remove = MagicMock()

        await sensor.async_added_to_hass()

        self.coordinator.async_add_listener.assert_called_once_with(sensor.async_write_ha_state)
        sensor.async_on_remove.assert_called_once()

    def test_is_on_when_online(self):
        """Test is_on returns True when project sensor is online."""
        project = {"Topic_id": 10}
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry, project)

        self.coordinator.get_project_sensors.return_value = [
            {"topic_info": {"is_online": True}}
        ]

        self.assertTrue(sensor.is_on)
        self.coordinator.get_project_sensors.assert_called_once_with(10)

    def test_is_on_when_offline(self):
        """Test is_on returns False when project sensor is offline."""
        project = {"Topic_id": 10}
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry, project)

        self.coordinator.get_project_sensors.return_value = [
            {"topic_info": {"is_online": False}}
        ]

        self.assertFalse(sensor.is_on)

    def test_is_on_no_sensors(self):
        """Test is_on returns False when no sensors exist."""
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry)
        self.coordinator.get_project_sensors.return_value = []

        self.assertFalse(sensor.is_on)

    def test_is_on_missing_is_online_key(self):
        """Test is_on returns False when topic_info lacks is_online key."""
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry)
        self.coordinator.get_project_sensors.return_value = [
            {"topic_info": {}}
        ]

        self.assertFalse(sensor.is_on)

    def test_extra_state_attributes_normal(self):
        """Test extra_state_attributes with valid ISO date and room sync times."""
        project = {"Topic_id": 10}
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry, project)

        self.coordinator.get_project_sensors.return_value = [
            {
                "Room_id": 1,
                "Room_Name": "Living Room",
                "topic_info": {
                    "rssi": -65,
                    "is_online": True,
                    "last_sync": "2026-07-01T10:00:00",
                },
            },
            {
                "Room_id": 2,
                "Room_Name": "Master Bedroom",
                "topic_info": {
                    "last_sync": "2026-07-01T10:05:00",
                },
            },
        ]

        attrs = sensor.extra_state_attributes

        self.assertEqual(attrs["wifi_signal"], -65)
        self.assertTrue(attrs["online_status"])
        self.assertEqual(attrs["system_last_sync"], datetime.fromisoformat("2026-07-01T10:00:00"))
        self.assertEqual(
            attrs["room_sync_times"],
            {
                "living_room": "2026-07-01T10:00:00",
                "master_bedroom": "2026-07-01T10:05:00",
            },
        )

    def test_extra_state_attributes_empty_sensors(self):
        """Test extra_state_attributes returns empty dict when no sensors found."""
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry)
        self.coordinator.get_project_sensors.return_value = []

        self.assertEqual(sensor.extra_state_attributes, {})

    def test_extra_state_attributes_invalid_date_format_fallback(self):
        """Test system_last_sync falls back to raw string on invalid ISO datetime."""
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry)
        self.coordinator.get_project_sensors.return_value = [
            {
                "Room_id": 1,
                "Room_Name": "Kitchen",
                "topic_info": {
                    "rssi": -70,
                    "is_online": True,
                    "last_sync": "invalid-date-format",
                },
            }
        ]

        attrs = sensor.extra_state_attributes

        self.assertEqual(attrs["system_last_sync"], "invalid-date-format")

    def test_extra_state_attributes_missing_room_name_fallback(self):
        """Test room sync time uses fallback room_{Room_id} when Room_Name is missing."""
        sensor = KoolnovaConnectivitySensor(self.coordinator, self.config_entry)
        self.coordinator.get_project_sensors.return_value = [
            {
                "Room_id": 99,
                "topic_info": {
                    "last_sync": "2026-07-01T12:00:00",
                },
            }
        ]

        attrs = sensor.extra_state_attributes

        self.assertIn("room_sync_times", attrs)
        self.assertEqual(attrs["room_sync_times"], {"room_99": "2026-07-01T12:00:00"})


if __name__ == "__main__":
    unittest.main()
