"""Reglas de privacidad de la configuracion local.

La skill `ai-image-studio-user-guide` promete tres cosas: que no se guardan claves en
texto plano, que no se puede habilitar un servicio externo con las subidas
desactivadas, y que hace falta reconocer la politica de datos. Aqui se comprueban.
"""

from __future__ import annotations

import json

import pytest

from ai_image_studio.user_config import (
    default_user_config,
    read_and_validate_user_config,
    validate_user_config,
    write_default_user_config,
)


def config_con_servicio(**cambios) -> dict:
    config = default_user_config()
    servicio = {
        "name": "ejemplo",
        "purpose": "prueba de reglas de privacidad",
        "enabled": True,
        "auth_env": "EJEMPLO_API_KEY",
        "data_policy_acknowledged": True,
    }
    servicio.update(cambios)
    config["external_services"] = [servicio]
    config["privacy"]["allow_external_uploads"] = True
    return config


def test_the_default_configuration_is_valid_and_fails_closed():
    config = default_user_config()
    validate_user_config(config)
    assert config["privacy"]["allow_external_uploads"] is False
    assert config["privacy"]["preserve_originals"] is True
    assert config["defaults"]["fail_closed"] is True


def test_a_plaintext_secret_is_rejected():
    """auth_env es el NOMBRE de una variable de entorno, nunca su valor."""
    with pytest.raises(ValueError, match="variable de entorno"):
        validate_user_config(config_con_servicio(auth_env="sk-clave-en-texto-plano"))


def test_an_external_service_cannot_be_enabled_with_uploads_disabled():
    config = config_con_servicio()
    config["privacy"]["allow_external_uploads"] = False
    with pytest.raises(ValueError, match="allow_external_uploads"):
        validate_user_config(config)


def test_an_enabled_service_requires_acknowledging_the_data_policy():
    with pytest.raises(ValueError, match="data_policy_acknowledged"):
        validate_user_config(config_con_servicio(data_policy_acknowledged=False))


def test_a_disabled_service_needs_no_acknowledgement():
    validate_user_config(config_con_servicio(enabled=False, data_policy_acknowledged=False))


def test_writing_does_not_overwrite_without_being_asked(tmp_path):
    destino = tmp_path / "config.json"
    write_default_user_config(str(destino))
    with pytest.raises(FileExistsError):
        write_default_user_config(str(destino))
    write_default_user_config(str(destino), overwrite=True)


def test_a_config_written_with_a_bom_can_be_read(tmp_path):
    """El Bloc de notas de Windows guarda con BOM; leerlo no puede fallar."""
    destino = tmp_path / "config.json"
    destino.write_bytes(
        b"\xef\xbb\xbf" + json.dumps(default_user_config()).encode("utf-8")
    )
    assert read_and_validate_user_config(str(destino))["valid"] is True


def test_an_invalid_schema_is_reported_with_the_offending_path(tmp_path):
    config = default_user_config()
    config["privacy"]["preserve_originals"] = "puede que si"
    destino = tmp_path / "config.json"
    destino.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="privacy/preserve_originals"):
        read_and_validate_user_config(str(destino))
