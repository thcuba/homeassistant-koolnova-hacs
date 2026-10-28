"""Tests for KoolnovaZoneSwitch entity and platform setup."""

import sys
import os
import types
import unittest
from unittest.mock import AsyncMock, MagicMock

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _install_home_assistant_stubs():
    """Register minimal stubs for HA modules so tests run in lightweight environments without Home Assistant installed."""
    if "homeassistant.components.switch" in sys.modules:
        return

    from enum import StrEnum

    class HVACMode(StrEnum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        HEAT_COOL = "heat_cool"
        AUTO = "auto"
        DRY = "dry"
        FAN_ONLY = "fan_only"

    class SwitchEntity:
        """Stub SwitchEntity simulating Home Assistant Entity property behavior."""
        _attr_should_poll = True
        _attr_name = None
        _attr_unique_id = None

        @property
        def name(self):
            return self._attr_name

        @property
        def unique_id(self):
            return self._attr_unique_id

        @property
        def should_poll(self):
            return self._attr_should_poll

        async def async_added_to_hass(self):
            pass

        def async_on_remove(self, func):
            pass

        def async_write_ha_state(self):
            pass

    ha = sys.modules.get("homeassistant")
    if ha is None:
        ha = types.ModuleType("homeassistant")
        ha.__path__ = []
        sys.modules["homeassistant"] = ha

    components = sys.modules.get("homeassistant.components")
    if components is None:
        components = types.ModuleType("homeassistant.components")
        components.__path__ = []
        sys.modules["homeassistant.components"] = components
        setattr(ha, "components", components)

    climate = sys.modules.get("homeassistant.components.climate")
    if climate is None:
        climate = types.ModuleType("homeassistant.components.climate")
        climate.HVACMode = HVACMode
        climate.FAN_LOW = "low"
        climate.FAN_MEDIUM = "medium"
        climate.FAN_HIGH = "high"
        climate.FAN_AUTO = "auto"
        sys.modules["homeassistant.components.climate"] = climate
        setattr(components, "climate", climate)

    switch = sys.modules.get("homeassistant.components.switch")
    if switch is None:
        switch = types.ModuleType("homeassistant.components.switch")
        switch.SwitchEntity = SwitchEntity
        sys.modules["homeassistant.components.switch"] = switch
        setattr(components, "switch", switch)
    elif not hasattr(switch, "SwitchEntity"):
        setattr(switch, "SwitchEntity", SwitchEntity)


_install_home_assistant_stubs()

from homeassistant.components.climate import HVACMode
from custom_components.koolnova.const import DOMAIN, HVAC_TO_KOOLNOVA_ZONE_STATUS
from custom_components.koolnova.switch import KoolnovaZoneSwitch, async_setup_entry


class TestKoolnovaZoneSwitch(unittest.IsolatedAsyncioTestCase):
    """Test suite for KoolnovaZoneSwitch."""

    def setUp(self):
        """Set up mock coordinator, config entry, and sensor data."""
        self.coordinator = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.async_add_listener = MagicMock()
        self.coordinator.async_update_sensor_data = AsyncMock(return_value={"ok": True})

        self.sensor = {
            "Room_id": 1,
            "Room_Name": "Living Room",
            "Room_status": "03",  # AUTO (ON)
            "Topic_id": 42,
        }
        self.coordinator.data = {"sensors": [self.sensor]}

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_id"

        self.switch = KoolnovaZoneSwitch(self.coordinator, self.config_entry, self.sensor)
        # Mock async_write_ha_state since entity is not fully added to real HA hass instance
        self.switch.async_write_ha_state = MagicMock()

    def test_init_and_properties(self):
        """Test switch initialization and entity properties."""
        self.assertEqual(self.switch.name, "Koolnova Living Room Power")
        self.assertEqual(self.switch.unique_id, "test_entry_id_zone_1_power")
        self.assertFalse(self.switch.should_poll)
        self.assertTrue(self.switch.available)

        # When coordinator last update failed
        self.coordinator.last_update_success = False
        self.assertFalse(self.switch.available)

    async def test_async_added_to_hass(self):
        """Test async_added_to_hass registers coordinator listener."""
        self.switch.async_on_remove = MagicMock()
        await self.switch.async_added_to_hass()

        self.coordinator.async_add_listener.assert_called_once_with(self.switch.async_write_ha_state)
        self.switch.async_on_remove.assert_called_once()

    def test_is_on_and_update_sensor_data(self):
        """Test is_on property logic and updating sensor data from coordinator."""
        # Initial status is "03" (AUTO), so is_on should be True
        self.assertTrue(self.switch.is_on)

        # Update coordinator sensor status to "02" (OFF)
        updated_sensor = {
            "Room_id": 1,
            "Room_Name": "Living Room",
            "Room_status": "02",
            "Topic_id": 42,
        }
        self.coordinator.data = {"sensors": [updated_sensor]}

        # is_on should fetch updated sensor data and return False
        self.assertFalse(self.switch.is_on)

        # Test non-off status code "00" (COOL)
        self.coordinator.data = {
            "sensors": [{"Room_id": 1, "Room_Name": "Living Room", "Room_status": "00"}]
        }
        self.assertTrue(self.switch.is_on)

        # Test non-off status code "01" (HEAT)
        self.coordinator.data = {
            "sensors": [{"Room_id": 1, "Room_Name": "Living Room", "Room_status": "01"}]
        }
        self.assertTrue(self.switch.is_on)

    async def test_async_turn_on(self):
        """Test turning switch on sends status AUTO ('03')."""
        await self.switch.async_turn_on()

        expected_status = HVAC_TO_KOOLNOVA_ZONE_STATUS[HVACMode.AUTO]
        self.assertEqual(expected_status, "03")
        self.coordinator.async_update_sensor_data.assert_called_once_with(1, {"status": "03"})
        self.switch.async_write_ha_state.assert_called_once()

    async def test_async_turn_off(self):
        """Test turning switch off sends status OFF ('02')."""
        await self.switch.async_turn_off()

        expected_status = HVAC_TO_KOOLNOVA_ZONE_STATUS[HVACMode.OFF]
        self.assertEqual(expected_status, "02")
        self.coordinator.async_update_sensor_data.assert_called_once_with(1, {"status": "02"})
        self.switch.async_write_ha_state.assert_called_once()

    async def test_async_setup_entry(self):
        """Test platform setup async_setup_entry."""
        hass = MagicMock()
        hass.data = {
            DOMAIN: {
                self.config_entry.entry_id: self.coordinator
            }
        }
        async_add_entities = MagicMock()

        await async_setup_entry(hass, self.config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        self.assertEqual(len(entities), 1)
        self.assertIsInstance(entities[0], KoolnovaZoneSwitch)
        self.assertEqual(entities[0].name, "Koolnova Living Room Power")
        self.assertFalse(async_add_entities.call_args[1].get("update_before_add", True))


if __name__ == "__main__":
    unittest.main()
