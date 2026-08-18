from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.config_manager import TestEnvironmentManager, get_config_manager
from src.config_manager.config_manager import ConfigManager, _clear_instances_for_testing


PRODUCTION_ADDRESS = "prod://s1-02-production-address"
TEST_ADDRESS = "test://s1-02-test-address"


STANDARD_YAML = f'''# standard-root source comment
__data__:
  project_name: s1_02_project
  test_mode: true
  database:
    address: "{PRODUCTION_ADDRESS}"
    test_address: "{TEST_ADDRESS}"
    host: "prod-db"
    port: 5432
  retained_field: "retain-me"
__type_hints__: {{}}
'''


RAW_YAML = f'''# raw-root source comment
project_name: s1_02_project
test_mode: true
database:
  address: "{PRODUCTION_ADDRESS}"
  test_address: "{TEST_ADDRESS}"
  host: "prod-db"
  port: 5432
retained_field: "retain-me"
'''


ONLY_TEST_ADDRESS_YAML = f'''project_name: s1_02_project
database:
  test_address: "{TEST_ADDRESS}"
'''


NO_DATABASE_YAML = '''__data__:
  project_name: s1_02_project
  test_mode: true
  retained_field: "retain-me"
__type_hints__: {}
'''


@pytest.fixture(autouse=True)
def clean_test_environment():
    """Keep each database-switch example isolated from instance/cache state."""
    _clear_instances_for_testing()
    os.environ.pop("CONFIG_MANAGER_TEST_MODE", None)
    os.environ.pop("CONFIG_MANAGER_TEST_BASE_DIR", None)

    yield

    TestEnvironmentManager.cleanup_current_test_environment()
    _clear_instances_for_testing()
    os.environ.pop("CONFIG_MANAGER_TEST_MODE", None)
    os.environ.pop("CONFIG_MANAGER_TEST_BASE_DIR", None)


def _write_source(tmp_path: Path, content: str) -> tuple[Path, bytes]:
    source_path = tmp_path / "production.yaml"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_bytes = content.encode("utf-8")
    source_path.write_bytes(source_bytes)
    return source_path, source_bytes


def _standard_yaml_with_database(database_body: str) -> str:
    indented_body = "\n".join(f"    {line}" for line in database_body.splitlines())
    return f'''__data__:
  project_name: s1_02_project
  database:
{indented_body}
__type_hints__: {{}}
'''


def _standard_yaml_with_database_value(database_value: str) -> str:
    return f'''__data__:
  project_name: s1_02_project
  database: {database_value}
__type_hints__: {{}}
'''


def test_ut01_standard_yaml_root_selects_test_address_and_preserves_source(tmp_path: Path):
    """UT-01/DO-01/DO-02: standard __data__ root selects the test address."""
    source_path, source_bytes = _write_source(tmp_path, STANDARD_YAML)

    cfg = get_config_manager(config_path=str(source_path), watch=False, test_mode=True)

    assert cfg.database.address == TEST_ADDRESS
    assert cfg.get("database.address") == TEST_ADDRESS
    assert cfg.get("database.host") == "prod-db"
    assert source_path.read_bytes() == source_bytes


def test_ut02_raw_yaml_root_selects_test_address_and_preserves_source(tmp_path: Path):
    """UT-02/DO-06: a raw YAML root follows the same fixed-key rule."""
    source_path, source_bytes = _write_source(tmp_path, RAW_YAML)

    cfg = get_config_manager(config_path=str(source_path), watch=False, test_mode=True)

    assert cfg.database.address == TEST_ADDRESS
    assert cfg.get("database.address") == TEST_ADDRESS
    assert cfg.get("database.host") == "prod-db"
    assert source_path.read_bytes() == source_bytes


def test_ut03_production_mode_ignores_config_test_mode_field(tmp_path: Path):
    """UT-03/DO-03: the data field named test_mode is not a general override."""
    source_path, _ = _write_source(tmp_path, STANDARD_YAML)

    cfg = get_config_manager(config_path=str(source_path), watch=False, test_mode=False)

    assert cfg.get("test_mode") is True
    assert cfg.get("database.address") == PRODUCTION_ADDRESS


def test_ut04_missing_database_is_compatible_in_test_mode(tmp_path: Path):
    """UT-04/DO-07: a missing database node remains a no-op."""
    source_path, source_bytes = _write_source(tmp_path, NO_DATABASE_YAML)

    cfg = get_config_manager(config_path=str(source_path), watch=False, test_mode=True)

    assert cfg.get("database") is None
    assert cfg.get("retained_field") == "retain-me"
    assert source_path.read_bytes() == source_bytes


@pytest.mark.parametrize(
    ("case_name", "database_body"),
    [
        ("missing", f'address: "{PRODUCTION_ADDRESS}"'),
        (
            "none",
            f'address: "{PRODUCTION_ADDRESS}"\ntest_address: null',
        ),
        (
            "empty",
            f'address: "{PRODUCTION_ADDRESS}"\ntest_address: ""',
        ),
        (
            "whitespace",
            f'address: "{PRODUCTION_ADDRESS}"\ntest_address: "  \\t  "',
        ),
        (
            "bool",
            f'address: "{PRODUCTION_ADDRESS}"\ntest_address: true',
        ),
        (
            "integer",
            f'address: "{PRODUCTION_ADDRESS}"\ntest_address: 123',
        ),
        (
            "list",
            f'address: "{PRODUCTION_ADDRESS}"\ntest_address: []',
        ),
        (
            "mapping",
            f'address: "{PRODUCTION_ADDRESS}"\ntest_address: {{nested: value}}',
        ),
    ],
)
def test_ut05_invalid_test_address_fails_fast_without_production_fallback(
    tmp_path: Path, case_name: str, database_body: str
):
    """UT-05/DO-04: missing, empty, whitespace, and non-string values fail closed."""
    del case_name
    source_path, source_bytes = _write_source(
        tmp_path, _standard_yaml_with_database(database_body)
    )

    with pytest.raises(ValueError, match=r"database\.test_address"):
        get_config_manager(config_path=str(source_path), watch=False, test_mode=True)

    assert source_path.read_bytes() == source_bytes
    assert not ConfigManager._instances


@pytest.mark.parametrize(
    "database_value",
    ["null", "[]", '"not-a-mapping"', "123"],
)
def test_ut06_non_mapping_database_fails_fast(tmp_path: Path, database_value: str):
    """UT-06/DO-04: a present database node must be a mapping."""
    source_path, source_bytes = _write_source(
        tmp_path, _standard_yaml_with_database_value(database_value)
    )

    with pytest.raises(ValueError, match=r"database"):
        get_config_manager(config_path=str(source_path), watch=False, test_mode=True)

    assert source_path.read_bytes() == source_bytes
    assert not ConfigManager._instances


def test_ut07_only_test_address_creates_activity_address(tmp_path: Path):
    """UT-07/DO-01: an absent address is created from a valid test_address."""
    source_path, source_bytes = _write_source(tmp_path, ONLY_TEST_ADDRESS_YAML)

    cfg = get_config_manager(config_path=str(source_path), watch=False, test_mode=True)

    assert cfg.get("database.address") == TEST_ADDRESS
    assert cfg.database.address == TEST_ADDRESS
    assert source_path.read_bytes() == source_bytes


def test_ut08_success_and_failure_leave_production_source_bytes_unchanged(tmp_path: Path):
    """UT-08/DO-05: both successful and failed selection are copy-only operations."""
    valid_path, valid_bytes = _write_source(tmp_path / "valid", STANDARD_YAML)
    valid_cfg = get_config_manager(config_path=str(valid_path), watch=False, test_mode=True)
    assert valid_cfg.get("database.address") == TEST_ADDRESS
    assert valid_path.read_bytes() == valid_bytes

    _clear_instances_for_testing()
    TestEnvironmentManager.cleanup_current_test_environment()

    invalid_path, invalid_bytes = _write_source(
        tmp_path / "invalid",
        _standard_yaml_with_database(
            f'address: "{PRODUCTION_ADDRESS}"\ntest_address: null'
        ),
    )
    with pytest.raises(ValueError):
        get_config_manager(config_path=str(invalid_path), watch=False, test_mode=True)
    assert invalid_path.read_bytes() == invalid_bytes


def test_ut09_runtime_and_serializable_snapshot_use_same_test_address(tmp_path: Path):
    """UT-09/DO-08: runtime and SerializableConfigData expose one selected value."""
    source_path, source_bytes = _write_source(tmp_path, STANDARD_YAML)

    cfg = get_config_manager(config_path=str(source_path), watch=False, test_mode=True)
    serializable = cfg.get_serializable_data()

    assert cfg.database.address == TEST_ADDRESS
    assert cfg.get("database.address") == TEST_ADDRESS
    assert serializable.database.address == TEST_ADDRESS
    assert serializable.get("database.address") == TEST_ADDRESS
    assert serializable.to_dict()["database"]["address"] == TEST_ADDRESS
    assert source_path.read_bytes() == source_bytes


def test_ut10_invalid_address_error_and_capture_do_not_leak_address_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """UT-10/DO-04/DO-08: failures never print production or test addresses."""
    sensitive_invalid_yaml = f'''__data__:
  project_name: s1_02_project
  database:
    address: "{PRODUCTION_ADDRESS}"
    test_address:
      - "{TEST_ADDRESS}"
__type_hints__: {{}}
'''
    source_path, source_bytes = _write_source(tmp_path, sensitive_invalid_yaml)

    with pytest.raises(ValueError):
        get_config_manager(config_path=str(source_path), watch=False, test_mode=True)

    captured = capsys.readouterr()
    output = f"{captured.out}\n{captured.err}"
    assert PRODUCTION_ADDRESS not in output
    assert TEST_ADDRESS not in output
    assert source_path.read_bytes() == source_bytes
    assert not ConfigManager._instances


def test_ut11_yaml_comments_and_non_target_fields_are_preserved(tmp_path: Path):
    """UT-11: conversion preserves comments and unrelated configuration fields."""
    source_yaml = f'''# keep this source comment
__data__:
  project_name: s1_02_project
  database:
    # keep this database comment
    address: "{PRODUCTION_ADDRESS}"
    test_address: "{TEST_ADDRESS}"
  retained_field: "retain-me"
__type_hints__: {{}}
'''
    source_path, source_bytes = _write_source(tmp_path, source_yaml)

    cfg = get_config_manager(config_path=str(source_path), watch=False, test_mode=True)
    copied_path = Path(cfg.get_config_file_path())
    copied_text = copied_path.read_text(encoding="utf-8")

    assert "# keep this database comment" in copied_text
    assert 'retained_field: "retain-me"' in copied_text
    assert cfg.get("retained_field") == "retain-me"
    assert cfg.get("database.address") == TEST_ADDRESS
    assert source_path.read_bytes() == source_bytes


def test_ut13_same_cache_key_reuses_consistent_selected_instance(tmp_path: Path):
    """UT-13: repeated access with one cache key does not diverge in address."""
    source_path, source_bytes = _write_source(tmp_path, STANDARD_YAML)

    first = get_config_manager(config_path=str(source_path), watch=False, test_mode=True)
    second = get_config_manager(config_path=str(source_path), watch=False, test_mode=True)

    assert second is first
    assert first.get("database.address") == TEST_ADDRESS
    assert second.get("database.address") == TEST_ADDRESS
    assert first.get_serializable_data().get("database.address") == TEST_ADDRESS
    assert source_path.read_bytes() == source_bytes
