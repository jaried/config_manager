from __future__ import annotations

from src.config_manager.config_node import ConfigNode


def test_dict_views_are_native_and_preserve_order():
    node = ConfigNode({"first": 1, "second": "two"})

    keys = node.keys()
    values = node.values()
    items = node.items()

    assert isinstance(keys, type({}.keys()))
    assert isinstance(values, type({}.values()))
    assert isinstance(items, type({}.items()))
    assert list(keys) == ["first", "second"]
    assert list(values) == [1, "two"]
    assert list(items) == [("first", 1), ("second", "two")]


def test_dict_views_reflect_later_node_changes():
    node = ConfigNode({"first": 1, "second": 2})
    keys = node.keys()
    values = node.values()
    items = node.items()

    node["third"] = 3
    node["first"] = 10
    del node["second"]

    assert list(keys) == ["first", "third"]
    assert list(values) == [10, 3]
    assert list(items) == [("first", 10), ("third", 3)]


def test_dict_views_for_empty_node_are_empty_native_views():
    node = ConfigNode()

    assert isinstance(node.keys(), type({}.keys()))
    assert isinstance(node.values(), type({}.values()))
    assert isinstance(node.items(), type({}.items()))
    assert list(node.keys()) == []
    assert list(node.values()) == []
    assert list(node.items()) == []


def test_dict_views_expose_nested_values_and_allow_same_name_item_access():
    node = ConfigNode(
        {
            "nested": {"enabled": True},
            "keys": "configured-keys",
            "values": "configured-values",
            "items": "configured-items",
        }
    )
    nested = node["nested"]

    assert isinstance(nested, ConfigNode)
    assert list(node.values())[0] is nested
    assert list(node.items())[0] == ("nested", nested)
    assert node["keys"] == "configured-keys"
    assert node["values"] == "configured-values"
    assert node["items"] == "configured-items"
    assert node.get("keys") == "configured-keys"
    assert node.get("values") == "configured-values"
    assert node.get("items") == "configured-items"
    assert callable(node.keys)
    assert callable(node.values)
    assert callable(node.items)
