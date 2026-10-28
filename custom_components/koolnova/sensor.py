"""Sensor entities for Koolnova: per-room humidity exposed from /devices/."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a humidity sensor for every room that reports one."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        KoolnovaHumiditySensor(coordinator, entry, sensor)
        for sensor in coordinator.data.get("sensors", [])
        if sensor.get("Room_humidity") is not None
    ]
    if entities:
        async_add_entities(entities, update_before_add=False)


class KoolnovaHumiditySensor(SensorEntity):
    """Room humidity sensor, populated from the /devices/ endpoint."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_should_poll = False  # Uses coordinator push updates via listener

    def __init__(self, coordinator, config_entry, sensor):
        """Initialize the humidity sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._sensor = sensor
        self._sensor_id = sensor["Room_id"]

        self._attr_name = f"{sensor['Room_Name']} Humidity"
        self._attr_unique_id = f"{config_entry.entry_id}_zone_{sensor['Room_id']}_humidity"

        project_id = sensor.get("Topic_id", "global")
        project_name = "System"
        for proj in self.coordinator.data.get("projects", []):
            if proj.get("Topic_id") == project_id:
                project_name = proj.get("Project_Name", "System")
                break

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.entry_id}_{project_id}")},
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

    def _update_sensor_data(self):
        """Refresh local sensor data from the coordinator."""
        for sensor in self.coordinator.data.get("sensors", []):
            if sensor.get("Room_id") == self._sensor_id:
                self._sensor = sensor
                break

    @property
    def available(self):
        """Return whether the coordinator last update succeeded."""
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        """Return the room humidity percentage."""
        self._update_sensor_data()
        return self._sensor.get("Room_humidity")
