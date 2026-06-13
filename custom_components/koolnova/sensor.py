"""Sensor platform for Koolnova."""
import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Koolnova sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Single connectivity sensor for the whole system
    async_add_entities([KoolnovaConnectivitySensor(coordinator, entry)], update_before_add=False)

class KoolnovaConnectivitySensor(SensorEntity):
    """Single sensor with all Koolnova system connectivity information."""

    _attr_has_entity_name = True
    _attr_translation_key = "connectivity_status"
    _attr_icon = "mdi:router-wireless"
    _attr_should_poll = False

    def __init__(self, coordinator, config_entry):
        """Initialize the connectivity sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_connectivity_status"

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def state(self):
        """State: Online/Offline based on system."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return "Unknown"

        topic_info = sensors[0].get("topic_info", {})
        is_online = topic_info.get("is_online")

        return "Online" if is_online else "Offline"

    @property
    def extra_state_attributes(self):
        """All connectivity attributes."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return {}

        # System info (global)
        topic_info = sensors[0].get("topic_info", {})
        attrs = {
            "WiFi Signal": topic_info.get("rssi"),
            "Online": topic_info.get("is_online"),
        }

        # System last sync
        system_last_sync = topic_info.get("last_sync")
        if system_last_sync:
            try:
                attrs["Last sync"] = datetime.fromisoformat(system_last_sync)
            except (ValueError, TypeError):
                attrs["Last sync"] = system_last_sync

        # Last sync for each room
        for sensor in sensors:
            room_name = sensor.get("Room_Name", f"room_{sensor.get('Room_id')}")
            sensor_topic_info = sensor.get("topic_info", {})
            room_last_sync = sensor_topic_info.get("last_sync")

            if room_last_sync:
                try:
                    attrs[f"Last sync {room_name}"] = datetime.fromisoformat(room_last_sync)
                except (ValueError, TypeError):
                    attrs[f"Last sync {room_name}"] = room_last_sync

        return attrs
