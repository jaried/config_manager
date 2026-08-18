import os
import pytest

from src.config_manager import get_config_manager
from src.config_manager.yaml_codec import YamlCodecError, dump_yaml


def make_prod_config(tmpdir, extra_data=None):
    """生成一个包含多种类型和嵌套的生产配置文件"""
    prod_dir = tmpdir / "src" / "config"
    prod_dir.mkdir(parents=True, exist_ok=True)
    prod_path = prod_dir / "config.yaml"
    data = {
        "__data__": {
            "project_name": "test_project",
            "base_dir": str(tmpdir),
            "assets": {
                "A": {"symbol": "A", "type": "stock"},
                "123": {"symbol": "B", "type": "stock"},
                "nested": {"sub": {"deep": 1}},
            },
            "time_periods": [1, 5, 15],
            "dl_model": {"name": "model", "path": "/abs/path/to/model"},
            "realtime_monitoring": True,
            "float_value": 1.23,
            "none_value": None,
            "bool_value": False,
            "list_mixed": [1, "a", {"b": 2}],
        },
        "__type_hints__": {},
    }
    if extra_data:
        data["__data__"].update(extra_data)
    with open(prod_path, "w", encoding="utf-8") as f:
        f.write(dump_yaml(data))
    return str(prod_path)


def validate_config_completeness(config):
    required_sections = ["assets", "time_periods", "dl_model", "realtime_monitoring"]
    missing = [k for k in required_sections if config.get(k) is None]
    assert not missing, f"缺少: {missing}"
    # assets内容完整
    assets = config.get("assets")
    assert assets is not None
    assert "A" in assets
    assert "123" in assets
    assert "nested" in assets and "sub" in assets["nested"]
    # 其他类型
    assert config.get("float_value") == 1.23
    assert config.get("none_value") is None
    assert config.get("bool_value") is False
    assert config.get("list_mixed")[2]["b"] == 2


def test_test_mode_config_copy_and_path_replace(tmp_path):
    # 1. 生成生产配置
    prod_path = make_prod_config(tmp_path)
    # 2. 设置环境变量，模拟生产环境
    os.environ["CONFIG_MANAGER_CONFIG_PATH"] = str(prod_path)
    # 3. test_mode复制
    config = get_config_manager(config_path=str(prod_path), test_mode=True)
    # 4. 校验完整性
    validate_config_completeness(config)
    # 5. 路径字段全部被替换到临时目录
    assert (
        str(config.base_dir).startswith(str(tmp_path))
        or "temp" in str(config.base_dir).lower()
    )
    # 6. 递归嵌套、字符串数字键、None、bool、float等类型都能正常保留
    # 7. 删除环境变量
    del os.environ["CONFIG_MANAGER_CONFIG_PATH"]


def test_yaml_codec_rejects_non_string_mapping_key():
    with pytest.raises(YamlCodecError, match="unsupported mapping key"):
        dump_yaml({"assets": {456: {"special": "yes"}}})


def test_test_mode_config_copy_with_extreme_types(tmp_path):
    # 生产配置包含极端类型
    prod_path = make_prod_config(
        tmp_path,
        extra_data={
            "list_of_dicts": [{"a": 1}, {"b": 2}],
            "dict_of_lists": {"x": [1, 2], "y": [3, 4]},
            "deep_nested": {"a": {"b": {"c": {"d": 1}}}},
        },
    )
    config = get_config_manager(config_path=str(prod_path), test_mode=True)
    assert config.get("list_of_dicts")[1]["b"] == 2
    assert config.get("dict_of_lists")["y"][1] == 4
    assert config.get("deep_nested")["a"]["b"]["c"]["d"] == 1


def test_test_mode_config_copy_with_invalid_yaml(tmp_path):
    # 生产配置为非法yaml时，test_mode只生成极简配置
    prod_dir = tmp_path / "src" / "config"
    prod_dir.mkdir(parents=True, exist_ok=True)
    prod_path = prod_dir / "config.yaml"
    with open(prod_path, "w", encoding="utf-8") as f:
        f.write("invalid: [unclosed_list\r\n")
    config = get_config_manager(config_path=str(prod_path), test_mode=True)
    # 只包含极简配置
    for k in ["project_name", "base_dir", "experiment_name", "first_start_time"]:
        assert config.get(k) is not None
    # 不会有assets等业务配置
    assert config.get("assets") is None


def test_test_mode_config_copy_with_empty_config(tmp_path):
    # 生产配置为空时，test_mode只生成极简配置
    prod_dir = tmp_path / "src" / "config"
    prod_dir.mkdir(parents=True, exist_ok=True)
    prod_path = prod_dir / "config.yaml"
    with open(prod_path, "w", encoding="utf-8") as f:
        f.write("")
    config = get_config_manager(config_path=str(prod_path), test_mode=True)

    # 验证基本属性存在
    assert config.base_dir is not None
    assert config.first_start_time is not None

    # 验证paths命名空间存在
    assert hasattr(config, "paths")
    assert config.paths.work_dir is not None
    assert config.paths.log_dir is not None

    # 验证业务配置不存在
    with pytest.raises(AttributeError):
        _ = config.assets
