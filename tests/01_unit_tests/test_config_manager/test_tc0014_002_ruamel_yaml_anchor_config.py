from __future__ import annotations

import os
import tempfile

from src.config_manager.yaml_codec import dump_yaml, load_yaml, semantically_equal


class TestYamlAnchorConfig:
    """测试 YAML 锚点和别名的语义往返。"""

    @staticmethod
    def _round_trip(yaml_content: str):
        parsed = load_yaml(yaml_content)
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".yaml", delete=False
        ) as stream:
            stream.write(dump_yaml(parsed))
            temp_path = stream.name

        try:
            with open(temp_path, "r", encoding="utf-8") as stream:
                saved_content = stream.read()
            return parsed, load_yaml(saved_content)
        finally:
            os.unlink(temp_path)

    def test_default_yaml_behavior(self):
        """锚点和别名解析后，保存再加载的数据语义保持一致。"""
        yaml_content = """config: &default_config
  timeout: 30
  retries: 3

service_a:
  settings: *default_config
service_b:
  settings: *default_config
"""
        expected = {
            "config": {"timeout": 30, "retries": 3},
            "service_a": {"settings": {"timeout": 30, "retries": 3}},
            "service_b": {"settings": {"timeout": 30, "retries": 3}},
        }

        parsed, round_tripped = self._round_trip(yaml_content)

        assert semantically_equal(parsed, expected)
        assert semantically_equal(round_tripped, expected)

    def test_alias_configuration_semantics(self):
        """重复引用的配置在安全 codec 往返后仍保持相同数据。"""
        yaml_content = """defaults: &defaults
  timeout: 30
  retries: 3
service_a:
  settings: *defaults
service_b:
  settings: *defaults
"""
        expected = {
            "defaults": {"timeout": 30, "retries": 3},
            "service_a": {"settings": {"timeout": 30, "retries": 3}},
            "service_b": {"settings": {"timeout": 30, "retries": 3}},
        }

        parsed, round_tripped = self._round_trip(yaml_content)

        assert semantically_equal(parsed, expected)
        assert semantically_equal(round_tripped, expected)

    def test_current_config_manager_yaml_setup(self):
        """当前 codec 对普通映射、序列和标量执行语义往返。"""
        data = {
            "test": "value",
            "settings": {"timeout": 30, "enabled": True},
            "sequence": [1, 2, 3],
        }

        assert semantically_equal(load_yaml(dump_yaml(data)), data)

    def test_complex_anchor_alias_scenario_semantics(self):
        """复杂配置中的多个别名引用只按解析后的数据语义比较。"""
        yaml_content = """__data__:
  defaults: &defaults
    timeout: 30
    retries: 3
__type_hints__: {}
config:
  app_settings: *defaults
monitoring:
  settings: *defaults
"""
        expected = {
            "__data__": {
                "defaults": {"timeout": 30, "retries": 3},
            },
            "__type_hints__": {},
            "config": {
                "app_settings": {"timeout": 30, "retries": 3},
            },
            "monitoring": {
                "settings": {"timeout": 30, "retries": 3},
            },
        }

        parsed, round_tripped = self._round_trip(yaml_content)

        assert semantically_equal(parsed, expected)
        assert semantically_equal(round_tripped, expected)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v", "-s"])
