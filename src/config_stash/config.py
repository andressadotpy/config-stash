import os
from typing import Any
from typing import List

from src.config_stash.loaders import EnvLoader
from src.config_stash.loaders import MultipleEnvLoader
from src.config_stash.loaders import PrefixedEnvLoader
from src.config_stash.loaders import VaultLoader
from src.config_stash.loaders import YamlLoader


class Config(dict):
    def __init__(self, vault_fetcher: Any = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vault_fetcher = vault_fetcher

    def load_many_keys_from_env(self, keys: List[str], loader: Any = MultipleEnvLoader()):
        values = loader.load(keys)
        self.update(values)

    def load_from_env(self, key: str, custom_key_name: str = None, loader: Any = EnvLoader()):
        value = loader.load(key)
        if not custom_key_name:
            self[key] = value
        else:
            self[custom_key_name] = value

    def load_prefixed_env_vars(self, allowed_prefixes: List[str] = None, loader: Any = PrefixedEnvLoader()):
        values = loader.load(allowed_prefixes)
        for key, value in values.items():
            if key not in self:
                self[key] = value

    def load_from_yaml_file(self, filepath: str, loader: Any = YamlLoader()):
        values = loader.load(filepath, self.vault_fetcher)
        self.update(values)

    def load_from_vault(
        self, vault_secret_path: str, vault_secret_key: str, custom_key_name: str = None, loader: Any = VaultLoader()
    ):
        vault_secret_value = loader.load(vault_secret_path, vault_secret_key, self.vault_fetcher)

        if custom_key_name and custom_key_name not in self:
            self[custom_key_name] = vault_secret_value
        else:
            self[vault_secret_key] = vault_secret_value

    def __setitem__(self, key: str, value: str):
        super().__setitem__(key, value)
        os.environ[key] = str(value)
