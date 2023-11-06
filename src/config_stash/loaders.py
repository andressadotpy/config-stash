import os
import yaml

from abc import ABC, abstractmethod
from typing import Any
from typing import List
from typing import Dict


class BaseLoader(ABC):
    @abstractmethod
    def load(self, *args, **kwargs) -> Any:
        """
        Abstract method for loading data from a specific source.
        """
        pass
    

class EnvLoader(BaseLoader):
    def load(self, key: str) -> Any:
        """
        Load a key from an environment variable.
        
        Raises:
            KeyError: If the specified environment variable is not set.
        """
        if key not in os.environ.keys():
            raise KeyError(f"Environment variable {key} isn't set")
        return os.environ.get(key)
    

class PrefixedEnvLoader(BaseLoader):
    def load(self, prefixes: List[str] = None) -> Dict[str, Any]:
        """
        Load keys starting with determined prefixes.

        Args:
            prefixes (List[str], optional): List of prefixes. Defaults to None.

        Raises:
            TypeError: If list of prefixes is not provided.

        Returns:
            Dict[Any]: Dictionary with key and values loaded from env.
        """
        if not prefixes:
            raise TypeError("You should provide the prefixes of the variables that should be loaded.")
        
        envvars = dict()
        for key in os.environ.keys():
            for prefix in prefixes:
                if key.startswith(prefix):
                    envvars[key] = os.environ.get(key)
                    
        return envvars
    
    
class MultipleEnvLoader(BaseLoader):
    def load(self, keys: List[str]) -> Dict[str, Any]:
        """
        Load multiple keys from environment variables.

        Args:
            keys (List[str]): List of keys to load.

        Raises:
            KeyError: If any of the specified environment variables are not set.

        Returns:
            Dict[str, Any]: Dictionary with key and values loaded from env.
        """
        envvars = dict()
        for key in keys:
            if key not in os.environ.keys():
                raise KeyError(f"Environment variable {key} isn't set")
            envvars[key] = os.environ.get(key)
            
        return envvars
    
    
class VaultLoader(BaseLoader):
    def load(self, vault_secret_path: str, vault_secret_key: str, vault_fetcher: Any) -> Any:
        if not vault_fetcher:
            raise AttributeError("Needs a vault fetcher object.")
        return vault_fetcher.get_value_from_vault(vault_secret_path, vault_secret_key)
    
    
class YamlLoader(BaseLoader):
    def __init__(self):
        self.data = dict()
    
    def load(self, filepath: str, vault_fetcher: Any = None) -> Dict[Any, Any]:
        """
        Load configuration data from a YAML file.

        Args:
            filepath (str): The path to the YAML file containing the configuration data.

        Raises:
            FileNotFoundError: If the specified file is not found.
            ValueError: If the file content is not valid YAML.
            yaml.YAMLError: If there is an error parsing the YAML data.

        Returns:
            Any: data loaded from the YAML file.
        """
        try:
            with open(filepath) as file:
                data = yaml.safe_load(file)
                self._load_yaml_data(data, vault_fetcher)
        except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
            raise type(e)(f"Error loading data from file: '{filepath}'") from e
        
        return self.data
        
    def _load_yaml_data(self, data: dict, parent_key: str = '', vault_fetcher: Any = None):
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
                        self._load_vault_secret(value, key, vault_fetcher)
                    elif key not in self.data:
                        self.data[key] = value
                else:
                    if key not in self.data:
                        self.data[key] = value
                        
    def _set_nested_dict(self, key: str, value: dict):
        keys = key.split('.')
        current_dict = self.data
        for k in keys[:-1]:
            current_dict = current_dict.setdefault(k, {})
        current_dict[keys[-1]] = value

    def _load_env_variable(self, yaml_value: str, yaml_key: str, loader: Any = EnvLoader()):
        env_key = yaml_value.strip("ENV.")
        value = loader.load(env_key)
        self.data[yaml_key] = value

    def _load_vault_secret(self, yaml_value: str, yaml_key: str, vault_fetcher: Any = None, loader: Any = VaultLoader()):
        vault_path, vault_key = yaml_value.strip("VAULT.").split(".")
        value = loader.load(vault_path, vault_key, vault_fetcher)
        self.data[yaml_key] = value
        