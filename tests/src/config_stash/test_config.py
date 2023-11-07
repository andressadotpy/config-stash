import os
from unittest.mock import MagicMock

import pytest

from src.config_stash.config import Config


def test_update_environment_variable_from_config():
    config = Config({"API_KEY": "default_api_key"})

    config["API_KEY"] = "new_api_key"

    assert os.environ["API_KEY"] == "new_api_key"


def test_get_many_variables_from_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "default_api_key")
    monkeypatch.setenv("DATABASE_URL", "default_database_url")

    config = Config()
    config.load_many_keys_from_env(["API_KEY", "DATABASE_URL"])

    assert config["API_KEY"] == "default_api_key"
    assert config["DATABASE_URL"] == "default_database_url"


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "default_api_key")

    config = Config()
    config.load_from_env("API_KEY")

    assert config["API_KEY"] == "default_api_key"


def test_load_prefixed_envvars(monkeypatch):
    monkeypatch.setenv("API_KEY", "default_api_key")
    monkeypatch.setenv("RM_API_KEY", "rm_api_key")
    monkeypatch.setenv("rm_database_url", "db_url")

    config = Config()
    config.load_prefixed_env_vars(["RM"])

    assert config["RM_API_KEY"] == "rm_api_key"
    assert "API_KEY" not in config.keys()
    assert "rm_database_url" not in config.keys()


def test_load_from_vault():
    vault_secret_path = "secret/path"
    vault_secret_key = "secret_key"
    vault_loader_mock = MagicMock()
    vault_loader_mock.get_value_from_vault.return_value = "vault_secret_value"

    config = Config(vault_loader_mock)

    config.load_from_vault(vault_secret_path, vault_secret_key)

    vault_loader_mock.get_value_from_vault.assert_called_once_with(vault_secret_path, vault_secret_key)
    assert config["secret_key"] == "vault_secret_value"


def test_load_from_vault_with_custom_key():
    vault_secret_path = "secret/path"
    vault_secret_key = "secret_key"
    vault_loader_mock = MagicMock()
    vault_loader_mock.get_value_from_vault.return_value = "vault_secret_value"

    config = Config(vault_loader_mock)

    config.load_from_vault(vault_secret_path, vault_secret_key, "custom_secret_key")

    vault_loader_mock.get_value_from_vault.assert_called_once_with(vault_secret_path, vault_secret_key)
    assert config["custom_secret_key"] == "vault_secret_value"


def test_config_without_vault_fetcher():
    vault_secret_path = "secret/path"
    vault_secret_key = "secret_key"

    config = Config()

    with pytest.raises(AttributeError):
        config.load_from_vault(vault_secret_path, vault_secret_key)
