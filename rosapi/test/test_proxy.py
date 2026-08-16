from __future__ import annotations

import unittest

import rclpy
from rclpy.node import Node

from rosapi import proxy


class TestGetActionType(unittest.TestCase):
    """
    Regression: get_action_type must work with the plain rclpy node rosapi has.

    It used to call ros2action.api's get_action_names_and_types(), which is
    just `node.get_action_names_and_types()` - a method that exists only on
    ros2cli's DirectNode wrapper. Against rosapi's own node it raised
    AttributeError, and because rosapi_node runs a bare rclpy.spin() that
    killed the node and every /rosapi/* service with it.
    """

    node: Node

    @classmethod
    def setUpClass(cls) -> None:
        rclpy.init()
        cls.node = Node("test_rosapi_proxy")
        proxy.init(cls.node)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def test_unknown_action_returns_empty_string(self) -> None:
        # The point is that this returns at all rather than raising.
        self.assertEqual(proxy.get_action_type("/no_such_action"), "")


if __name__ == "__main__":
    unittest.main()
