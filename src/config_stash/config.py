import os
from typing import Any
from typing import List

import yaml


class Config(dict):
    """
    Custom configuration class that extends the Python dict class.
    This class provides methods to load configuration data from environment variables,
    YAML files and vault secrets.

    Example Usage:
        # Creating a Config instance with optional VaultFetcher instance
        config = Config(vault_fetcher=VaultFetcher())

        # Loading keys from environment variables
        config.load_many_keys_from_env(["ENV_KEY1", "ENV_KEY2"])

        # Loading a specific key from an environment variable
        config.load_from_env("ENV_KEY3")

        # Loading environment variables with specific prefixes
        config.load_prefixed_env_vars(allowed_prefixes=["PREFIX1_", "PREFIX2_"])

        # Loading configuration data from a YAML file
        config.load_from_yaml_file("config.yaml")

        # Loading a secret from Vault
        config.load_from_vault("secret/path", "secret_key", custom_key_name="custom_key")

        # Accessing configuration values
        value1 = config.get("ENV_KEY1")
        value2 = config.get("ENV_KEY2")
        value3 = config.get("ENV_KEY3")
        nested_value = config.get("nested.key")

        # Setting a new key-value pair
        config["new_key"] = "new_value"
    """

    def __init__(self, vault_fetcher: Any = None, *args, **kwargs):
        """
        Initialize a new Config instance.

        Args:
            vault_fetcher (Any, optional): An object with a method get_value_from_vault(path, key)
                to fetch secret values from Vault.
            *args: Additional positional arguments to pass to the base class constructor.
            **kwargs: Additional keyword arguments to pass to the base class constructor.
        """
        super().__init__(*args, **kwargs)
        self.vault_fetcher = vault_fetcher

    def load_many_keys_from_env(self, keys: List[str]):
        """
        Load multiple keys from environment variables and store them in the Config object.

        Args:
            keys (list): A list of environment variable keys to load.

        Raises:
            KeyError: If any of the specified environment variables are not set.
        """
        for key in keys:
            if key not in os.environ.keys():
                raise KeyError(f"Environment variable {key} isn't set")

            self[key] = os.environ.get(key)

    def load_from_env(self, key: str, custom_key_name: str = None):
        """
        Load a key from an environment variable and store it in the Config object.

        Args:
            key (str): The environment variable key to load.
            custom_key_name (str, optional): The custom key name to use in the Config object.
                If not provided, the environment variable key is used as the key name.

        Raises:
            KeyError: If the specified environment variable is not set.
        """
        if key not in os.environ.keys():
            raise KeyError(f"Environment variable {key} isn't set")

        if not custom_key_name:
            self[key] = os.environ.get(key)
        else:
            self[custom_key_name] = os.environ.get(key)

    def load_prefixed_env_vars(self, allowed_prefixes: List[str] = None):
        """
        Load environment variables with specified prefixes and store them in the Config object.

        Args:
            allowed_prefixes (list, optional): A list of allowed prefixes for environment variables.

        Raises:
            TypeError: If allowed_prefixes is not provided.
        """
        if not allowed_prefixes:
            raise TypeError("You should provide the prefixes of the variables that should be loaded.")

        for key in os.environ.keys():
            for prefix in allowed_prefixes:
                if key.startswith(prefix) and key not in self:
                    self[key] = os.environ.get(key)

    def _load_env_variable(self, yaml_value: str, yaml_key: str):
        env_key = yaml_value.strip("ENV.")
        self.load_from_env(env_key, yaml_key)

    def _load_vault_secret(self, yaml_value: str, yaml_key: str):
        vault_path, vault_key = yaml_value.strip("VAULT.").split(".")
        self.load_from_vault(vault_path, vault_key, yaml_key)

    def load_from_yaml_file(self, filepath: str):
        """
        Load configuration data from a YAML file and store it in the Config object.

        Args:
            filepath (str): The path to the YAML file containing the configuration data.

        Raises:
            FileNotFoundError: If the specified file is not found.
            ValueError: If the file content is not valid YAML.
            yaml.YAMLError: If there is an error parsing the YAML data.
        """
        try:
            with open(filepath) as file:
                data = yaml.safe_load(file)
                self._load_yaml_data(data)
        except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
            raise type(e)(f"Error loading data from file: '{filepath}'") from e

    def _load_yaml_data(self, data: dict, parent_key: str = ''):
        for key, value in data.items():
            if isinstance(value, dict):
                nested_key = f'{parent_key}.{key}' if parent_key else key
                self._load_yaml_data(value, nested_key)
                self._set_nested_dict(nested_key, value)
            else:
                if isinstance(value, str):
                    if value.startswith("ENV."):
                        self._load_env_variable(value, key)
                    elif value.startswith("VAULT."):
                        self._load_vault_secret(value, key)
                    elif key not in self:
                        self[key] = value
                else:
                    if key not in self:
                        self[key] = value

    def _set_nested_dict(self, key: str, value: dict):
        keys = key.split('.')
        current_dict = self
        for k in keys[:-1]:
            current_dict = current_dict.setdefault(k, {})
        current_dict[keys[-1]] = value

    def load_from_vault(
        self,
        vault_secret_path: str,
        vault_secret_key: str,
        custom_key_name: str = None,
    ):
        """
        Load a secret value from Vault and store it in the Config object.

        Args:
            vault_secret_path (str): The path to the secret in Vault.
            vault_secret_key (str): The key of the secret within the specified path.
            custom_key_name (str, optional): The custom key name to use in the Config object.
                If not provided, the vault_secret_key is used as the key name.

        Raises:
            KeyError: If the specified Vault secret path or key is not found.
        """
        vault_secret_value = self.vault_fetcher.get_value_from_vault(vault_secret_path, vault_secret_key)

        if custom_key_name and custom_key_name not in self:
            self[custom_key_name] = vault_secret_value
        else:
            self[vault_secret_key] = vault_secret_value

    def __setitem__(self, key: str, value: str):
        super().__setitem__(key, value)
        os.environ[key] = str(value)
