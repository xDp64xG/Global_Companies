import json
import os
import requests
import discord
#from datetime import datetime
import time
from helpers.loggers_utils import setup_logger
import aiofiles
import threading
#from helpers.config_utils import ConfigUtils
logger = setup_logger("ConfigUtils")

CONFIG_FILE = "./data/config/config.json"

DEFAULT_FILE_CONTENT = {
    "employee_data": {},
    "training_data": {"employees": []},
    "stock_data": {"records": []},
    "profit_data": {"logs": []},
    "applications_data": {"applications": []},
    "news_data": {"news": []}
}
#config_utils = ConfigUtils()
# Generalized function to load JSON data from a file
import json
import os

# Cache to store already loaded JSON files
_JSON_CACHE = {}


import aiofiles
import asyncio
import json



async def load_json_async(file_path):
    async_file_lock = asyncio.Lock()
    async with async_file_lock:
        if os.path.exists(file_path):
            try:
                async with aiofiles.open(file_path, mode="r") as f:
                    contents = await f.read()
                    return json.loads(contents)
            except (json.JSONDecodeError, OSError) as e:
                print(f"[ERROR] Reading {file_path}: {e}")
                return {}
        return {}

async def save_json_async(data, file_path):
    async_file_lock = asyncio.Lock()
    async with async_file_lock:
        try:
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(data, indent=4))
        except OSError as e:
            print(f"[ERROR] Writing {file_path}: {e}")


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

# Generalized function to save JSON data to a file


# Function to fetch data from a URL
"""def fetch_data(url):
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        print(f"[ERROR] Invalid URL provided to fetch_data: {url}")
        return {}
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] Error fetching data: {e}")
        return {}"""

def fetch_data(url, max_retries=3, delay=1):
        try:
            max_retries = int(max_retries)  # Ensure max_retries is an integer
        except ValueError:
            raise ValueError(f"Expected 'max_retries' to be an integer, got {type(max_retries).__name__}")

        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to fetch data from {url}. HTTP {response.status_code}")
            except requests.RequestException as e:
                logger.error(f"Request error: {e}")
            
            retries += 1
            time.sleep(delay)

        raise RuntimeError(f"Failed to fetch data after {max_retries} attempts.")

def generate_api_urls(api_key):
        comment = "Project_Glo_Co_Bot"
        #self.base_url = f"https://api.torn.com/company/?key={api_key}&comment=Project_Glo_Co_Bot"
        return {
            "profile": f"https://api.torn.com/company/?key={api_key}&comment={comment}&selections=profile",
            "stock": f"https://api.torn.com/company/?key={api_key}&comment={comment}&selections=stock",
            "employees": f"https://api.torn.com/company/?key={api_key}&comment={comment}&selections=employees",
            "detailed": f"https://api.torn.com/company/?key={api_key}&comment={comment}&selections=detailed",
            "applications": f"https://api.torn.com/company/?key={api_key}&comment={comment}&selections=applications",
            "news": f"https://api.torn.com/company/?key={api_key}&comment={comment}&selections=news",
        }

# Function to resolve a target (channel or DM) in Discord
async def resolve_target(bot, target_id):
    try:
        target = bot.get_channel(target_id)
        if target:
            return target
        user = await bot.fetch_user(target_id)
        if user:
            return await user.create_dm()
    except discord.Forbidden:
        print(f"[ERROR] Permission denied to access target ID: {target_id}.")
    except discord.HTTPException as e:
        print(f"[ERROR] HTTP error resolving target ID {target_id}: {e}")
    return None

# UPDATED send_or_edit_message FUNCTION
async def send_or_edit_message(bot, api_key, section, target_id, embeds):
    target = await resolve_target(bot, target_id)
    if not target:
        print(f"[ERROR] Cannot resolve target for section '{section}', target ID: {target_id}.")
        return

    try:
        config = await load_json_async(CONFIG_FILE)
        message_ids = config["api_keys"].get(api_key, {}).get(section, {}).get("message_ids", [])

        embed_chunks = [embeds[i:i + 10] for i in range(0, len(embeds), 10)]
        new_message_ids = []

        for i, chunk in enumerate(embed_chunks):
            if i < len(message_ids):
                try:
                    msg = await target.fetch_message(message_ids[i])
                    await msg.edit(embeds=chunk)
                    new_message_ids.append(msg.id)
                except discord.NotFound:
                    print(f"[WARNING] Message ID {message_ids[i]} not found. Creating new message.")
                    msg = await target.send(embeds=chunk)
                    new_message_ids.append(msg.id)
            else:
                msg = await target.send(embeds=chunk)
                new_message_ids.append(msg.id)

        set_json_key(CONFIG_FILE, f"api_keys.{api_key}.{section}.message_ids", new_message_ids)

    except Exception as e:
        print(f"[ERROR] Failed to send message for section '{section}': {e}")

import json
import os

def set_json_key(file_path, key, value):
    """
    Update a nested JSON key with a new value and save it back to the file.
    Ensures that lists are appended correctly instead of being overwritten.
    
    :param file_path: Path to the JSON file.
    :param key: Key in dot notation (e.g., "api_keys.api_key.section.message_ids").
    :param value: Value to be set or appended.
    """
    # Load existing JSON data
    if not os.path.exists(file_path):
        data = {}
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):  # Ensure JSON is a dictionary
                    data = {}
        except json.JSONDecodeError:
                print(f"[ERROR] Corrupted JSON: {file_path}. Resetting...")
                data = {}

    # Navigate through nested keys
    keys = key.split(".")
    temp = data
    for k in keys[:-1]:  # Traverse to the second-last key
        temp = temp.setdefault(k, {})

    # Handle appending to lists correctly
    last_key = keys[-1]
    if isinstance(temp.get(last_key), list) and isinstance(value, list):
        temp[last_key].extend(value)  # Append to existing list
    else:
        temp[last_key] = value  # Overwrite if not a list

    # Save updated JSON data
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"[INFO] Updated JSON key: {key} in {file_path}")

async def get_json_key_async(file_path, key, default=None):
    data = await load_json_async(file_path)
    keys = key.split(".")
    for k in keys[:-1]:
        if not isinstance(data, dict):
            return default
        data = data.get(k, {})
    return data.get(keys[-1], default)



def validate_json_structure(data, expected_structure):
    """Ensure JSON data matches expected dictionary structure."""
    if not isinstance(data, dict):
        print("[ERROR] Invalid JSON format. Expected dictionary but got:", type(data).__name__)
        return False
    for key in expected_structure:
        if key not in data:
            print(f"[WARNING] Missing expected key: {key}")
    return True
