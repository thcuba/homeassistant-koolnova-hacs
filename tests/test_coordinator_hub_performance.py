"""Benchmark performance test for hub state fetching in KoolnovaDataUpdateCoordinator."""

import sys
import os
import time
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root and custom_components are in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator


class TestHubPerformance(unittest.TestCase):
    """Benchmark test for hub state fetching."""

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

    def test_benchmark_hub_fetching(self):
        """Benchmark fetching states for 10 hubs with simulated network latency."""
        num_hubs = 10
        hub_ids = [f"HB{i}" for i in range(num_hubs)]
        latency_per_request = 0.05  # 50ms latency per API request

        self.coordinator.client.search_all_ids = MagicMock(
            return_value={"koolnova": [], "hub": hub_ids}
        )

        def mock_get_hub_state(hub_id):
            time.sleep(latency_per_request)
            return {"state": True, "mode": "auto"}

        self.coordinator.client.get_hub_state = MagicMock(side_effect=mock_get_hub_state)

        start_time = time.perf_counter()
        hubs = self.coordinator._fetch_hubs() if hasattr(self.coordinator, "_fetch_hubs") else self._legacy_fetch_hubs()
        elapsed_time = time.perf_counter() - start_time

        print(f"\n[BENCHMARK] Fetched {len(hubs)} hubs in {elapsed_time:.4f} seconds (simulated latency per call: {latency_per_request}s)")
        self.assertEqual(len(hubs), num_hubs)

    def _legacy_fetch_hubs(self):
        """Replicate legacy sequential hub fetching for initial baseline comparison if _fetch_hubs is not yet implemented."""
        hubs = []
        try:
            module_ids = self.coordinator.client.search_all_ids()
            for hub_id in module_ids.get("hub", []):
                try:
                    hub_state = self.coordinator.client.get_hub_state(hub_id)
                    hubs.append({
                        "Hub_id": hub_id,
                        "State": hub_state.get("state"),
                        "Mode": hub_state.get("mode")
                    })
                except Exception as e:
                    pass
        except Exception as e:
            pass
        return hubs


if __name__ == "__main__":
    unittest.main()
