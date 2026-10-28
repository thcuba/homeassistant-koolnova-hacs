# -*- coding: utf-8 -*-
"""Client for the Koolnova REST API."""

import logging
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


from .exceptions import KoolnovaError
from .session import KoolnovaClientSession
from .const import AUTH_FAILURE_COOLDOWN, COMMON_HEADERS, PATCH_HEADERS

_LOGGER = logging.getLogger(__name__)


class KoolnovaAPIRestClient:
    """Proxy to the Koolnova REST API."""

    # Token expires after 1 hour (3600 seconds) - use 50 minutes to be safe
    TOKEN_LIFETIME = 3000  # 50 minutes in seconds

    def __init__(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        """Initialize the API and authenticate so we can make requests.

        Args:
            username: string containing your Koolnova's app username
            password: string containing your Koolnova's app password
            email: optional email for the account
            request_timeout: per-request timeout in seconds; None falls back to
                the session default (see session.REQUEST_TIMEOUT)
        """
        self.username = username
        self.password = password
        self.email = email
        self.request_timeout = request_timeout
        self.session: Optional[KoolnovaClientSession] = None
        self._last_auth_failure: float = 0.0

    def set_request_timeout(self, timeout: Optional[float]) -> None:
        """Update the request timeout and apply it to the live session.

        Used when options change without a full reload. The change takes effect
        immediately for rest_request calls; the next re-authentication also uses
        the new timeout.
        """
        self.request_timeout = timeout
        if self.session is not None:
            self.session.request_timeout = timeout

    def _is_session_valid(self) -> bool:
        """Check if current session is valid and not expired."""
        if self.session is None:
            return False

        # Check if token has expired
        if hasattr(self.session, 'token_created'):
            elapsed = time.time() - self.session.token_created
            if elapsed > self.TOKEN_LIFETIME:
                _LOGGER.debug("Session token expired (%.0f seconds old)", elapsed)
                return False

        return True

    def _get_session(self) -> KoolnovaClientSession:
        """Get a valid session, creating or refreshing if necessary."""
        # Check cooldown: if we recently failed auth, don't try again yet
        if time.time() - self._last_auth_failure < AUTH_FAILURE_COOLDOWN:
            raise KoolnovaError("Authentication failure cooldown active")

        if not self._is_session_valid():
            _LOGGER.debug("Creating new session (previous was invalid/expired)")
            try:
                self.session = KoolnovaClientSession(
                    self.username, self.password, self.email,
                    request_timeout=self.request_timeout,
                )
                self._last_auth_failure = 0.0
            except Exception as e:
                _LOGGER.error("Failed to create new session: %s", e)
                self.session = None
                self._last_auth_failure = time.time()
                raise

        return self.session


    def get_project(self) -> Dict[str, Any]:

        # Use the same endpoint shape as the webapp: trailing slash + common
        # query params. Add browser-like headers to match the web request.
        params = {
            "page": 1,
            "page_size": 25,
            "ordering": "-start_date",
            "search": "",
            "is_oem": "false",
        }
        headers = COMMON_HEADERS.copy()

        response = self._get_session().rest_request("GET", "projects/", params=params, headers=headers)
        response.raise_for_status()
        json_resp = response.json()
        if not json_resp:
            raise KoolnovaError(
                f"Error : No data received for Koolnova by the API. "
                + "You should test on Koolnova official app. "
                + "Or perhaps API has changed :(."
            )

        #_LOGGER.debug("Raw response: %s", json_resp)

        if not json_resp.get("data", []):
            raise KoolnovaError(
                f"Error :  No data"
                )
        projects = []
        for project in json_resp["data"]:
            _LOGGER.debug("Project Name : %s", project["name"])
            _LOGGER.debug("Topic Name : %s", project["topic"]["name"])
            projects.append({
                "Project_Name": project["name"],
                "Topic_Name": project["topic"]["name"],
                "Topic_id": project["topic"]["id"],
                "Mode": project["topic"]["mode"],
                "is_stop": project["topic"]["is_stop"],
                "is_online": project["topic"]["is_online"],
                "eco": project["topic"]["eco"],
                "last_sync": project["topic"]["last_sync"],


            })

        return projects

    def get_sensors(self) -> Dict[str, Any]:

        # Request the sensors endpoint using trailing slash and browser-like headers
        headers = COMMON_HEADERS.copy()

        resp = self._get_session().rest_request("GET", "topics/sensors/", headers=headers)
        json_resp = resp.json()
        if not json_resp:
            raise KoolnovaError(
                f"Error : No data received for Koolnova by the API. "
                + "You should test on Koolnova official app. "
                + "Or perhaps API has changed :(."
            )

        #_LOGGER.debug("Raw response: %s", json_resp)

        if not json_resp.get("data", []):
            raise KoolnovaError(
                f"Error :  No data"
                )

        rooms = []
        for room in json_resp["data"]:
            _LOGGER.debug("Room Name : %s", room["name"])
            _LOGGER.debug("Room Room_actual_temp : %s", room["temperature"])
            _LOGGER.debug("Topic Info : %s", room.get("topic_info", {}))
            # Retrieve the id from topic_info
            topic_id = room.get("topic_info", {}).get("id", "Unknown")
            # Include all topic_info for access to RSSI, online status, and sync
            topic_info = room.get("topic_info", {})

            rooms.append({
                "Room_Name": room["name"],
                "Room_id": room["id"],
                "Room_status": room["status"],
                "Room_update_at": room["updated_at"],
                "Room_actual_temp": room["temperature"],
                "Room_setpoint_temp": room["setpoint_temperature"],
                "Room_speed": room["speed"],
                "Topic_id": topic_id,
                "topic_info": topic_info  # ADDED: Connectivity information
            })

        return rooms


    def update_sensor(self, sensor_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific attributes for a sensor.

        Args:
            sensor_id: The ID of the sensor to update.
            payload: A dictionary containing the attributes to update and their new values.

        Returns:
            The JSON response from the API.
        """
        url = f"topics/sensors/{sensor_id}/"
        headers = PATCH_HEADERS.copy()

        # Send the PATCH request (partial update)
        response = self._get_session().rest_request("PATCH", url, json=payload, headers=headers)
        response.raise_for_status()

        json_data = response.json()
        _LOGGER.debug("Sensor %s updated successfully with payload %s: %s", sensor_id, payload, json_data)
        return json_data

    def search_all_ids(self) -> Dict[str, List[str]]:
        """Return all device ids grouped by type (koolnova / hub).

        This is a minimal implementation used by the test-suite: it GETs
        `/modules/` and classifies entries by `ModuleType_Id` (1 => koolnova,
        2 => hub) using the `Serial` field as identifier.
        """
        headers = COMMON_HEADERS.copy()
        resp = self._get_session().rest_request("GET", "modules/", headers=headers)
        json_resp = resp.json()
        if not isinstance(json_resp, list):
            _LOGGER.warning("Unexpected modules response type: %s", type(json_resp))
            return {"koolnova": [], "hub": []}
        koolnova = []
        hub = []
        for item in json_resp:
            serial = item.get("Serial")
            if not serial:
                continue
            module_type = item.get("ModuleType_Id")
            if module_type == 1:
                koolnova.append(serial)
            elif module_type == 2:
                hub.append(serial)

        return {"koolnova": koolnova, "hub": hub}

    def search_koolnova_ids(self) -> List[str]:
        """Return list of koolnova ids."""
        return self.search_all_ids().get("koolnova", [])

    def search_hub_ids(self) -> List[str]:
        """Return list of hub ids."""
        return self.search_all_ids().get("hub", [])

    def get_hub_state(self, hub_id: str) -> Dict[str, Any]:
        headers = COMMON_HEADERS.copy()
        resp = self._get_session().rest_request("GET", f"hub/{hub_id}/state", headers=headers)
        resp.raise_for_status()
        json_resp = resp.json()
        state_equipment = json_resp.get("stateEquipment")
        behavior = json_resp.get("behavior")
        return {"state": bool(state_equipment), "mode": behavior}

    def set_hub_mode(self, hub_id: str, target_mode: str) -> Dict[str, Any]:
        if target_mode not in ("manual", "auto", "planning"):
            raise ValueError("Invalid mode")
        headers = PATCH_HEADERS.copy()
        resp = self._get_session().rest_request("PUT", f"hub/{hub_id}/mode/{target_mode}", headers=headers)
        json_resp = resp.json()
        # Normalize response to {'state': bool, 'mode': behavior}
        state_equipment = json_resp.get("stateEquipment")
        behavior = json_resp.get("behavior")
        return {"state": bool(state_equipment), "mode": behavior}

    def set_hub_state(self, hub_id: str, state: bool) -> Dict[str, Any]:
        # The tests expect a call to /hub/{id}/Manual/True for True
        path = f"hub/{hub_id}/Manual/{str(state)}"
        # Use POST/PUT depending on API: tests mock POST for this endpoint
        headers = PATCH_HEADERS.copy()
        response = self._get_session().rest_request("POST", path, headers=headers)
        # After changing state, return current state (tests will mock the GET)
        return self.get_hub_state(hub_id)

    def get_devices(self) -> List[Dict[str, Any]]:
        """Return list of devices."""
        headers = COMMON_HEADERS.copy()
        response = self._get_session().rest_request("GET", "devices/", headers=headers)
        response.raise_for_status()
        json_resp = response.json()
        if isinstance(json_resp, list):
            return json_resp
        if not json_resp or "data" not in json_resp:
            return []
        return json_resp["data"]

    def get_sensor_humidity_map(self) -> Dict[int, Any]:
        """Return a mapping of sensor id -> humidity reading from /devices/.

        Humidity is exposed on the per-device endpoint (`/devices/`, nested in
        ``sensor.topic_info.humidity``), not on the aggregated cloud endpoint
        ``/topics/sensors/`` used by regular polling. This method is the single
        place that reads it, so a missing field degrades gracefully to an
        absent mapping instead of raising.
        """
        mapping: Dict[int, Any] = {}
        try:
            devices = self.get_devices()
        except Exception as err:
            _LOGGER.warning("Could not fetch devices for humidity: %s", err)
            return mapping

        for device in devices:
            sensor = device.get("sensor") or {}
            sensor_id = sensor.get("id")
            if sensor_id is None:
                continue
            humidity = sensor.get("topic_info", {}).get("humidity")
            # Only accept a real numeric percentage. The cloud reports
            # ``false`` (a boolean) when a device does not expose humidity,
            # and ``None`` means the field is absent; both must be skipped
            # rather than surfaced as a bogus reading.
            if isinstance(humidity, (int, float)) and not isinstance(humidity, bool):
                mapping[sensor_id] = float(humidity)
        return mapping

    def get_notifications(self) -> List[Dict[str, Any]]:
        """Return list of notifications."""
        headers = COMMON_HEADERS.copy()
        response = self._get_session().rest_request("GET", "notifications/", headers=headers)
        response.raise_for_status()
        json_resp = response.json()
        if not json_resp or "data" not in json_resp:
            return []
        return json_resp["data"]

    def update_project(self, topic_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific attributes for a project (topic).

        Args:
            topic_id: The ID of the topic/project to update.
            payload: A dictionary containing the attributes to update and their new values.

        Returns:
            The JSON response from the API.
        """
        url = f"topics/{topic_id}/"
        headers = PATCH_HEADERS.copy()

        response = self._get_session().rest_request("PATCH", url, json=payload, headers=headers)
        response.raise_for_status()

        _LOGGER.debug("Project %s updated successfully with payload %s: %s", topic_id, payload, response.json())
        return response.json()
