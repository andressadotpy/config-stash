import yaml
import os
from typing import Any, List


class Config(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load_many_keys_from_env(self, keys: List[str]):
        for key in keys:
            if key not in os.environ.keys():
                raise KeyError(f"Environment variable {key} isn't set")

            self[key] = os.environ.get(key)

    def load_from_env(self, key: str, custom_key_name: str = None):
        if key not in os.environ.keys():
            raise KeyError(f"Environment variable {key} isn't set")

        if not custom_key_name:
            self[key] = os.environ.get(key)
        else:
            self[custom_key_name] = os.environ.get(key)

    def load_prefixed_env_vars(self, allowed_prefixes: List[str] = None):
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
        try:
            with open(filepath) as file:
                data = yaml.safe_load(file)
                self._load_yaml_data(data)
        except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
            raise type(e)(f"Error loading data from file: '{filepath}'") from e
        
    def _load_yaml_data(self, data: dict, parent_key=''):
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
        fetcher: Any,
        custom_key_name: str = None,
    ):
        vault_secret_value = fetcher.get_value_from_vault(vault_secret_path, vault_secret_key)

        if custom_key_name and custom_key_name not in self:
            self[custom_key_name] = vault_secret_value
        else:
            self[vault_secret_key] = vault_secret_value

    def __setitem__(self, key: str, value: str):
        super().__setitem__(key, value)
        os.environ[key] = str(value)