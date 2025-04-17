import json
import os

# ---------------- FILE UTILITIES ----------------

def load_json(file_path):
    """
    Load data from a JSON file.
    :param file_path: Path to the JSON file.
    :return: Parsed JSON data as a Python dictionary or an empty dict on failure.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON from {file_path}: {e}")
    return {}

def save_json(data, file_path):
    """
    Save data to a JSON file.
    :param data: The data to save.
    :param file_path: Path to the JSON file.
    """
    if not isinstance(file_path, str):
        raise TypeError(f"[ERROR] Expected file_path to be a string, got {type(file_path).__name__}")

    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save JSON to {file_path}: {e}")

def initialize_file(file_path, default_data=None):
    """
    Initialize a file with default data if it does not exist.
    :param file_path: Path to the file.
    :param default_data: Default data to write if the file doesn't exist.
    """
    if not os.path.exists(file_path):
        save_json(default_data or {}, file_path)

# Example usage:
# data = load_json("config.json")
# save_json(data, "config.json")
