import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import yaml

from src.config_stash.config import Config


def test_initializing_config_with_key_value_pairs():
    config = Config({"API_KEY": "default_api_key", "DATABASE_URL": "default_database_url"})

    assert config["API_KEY"] == "default_api_key"
    assert config["DATABASE_URL"] == "default_database_url"


def test_update_environment_variable_from_config():
    config = Config({"API_KEY": "default_api_key"})

    config["API_KEY"] = "new_api_key"

    assert os.environ["API_KEY"] == "new_api_key"


def test_load_envvars_from_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "default_api_key")
    monkeypatch.setenv("DATABASE_URL", "default_database_url")

    config = Config()
    config.load_many_keys_from_env(["API_KEY", "DATABASE_URL"])

    assert config["API_KEY"] == "default_api_key"
    assert config["DATABASE_URL"] == "default_database_url"


def test_load_envvars_from_env_wrong_key():
    config = Config()

    with pytest.raises(KeyError):
        config.load_many_keys_from_env(["NON_EXISTENT_KEY"])


def test_load_list_of_envvars_with_one_invalid_value(monkeypatch):
    monkeypatch.setenv("API_KEY", "default_api_key")
    monkeypatch.setenv("DATABASE_URL", "default_database_url")

    config = Config()
    with pytest.raises(KeyError):
        config.load_many_keys_from_env(["API_KEY", "DATABASE_URL", "INVALID_KEY"])

    assert config["API_KEY"] == "default_api_key"
    assert config["DATABASE_URL"] == "default_database_url"
    assert "INVALID_KEY" not in config


def test_load_prefixed_envvars(monkeypatch):
    monkeypatch.setenv("rainmaker_API_KEY", "rainmaker_api_key")
    monkeypatch.setenv("rm_database_url", "rm_database_url")
    monkeypatch.setenv("RM_PASSWORD", "rm_password")

    config = Config()
    config.load_prefixed_env_vars(["Rainmaker", "RM", "rm", "rainmaker"])

    assert config["rainmaker_API_KEY"] == "rainmaker_api_key"
    assert config["rm_database_url"] == "rm_database_url"
    assert config["RM_PASSWORD"] == "rm_password"


def test_load_prefixed_envvars_without_sending_list_of_prefixes(monkeypatch):
    monkeypatch.setenv("Prefix_API_KEY", "default_api_key")
    monkeypatch.setenv("DATABASE_URL", "database_url")

    config = Config()
    with pytest.raises(TypeError):
        config.load_prefixed_env_vars()

    assert "Prefix_API_KEY" not in config
    assert "DATABASE_URL" not in config


def test_load_prefixed_envvars_case_sensitive(monkeypatch):
    monkeypatch.setenv("InvalidPrefix_API_KEY", "invalid_api_key")
    monkeypatch.setenv("INVALID_DATABASE_URL", "invalid_database_url")

    config = Config()
    config.load_prefixed_env_vars(["invalid", "iNvAlId"])

    assert "InvalidPrefix_API_KEY" not in config
    assert "INVALID_DATABASE_URL" not in config


@pytest.fixture
def temp_config_file(tmpdir):
    config_data = {
        'url': 'stage',
        'database': 'db_address',
        'db_pass': 'VAULT.vault_secret_path.vault_secret_key',
        'username': 'ENV.USER',
        'cloudaccessdb': {
            'prefix_name': 'cloud_db',
            'user': 'cloud_access_user',
            'host': 'example.com',
        },
        'cloud_access_db': {'port': 1234, 'dbName': 'cloud_access'},
    }
    filepath = tmpdir.join("config.yaml")
    with open(filepath, 'w') as file:
        yaml.safe_dump(config_data, file)
    return str(filepath)


@pytest.fixture
def config_data():
    return {
        'url': 'stage',
        'database': 'db_address',
        'db_pass': 'VAULT.vault_secret_path.vault_secret_key',
        'username': 'ENV.USER',
        'cloudaccessdb': {
            'prefix_name': 'cloud_db',
            'user': 'cloud_access_user',
            'host': 'example.com',
        },
        'cloud_access_db': {'port': 1234, 'dbName': 'cloud_access'},
    }


@patch('src.config_stash.config.Config._load_yaml_data')
def test_load_from_yaml_file(mock_load_yaml_data, temp_config_file, config_data):
    config = Config()

    config.load_from_yaml_file(temp_config_file)

    mock_load_yaml_data.assert_called_once_with(config_data)


@patch('src.config_stash.config.Config._load_vault_secret')
@patch('src.config_stash.config.Config._load_env_variable')
def test_load_from_yaml_file_envvars_prefixed_with_ENV_and_VAULT(
    mock_load_env_variable, mock_load_vault_secret, config_data
):
    config = Config()

    config._load_yaml_data(config_data)

    mock_load_vault_secret.assert_called_once_with("VAULT.vault_secret_path.vault_secret_key", "db_pass")
    mock_load_env_variable.assert_called_once_with("ENV.USER", "username")
    assert isinstance(config["cloudaccessdb"], dict)
    assert config["url"] == "stage"


@pytest.fixture
def data_VAULT_and_ENV_in_nested_dict():
    return {
        'url': 'stage',
        'database': 'db_address',
        'cloudaccessdb': {
            'prefix_name': 'VAULT.vault_secret_path.vault_secret_key',
            'user': 'ENV.USER',
            'host': 'example.com',
        },
        'cloud_access_db': {'port': 1234, 'dbName': 'cloud_access'},
    }


@patch('src.config_stash.config.Config._load_vault_secret')
@patch('src.config_stash.config.Config._load_env_variable')
def test_load_yaml_data_with_VAULT_and_ENV_in_nested_dict(
    mock_load_env_variable, mock_load_vault_secret, data_VAULT_and_ENV_in_nested_dict
):
    config = Config()
    config._load_yaml_data(data_VAULT_and_ENV_in_nested_dict)

    mock_load_vault_secret.assert_called_once_with("VAULT.vault_secret_path.vault_secret_key", "prefix_name")
    mock_load_env_variable.assert_called_once_with("ENV.USER", "user")
    assert isinstance(config["cloudaccessdb"], dict)


@patch('src.config_stash.config.Config.load_from_env')
def test_private_method_load_env_variable(mock_load_from_env):
    config = Config()

    config._load_env_variable("ENV.USER", "username")

    mock_load_from_env.assert_called_once_with("USER", "username")


@patch('src.config_stash.config.Config.load_from_vault')
def test_private_method_load_vault_secret(mock_load_from_vault):
    config = Config()

    config._load_vault_secret("VAULT.vault_secret_path.vault_secret_key", "db_pass")

    mock_load_from_vault.assert_called_once_with("vault_secret_path", "vault_secret_key", "db_pass")


@pytest.fixture
def temp_config_file_nested_data(tmpdir):
    config_data = {
        'cloudaccessdb': {
            'prefix_name': 'cloud_db',
            'user': 'cloud_access_user',
            'host': 'example.com',
        },
        'cloud_access_db': {'port': 1234, 'dbName': 'cloud_access'},
    }
    filepath = tmpdir.join("config.yaml")
    with open(filepath, 'w') as file:
        yaml.safe_dump(config_data, file)
    return str(filepath)


def test_nested_keys_from_yaml(temp_config_file_nested_data):
    config = Config()

    config.load_from_yaml_file(temp_config_file_nested_data)

    assert "cloudaccessdb" in config.keys()
    assert isinstance(config["cloudaccessdb"], dict)
    assert config.get("cloudaccessdb").get("prefix_name") == "cloud_db"
    assert config.get("cloudaccessdb").get("user") == "cloud_access_user"
    assert config.get("cloudaccessdb").get("host") == "example.com"


def test_multiple_nested_keys_from_yaml(temp_config_file_nested_data):
    config = Config()

    config.load_from_yaml_file(temp_config_file_nested_data)

    assert "cloudaccessdb" in config.keys()
    assert isinstance(config["cloudaccessdb"], dict)
    assert config.get("cloudaccessdb").get("prefix_name") == "cloud_db"
    assert config.get("cloudaccessdb").get("user") == "cloud_access_user"
    assert config.get("cloudaccessdb").get("host") == "example.com"

    assert "cloud_access_db" in config.keys()
    assert isinstance(config["cloud_access_db"], dict)
    assert config.get("cloud_access_db").get("port") == 1234
    assert config.get("cloud_access_db").get("dbName") == "cloud_access"


@pytest.fixture
def temp_file_with_int_values(tmpdir):
    config_data = {'port': 1234}
    filepath = tmpdir.join("config.yaml")
    with open(filepath, 'w') as file:
        yaml.safe_dump(config_data, file)
    return str(filepath)


def test_int_values_in_file(temp_file_with_int_values):
    config = Config()

    config.load_from_yaml_file(temp_file_with_int_values)

    assert config["port"] == 1234


def test_load_envvars_from_non_existent_file():
    config = Config()
    with pytest.raises(FileNotFoundError):
        config.load_from_yaml_file("invalid_filepath.yaml")


def test_load_from_vault():
    vault_secret_path = "secret/path"
    vault_secret_key = "secret_key"
    vault_loader_mock = MagicMock()
    vault_loader_mock.get_value_from_vault.return_value = "vault_secret_value"

    config = Config()

    config.load_from_vault(vault_secret_path, vault_secret_key, vault_loader_mock)

    vault_loader_mock.get_value_from_vault.assert_called_once_with(vault_secret_path, vault_secret_key)
    assert config["secret_key"] == "vault_secret_value"


def test_load_from_vault_with_custom_key():
    vault_secret_path = "secret/path"
    vault_secret_key = "secret_key"
    vault_loader_mock = MagicMock()
    vault_loader_mock.get_value_from_vault.return_value = "vault_secret_value"

    config = Config()

    config.load_from_vault(vault_secret_path, vault_secret_key, vault_loader_mock, "custom_secret_key")

    vault_loader_mock.get_value_from_vault.assert_called_once_with(vault_secret_path, vault_secret_key)
    assert config["custom_secret_key"] == "vault_secret_value"
