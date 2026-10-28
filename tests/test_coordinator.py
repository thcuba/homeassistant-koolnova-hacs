"""Tests for KoolnovaDataUpdateCoordinator methods, specifically async_update_all_sensors_status."""

import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure project root and custom_components are in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator


class TestKoolnovaCoordinatorStatus(unittest.IsolatedAsyncioTestCase):
    """Test suite for KoolnovaDataUpdateCoordinator.async_update_all_sensors_status."""

    def setUp(self):
        """Set up mock HomeAssistant and ConfigEntry for coordinator testing."""
        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.data = {
            "email": "test@example.com",
            "password": "secretpassword",
            "update_interval": 60,
            "project_update_frequency": 10,
        }
        self.config_entry.options = {}
        self.config_entry.entry_id = "test_entry_id"

        # Patch KoolnovaAPIRestClient during initialization so no network calls occur
        with patch("custom_components.koolnova.coordinator.KoolnovaAPIRestClient"):
            self.coordinator = KoolnovaDataUpdateCoordinator(
                self.hass, self.config_entry
            )

    async def test_async_update_all_sensors_status_all_sensors_success(self):
        """Test updating status for all sensors when topic_id is None."""
        self.coordinator.data = {
            "sensors": [
                {"Room_id": 1, "Room_Name": "Living Room", "Topic_id": 42},
                {"Room_id": 2, "Room_Name": "Bedroom", "Topic_id": 42},
            ]
        }

        self.coordinator.async_update_sensor_data = AsyncMock(
            return_value={"ok": True}
        )

        result = await self.coordinator.async_update_all_sensors_status("01", topic_id=None)

        self.assertEqual(result, {"updated": 2, "failed": 0})
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 2)
        self.coordinator.async_update_sensor_data.assert_any_call(1, {"status": "01"})
        self.coordinator.async_update_sensor_data.assert_any_call(2, {"status": "01"})

    async def test_async_update_all_sensors_status_filtered_by_topic_id(self):
        """Test updating status filtered by specific topic_id."""
        self.coordinator.data = {
            "sensors": [
                {"Room_id": 10, "Room_Name": "Room A", "Topic_id": 100},
                {"Room_id": 20, "Room_Name": "Room B", "Topic_id": 200},
                {"Room_id": 30, "Room_Name": "Room C", "Topic_id": 100},
            ]
        }

        self.coordinator.async_update_sensor_data = AsyncMock(
            return_value={"ok": True}
        )

        result = await self.coordinator.async_update_all_sensors_status("02", topic_id=100)

        self.assertEqual(result, {"updated": 2, "failed": 0})
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 2)
        self.coordinator.async_update_sensor_data.assert_any_call(10, {"status": "02"})
        self.coordinator.async_update_sensor_data.assert_any_call(30, {"status": "02"})

    async def test_async_update_all_sensors_status_partial_failure(self):
        """Test handling partial failures when updating individual sensors."""
        self.coordinator.data = {
            "sensors": [
                {"Room_id": 1, "Room_Name": "Room 1", "Topic_id": 10},
                {"Room_id": 2, "Room_Name": "Room 2", "Topic_id": 10},
            ]
        }

        async def _mock_update(sensor_id, payload):
            if sensor_id == 2:
                raise Exception("API failure")
            return {"ok": True}

        self.coordinator.async_update_sensor_data = AsyncMock(
            side_effect=_mock_update
        )

        result = await self.coordinator.async_update_all_sensors_status("00", topic_id=10)

        self.assertEqual(result, {"updated": 1, "failed": 1})
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 2)

    async def test_async_update_all_sensors_status_empty_sensors(self):
        """Test updating status when no sensors exist in coordinator data."""
        self.coordinator.data = {"sensors": []}
        self.coordinator.async_update_sensor_data = AsyncMock()

        result = await self.coordinator.async_update_all_sensors_status("00")

        self.assertEqual(result, {"updated": 0, "failed": 0})
        self.coordinator.async_update_sensor_data.assert_not_called()

    async def test_async_update_all_sensors_status_missing_room_id(self):
        """Test that sensors missing Room_id or with Room_id=None are skipped."""
        self.coordinator.data = {
            "sensors": [
                {"Room_Name": "Room No ID", "Topic_id": 10},
                {"Room_id": None, "Room_Name": "Room None ID", "Topic_id": 10},
                {"Room_id": 5, "Room_Name": "Valid Room", "Topic_id": 10},
            ]
        }

        self.coordinator.async_update_sensor_data = AsyncMock(
            return_value={"ok": True}
        )

        result = await self.coordinator.async_update_all_sensors_status("01", topic_id=10)

        self.assertEqual(result, {"updated": 1, "failed": 0})
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 1)
        self.coordinator.async_update_sensor_data.assert_called_once_with(5, {"status": "01"})

    async def test_async_update_all_sensors_status_outer_exception_handling(self):
        """Test outer try-except block re-raises unexpected exceptions."""
        self.coordinator.data = None  # None.get("sensors") raises AttributeError

        with self.assertRaises(AttributeError):
            await self.coordinator.async_update_all_sensors_status("00")


if __name__ == "__main__":
    unittest.main()


class TestKoolnovaCoordinatorHubs(unittest.TestCase):
    """Test suite for KoolnovaDataUpdateCoordinator._fetch_hubs."""

    def setUp(self):
        """Set up mock HomeAssistant and ConfigEntry for coordinator testing."""
        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.data = {
            "email": "test@example.com",
            "password": "secretpassword",
            "update_interval": 60,
            "project_update_frequency": 10,
        }
        self.config_entry.options = {}
        self.config_entry.entry_id = "test_entry_id"

        with patch("custom_components.koolnova.coordinator.KoolnovaAPIRestClient"):
            self.coordinator = KoolnovaDataUpdateCoordinator(
                self.hass, self.config_entry
            )

    def test_fetch_hubs_success(self):
        """Test fetching hubs concurrently when all requests succeed."""
        self.coordinator.client.search_all_ids = MagicMock(
            return_value={"koolnova": [], "hub": ["HB1", "HB2"]}
        )

        def mock_get_hub_state(hub_id):
            return {"state": True, "mode": "auto" if hub_id == "HB1" else "manual"}

        self.coordinator.client.get_hub_state = MagicMock(side_effect=mock_get_hub_state)

        hubs = self.coordinator._fetch_hubs()

        self.assertEqual(len(hubs), 2)
        hub_ids = {h["Hub_id"] for h in hubs}
        self.assertEqual(hub_ids, {"HB1", "HB2"})

    def test_fetch_hubs_partial_failure(self):
        """Test fetching hubs when one hub request fails with an exception."""
        self.coordinator.client.search_all_ids = MagicMock(
            return_value={"koolnova": [], "hub": ["HB1", "HB2_FAIL"]}
        )

        def mock_get_hub_state(hub_id):
            if hub_id == "HB2_FAIL":
                raise Exception("Network error")
            return {"state": True, "mode": "auto"}

        self.coordinator.client.get_hub_state = MagicMock(side_effect=mock_get_hub_state)

        hubs = self.coordinator._fetch_hubs()

        self.assertEqual(len(hubs), 1)
        self.assertEqual(hubs[0]["Hub_id"], "HB1")

    def test_fetch_hubs_empty(self):
        """Test fetching hubs when search_all_ids returns no hubs."""
        self.coordinator.client.search_all_ids = MagicMock(
            return_value={"koolnova": [], "hub": []}
        )

        hubs = self.coordinator._fetch_hubs()

        self.assertEqual(hubs, [])


class TestKoolnovaCoordinatorHumidity(unittest.TestCase):
    """Test suite for KoolnovaDataUpdateCoordinator._enrich_humidity."""

    def setUp(self):
        """Set up mock HomeAssistant and ConfigEntry for coordinator testing."""
        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.data = {
            "email": "test@example.com",
            "password": "secretpassword",
            "update_interval": 60,
            "project_update_frequency": 10,
        }
        self.config_entry.options = {}
        self.config_entry.entry_id = "test_entry_id"

        with patch("custom_components.koolnova.coordinator.KoolnovaAPIRestClient"):
            self.coordinator = KoolnovaDataUpdateCoordinator(
                self.hass, self.config_entry
            )

    def test_enrich_humidity_merges_values_by_room_id(self):
        """Humidity from /devices/ is attached to the matching sensors."""
        self.coordinator.client.get_sensor_humidity_map = MagicMock(
            return_value={1: 55.0, 2: 61.0}
        )
        sensors = [
            {"Room_id": 1, "Room_Name": "Living Room"},
            {"Room_id": 2, "Room_Name": "Bedroom"},
            {"Room_id": 3, "Room_Name": "Kitchen"},  # no humidity reported
        ]

        self.coordinator._enrich_humidity(sensors)

        self.assertEqual(sensors[0]["Room_humidity"], 55.0)
        self.assertEqual(sensors[1]["Room_humidity"], 61.0)
        self.assertNotIn("Room_humidity", sensors[2])

    def test_enrich_humidity_keeps_sensors_when_api_fails(self):
        """A failed /devices/ call must not break the sensor list."""
        self.coordinator.client.get_sensor_humidity_map = MagicMock(
            side_effect=RuntimeError("boom")
        )
        sensors = [{"Room_id": 1, "Room_Name": "Living Room"}]

        self.coordinator._enrich_humidity(sensors)

        self.assertEqual(sensors, [{"Room_id": 1, "Room_Name": "Living Room"}])
