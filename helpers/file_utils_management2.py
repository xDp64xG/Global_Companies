import json
import os
from .loggers_utils import setup_logger
from datetime import datetime

# ---------------- CONFIGURE LOGGER ----------------
logger = setup_logger("FileUtils")

# ---------------- FILE OPERATIONS ----------------

DEFAULT_FILE_CONTENT = {
    "employee_data": {},
    "training_data": {"employees": []},
    "stock_data": {"records": []},
    "profit_data": {"logs": []},
    "applications_data": {"applications": []},
    "news_data": {"news": []}
}


class FileUtils:
    """
    A class for handling file operations.
        """
    def __init__(self):
        pass

    @staticmethod
    def ensure_file_exists(file_path, file_type):
        """
        Ensure the specified file exists with a default structure based on the file type.

        :param file_path: Path to the file.
        :param file_type: Type of data the file stores (e.g., 'employee_data', 'profit_data').
        """
        if not os.path.exists(file_path):
            default_content = DEFAULT_FILE_CONTENT.get(file_type, {})
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as file:
                    json.dump(default_content, file, indent=4)
                logger.info(f"Created missing file: {file_path}")
            except Exception as e:
                logger.error(f"Error creating file {file_path}: {e}")

    def load_json(file_path):
        """
        Load JSON data from a file.

        :param file_path: Path to the JSON file.
        :return: Parsed JSON object or empty dict if file doesn't exist or error occurs.
        """
        try:
            logger.debug(f"Loading JSON from {file_path}")
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return {}
            with open(file_path, "r") as file:
                data = json.load(file)
            logger.info(f"Successfully loaded JSON from {file_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {file_path}: {e}")
            return {}
        except Exception as e:
            logger.exception(f"Unexpected error loading JSON from {file_path}: {e}")
            return {}

    def save_json(file_path, data):
        """
        Save data to a JSON file.

        :param file_path: Path to the JSON file.
        :param data: Data to save.
        """
        try:
            logger.debug(f"Saving JSON to {file_path}")
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
            logger.info(f"Successfully saved JSON to {file_path}")
        except Exception as e:
            logger.exception(f"Error saving JSON to {file_path}: {e}")

    def append_json_entry(file_path, new_entry):
        """
        Append a new entry to a JSON file. If the file doesn't exist, create it.

        :param file_path: Path to the JSON file.
        :param new_entry: Dictionary entry to append.
        """
        logger.debug(f"Appending entry to {file_path}")
        data = FileUtils.load_json(file_path)
        if not isinstance(data, list):
            data = []
        data.append(new_entry)
        FileUtils.save_json(file_path, data)

    def update_json_key(file_path, key, value):
        """
        Update a specific key in a JSON file. Create the file if it doesn't exist.

        :param file_path: Path to the JSON file.
        :param key: Key to update.
        :param value: Value to set for the key.
        """
        logger.debug(f"Updating key '{key}' in {file_path}")
        data = FileUtils.load_json(file_path)
        data[key] = value
        FileUtils.save_json(file_path, data)

    def get_json_key(file_path, key, default=None):
        """
        Retrieve a specific key from a JSON file.

        :param file_path: Path to the JSON file.
        :param key: Key to retrieve.
        :param default: Default value if the key doesn't exist.
        :return: Value for the key, or the default value.
        """
        logger.debug(f"Retrieving key '{key}' from {file_path}")
        data = FileUtils.load_json(file_path)
        return data.get(key, default)
