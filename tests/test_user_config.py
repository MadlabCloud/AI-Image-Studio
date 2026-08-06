from pathlib import Path

import pytest

from ai_image_studio.user_config import (
    default_user_config,
    read_and_validate_user_config,
    validate_user_config,
    write_default_user_config,
)


def test_default_config_is_valid():
    config = default_user_config("./workspace")
    validate_user_config(config)
    assert config["privacy"]["preserve_originals"] is True
    assert config["defaults"]["fail_closed"] is True


def test_external_service_requires_upload_permission():
    config = default_user_config("./workspace")
    config["external_services"] = [{"name": "example", "enabled": True, "purpose": "test", "auth_env": "EXAMPLE_KEY", "data_policy_acknowledged": True}]
    with pytest.raises(ValueError):
        validate_user_config(config)


def test_plain_secret_name_is_rejected():
    config = default_user_config("./workspace")
    config["privacy"]["allow_external_uploads"] = True
    config["external_services"] = [{"name": "example", "enabled": True, "purpose": "test", "auth_env": "secret-value", "data_policy_acknowledged": True}]
    with pytest.raises(ValueError):
        validate_user_config(config)


def test_write_and_read_config(tmp_path):
    path = tmp_path / "config.json"
    out = write_default_user_config(str(path), str(tmp_path / "workspace"))
    assert Path(out["path"]).is_file()
    validated = read_and_validate_user_config(str(path))
    assert validated["valid"] is True
