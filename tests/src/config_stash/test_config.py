import yaml
import os
import pytest
from unittest.mock import MagicMock, patch

from src.config_stash.config import Config


def test_envvars_with_config():
    config = Config({"API_KEY": "default_api_key", "DATABASE_URL": "default_database_url"})
    assert config["API_KEY"] == "default_api_key"
    assert config["DATABASE_URL"] == "default_database_url"

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


def test_load_envvars_from_env_with_wrong_key_between_right_keys(monkeypatch):
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


def test_load_invalid_prefixes(monkeypatch):
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
            'host': 'dbproxy01.dba-001.prod.iad2.dc.redhat.com',
        },
        'cloud_access_db': {'port': 2317, 'dbName': 'cloud_access'},
    }
    filepath = tmpdir.join("config.yaml")
    with open(filepath, 'w') as file:
        yaml.safe_dump(config_data, file)
    return str(filepath)


@patch('src.config_stash.config.Config._load_vault_secret')
@patch('src.config_stash.config.Config._load_env_variable')
def test_load_from_yaml_file_envvars_prefixed_with_ENV(mock_load_env_variable, mock_load_vault_secret, temp_config_file):
    config = Config()

    config.load_from_yaml_file(temp_config_file)

    mock_load_vault_secret.assert_called_once_with("VAULT.vault_secret_path.vault_secret_key", "db_pass")
    mock_load_env_variable.assert_called_once_with("ENV.USER", "username")
    assert isinstance(config["cloudaccessdb"], dict)
    
    
@patch('src.config_stash.config.Config.load_from_env')
def test_private_method_load_env_variable(mock_load_from_env):
    config = Config()
    
    config._load_env_variable("ENV.USER", "username")
    
    mock_load_from_env.assert_called_once_with("USER", "username")
    

@patch('src.config_stash.config.Config.load_from_vault')
def test_private_method_load_env_variable(mock_load_from_vault):
    config = Config()
    
    config._load_vault_secret("VAULT.vault_secret_path.vault_secret_key", "db_pass")
    
    mock_load_from_vault.assert_called_once_with("vault_secret_path", "vault_secret_key", "db_pass")
    
 
@pytest.fixture
def temp_nested_data_config_file(tmpdir):
    config_data = {
        'cloudaccessdb': {
            'prefix_name': 'cloud_db',
            'user': 'cloud_access_user',
            'host': 'dbproxy01.dba-001.prod.iad2.dc.redhat.com',
        },
        'cloud_access_db': {'port': 2317, 'dbName': 'cloud_access'},
    }
    filepath = tmpdir.join("config.yaml")
    with open(filepath, 'w') as file:
        yaml.safe_dump(config_data, file)
    return str(filepath)


def test_nested_keys_from_yaml(temp_nested_data_config_file):
    config = Config()
    
    config.load_from_yaml_file(temp_nested_data_config_file)
    
    assert "cloudaccessdb" in config.keys()
    assert isinstance(config["cloudaccessdb"], dict)
    assert config.get("cloudaccessdb").get("prefix_name") == "cloud_db"
    assert config.get("cloudaccessdb").get("user") == "cloud_access_user"
    assert config.get("cloudaccessdb").get("host") == "dbproxy01.dba-001.prod.iad2.dc.redhat.com"
    

def test_multiple_nested_keys_from_yaml(temp_nested_data_config_file):
    config = Config()
    
    config.load_from_yaml_file(temp_nested_data_config_file)
    
    assert "cloudaccessdb" in config.keys()
    assert isinstance(config["cloudaccessdb"], dict)
    assert config.get("cloudaccessdb").get("prefix_name") == "cloud_db"
    assert config.get("cloudaccessdb").get("user") == "cloud_access_user"
    assert config.get("cloudaccessdb").get("host") == "dbproxy01.dba-001.prod.iad2.dc.redhat.com"
    
    assert "cloud_access_db" in config.keys()
    assert isinstance(config["cloud_access_db"], dict)
    assert config.get("cloud_access_db").get("port") == 2317
    assert config.get("cloud_access_db").get("dbName") == "cloud_access" 
    
    
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