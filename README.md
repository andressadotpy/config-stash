# Configuration Stash

Configuration Stash is a Storage Configuration Manager designed to manage configuration data efficiently.

The `Config` class is a custom configuration class in Python that extends the built-in `dict` class.
It provides convenient methods to load configuration data from environment variables, YAML files and Vault secrets.

# Example Usage

```python
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
vault_fetcher = VaultFetcher()  # Assuming VaultFetcher is a class with a get_value_from_vault method
config.load_from_vault("secret/path", "secret_key")

# Accessing configuration values
value1 = config.get("ENV_KEY1")
value2 = config.get("ENV_KEY2")
value3 = config.get("ENV_KEY3")
nested_value = config.get("nested.key")

# Setting a new key-value pair
config["new_key"] = "new_value"
```

# Config.load_many_keys_from_env(keys: List[str], loader: Any = MultipleEnvLoader())

Load multiple keys from environment variables and store them in the `Config` object.

- **Args**:
  - `keys (list)`: A list of environment variable keys to load.
  - `loader (Any, optional)`: Loader object to load environment variables. Defaults to `MultipleEnvLoader()`.
- **Raises**:
  - `KeyError`: If any of the specified environment variables are not set.

# Config.load_from_env(key: str, custom_key_name: str = None, loader: Any = EnvLoader())

Load a key from an environment variable and store it in the `Config` object.

- **Args**:
  - `key (str)`: The environment variable key to load.
  - `custom_key_name (str, optional)`: The custom key name to use in the Config object. If not provided, the environment variable key is used as the key name.
  - `loader (Any, optional)`: Loader object to load the environment variable. Defaults to `EnvLoader()`.
- **Raises**:
  - `KeyError`: If the specified environment variable is not set.

# Config.load_prefixed_env_vars(allowed_prefixes: List[str], loader: Any = PrefixedEnvLoader())

Load environment variables with specified prefixes and store them in the `Config` object.

- **Args**:
  - `allowed_prefixes (list)`: A list of allowed prefixes for environment variables.
  - `loader (Any, optional)`: Loader object to load environment variables. Defaults to `PrefixedEnvLoader()`.
- **Raises**:
  - `TypeError`: If allowed_prefixes is not provided.

# Config.load_from_yaml_file(filepath: str, loader: Any = YamlLoader())

Load configuration data from a YAML file and store it in the `Config` object.
The YAML can have values prefixed with `VAULT.` and `ENV.`.

```yaml
url: "stage"
database: "db_address"
db_pass: "VAULT.vault_secret_path.vault_secret_key"
username: "ENV.USER"

cloudaccessdb:
  prefix_name: "cloud_db"
  user: "cloud_access_user"
  host: "example.com"

cloud_access_db:
  port: 1111
  dbName: "cloud_access"
```

- **Args**:
  - `filepath (str)`: The path to the YAML file containing the configuration data.
  - `loader (Any, optional)`: Loader object to load YAML data. Defaults to `YamlLoader()`.
- **Raises**:
  - `FileNotFoundError`: If the specified file is not found.
  - `ValueError`: If the file content is not valid YAML.
  - `yaml.YAMLError`: If there is an error parsing the YAML data.

## How to use the VAULT prefix within YAML

The value prefixed with `VAULT` must be dot separated and followed respectively by Vault's path and Vault's secret key.
The key saved in the `Config` object is the one pointed out as key in the YAML file. In the YAML example above it's `db_pass`.

To use this method, `Config` object must be initialized with a `VaultFetcher` object that satisfies the Interface example:

```python
from abc import ABC, abstractmethod

class VaultFetcherInterface(ABC):
    @abstractmethod
    def get_value_from_vault(self, path: str, key: str) -> str:
        """
        Abstract method to fetch a secret value from Vault.

        Args:
            path (str): The path to the secret in Vault.
            key (str): The key of the secret within the specified path.

        Returns:
            str: The secret value fetched from Vault.
        """
        pass
```

## How to use the ENV prefix within YAML

The value prefixed with `ENV` must be dot separated and followed by the environment variable key that should be loaded.

# Config.load_from_vault(vault_secret_path: str, vault_secret_key: str, fetcher: Any, custom_key_name: str = None, loader: Any = VaultLoader())

Load a secret value from Vault and store it in the `Config` object.

To use this method, `Config` object must also be initialized with a `VaultFetcher` (see example above).

- **Args**:
  - `vault_secret_path (str)`: The path to the secret in Vault.
  - `vault_secret_key (str)`: The key of the secret within the specified path.
  - `custom_key_name (str, optional)`: The custom key name to use in the Config object. If not provided, the vault_secret_key is used as the key name.
  - `loader (Any, optional)`: Loader object to load the Vault secret. Defaults to `VaultLoader()`.
- **Raises**:
  - `KeyError`: If the specified Vault secret path or key is not found.

# Config.\_\_setitem\_\_(key: str, value: str)

Override the \_\_setitem\_\_() method to update both the `Config` object and the corresponding environment variable.

- **Args**:
  - `key (str)`: The key to set.
  - `value (str)`: The value to associate with the key.
