import os
from typing import Any
from typing import List

from src.config_stash.loaders import EnvLoader
from src.config_stash.loaders import MultipleEnvLoader
from src.config_stash.loaders import PrefixedEnvLoader
from src.config_stash.loaders import VaultLoader
from src.config_stash.loaders import YamlLoader


class Config(dict):
    """
    A configuration class that extends the built-in Python dictionary.
    It provides methods to load configuration values from various sources
    such as environment variables, YAML files, and Vault secrets.
    """

    def __init__(self, vault_fetcher: Any = None, *args, **kwargs):
        """
        Initialize a new Config object.

        Args:
            vault_fetcher (Any, optional): An object used to fetch secrets from Vault. Defaults to None.
            *args: Positional arguments to initialize the parent dictionary.
            **kwargs: Keyword arguments to initialize the parent dictionary.
        """
        super().__init__(*args, **kwargs)
        self.vault_fetcher = vault_fetcher

    def load_many_keys_from_env(self, keys: List[str], loader: Any = MultipleEnvLoader()):
        """
        Load multiple keys from environment variables using the specified loader.

        Args:
            keys (List[str]): List of environment variable keys to load.
            loader (Any, optional): Loader object to load environment variables. Defaults to MultipleEnvLoader().
        """
        values = loader.load(keys)
        self.update(values)

    def load_from_env(self, key: str, custom_key_name: str = None, loader: Any = EnvLoader()):
        """
        Load a key from an environment variable using the specified loader.

        Args:
            key (str): Environment variable key to load.
            custom_key_name (str, optional): Optional custom key name for the loaded value. Defaults to None.
            loader (Any, optional): Loader object to load the environment variable. Defaults to EnvLoader().
        """
        value = loader.load(key)
        if not custom_key_name:
            self[key] = value
        else:
            self[custom_key_name] = value

    def load_prefixed_env_vars(self, allowed_prefixes: List[str] = None, loader: Any = PrefixedEnvLoader()):
        """
        Load environment variables with specified prefixes using the specified loader.

        Args:
            allowed_prefixes (List[str], optional): List of allowed prefixes for environment variables.
            Defaults to None.
            loader (Any, optional): Loader object to load environment variables.
            Defaults to PrefixedEnvLoader().
        """
        values = loader.load(allowed_prefixes)
        for key, value in values.items():
            if key not in self:
                self[key] = value

    def load_from_yaml_file(self, filepath: str, loader: Any = YamlLoader()):
        """
        Load configuration data from a YAML file using the specified loader.

        Args:
            filepath (str): The path to the YAML file containing the configuration data.
            loader (Any, optional): Loader object to load YAML data. Defaults to YamlLoader().
        """
        values = loader.load(filepath, self.vault_fetcher)
        self.update(values)

    def load_from_vault(
        self, vault_secret_path: str, vault_secret_key: str, custom_key_name: str = None, loader: Any = VaultLoader()
    ):
        """
        Load a secret value from Vault using the specified loader.

        Args:
            vault_secret_path (str): Path to the Vault secret.
            vault_secret_key (str): Key of the secret within the specified path.
            custom_key_name (str, optional): Optional custom key name for the loaded value. Defaults to None.
            loader (Any, optional): Loader object to load the Vault secret. Defaults to VaultLoader().
        """
        vault_secret_value = loader.load(vault_secret_path, vault_secret_key, self.vault_fetcher)

        if custom_key_name and custom_key_name not in self:
            self[custom_key_name] = vault_secret_value
        else:
            self[vault_secret_key] = vault_secret_value

    def __setitem__(self, key: str, value: str):
        super().__setitem__(key, value)
        os.environ[key] = str(value)
