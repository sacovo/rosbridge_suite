from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from rcl_interfaces.srv import GetParameters
from rclpy.clock import ClockType
from rclpy.time import Time

from rosapi import params


class TestCachedClientClockType(unittest.TestCase):
    """
    Regression: the cached-client timestamp must come from the node's clock.

    It used to be a bare `Time()`, which is `ClockType.SYSTEM_TIME`, while
    `_cleanup_timer_callback` subtracts it from `_node.get_clock().now()`.
    rclpy refuses to subtract Times of differing clock types, so as soon as one
    client was cached the 0.5s cleanup timer raised on every tick.
    """

    def setUp(self) -> None:
        self._saved_clients = dict(params._cached_clients)
        params._cached_clients.clear()

    def tearDown(self) -> None:
        params._cached_clients.clear()
        params._cached_clients.update(self._saved_clients)

    @staticmethod
    def _node_with_clock(clock_type: ClockType) -> MagicMock:
        node = MagicMock()
        node.get_clock.return_value.now.return_value = Time(seconds=10, clock_type=clock_type)
        return node

    def test_cached_client_uses_the_nodes_clock_type(self) -> None:
        node = self._node_with_clock(ClockType.ROS_TIME)

        with patch.object(params, "_node", node):
            params._get_client("/some_node/get_parameters", GetParameters)

        cached = params._cached_clients["/some_node/get_parameters"]
        self.assertEqual(cached.last_used_time.clock_type, ClockType.ROS_TIME)

    def test_cleanup_does_not_raise_under_sim_time(self) -> None:
        node = self._node_with_clock(ClockType.ROS_TIME)

        with patch.object(params, "_node", node):
            params._get_client("/some_node/get_parameters", GetParameters)
            # Raised "can't subtract times with different time sources" before.
            params._cleanup_timer_callback()

    def test_cleanup_still_evicts_an_idle_client(self) -> None:
        node = self._node_with_clock(ClockType.ROS_TIME)

        with patch.object(params, "_node", node):
            params._get_client("/some_node/get_parameters", GetParameters)
            # Jump the clock past the persistence window.
            node.get_clock.return_value.now.return_value = Time(
                seconds=10 + params._client_persistence_sec + 1,
                clock_type=ClockType.ROS_TIME,
            )
            params._cleanup_timer_callback()

        self.assertNotIn("/some_node/get_parameters", params._cached_clients)
        node.destroy_client.assert_called_once()


if __name__ == "__main__":
    unittest.main()
