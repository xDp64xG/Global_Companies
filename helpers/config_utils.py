import json
import os
from .loggers_utils import setup_logger
#from tasks.utils import load_json
logger = setup_logger("ConfigUtils")

# Initialize ConfigUtils with the base directory pointing to the data folder
#config_utils = ConfigUtils(base_directory="./data")
#from file_utils_management import FileUtils

_JSON_CACHE = {}
# ---------------- CONFIG UTILITIES ----------------

class ConfigUtils:
    
    """
    Utility class to manage configuration files and JSON operations.
    """

    def __init__(self, base_directory="./data/config"):
        """
        Initialize ConfigUtils with a base directory for all JSON files.

        :param base_directory: Base path for all JSON files.
        """
        self.base_directory = base_directory
        self.config_path = os.path.join(self.base_directory, "config", "config.json")
        self._JSON_CACHE = {}

    def _get_file_path(self, filename):
        """
        Construct the full path for a JSON file.

        :param filename: Name of the file (e.g., "config.json").
        :return: Full file path.
        """
        return os.path.join(self.base_directory, filename)

    def get_api_key_by_discord_id(self, discord_id):
        """
        Retrieve the API key associated with a given Discord ID.
        """
        config_data = self.load_json("config.json")
        api_keys = config_data.get("api_keys", {})

        user_data = api_keys.get(str(discord_id))  # Ensure discord_id is a string
        if user_data and "api_key" in user_data:
            return user_data["api_key"]

        logger.error(f"API key not found for Discord ID {discord_id}.")
        return None
        """data = self.load_json("config.json")
        api_key = data.get("api_keys", {}).get(str(discord_id), {}).get("api_key")
        if not api_key:
            logger.error(f"No API key found for Discord ID {discord_id}.")
        return api_key"""

        #return api_key_entry.get("api_key")

    
    def load_json(file_path, force_reload=False):
        """
        Load data from a JSON file, using cache to prevent unnecessary reloading.
        :param file_path: Path to the JSON file.
        :param force_reload: If True, forces reloading from disk.
        :return: Parsed JSON data as a Python dictionary or an empty dict on failure.
        """
        global _JSON_CACHE
        #_JSON_CACHE = self._JSON_CACHE

        # Return from cache if already loaded and reload is not forced
        if file_path in _JSON_CACHE and not force_reload:
            return _JSON_CACHE[file_path]

        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            _JSON_CACHE[file_path] = {}
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    print(f"[WARNING] {file_path} is empty. Returning an empty dictionary.")
                    _JSON_CACHE[file_path] = {}
                    return {}

                data = json.loads(content)
                if not isinstance(data, dict):
                    print(f"[ERROR] Expected dictionary but got {type(data).__name__}. Resetting file.")
                    _JSON_CACHE[file_path] = {}
                    return {}

                # Store in cache and return
                _JSON_CACHE[file_path] = data
                return data

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON from {file_path}: {e}")
            _JSON_CACHE[file_path] = {}
            return {}  # Ensure a dictionary is always returned

    def load_json2(self, filename):
        """
        Load JSON data from a file.

        :param filename: Name of the JSON file.
        :return: Dictionary with the loaded data, or an empty dict if an error occurs.
        """
        filepath = self._get_file_path(filename=filename)
        print(f"[DEBUG] Loading JSON from {filename} at {filepath}")
        try:
            if not os.path.exists(filepath):
                logger.warning(f"File does not exist: {filename}. Returning empty data.")
                return {}
            with open(filepath, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {filename}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading {filename}: {e}")
            return {}

    def save_json(self, filename, data):
        """
        Save data to a JSON file.

        :param filename: Name of the JSON file.
        :param data: Dictionary to save.
        """
        filepath = self._get_file_path(filename)
        try:
            with open(filepath, "w") as file:
                json.dump(data, file, indent=4)
            logger.info(f"Successfully saved data to {filename}.")
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}")

    def validate_config(self, filename, required_keys, auto_fill_defaults=None):
        """
        Validate a JSON configuration file against required keys and optionally add missing keys.

        :param filename: Name of the JSON file.
        :param required_keys: List of keys that must exist in the file.
        :param auto_fill_defaults: Dictionary of default values for missing keys (optional).
        :return: Tuple (bool, list of missing keys).
        """
        config_data = ConfigUtils.load_json(filename)
        missing_keys = [key for key in required_keys if key not in config_data]

        if missing_keys:
            if auto_fill_defaults:
                for key in missing_keys:
                    if key in auto_fill_defaults:
                        config_data[key] = auto_fill_defaults[key]
                self.save_json(filename, config_data)
                logger.info(f"Added missing keys with defaults to {filename}: {missing_keys}")
            else:
                logger.warning(f"Validation failed for {filename}. Missing keys: {missing_keys}")
                return False, missing_keys

        logger.info(f"Validation passed for {filename}.")
        return True, []

    def update_json_key(self, filename, key, value, nested_keys=None):
        """
        Update a specific key or nested keys in a JSON file.

        :param filename: Name of the JSON file.
        :param key: Top-level key to update.
        :param value: New value for the key.
        :param nested_keys: List of nested keys for updating deeply nested values (optional).
        """
        data = ConfigUtils.load_json(filename)
        if nested_keys:
            d = data.get(key, {})
            temp = d
            for nk in nested_keys[:-1]:
                temp = temp.setdefault(nk, {})
            temp[nested_keys[-1]] = value
            data[key] = d
        else:
            data[key] = value
        self.save_json(filename, data)

    def get_json_key(self, filename, key, default=None):
        """
        Retrieve a specific key or nested key from a JSON file.
        :param filename: Name of the JSON file.
        :param key: Key to retrieve. Use dot notation (e.g., "key.subkey") for nested keys.
        :param default: Default value if the key does not exist.
        :return: Value for the key, or the default value.
        """
        data = ConfigUtils.load_json(filename)
        logger.debug(f"Loaded data from {filename}: {data}")

        if "." in key:
            keys = key.split(".")
            current_value = data
            for k in keys:
                if isinstance(current_value, dict) and k in current_value:
                    current_value = current_value[k]
                else:
                    logger.warning(f"Key '{key}' not found in {filename}. Returning default value.")
                    return default
            return current_value
        else:
            return data.get(key, default)


        
