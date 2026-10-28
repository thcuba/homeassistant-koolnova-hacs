"""Binary sensor entities for Koolnova."""
import logging
from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Koolnova binary sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    projects = coordinator.data.get("projects", [])
    if projects:
        for project in projects:
            entities.append(KoolnovaConnectivitySensor(coordinator, entry, project))
    else:
        entities.append(KoolnovaConnectivitySensor(coordinator, entry))

    async_add_entities(entities, update_before_add=False)

class KoolnovaConnectivitySensor(BinarySensorEntity):
    """Connectivity sensor for a Koolnova project."""

    _attr_has_entity_name = True
    _attr_translation_key = "connectivity_status"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_should_poll = False  # Uses coordinator push updates via listener

    def __init__(self, coordinator, config_entry, project=None):
        """Initialize the connectivity sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._project = project

        topic_id = project.get("Topic_id", "global") if project else "global"
        project_name = project.get("Project_Name", "System") if project else "System"

        self._attr_unique_id = f"{config_entry.entry_id}_connectivity_{topic_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.entry_id}_{topic_id}")},
            name=f"Koolnova {project_name}",
            manufacturer="Koolnova",
            model="REST API Gateway",
        )

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self):
        """Return true if system is online."""
        topic_id = self._project.get("Topic_id") if self._project else None
        sensors = self.coordinator.get_project_sensors(topic_id)

        if not sensors:
            return False

        topic_info = sensors[0].get("topic_info", {})
        return topic_info.get("is_online", False)

    @property
    def extra_state_attributes(self):
        """Return connectivity attributes in English snake_case."""
        topic_id = self._project.get("Topic_id") if self._project else None
        sensors = self.coordinator.get_project_sensors(topic_id)

        if not sensors:
            return {}

        topic_info = sensors[0].get("topic_info", {})
        attrs = {
            "wifi_signal": topic_info.get("rssi"),
            "online_status": topic_info.get("is_online"),
        }

        system_last_sync = topic_info.get("last_sync")
        if system_last_sync:
            try:
                attrs["system_last_sync"] = datetime.fromisoformat(system_last_sync)
            except (ValueError, TypeError):
                attrs["system_last_sync"] = system_last_sync

        # Room sync times
        room_sync_times = {}
        for sensor in sensors:
            room_name = sensor.get("Room_Name", f"room_{sensor.get('Room_id')}")
            sensor_topic_info = sensor.get("topic_info", {})
            room_last_sync = sensor_topic_info.get("last_sync")
            if room_last_sync:
                room_sync_times[room_name.lower().replace(" ", "_")] = room_last_sync

        if room_sync_times:
            attrs["room_sync_times"] = room_sync_times

        return attrs