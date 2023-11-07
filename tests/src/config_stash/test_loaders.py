from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import yaml

from src.config_stash.loaders import EnvLoader
from src.config_stash.loaders import MultipleEnvLoader
from src.config_stash.loaders import PrefixedEnvLoader
from src.config_stash.loaders import VaultLoader
from src.config_stash.loaders import YamlLoader


def test_load_from_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "default_api_key")
    monkeypatch.setenv("DATABASE_URL", "default_database_url")

    loader = EnvLoader()

    assert loader.load("API_KEY") == "default_api_key"
    assert loader.load("DATABASE_URL") == "default_database_url"


def test_load_multiple_envvars(monkeypatch):
    monkeypatch.setenv("API_KEY", "default_api_key")
    monkeypatch.setenv("DATABASE_URL", "default_database_url")

    loader = MultipleEnvLoader()
    result = loader.load(["API_KEY", "DATABASE_URL"])

    assert "API_KEY" in result.keys() and result.get("API_KEY") == "default_api_key"
    assert "DATABASE_URL" in result.keys() and result.get("DATABASE_URL") == "default_database_url"


def test_load_list_of_envvars_with_one_invalid_value(monkeypatch):
    monkeypatch.setenv("API_KEY", "default_api_key")
    monkeypatch.setenv("DATABASE_URL", "default_database_url")

    loader = MultipleEnvLoader()
    with pytest.raises(KeyError):
        loader.load(["API_KEY", "DATABASE_URL", "INVALID_KEY"])


def test_load_prefixed_envvars(monkeypatch):
    monkeypatch.setenv("rainmaker_API_KEY", "rainmaker_api_key")
    monkeypatch.setenv("rm_database_url", "rm_database_url")
    monkeypatch.setenv("RM_PASSWORD", "rm_password")

    loader = PrefixedEnvLoader()
    result = loader.load(["rainmaker", "rm", "RM"])

    assert "rainmaker_api_key" in result.values()
    assert "rm_database_url" in result.values()
    assert "rm_password" in result.values()


def test_load_prefixed_envvars_without_sending_list_of_prefixes(monkeypatch):
    monkeypatch.setenv("Prefix_API_KEY", "default_api_key")
    monkeypatch.setenv("DATABASE_URL", "database_url")

    loader = PrefixedEnvLoader()
    with pytest.raises(TypeError):
        loader.load()


def test_load_prefixed_envvars_case_sensitive(monkeypatch):
    monkeypatch.setenv("InvalidPrefix_API_KEY", "invalid_api_key")
    monkeypatch.setenv("INVALID_DATABASE_URL", "invalid_database_url")

    loader = PrefixedEnvLoader()
    result = loader.load(["invalid", "iNvAlId"])

    assert result == {}


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


@patch('src.config_stash.loaders.YamlLoader._load_yaml_data')
def test_load_from_yaml_file(mock_load_yaml_data, temp_config_file, config_data):
    loader = YamlLoader()

    loader.load(temp_config_file)

    mock_load_yaml_data.assert_called_once_with(config_data, vault_fetcher=None)


@patch('src.config_stash.loaders.YamlLoader._load_vault_secret')
@patch('src.config_stash.loaders.YamlLoader._load_env_variable')
def test_load_from_yaml_file_envvars_prefixed_with_ENV_and_VAULT(
    mock_load_env_variable,
    mock_load_vault_secret,
    config_data,
):
    loader = YamlLoader()

    loader._load_yaml_data(config_data)

    mock_load_vault_secret.assert_called_once_with("VAULT.vault_secret_path.vault_secret_key", "db_pass", None)
    mock_load_env_variable.assert_called_once_with("ENV.USER", "username")
    assert isinstance(loader.data["cloudaccessdb"], dict)
    assert loader.data["url"] == "stage"


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


@patch('src.config_stash.loaders.YamlLoader._load_vault_secret')
@patch('src.config_stash.loaders.YamlLoader._load_env_variable')
def test_load_yaml_data_with_VAULT_and_ENV_in_nested_dict(
    mock_load_env_variable,
    mock_load_vault_secret,
    data_VAULT_and_ENV_in_nested_dict,
):
    loader = YamlLoader()
    loader._load_yaml_data(data_VAULT_and_ENV_in_nested_dict)

    mock_load_vault_secret.assert_called_once_with("VAULT.vault_secret_path.vault_secret_key", "prefix_name", None)
    mock_load_env_variable.assert_called_once_with("ENV.USER", "user")
    assert isinstance(loader.data["cloudaccessdb"], dict)


@patch('src.config_stash.loaders.EnvLoader.load')
def test_private_method_load_env_variable(mock_load_env_loader):
    loader = YamlLoader()

    loader._load_env_variable("ENV.USER", "username")

    mock_load_env_loader.assert_called_once_with("USER")
    assert "username" in loader.data.keys()


@pytest.fixture
def vault_fetcher_mock():
    vault_fetcher_mock = MagicMock()
    vault_fetcher_mock.get_value_from_vault = "mocked_secret_value"
    return vault_fetcher_mock


@patch('src.config_stash.loaders.VaultLoader.load')
def test_private_method_load_vault_secret(vault_loader_magic_mock, vault_fetcher_mock):
    loader = YamlLoader()

    loader._load_vault_secret("VAULT.vault_secret_path.vault_secret_key", "db_pass", vault_fetcher_mock)

    vault_loader_magic_mock.assert_called_once_with("vault_secret_path", "vault_secret_key", vault_fetcher_mock)
    assert "db_pass" in loader.data.keys()


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
    loader = YamlLoader()

    loader.load(temp_config_file_nested_data)

    assert "cloudaccessdb" in loader.data.keys()
    assert isinstance(loader.data["cloudaccessdb"], dict)
    assert loader.data.get("cloudaccessdb").get("prefix_name") == "cloud_db"
    assert loader.data.get("cloudaccessdb").get("user") == "cloud_access_user"
    assert loader.data.get("cloudaccessdb").get("host") == "example.com"


def test_multiple_nested_keys_from_yaml(temp_config_file_nested_data):
    loader = YamlLoader()

    loader.load(temp_config_file_nested_data)

    assert "cloudaccessdb" in loader.data.keys()
    assert isinstance(loader.data["cloudaccessdb"], dict)
    assert loader.data.get("cloudaccessdb").get("prefix_name") == "cloud_db"
    assert loader.data.get("cloudaccessdb").get("user") == "cloud_access_user"
    assert loader.data.get("cloudaccessdb").get("host") == "example.com"

    assert "cloud_access_db" in loader.data.keys()
    assert isinstance(loader.data["cloud_access_db"], dict)
    assert loader.data.get("cloud_access_db").get("port") == 1234
    assert loader.data.get("cloud_access_db").get("dbName") == "cloud_access"


@pytest.fixture
def temp_file_with_int_values(tmpdir):
    config_data = {'port': 1234}
    filepath = tmpdir.join("config.yaml")
    with open(filepath, 'w') as file:
        yaml.safe_dump(config_data, file)
    return str(filepath)


def test_int_values_in_file(temp_file_with_int_values):
    loader = YamlLoader()

    loader.load(temp_file_with_int_values)

    assert loader.data["port"] == 1234


def test_load_envvars_from_non_existent_file():
    loader = YamlLoader()
    with pytest.raises(FileNotFoundError):
        loader.load("invalid_filepath.yaml")


def test_vault_loader():
    vault_fetcher_mock = MagicMock()
    vault_fetcher_mock.get_value_from_vault.return_value = "vault_secret_value"

    loader = VaultLoader()
    result = loader.load("vault/secret/path", "vault_secret_key", vault_fetcher_mock)

    assert result == "vault_secret_value"
