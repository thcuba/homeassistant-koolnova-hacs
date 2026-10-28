"""Switch entities for Koolnova: per-zone on/off."""

import logging

from homeassistant.components.climate import HVACMode
from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .const import HVAC_TO_KOOLNOVA_ZONE_STATUS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a power switch for every zone/room."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        KoolnovaZoneSwitch(coordinator, entry, sensor)
        for sensor in coordinator.data.get("sensors", [])
    ]
    async_add_entities(entities, update_before_add=False)


class KoolnovaZoneSwitch(SwitchEntity):
    """On/off switch for a single zone.

    Turning it on sends zone status AUTO ("03"), off sends status OFF ("02") —
    the exact same codes the climate entity already uses. No API mapping changes.
    """

    _attr_should_poll = False

    def __init__(self, coordinator, config_entry, sensor):
        """Initialize the zone switch."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._sensor = sensor
        self._sensor_id = sensor["Room_id"]

        self._attr_name = f"Koolnova {sensor['Room_Name']} Power"
        self._attr_unique_id = f"{config_entry.entry_id}_zone_{sensor['Room_id']}_power"

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
    def is_on(self):
        """Return True when the zone is not in the OFF status ("02")."""
        self._update_sensor_data()
        return self._sensor.get("Room_status") != "02"

    async def async_turn_on(self):
        """Turn the zone on (status AUTO, "03")."""
        await self._set_status(HVAC_TO_KOOLNOVA_ZONE_STATUS[HVACMode.AUTO])

    async def async_turn_off(self):
        """Turn the zone off (status OFF, "02")."""
        await self._set_status(HVAC_TO_KOOLNOVA_ZONE_STATUS[HVACMode.OFF])

    async def _set_status(self, status_code: str):
        """Send the status to the API and refresh the state."""
        await self.coordinator.async_update_sensor_data(self._sensor_id, {"status": status_code})
        self.async_write_ha_state()
        _LOGGER.info("Zone switch %s set to status %s", self._attr_name, status_code)
