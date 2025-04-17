import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
import requests
import re
from bs4 import BeautifulSoup
import asyncio
import matplotlib.pyplot as plt
import numpy as np

# --------- SETTINGS ---------
TOKEN = "MTMxNTcwNzMzNzQwMjYxNzkzNg.GrG3kG.-khSgsHco7MQFPPy-s5XTGxL6MoabPfrQgmJH0"  # Replace with your bot token
PREFIX = "="
CONFIG_FILE = "config.json"
API_KEYS_FILE = "api_keys.json"
APPROVED_KEYS_FILE = "approved_keys.json"
LAST_COUNTED_DATE = "last_counted_date.json"
PROFIT_LOG_FILE = "profit_log.json"
LOYALTY_TRACKING_FILE = "loyalty_tracking.json"
REGISTERED_USERS_FILE = "registered_users.json"  # File to store registered users
PROFIT_TRACKING_FILE = "profit_tracking.json"
LAST_ACTION_FILE = "last_actions.json"
Company_Positions_File = "company_data.json"
TRAINING_TRACKING_FILE = "training_tracking.json"  # File to store training progress

DATA_FILES = {
    "news_log": "news_log.json",
    "profit_tracking": "profit_tracking.json",
    "loyalty_tracking": "loyalty_tracking.json",
    "training_counts": "training_counts.json",
    "training_tracking": "training_tracking.json",
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --------- HELPER FUNCTIONS ---------

async def handle_rate_limits(response):
    if response.status_code == 429:
        retry_after = response.json().get("retry_after", 1)
        print(f"[WARNING] Rate limit hit. Retrying after {retry_after} seconds.")
        await asyncio.sleep(retry_after)

def get_all_stock_data(api_key):
    """
    Retrieve all logged stock data for an API key.
    :param api_key: The API key for the company.
    :return: A dictionary with dates as keys and stock data as values.
    """
    stock_log = get_company_data(api_key, STOCK_LOG_FILE)
    data_by_date = {}
    for entry in stock_log.get("entries", []):
        date = entry.get("date")
        stock_data = entry.get("stock_data", {})
        if date and stock_data:
            data_by_date[date] = stock_data
    return data_by_date

def prepare_graph_data(api_key):
    """
    Prepare data for graphing from the stock log.
    :param api_key: The API key for the company.
    :return: Dictionary organized for plotting.
    """
    data_by_date = get_all_stock_data(api_key)
    organized_data = {}

    for date, stock_data in data_by_date.items():
        for item, details in stock_data.items():
            if item not in organized_data:
                organized_data[item] = {"dates": [], "sold_amount": [], "sold_worth": [], "in_stock": []}

            organized_data[item]["dates"].append(date)
            organized_data[item]["sold_amount"].append(details.get("sold_amount", 0))
            organized_data[item]["sold_worth"].append(details.get("sold_worth", 0))
            organized_data[item]["in_stock"].append(details.get("in_stock", 0))

    return organized_data


"""def get_api_data(api_key, category):

    if category == "config":
        config = load_json(CONFIG_FILE).get("api_keys", {})
        return config.get(api_key, {})  # Return configuration for the API key

    if category not in DATA_FILES:
        raise ValueError(f"Invalid category: {category}")

    data = load_json(DATA_FILES[category])
    return data.get(api_key, {})"""



"""def save_api_data(api_key, category, new_data):

    if category not in DATA_FILES:
        raise ValueError(f"Invalid category: {category}")

    data = load_json(DATA_FILES[category])
    data[api_key] = new_data
    save_json(data, DATA_FILES[category])"""



"""def update_api_data(api_key, category, key, value):
    
    data = get_api_data(api_key, category)
    data[key] = value
    save_api_data(api_key, category, data)"""

"""def append_api_data(api_key, category, key, value):
    
    data = get_api_data(api_key, category)
    data.setdefault(key, []).append(value)
    save_api_data(api_key, category, data)"""


def validate_config(config, required_sections):
    """Ensure the configuration has all required sections."""
    for section in required_sections:
        if section not in config or not isinstance(config[section], dict):
            return False, f"Missing or invalid section: {section}"
    return True, None

def get_company_data(api_key, file):
    data = load_json(file)
    if isinstance(api_key, dict):
        print(f"[ERROR] Invalid API key type: {type(api_key)} - {api_key}")
        return {}
    return data.get(api_key, {})


def save_company_data(api_key, file, new_data):
    """Save data for a specific API key."""
    data = load_json(file)
    data[api_key] = new_data
    save_json(data, file)

def extract_stock_data(stock_data, key):
    """
    Extract stock data for sold_amount or sold_worth, along with in_stock as a baseline.
    Only retrieves the last 2 values for comparison.
    
    :param stock_data: Dictionary of stock data from `company_stocks`.
    :param key: Key to extract (`sold_amount` or `sold_worth`).
    :return: Dictionary with stock names as keys and dictionaries containing the last 2 values and in_stock.
    """
    stock_points = {}
    
    for stock_name, details in stock_data.items():
        # Retrieve key-specific values
        value = details.get(key, None)
        in_stock = details.get("in_stock", 0)  # Fallback to 0 if missing
        
        # Handle data extraction
        if value is not None:
            last_values = [value] if isinstance(value, (int, float)) else value[-2:]  # Last 2 values
            stock_points[stock_name] = {
                "last_values": last_values,  # The last 2 values for the given key
                "baseline": in_stock        # Use in_stock as the baseline
            }
    
    return stock_points

import matplotlib.pyplot as plt

import matplotlib.pyplot as plt

import matplotlib.dates as mdates
from datetime import datetime

def plot_stock_data(api_key):
    """
    Generate a graph of stock data over time.
    :param api_key: The API key for the company.
    """
    organized_data = prepare_graph_data(api_key)
    plt.figure(figsize=(14, 8))

    for item, data in organized_data.items():
        print(f"Data: {data}")
        dates = [datetime.strptime(date, "%Y-%m-%d") for date in data["dates"]]  # Convert dates to datetime objects
        sold_amount = data["sold_amount"]
        sold_worth = data["sold_worth"]
        in_stock = data["in_stock"]

        print(f"Dates: {dates}")
        print(f"Sold Amount: {sold_amount}")
        print(f"Sold Worth: {sold_worth}")
        print(f"In Stock: {in_stock}")

        # Plot sold_amount
        plt.plot(dates, sold_amount, label=f"{item} - Sold Amount", linestyle="-", marker="o", color="blue")

        # Plot sold_worth
        plt.plot(dates, sold_worth, label=f"{item} - Sold Worth", linestyle="--", marker="x", color="orange")

        # Plot in_stock as a baseline
        plt.plot(dates, in_stock, label=f"{item} - Baseline", linestyle=":", marker="s", color="green")

    # Format x-axis with date labels
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gcf().autofmt_xdate()  # Automatically rotate date labels

    plt.title("Sold Amount and Worth Over Time")
    plt.xlabel("Date")
    plt.ylabel("Values")
    plt.legend()
    plt.tight_layout()

    # Save the graph to a file
    filename = f"stock_graph_{api_key}.png"
    plt.savefig(filename)
    plt.close()

    print(f"[INFO] Stock graph saved as {filename}")
    return filename

async def send_stock_graph(api_key, info):
    """
    Generate and send a stock graph embed to a Discord channel.
    :param api_key: The API key for the company.
    :param channel_id: The Discord channel ID.
    """
    channel_id = info.get("channel_id")
    print(f"[Debug] Generating stock graph for API key: {api_key}\nChannel ID: {channel_id}")
    graph_filename = plot_stock_data(api_key)
    embed = discord.Embed(
        title="Stock Metrics Over Time",
        description="This graph tracks sold amount, sold worth, and in-stock quantities over time for each item.",
        color=discord.Color.blue(),
    )
    embed.set_image(url=f"attachment://{graph_filename}")
    embed.set_footer(text=f"Generated for API key: {api_key}")

    # Attach the file and send
    target = await resolve_target(channel_id)
    if target:
        with open(graph_filename, "rb") as file:
            discord_file = discord.File(file, filename=graph_filename)
            await target.send(embed=embed, file=discord_file)


STOCK_LOG_FILE = "daily_stock_log.json"

def initialize_stock_log(api_key):
    """
    Initialize the stock log for a specific API key if it does not exist.
    """
    stock_log = get_company_data(api_key, STOCK_LOG_FILE)
    if not stock_log:
        print(f"[DEBUG] Initializing stock log for API key: {api_key}")
        save_company_data(api_key, STOCK_LOG_FILE, {"entries": []})

def log_daily_stock(api_key, stock_data):
    """
    Log daily stock data for a specific API key.
    """
    initialize_stock_log(api_key)
    stock_log = get_company_data(api_key, STOCK_LOG_FILE)
    stock_log.setdefault("entries", [])

    today_date = datetime.now().strftime("%Y-%m-%d")

    # Check if today's entry exists
    if any(entry.get("date") == today_date for entry in stock_log["entries"]):
        print(f"[INFO] Stock data already logged for today ({today_date}).")
        return

    # Log today's stock data
    stock_log["entries"].append({
        "date": today_date,
        "stock_data": stock_data,
    })
    save_company_data(api_key, STOCK_LOG_FILE, stock_log)
    print(f"[INFO] Logged today's stock data for API key: {api_key}")

def get_stock_data_for_date(api_key, date):
    """
    Retrieve stock data for a specific date from the stock log.
    """
    stock_log = get_company_data(api_key, STOCK_LOG_FILE)
    for entry in stock_log.get("entries", []):
        if entry.get("date") == date:
            return entry.get("stock_data", {})
    return {}

@tasks.loop(hours=24)
async def log_daily_stock_task(api_key, stock_url):
    """
    Periodically log daily stock data.
    """
    try:
        stock_data = fetch_data(stock_url).get("company_stock", {})
        if not stock_data:
            print(f"[ERROR] No stock data found for API key: {api_key}")
            return

        log_daily_stock(api_key, stock_data)
    except Exception as e:
        print(f"[ERROR] Exception in log_daily_stock_task for API key '{api_key}': {e}")


def clean_html(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text().strip().lower()

def extract_employee_name(raw_html):
    """Extract employee name from the raw HTML string."""
    soup = BeautifulSoup(raw_html, 'html.parser')
    link = soup.find('a')  # Finds the first <a> tag
    return link.text.strip() if link else None  # Returns the text inside <a>, if it exists

# Generalized function to load JSON data from a file
def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON from {file_path}: {e}")
    return {}

# Generalized function to save JSON data to a file
def save_json(data, file_path):
    """
    Save data to a JSON file.
    :param data: The data to save.
    :param file_path: Path to the JSON file.
    """
    if not isinstance(file_path, str):
        raise TypeError(f"[ERROR] Expected file_path to be a string, got {type(file_path).__name__}")

    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save JSON to {file_path}: {e}")

def load_config():
    return load_json(CONFIG_FILE)

def save_config(config):
    save_json(config, CONFIG_FILE)

def load_api_keys():
    config = load_json(CONFIG_FILE).get("api_keys", {})
    valid_keys = {}
    for user_id, user_data in config.items():
        if isinstance(user_data, dict) and "api_key" in user_data:
            valid_keys[user_id] = user_data
        else:
            print(f"[ERROR] Invalid data for user ID {user_id}: {user_data}")
    return valid_keys

"""def get_api_config(api_key):
    config = load_json(CONFIG_FILE).get("api_keys", {})
    return config.get(api_key, {})"""

"""def save_api_keys(api_keys):
    save_json(api_keys, API_KEYS_FILE)"""

def load_approved_keys():
    return load_json(APPROVED_KEYS_FILE)

def save_approved_keys(approved_keys):
    save_json(approved_keys, APPROVED_KEYS_FILE)

def update_config(api_key, section, target_id):
    """
    Update the configuration for a specific API key.
    """
    if not isinstance(api_key, str):
        raise TypeError(f"[ERROR] Expected api_key to be a string, got {type(api_key).__name__}")

    config_data = load_json(CONFIG_FILE)
    api_keys = config_data.get("api_keys", {})

    if api_key not in api_keys:
        raise ValueError(f"[ERROR] API key {api_key} not found in config.")

    # Ensure section is a dictionary
    if section not in api_keys[api_key] or not isinstance(api_keys[api_key][section], dict):
        api_keys[api_key][section] = {}

    # Update the section data
    api_keys[api_key][section]["channel_id"] = target_id
    config_data["api_keys"] = api_keys
    save_json(config_data, CONFIG_FILE)

def get_channel_id(api_key, section):
    config = load_json(CONFIG_FILE)
    return config.get("api_keys", {}).get(api_key, {}).get(section, {}).get("channel_id")

def get_message_ids(api_key, section):
    config = load_json(CONFIG_FILE)
    api_keys = config.get("api_keys", {})
    #print(f"[DEBUG] Loaded API keys: {api_keys}")

    for user_id, user_data in api_keys.items():
        if user_data.get("api_key") == api_key:
            print(f"[DEBUG] Found user ID '{user_id}' for API key '{api_key}'")
            return user_data.get(section, {}).get("message_ids", [])
    
    print(f"[ERROR] API key '{api_key}' not found in config.")
    return []

def save_message_ids(api_key, section, message_ids):
    """
    Update and save message IDs for specific sections of a specific API key.
    Only updates `company`, `employees`, and `training` sections.
    """
    # Sections allowed for message ID updates
    allowed_sections = {"company", "employees", "training", "warnings_inactivity", "warnings_addiction", "applications"}
    if section not in allowed_sections:
        print(f"[DEBUG] Skipping message ID update for section '{section}' as it is not allowed.")
        return

    # Load configuration
    config = load_json(CONFIG_FILE)

    # Find the user ID associated with the API key
    for user_id, user_data in config.get("api_keys", {}).items():
        if user_data.get("api_key") == api_key:
            # Check and update the section if allowed
            if section in user_data:
                user_data[section]["message_ids"] = message_ids
                save_json(config, CONFIG_FILE)
                print(f"[SUCCESS] Updated message IDs for API key '{api_key}' section '{section}' to {message_ids}.")
                return
            else:
                print(f"[ERROR] Section '{section}' not found for API key '{api_key}'.")
                return

    print(f"[ERROR] API key '{api_key}' not found in config.")

def fetch_data(url):
    """
    Fetch data from a given URL.
    Validate that the input is a URL to avoid errors with dictionaries.
    """
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        print(f"[ERROR] Invalid URL provided to fetch_data: {url}")
        return {}

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] Error fetching data: {e}")
        return {}


def initialize_loyalty_tracking():
    if not os.path.exists(LOYALTY_TRACKING_FILE):
        save_json({}, LOYALTY_TRACKING_FILE)

# Load JSON data from the file
def load_business_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Get specific business type and position
def get_business_position(json_data, business_index, position_name):
    # Calculate the actual key (x-1 since index starts at 0)
    business_key = str(business_index)
    
    # Retrieve the business data
    business_data = json_data.get(business_key, {})
    if not business_data:
        return f"❌ Business with index {business_index} not found."
    
    # Retrieve the position data
    positions = business_data.get("Positions", {})
    position_data = positions.get(position_name, {})
    if not position_data:
        return f"❌ Position '{position_name}' not found in business type '{business_data.get('Type', 'Unknown')}'."
    
    return {
        "Business Type": business_data.get("Type", "Unknown"),
        "Position": position_name,
        "Requirements": position_data
    }

def update_last_actions(api_key, last_action_data):
    last_actions = get_company_data(api_key, LAST_ACTION_FILE)
    last_actions["employees"] = last_actions.get("employees", {})
    last_actions = last_action_data
    #last_actions["employees"][employee_name] = last_action_data
    save_company_data(api_key, LAST_ACTION_FILE, last_actions)

def get_application_status_color(status):
    """Return a color for the embed based on application status."""
    status = status.lower()
    if status == "pending":
        return discord.Color.yellow()
    elif status == "approved":
        return discord.Color.green()
    elif status == "rejected":
        return discord.Color.red()
    else:
        return discord.Color.blue()

def is_relevant_news(news_text):
    """Check if the news is relevant for logging."""
    return (
        "has been trained by the director" in news_text or
        "has left the company" in news_text or
        "withdrawn from the company funds" in news_text
    )

def get_news_emoji(news_text):
    """Return appropriate emoji based on the news content."""
    if "has been trained by the director" in news_text:
        return "📘"
    if "has left the company" in news_text or "has been fired from the company" in news_text:
        return "🚪"
    if "withdrawn from the company funds" in news_text or "made a deposit" in news_text:
        return "💰"
    return "📰"  # Default emoji

import matplotlib.pyplot as plt
import numpy as np


# ----------- Generate Graph -----------
def generate_profit_graph(api_key):
    data = load_json(PROFIT_LOG_FILE)
    if api_key not in data:
        raise ValueError(f"No data found for API key: {api_key}")
    
    entries = data[api_key]["entries"]
    dates = [entry["date"] for entry in entries]
    profits = [entry["profit"] for entry in entries]
    customers = [entry["customers"] for entry in entries]

    if not profits or not customers:
        raise ValueError("Data for profits or customers is missing or invalid.")

    plt.figure(figsize=(12, 6))
    bar_width = 0.4
    x_indices = range(len(dates))

    # Plot profits on the primary Y-axis
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(x_indices, profits, width=bar_width, label="Profit", color="blue", alpha=0.7)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Profit ($)", color="blue")
    ax1.tick_params(axis='y', labelcolor="blue")

    # Add secondary Y-axis for customers
    ax2 = ax1.twinx()
    ax2.bar([x + bar_width for x in x_indices], customers, width=bar_width, label="Customers", color="orange", alpha=0.7)
    ax2.set_ylabel("Customers", color="orange")
    ax2.tick_params(axis='y', labelcolor="orange")

    # Add labels, title, and legend
    ax1.set_xticks([x + bar_width / 2 for x in x_indices])
    ax1.set_xticklabels(dates, rotation=45, ha="right")
    plt.title(f"Profit and Customers for API Key: {api_key}")

    # Combine legends from both axes
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9), bbox_transform=ax1.transAxes)

    # Debugging: Print data to confirm plotting values
    print(f"Dates: {dates}")
    print(f"Profits: {profits}")
    print(f"Customers: {customers}")

    # Save the chart as an image
    plt.tight_layout()
    plt.savefig(f"profit_graph{api_key}.png")
    plt.close()

def generate_profit_line_graph_with_secondary_axis(api_key):
    data = load_json(PROFIT_LOG_FILE)
    #data = load_json(PROFIT_LOG_FILE)
    if api_key not in data:
        raise ValueError(f"No data found for API key: {api_key}")
    
    entries = data[api_key]["entries"]
    dates = [entry["date"] for entry in entries]
    profits = [entry["profit"] for entry in entries]
    customers = [entry["customers"] for entry in entries]

    if not profits or not customers:
        raise ValueError("Data for profits or customers is missing or invalid.")

    plt.figure(figsize=(12, 6))

    # Create the first y-axis for profit
    fig, ax1 = plt.subplots()
    ax1.plot(dates, profits, label="Profit", color="blue", marker="o", linestyle="-", linewidth=2)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Profit", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.set_title(f"Profit and Customers for API Key: {api_key}")
    ax1.set_xticks(range(len(dates)))
    ax1.set_xticklabels(dates, rotation=45)

    # Add data points for profit
    for i, profit in enumerate(profits):
        ax1.annotate(f"{profit}", (i, profit), textcoords="offset points", xytext=(-5, 5), ha='center', color="blue")

    # Create the second y-axis for customers
    ax2 = ax1.twinx()
    ax2.plot(dates, customers, label="Customers", color="orange", marker="o", linestyle="--", linewidth=2)
    ax2.set_ylabel("Customers", color="orange")
    ax2.tick_params(axis="y", labelcolor="orange")

    # Add data points for customers
    for i, customer in enumerate(customers):
        ax2.annotate(f"{customer}", (i, customer), textcoords="offset points", xytext=(-5, 5), ha='center', color="orange")

    # Add a legend for clarity
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    # Save the chart as an image
    plt.tight_layout()
    plt.savefig(f"profit_line_graph_secondary_axis{api_key}.png")
    plt.close()


# ----------- Discord Command -----------

async def send_line_graph(api_key):
    try:
        generate_profit_line_graph_with_secondary_axis(api_key)  # Generate the line graph
        file_path = f"profit_line_graph_secondary_axis{api_key}.png"
        file = discord.File(file_path, filename=f"profit_line_graph_secondary_axis{api_key}.png")  # Prepare the file
        embed = discord.Embed(title="Profit and Customers Line Graph", description=f"Data for API Key: {api_key}", color=discord.Color.blue())
        embed.set_image(url=f"attachment://{file.filename}")
        return embed, file
    except ValueError as ve:
        print(f"[ERROR] ValueError in send_line_graph: {ve}")
        return None, None
    except Exception as e:
        print(f"[ERROR] Exception in send_line_graph: {e}")
        return None, None


def initialize_profit_log(api_key):
    """Initialize the profit log for a specific API key if it does not exist."""
    profit_log = get_company_data(api_key, PROFIT_LOG_FILE)
    if not profit_log:
        print(f"[DEBUG] Initializing profit log for API Key: {api_key}")
        save_company_data(api_key, PROFIT_LOG_FILE, {"entries": []})

def initialize_profit_tracking(api_key):
    """Initialize the profit tracking for a specific API key if it does not exist."""
    profit_tracking = get_company_data(api_key, PROFIT_TRACKING_FILE)
    if not profit_tracking:
        print(f"[DEBUG] Initializing profit tracking for API Key {api_key}.")
        save_company_data(api_key, PROFIT_TRACKING_FILE, {"entries": []})

def initialize_last_counted_date(api_key):
    """Initialize the last counted date for a specific API key."""
    last_counted_data = get_company_data(api_key, LAST_COUNTED_DATE)
    if not last_counted_data:
        save_company_data(api_key, LAST_COUNTED_DATE, {"last_counted": ""})

def update_last_counted_date(api_key):
    last_counted = get_company_data(api_key, LAST_COUNTED_DATE)
    today = datetime.now().strftime("%Y-%m-%d")
    last_counted["last_counted"] = today
    save_company_data(api_key, LAST_COUNTED_DATE, last_counted)

def should_count_day(api_key):
    last_counted = get_company_data(api_key, LAST_COUNTED_DATE).get("last_counted", "")
    today = datetime.now().strftime("%Y-%m-%d")
    return today != last_counted

def log_daily_metrics(api_key, current_profit, current_customers):
    """
    Log daily profits and customers for calculating averages, avoiding duplicate entries after 1:10 PM.
    """
    initialize_profit_log(api_key)
    logs = get_company_data(api_key, PROFIT_LOG_FILE)
    logs.setdefault("entries", [])

    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    current_time = now.time()

    cutoff_time = datetime.strptime("13:10", "%H:%M").time()

    # Check if today's entry already exists
    if any(entry.get("date") == today_date for entry in logs["entries"]):
        if current_time < cutoff_time:
            print(f"[INFO] Data already logged for today ({today_date}) before cutoff time. Skipping duplicate entry.")
            return False
        else:
            # Remove existing entry to replace with updated data
            logs["entries"] = [entry for entry in logs["entries"] if entry.get("date") != today_date]

    # Log data if past cutoff time
    if current_time >= cutoff_time:
        logs["entries"].append({
            "date": today_date,
            "time_logged": now.strftime("%H:%M:%S"),
            "profit": current_profit,
            "customers": current_customers,
        })
        save_company_data(api_key, PROFIT_LOG_FILE, logs)
        print(f"[INFO] Logged today's metrics: Date={today_date}, Profit=${current_profit}, Customers={current_customers}")
        return True

    print(f"[INFO] Current time ({now.strftime('%H:%M:%S')}) is before cutoff time (13:10). Skipping logging.")
    return False

def calculate_averages(api_key):
    """Calculate average profit and customers from the logs for a specific API key."""
    initialize_profit_log(api_key)
    logs = get_company_data(api_key, PROFIT_LOG_FILE).get("entries", [])
    if not logs:
        return {"average_profit": 0, "average_customers": 0}

    total_profit = sum(entry["profit"] for entry in logs)
    total_customers = sum(entry["customers"] for entry in logs)
    num_entries = len(logs)

    return {
        "average_profit": total_profit / num_entries if num_entries > 0 else 0,
        "average_customers": total_customers / num_entries if num_entries > 0 else 0,
    }

def update_profit_tracking(api_key, current_profit=None, current_customers=None, is_daily_update=False):
    """Update aggregated stats for profit tracking."""
    initialize_profit_tracking(api_key)
    logs = get_company_data(api_key, PROFIT_TRACKING_FILE)
    logs.setdefault("entries", [])

    # Add daily metrics if needed
    if is_daily_update and should_count_day(api_key):
        if current_profit is not None and current_customers is not None:
            logs["entries"].append({"profit": current_profit, "customers": current_customers})
            save_company_data(api_key, PROFIT_TRACKING_FILE, logs)
            print(f"[DEBUG] Appended profit tracking: Profit={current_profit}, Customers={current_customers}")
        update_last_counted_date(api_key)

    # Calculate aggregated stats
    total_profit = sum(entry["profit"] for entry in logs["entries"])
    total_customers = sum(entry["customers"] for entry in logs["entries"])
    num_entries = len(logs["entries"])

    return {
        "total_days": num_entries,
        "total_profit": total_profit,
        "average_profit": total_profit / num_entries if num_entries > 0 else 0,
        "average_customers": total_customers / num_entries if num_entries > 0 else 0,
        "highest_profit": max((entry["profit"] for entry in logs["entries"]), default=0),
        "lowest_profit": min((entry["profit"] for entry in logs["entries"]), default=0),
        "highest_customers": max((entry["customers"] for entry in logs["entries"]), default=0),
        "lowest_customers": min((entry["customers"] for entry in logs["entries"]), default=0),
    }


running_tasks_registry = {
    "post_company_update": {},
    "update_employee_stats": {},
    "check_applications": {},
    "post_training_regimen": {},
    "process_company_news": {},
    "post_warnings": {},
    "monitor_company_funds" :{},
    "stock_logger" : {},
    "stock_poster": {}
}

# Stop tasks for a specific API key
def stop_tasks_for_key(api_key):
    global running_tasks_registry
    for task_name, tasks in running_tasks_registry.items():
        task = tasks.pop(api_key, None)
        if task and not task.done():
            task.cancel()
            print(f"[INFO] Stopped {task_name} for API key: {api_key}")

@tasks.loop(hours=24)
async def generate_and_post_stock_graph(api_key, channel_id):
    """
    Generate and post the stock graph daily.
    """
    try:
        await send_stock_graph(api_key, channel_id)
    except Exception as e:
        print(f"[ERROR] Failed to generate or post stock graph for API key {api_key}: {e}")


def generate_api_urls(api_key):
    """Generate Torn API URLs for a specific API key."""
    base_url = f"https://api.torn.com/company/?key={api_key}&comment=Project_Glo_Co_Bot"
    return {
        "profile": f"{base_url}&selections=profile",
        "stock": f"{base_url}&selections=stock",
        "employees": f"{base_url}&selections=employees",
        "detailed": f"{base_url}&selections=detailed",
        "applications": f"{base_url}&selections=applications",
        "news": f"{base_url}&selections=news",
    }

REQUIRED_SECTIONS = ["company", "employees", "applications", "training", "news", "bonuses", "warnings_inactivity", "warnings_addiction"]
# Validate and fix configuration
def validate_and_fix_config():
    """
    Validate and fix the configuration file (config.json).
    Ensures that all required sections are present for every API key.
    """
    config = load_json(CONFIG_FILE)
    api_keys = config.setdefault("api_keys", {})

    for user_id, user_config in api_keys.items():
        if isinstance(user_config, str):  # Skip actual API keys stored as strings
            continue
        if isinstance(user_config, dict):
            for section in REQUIRED_SECTIONS:
                if section not in user_config or not isinstance(user_config[section], dict):
                    user_config[section] = {"channel_id": None, "message_ids": []}

    # Debug: Check the type of CONFIG_FILE before passing to save_json
    print(f"[DEBUG] CONFIG_FILE type: {type(CONFIG_FILE)}, value: {CONFIG_FILE}")

    # Save the validated and fixed configuration
    save_json(config, CONFIG_FILE)
    print("[INFO] Configuration validated and fixed.")

def get_company_vault_threshold(api_key):
    """
    Retrieve the company vault threshold for the given API key.
    """
    config = load_json(CONFIG_FILE)
    for user_id, user_data in config.get("api_keys", {}).items():
        if user_data.get("api_key") == api_key:
            return user_data.get("news", {}).get("company_vault", None)
    return None

def get_addiction_level(api_key):
    """
    Retrieve the addiction level for the given API key.
    """
    config = load_json(CONFIG_FILE)
    for user_id, user_data in config.get("api_keys", {}).items():
        if user_data.get("api_key") == api_key:
            return user_data.get("warnings_addiction", {}).get("addiction_level", None)
    return None

# --------- COMMANDS ---------

@bot.command(name="sendgraph")
async def send_graph(ctx, api_key: str):
    try:
        generate_profit_graph(api_key)  # Generate the graph for the provided API key
        file = discord.File(f"profit_graph{api_key}.png", filename=f"profit_graph{api_key}.png")  # Attach the image
        embed = discord.Embed(title="Profit and Customers Graph", description=f"Data for API Key: {api_key}", color=discord.Color.blue())
        embed.set_image(url=f"attachment://profit_graph{api_key}.png")
        await ctx.send(embed=embed, file=file)
    except ValueError as ve:
        await ctx.send(f"❌ {ve}")
    except Exception as e:
        await ctx.send(f"❌ Failed to generate graph: {e}")

@bot.command(name="update_config")
async def update_config_command(ctx, api_key: str = None, section: str = None, setting: str = None, value: str = None):
    """
    Update or add a configuration setting for a specific API key and section.
    If no arguments are passed, display a usage guide.
    """
    if not all([api_key, section, setting, value]):
        await ctx.send(
            "**Usage:**\n"
            "`=update_config <api_key> <section> <setting> <value>`\n\n"
            "**Examples:**\n"
            "`=update_config DLXPDjSEDqXCDBcG news company_vault $100,000`\n"
            "Updates the `company_vault` threshold in the `news` section for the specified API key."
        )
        return

    try:
        config = load_json(CONFIG_FILE)
        api_keys = config.get("api_keys", {})

        # Validate API key
        api_config = None
        for user_id, user_data in api_keys.items():
            if user_data.get("api_key") == api_key:
                api_config = user_data
                break
        if not api_config:
            await ctx.send(f"❌ API key '{api_key}' not found in the configuration.")
            return

        # Validate section
        if section not in api_config:
            await ctx.send(f"❌ Section '{section}' not found for the given API key.")
            return

        # Process value (remove $ and , if numeric)
        if setting == "company_vault":
            value = value.replace("$", "").replace(",", "")
            if not value.isdigit():
                await ctx.send(f"❌ Value for '{setting}' must be an integer.")
                return
            value = int(value)
        if setting == "addiction_level":
            if not value.isdigit():
                await ctx.send(f"❌ Value for '{setting}' must be an integer.")
                return
            value = int(value)

        # Update configuration
        api_config[section][setting] = value
        save_json(config, CONFIG_FILE)
        await ctx.send(f"✅ Successfully updated '{setting}' in section '{section}' for API key '{api_key}'.")
    except Exception as e:
        print(f"[ERROR] Failed to update configuration: {e}")
        await ctx.send(f"❌ Failed to update configuration: {e}")

@tasks.loop(hours=2)
async def monitor_company_funds(api_key, news_config, company_funds_url, employees_url):
    """
    Monitor company funds and post a warning if funds fall below the threshold.
    """
    try:
        print(f"[INFO] Monitoring Company Funds for {api_key}")
        company_funds_data = fetch_data(company_funds_url)
        company_funds = company_funds_data.get("company_detailed", {}).get("company_funds", 0)
        ad_budget = company_funds_data.get("company_detailed", {}).get("advertising_budget", 0)
        fund_threshold = get_company_vault_threshold(api_key)
        employees_data = fetch_data(employees_url)
        total_wage = 0

        for emp_id in employees_data.get("company_employees", {}):
            wage = employees_data.get("company_employees", {}).get(emp_id, {}).get("wage", 0)
            total_wage += wage
        print(f"Total wage: {total_wage}")
        total_deduction = total_wage + ad_budget
        after_deduction = company_funds - total_deduction
        print(f"After deduction: {after_deduction}")

        #if fund_threshold is not None and company_funds < fund_threshold:
        if fund_threshold is not None and after_deduction < fund_threshold:
            # Retrieve user ID for mention
            config = load_json(CONFIG_FILE)
            discord_id = None
            for user_id, user_data in config.get("api_keys", {}).items():
                if user_data.get("api_key") == api_key:
                    discord_id = user_id
                    break

            if not discord_id:
                print(f"[ERROR] No Discord ID found for API key: {api_key}")
                return

            news_channel_id = news_config.get("channel_id")
            if not isinstance(news_channel_id, int):
                print(f"[ERROR] Invalid news channel ID: {news_channel_id}")
                return

            target = await resolve_target(news_channel_id)
            if not target:
                print(f"[ERROR] Failed to resolve target for news channel.")
                return

            embed = discord.Embed(
                title="⚠️ Low Company Funds",
                description=(
                    f"🔴 The company funds have dropped below the threshold of **${fund_threshold:,}**.\n"
                    f"<@{discord_id}>, please take action!"
                ),
                color=discord.Color.red(),
            )
            embed.set_footer(text=f"Last checked: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            await target.send(embed=embed)
    except Exception as e:
        print(f"[ERROR] Exception in monitor_company_funds: {e}")

# Self-register command
@bot.command(name="selfregister")
async def self_register(ctx, torn_id: str):
    if not torn_id.isdigit():
        await ctx.send("❌ Torn ID must be numeric.")
        return

    registered_users = load_json(REGISTERED_USERS_FILE)
    registered_users[ctx.author.id] = {
        "discord_name": ctx.author.name,
        "discord_id" : ctx.author.id,
        "torn_id": torn_id
    }
    save_json(registered_users, REGISTERED_USERS_FILE)
    await ctx.send(f"✅ You have been registered with Torn ID {torn_id}.")

# Register users manually
@bot.command(name="register")
async def register_user(ctx, discord_user: discord.Member, torn_id: str):
    if not torn_id.isdigit():
        await ctx.send("❌ Torn ID must be numeric.")
        return

    registered_users = load_json(REGISTERED_USERS_FILE)
    registered_users[discord_user.id] = {
        "discord_name": discord_user.name,
        "discord_id" : discord_user.id,
        "torn_id": torn_id
    }
    save_json(registered_users, REGISTERED_USERS_FILE)
    await ctx.send(f"✅ User {discord_user.mention} registered with Torn ID {torn_id}.")

# List registered users
@bot.command(name="listregistered")
async def list_registered_users(ctx):
    registered_users = load_json(REGISTERED_USERS_FILE)
    if not registered_users:
        await ctx.send("No users are registered.")
        return

    message = "**Registered Users:**\n"
    for discord_id, info in registered_users.items():
        message += f"- <@{discord_id}> (Torn ID: {info['torn_id']})\n"

    await ctx.send(message)

def fix_json_config(file):
    with open(file, "r") as f:
        config = json.load(f)

    api_keys = config.get("api_keys", {})
    required_sections = ["company", "employees", "applications", "training", "news", "bonuses", "warnings_inactivity", "warnings_addiction"]

    for user_id, user_config in api_keys.items():
        if isinstance(user_config, str):  # Skip actual API keys stored as strings
            continue
        if isinstance(user_config, dict):
            for section in required_sections:
                if section not in user_config or not isinstance(user_config[section], dict):
                    user_config[section] = {"channel_id": None, "message_ids": []}

    config["api_keys"] = api_keys
    with open(file, "w") as f:
        json.dump(config, f, indent=4)
    print("[INFO] JSON config validated and fixed.")

@bot.command(name="fix_config")
async def fix_config(ctx):
    """
    Command to fix the JSON configuration file.
    """
    try:
        validate_and_fix_config()
        await ctx.send("✅ JSON config fixed and saved.")
    except Exception as e:
        print(f"[ERROR] Exception in fix_config: {e}")
        await ctx.send(f"❌ Failed to fix JSON config: {e}")

@bot.command(name="update")
async def update_api_keys(ctx):
    """
    Update the configuration with new API keys from config.json and initialize their tasks.
    """
    # Load existing configuration
    config_data = load_json(CONFIG_FILE)
    api_keys = config_data.setdefault("api_keys", {})

    # Check for missing API keys (new users added manually to config.json)
    updated = False

    for user_id, user_config in api_keys.items():
        if isinstance(user_config, dict) and "api_key" in user_config:
            api_key = user_config["api_key"]
            # Check if the API key is already in the running tasks
            if api_key not in running_tasks_registry["post_company_update"]:
                print(f"[INFO] Detected new API key: {api_key} for user {user_id}.")
                try:
                    # Validate configuration and initialize tasks
                    valid, error = validate_config(user_config, REQUIRED_SECTIONS)
                    if not valid:
                        print(f"[ERROR] Invalid configuration for API key {api_key}: {error}")
                        continue

                    # Start tasks for the API key
                    await start_tasks_for_key(api_key, user_config)
                    updated = True
                except Exception as e:
                    print(f"[ERROR] Failed to initialize tasks for API key {api_key}: {e}")
        else:
            print(f"[INFO] Skipping invalid or existing configuration for user {user_id}.")

    # Save updated configuration to ensure consistency
    save_json(config_data, CONFIG_FILE)

    # Notify the user
    if updated:
        await ctx.send("✅ New API keys detected and initialized.")
    else:
        await ctx.send("✅ No new API keys to update.")

@bot.command(name="check_tasks")
async def check_running_tasks(ctx):
    if not running_tasks:
        await ctx.send("No tasks are currently running.")
        return

    status_report = "\n".join(
        [f"API Key: {api_key} - {'Running' if state else 'Stopped'}"
         for api_key, state in running_tasks.items()]
    )
    await ctx.send(f"Task Status:\n{status_report}")

@bot.command(name="manage_tasks")
@commands.has_permissions(administrator=True)
async def manage_tasks(ctx):
    global running_tasks_registry

    # Load API keys and configurations
    api_keys = load_api_keys()
    if not api_keys:
        await ctx.send("❌ No valid API keys found.")
        return

    new_tasks_started = 0
    tasks_restarted = 0
    unchanged_tasks = 0

    for user_id, user_config in api_keys.items():
        api_key = user_config.get("api_key")
        if not api_key:
            print(f"[ERROR] API key missing for user ID: {user_id}")
            continue

        # Validate configuration
        valid, error = validate_config(user_config, ["news", "applications", "training", "employees", "company"])
        if not valid:
            print(f"[ERROR] Invalid configuration for API key {api_key}: {error}")
            continue

        # Check if tasks are already running
        if api_key in running_tasks_registry["post_company_update"]:
            print(f"Tasks already running for API key: {api_key}")
            unchanged_tasks += 1
        else:
            # Start tasks for the API key
            await start_tasks_for_key(api_key, user_config)
            new_tasks_started += 1

    await ctx.send(
        f"✅ Task Management Summary:\n"
        f"- New Tasks Started: {new_tasks_started}\n"
        f"- Tasks Restarted: {tasks_restarted}\n"
        f"- Unchanged Tasks: {unchanged_tasks}\n"
    )

@bot.command(name="addapikey")
async def add_api_key(ctx, api_key: str):
    config = load_json(CONFIG_FILE)
    api_keys = config.setdefault("api_keys", {})

    user_id = str(ctx.author.id)
    if user_id in api_keys:
        await ctx.send(f"❌ API key already registered for user {ctx.author.name}.")
        return

    # Initialize all sections
    api_keys[user_id] = {
        "api_key": api_key,
        **{section: {"channel_id": None, "message_ids": []} for section in REQUIRED_SECTIONS}
    }
    save_json(config, CONFIG_FILE)
    await ctx.send(f"✅ API key registered for {ctx.author.name}.")

@bot.command(name="setdms")
async def set_all_channels_as_dms(ctx):
    """
    Set all sections to use direct messages for updates.
    """
    valid_sections = ["news", "applications", "training", "employees", "company", "bonuses", "warnings"]

    api_keys = load_api_keys()
    user_id = str(ctx.author.id)
    user_config = api_keys.get(user_id)

    if not user_config:
        await ctx.send("❌ You have not registered an API key. Use `addapikey` to register one.")
        return

    try:
        for section in valid_sections:
            update_config(user_id, section, ctx.author.id)
        await ctx.send("✅ All sections set to send updates via DM.")
    except Exception as e:
        print(f"[ERROR] Failed to set all sections to DM: {e}")
        await ctx.send(f"❌ Failed to set all sections to DM: {e}")

@bot.command(name="setchannel")
async def set_channel(ctx, section: str, channel: discord.TextChannel):
    """
    Set a channel for a specific section for the user's API key.
    """
    valid_sections = ["news", "applications", "training", "employees", "company", "bonuses", "warnings"]
    if section not in valid_sections:
        await ctx.send(f"❌ Invalid section. Valid sections: {', '.join(valid_sections)}")
        return

    api_keys = load_api_keys()
    user_id = str(ctx.author.id)
    user_config = api_keys.get(user_id)

    if not user_config:
        await ctx.send("❌ You have not registered an API key. Use `addapikey` to register one.")
        return

    try:
        update_config(user_id, section, channel.id)
        await ctx.send(f"✅ {section.capitalize()} channel set for your API key in {channel.mention}.")
    except Exception as e:
        print(f"[ERROR] Failed to set channel: {e}")
        await ctx.send(f"❌ Failed to set channel: {e}")

@bot.command(name="setdm")
async def set_dm(ctx, section: str):
    """
    Set direct messages for a specific section.
    """
    valid_sections = ["news", "applications", "training", "employees", "company", "bonuses", "warnings"]
    if section not in valid_sections:
        await ctx.send(f"❌ Invalid section. Valid sections: {', '.join(valid_sections)}")
        return

    api_keys = load_api_keys()
    user_id = str(ctx.author.id)
    user_config = api_keys.get(user_id)

    if not user_config:
        await ctx.send("❌ You have not registered an API key. Use `addapikey` to register one.")
        return

    try:
        update_config(user_id, section, ctx.author.id)
        await ctx.send(f"✅ {section.capitalize()} updates will now be sent to your DM.")
    except Exception as e:
        print(f"[ERROR] Failed to set DM: {e}")
        await ctx.send(f"❌ Failed to set DM: {e}")

@bot.command(name="setchannels")
async def set_all_channels(ctx, channel: discord.TextChannel):
    """
    Set the same channel for all sections.
    """
    valid_sections = ["company", "employees", "applications", "training", "news", "bonuses", "warnings_inactivity", "warnings_addiction"]

    api_keys = load_api_keys()
    user_id = str(ctx.author.id)
    user_config = api_keys.get(user_id)

    if not user_config:
        await ctx.send("❌ You have not registered an API key. Use `addapikey` to register one.")
        return

    try:
        for section in valid_sections:
            update_config(user_id, section, channel.id)
        await ctx.send(f"✅ All sections set to {channel.mention}.")
    except Exception as e:
        print(f"[ERROR] Failed to set all sections to channel: {e}")
        await ctx.send(f"❌ Failed to set all sections to channel: {e}")

@bot.command(name="end")
async def stop_logging(ctx):
    # Stop tasks that are loops
    post_company_update.stop()
    update_employee_stats.stop()
    check_applications.stop()
    post_training_regimen.stop()
    post_warnings.stop()

    
    # Handle non-loop functions separately if needed
    # process_news2 is an async function, not a loop, so it does not require stopping

    await ctx.send("✅ All tasks stopped.")

@bot.command(name="viewstats")
async def view_stats(ctx, api_key: str):
    profit_logs = get_company_data(api_key, PROFIT_LOG_FILE)
    last_actions = get_company_data(api_key, LAST_ACTION_FILE)
    training_reports = get_company_data(api_key, TRAINING_TRACKING_FILE)

    await ctx.send(f"**Stats for API Key {api_key}:**\n"
                   f"Profit Logs: {len(profit_logs.get('entries', []))} entries\n"
                   f"Last Actions: {len(last_actions.get('employees', {}))} employees\n"
                   f"Training Reports: {training_reports.get('report', 'No data')}")

# --------- TASK FUNCTIONS ---------


def initialize_training_tracking(api_key):
    """Initialize training tracking for a company."""
    training_data = get_company_data(api_key, TRAINING_TRACKING_FILE)
    if not training_data:
        save_company_data(api_key, TRAINING_TRACKING_FILE, {})

def save_training_report(api_key, report):
    """Save training reports under the company."""
    training_data = get_company_data(api_key, TRAINING_TRACKING_FILE)
    training_data["report"] = report
    save_company_data(api_key, TRAINING_TRACKING_FILE, training_data)

def calculate_trains_needed(stats, required_stats):
    """Calculate the number of training sessions needed for the most deficient stat."""
    trains_needed = {}
    max_deficit = 0
    primary_stat = None

    for skill, required in required_stats.items():
        current_stat = stats.get(skill, 0)
        deficit = max(0, required - current_stat)  # Ensure deficit is non-negative
        print(f"[DEBUG] Stat: {skill}, Required: {required}, Current: {current_stat}, Deficit: {deficit}")
        if deficit > max_deficit:
            max_deficit = deficit
            primary_stat = skill

    if primary_stat:
        increment = 50 if primary_stat == "Manual Labor" else 25
        trains_needed[primary_stat] = -(-max_deficit // increment)  # Ceiling division
        print(f"[DEBUG] Selected Stat for Training: {primary_stat}, Trains Needed: {trains_needed[primary_stat]}")

    return trains_needed

# Global dictionary to track running tasks for each API key
running_tasks = {}

async def start_tasks_for_key(api_key, config):
    global running_tasks_registry

    stop_tasks_for_key(api_key)  # Stop any running tasks

    try:
        print(f"Starting tasks for API key: {api_key}")
        urls = generate_api_urls(api_key)

        # Extract and validate config sections
        company_config = config.get("company", {})
        employees_config = config.get("employees", {})
        applications_config = config.get("applications", {})
        training_config = config.get("training", {})
        news_config = config.get("news", {})
        warnings_config = config.get("warnings", {})

        # Check if the config sections are valid

        if not isinstance(company_config, dict) or "channel_id" not in company_config:
            print(f"[ERROR] Invalid company config: {company_config}")
            return

        # Start tasks
        running_tasks_registry["post_company_update"][api_key] = asyncio.create_task(
            post_company_update(company_config, api_key, urls["profile"], urls["detailed"], urls["stock"])
        )
        running_tasks_registry["update_employee_stats"][api_key] = asyncio.create_task(
            update_employee_stats(employees_config, api_key, urls["profile"], urls["employees"], warnings_config)
        )
        running_tasks_registry["check_applications"][api_key] = asyncio.create_task(
            check_applications(applications_config, urls["applications"], api_key)
        )
        running_tasks_registry["post_training_regimen"][api_key] = asyncio.create_task(
            post_training_regimen(training_config, api_key, urls["profile"], urls["employees"], urls["detailed"])
        )
        running_tasks_registry["process_company_news"][api_key] = asyncio.create_task(
            process_company_news(api_key, news_config)
        )

        running_tasks_registry["post_warnings"][api_key] = asyncio.create_task(
            post_warnings(warnings_config, api_key, urls["employees"])
        )
        running_tasks_registry["monitor_company_funds"][api_key] = asyncio.create_task(
            monitor_company_funds(api_key, news_config, urls["detailed"], urls["employees"]))
        
        running_tasks_registry['stock_logger'][api_key] = asyncio.create_task(
            log_daily_stock_task(api_key, urls['stock']))
        
        running_tasks_registry['stock_poster'][api_key] = asyncio.create_task(
            generate_and_post_stock_graph(api_key, company_config))
        
        print(f"[INFO] Tasks successfully started for API key: {api_key}")
    except Exception as e:
        print(f"[ERROR] Starting tasks for API key {api_key}: {e}")
        stop_tasks_for_key(api_key)

@tasks.loop(hours=1)
async def post_warnings(warnings_config, api_key, employee_url):
    """
    Post or update warnings embed for employees with inactivity or addiction issues.
    """
    try:
        # Extract the channel ID from the configuration
        channel_id = warnings_config.get("channel_id")
        if not isinstance(channel_id, int):
            print(f"[ERROR] Invalid channel_id for warnings: {channel_id}")
            return

        # Resolve the target channel
        target = await resolve_target(channel_id)
        if not target:
            print(f"[ERROR] Failed to resolve target for warnings.")
            return

        # Fetch employee data
        employee_data = fetch_data(employee_url).get("company_employees", {})
        inactivity_warnings = []
        addiction_warnings = []

        # Load registered users
        registered_users = load_json("registered_users.json")
        print(f"[DEBUG] Loaded registered users: {registered_users}")

        # Process employee warnings
        for emp_id, details in employee_data.items():
            name = details.get("name", "Unknown")
            last_action = details.get("last_action", {}).get("relative", "Unknown")
            addiction_level = details.get("effectiveness", {}).get("addiction", "N/A")

            torn_id = str(emp_id)  # Ensure torn_id is a string for comparison
            discord_id = None

            # Find discord_id for the torn_id
            for user_data in registered_users.values():
                if user_data.get("torn_id") == torn_id:
                    discord_id = user_data.get("discord_id")
                    break

            # Format mention if discord_id is found
            mention = f"<@{discord_id}>" if discord_id else name

            # Check inactivity
            if "days ago" in last_action or "weeks ago" in last_action:
                inactivity_warnings.append(f"⚠️ **{mention}**: Last action was **{last_action}**.")

            # Check addiction (only on Fridays, Saturdays, and Sundays)
            #current_day = datetime.timetz
            current_day = datetime.utcnow().strftime('%A')

            addiction_threshold = warnings_config.get("addiction_threshold", -10)

            if current_day in {"Friday", "Saturday", "Sunday"}:
                if isinstance(addiction_level, int) and addiction_level <= -addiction_threshold:  # Threshold for high addiction
                    addiction_warnings.append(f"🚨 **{mention}**: Addiction level is **{addiction_level}**.")

        # Prepare and send inactivity warnings
        inactivity_data = "\n".join(inactivity_warnings) if inactivity_warnings else "✅ No inactivity warnings."
        inactivity_embed = discord.Embed(
            title="Inactivity Warnings",
            description=inactivity_data,
            color=discord.Color.red() if inactivity_warnings else discord.Color.green(),
            timestamp=datetime.utcnow(),
        )
        inactivity_embed.set_footer(text=f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        await send_or_edit_message(api_key, "warnings_inactivity", channel_id, [inactivity_embed])

        # Prepare and send addiction warnings (only on specified days)
        if current_day in {"Friday", "Saturday", "Sunday"}:
            addiction_data = "\n".join(addiction_warnings) if addiction_warnings else "✅ No addiction warnings."
            addiction_embed = discord.Embed(
                title="Addiction Warnings",
                description=addiction_data,
                color=discord.Color.orange() if addiction_warnings else discord.Color.green(),
                timestamp=datetime.utcnow(),
            )
            addiction_embed.add_field(name="Please rehab by Sunday", value="🚨", inline=False)
            
            addiction_embed.set_footer(text=f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            await send_or_edit_message(api_key, "warnings_addiction", channel_id, [addiction_embed])

    except asyncio.CancelledError:
        print(f"[INFO] Task post_warnings for API key '{api_key}' was cancelled.")
    except Exception as e:
        print(f"[ERROR] Exception in post_warnings for API key '{api_key}': {e}")

@tasks.loop(hours=1)
async def post_training_regimen(config, api_key, profile_url, employee_url, detailed_url):
    """
    Post or update the training regimen embed every hour.
    """
    try:
        channel_id = config.get("channel_id")
        if not isinstance(channel_id, int):
            print(f"[ERROR] Invalid channel_id for training: {channel_id}")
            return

        target = await resolve_target(channel_id)
        if not target:
            print(f"[ERROR] Failed to resolve target for training regimen.")
            return

        training_report, trains_needed = await generate_training_report(employee_url, detailed_url, profile_url)
        #print(f"Training report: {training_report}, traineeded: {trains_needed}")
        if training_report:
            embeds = [
                discord.Embed(
                    title="Training Regimen",
                    description=f"Trains needed: {trains_needed}",
                    color=discord.Color.gold()
                )
            ]
            for report in training_report:
                trains_needed_str = "\n".join(
                    f"{stat}: {count}" for stat, count in report["trains_needed"].items()
                )
                embeds[0].add_field(
                    name=report["name"],
                    value=f"Position: {report['position']}\nTrains Needed:\n{trains_needed_str}",
                    inline=False
                )
            await send_or_edit_message(api_key, "training", channel_id, embeds)
    except asyncio.CancelledError:
        print(f"[INFO] Task post_training_regimen for API key '{api_key}' was cancelled.")
    except Exception as e:
        print(f"[ERROR] Exception in post_training_regimen for API key '{api_key}': {e}")

async def generate_training_report(employee_url, detailed_url, profile_url):
    print("Generating training report...\n\n")
    try:
        employee_data = fetch_data(employee_url).get("company_employees", {})
        company_data = fetch_data(detailed_url)
        profile_data = fetch_data(profile_url)

        company_type = profile_data.get("company", {}).get("company_type", "Unknown")
        job_stats = load_json("company_data.json").get(str(company_type), {}).get("Positions", {})
        print(f"[DEBUG] Company Type: {company_type}\nJob Stats: {job_stats}")

        report = []
        total_trains = 0

        for emp_id, details in employee_data.items():
            position = details.get("position", "Unassigned")
            if position not in job_stats:
                print(f"[WARN] Position '{position}' not found in job stats. Skipping.")
                continue

            #stats = {k: details.get(k.lower(), 0) for k in ["Manual_Labor", "Intelligence", "Endurance"]}
            # Correctly map keys to match job_stats naming
            stats = {
                "Manual Labor": details.get("manual_labor", 0),  # Use the actual key name from employee_data
                "Intelligence": details.get("intelligence", 0),
                "Endurance": details.get("endurance", 0),
            }

            required_stats = job_stats[position]
            print(f"[DEBUG] Employee: {details.get('name', 'Unknown')}, Stats: {stats}, Required: {required_stats}")
            trains_needed = calculate_trains_needed(stats, required_stats)
            print(f"[DEBUG] Trains Needed: {trains_needed}")

            if trains_needed:
                train_count = sum(trains_needed.values())  # Sum all train counts for this employee
                total_trains += train_count
                report.append({
                    "name": details.get("name", "Unknown"),
                    "position": position,
                    "trains_needed": trains_needed,
                })
                print(f"[DEBUG] Total Trains Incremented: {total_trains}")

        return report, total_trains
    except Exception as e:
        print(f"[ERROR] Failed to generate training report: {e}")
        return [], 0

# --------- TASK IMPLEMENTATIONS ---------

def get_stock_by_type(data, business_id):
    """
    Get categorized stock for a given business.
    """
    business = data.get(business_id, {})
    stock = business.get("Stock", {})
    return {
        "Services": stock.get("Services", []),
        "ProducedGoods": stock.get("ProducedGoods", []),
        "OrderedGoods": stock.get("OrderedGoods", [])
    }


def get_available_goods(stock_list, stock_type):
    """
    Filter and retrieve only the available goods from a given stock list.
    :param stock_list: List of stock items to filter.
    :param stock_type: Type of stock (e.g., 'Services', 'ProducedGoods', 'OrderedGoods').
    :return: List of available goods.
    """
    available_goods = []
    
    for item in stock_list:
        # For 'Services', availability is based on whether it can be offered.
        if stock_type == "Services" and item.get("Cost", "N/A") == "Cannot be ordered":
            available_goods.append(item)
        
        # For 'ProducedGoods', availability might depend on production status.
        elif stock_type == "ProducedGoods" and item.get("Cost", "N/A") == "Cannot be ordered":
            available_goods.append(item)
        
        # For 'OrderedGoods', availability is determined by having a valid cost.
        elif stock_type == "OrderedGoods" and item.get("Cost", 0) > 0:
            available_goods.append(item)
    
    return available_goods



async def generate_company_embed(api_key, COMPANY_PROFILE_URL, COMPANY_STOCK_URL, COMPANY_DATA_URL):
    # Fetch company data
    await asyncio.sleep(2)
    profile_data = fetch_data(COMPANY_PROFILE_URL)
    stock_data = fetch_data(COMPANY_STOCK_URL)
    await asyncio.sleep(2)
    company_data = fetch_data(COMPANY_DATA_URL)

    company_name = profile_data.get("company", {}).get("name", "Unknown")
    #company_type = profile_data.get("company", {}).get("company_type", "Unknown")

    company_funds = company_data.get("company_detailed", {}).get("company_funds", 0)
    popularity = company_data.get("company_detailed", {}).get("popularity", 0)
    efficiency = company_data.get("company_detailed", {}).get("efficiency", 0)
    environment = company_data.get("company_detailed", {}).get("environment", 0)
    trains_available = company_data.get("company_detailed", {}).get("trains_available", 0)
    advertising_budget = company_data.get("company_detailed", {}).get("advertising_budget", 0)
    rating = profile_data.get("company", {}).get("rating", 0)
   


    if not profile_data or not stock_data:
        return None

    # Extract daily metrics
    current_profit = profile_data['company']['daily_income']
    current_customers = profile_data['company']['daily_customers']

    # Update profit tracking
    value = log_daily_metrics(api_key, current_profit, current_customers)
    if value != None:

        profit_stats = update_profit_tracking(api_key, current_profit, current_customers, is_daily_update=True)

        # Create embed with profit stats
        embed = discord.Embed(
            title=f"Company Profile: {profile_data['company']['name']} [{profile_data['company']['company_type']}]",
            color=discord.Color.blue()
        )
        embed.add_field(name="Company Funds", value=f"${company_funds:,}", inline=True)
        embed.add_field(name="Popularity", value=f"{popularity}", inline=True)
        embed.add_field(name="Efficiency", value=f"{efficiency}", inline=True)
        embed.add_field(name="Environment", value=f"{environment}", inline=True)
        embed.add_field(name="Rating", value=f"{rating}", inline=True)
        embed.add_field(name="Trains Available", value=f"{trains_available}", inline=True)
        embed.add_field(name="Advertising Budget", value=f"${advertising_budget:,}", inline=True)
        embed.add_field(name="Today's Profit", value=f"${current_profit:,}", inline=True)
        embed.add_field(name="Today's Customers", value=f"{current_customers}", inline=True)
        if current_profit < 150000:
            embed.add_field(name="Warning", value="⚠️ Low profit day detected!", inline=False)
        elif current_profit > 200000:
            embed.add_field(name="Compliment", value="🎉 High profit day! Great job!", inline=False)

        embed.add_field(name="Total Profit", value=f"${profit_stats['total_profit']:,}", inline=False)
        embed.add_field(name="Average Daily Profit", value=f"${profit_stats['average_profit']:,}", inline=True)
        embed.add_field(name="Highest Profit", value=f"${profit_stats['highest_profit']:,}", inline=True)
        embed.add_field(name="Lowest Profit", value=f"${profit_stats['lowest_profit']:,}", inline=True)
        embed.add_field(name="Average Customers", value=f"{profit_stats['average_customers']:.0f}", inline=False)
        embed.add_field(name="Highest Customers", value=f"{profit_stats['highest_customers']:,}", inline=True)
        embed.add_field(name="Lowest Customers", value=f"{profit_stats['lowest_customers']:,}", inline=True)

        # Additional embed fields
        #stock = stock_data.get("company_stock", {})
        for item, details in stock_data.get('company_stock', {}).items():
            stock = details['in_stock']
            if stock < 1750:
                warning = f"⚠️ Low stock detected! Only {stock} left. <@&1321602638357336187> get ahold of the <@&1313749451998761010>"
            if stock > 3000:
                warning = "🎉 High stock! Switch up the staff for more Salespersons <@&1321602638357336187>"
            else:
                if stock < 1000:
                    warning = "⚠️ Critical stock level! <@&1321602638357336187> get ahold of the <@&1313749451998761010>"
                elif stock < 1500:
                    warning = "Stock is looking good!"
                else:
                    warning = "Stock is getting low."
                
            embed.add_field(
                name=f"Stock: {item}",
                value=(
                    f"Cost: ${details['cost']:,}\n"
                    f"In Stock: {details['in_stock']}\n"
                    f"Sold Amount: {details['sold_amount']}\n"
                    f"Price: ${details['price']:,}\n"
                    f"RRP: ${details['rrp']:,}\n"
                    f"Profit: ${details['sold_worth']:,}\n\n"
                    f"Incoming stock: {details['on_order']}\n"
                ),
                inline=False
            )
            embed.add_field(name="Stock alert:", value=warning, inline=False)

            

        embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return embed




async def post_all_embeds(api_key, channel_id, embeds_and_files):
    """
    Post all embeds to the specified channel.
    """
    try:
        target = await resolve_target(channel_id)
        if not target:
            print(f"[ERROR] Failed to resolve target for channel ID: {channel_id}")
            return

        message_ids = get_message_ids(api_key, "company") or []
        updated_message_ids = []

        for idx, (embed, file) in enumerate(embeds_and_files):
            if idx < len(message_ids):
                try:
                    message = await target.fetch_message(message_ids[idx])
                    if file:
                        await message.delete()
                        new_message = await target.send(embed=embed, file=file)
                    else:
                        await message.edit(embed=embed)
                        new_message = message
                except discord.NotFound:
                    new_message = await target.send(embed=embed, file=file)
            else:
                new_message = await target.send(embed=embed, file=file)

            updated_message_ids.append(new_message.id)

        for extra_id in message_ids[len(embeds_and_files):]:
            try:
                message = await target.fetch_message(extra_id)
                await message.delete()
            except discord.NotFound:
                print(f"[WARN] Message ID {extra_id} not found for deletion.")

        save_message_ids(api_key, "company", updated_message_ids)
        print(f"[INFO] Successfully posted embeds for API key: {api_key}")

    except Exception as e:
        print(f"[ERROR] Failed to post all embeds for API key {api_key}: {e}")


@tasks.loop(hours=1)
async def post_company_update(config, api_key, profile_url, detailed_url, stock_url):
    """
    Periodically updates the company profile and posts relevant embeds.
    """
    try:
        channel_id = config.get("channel_id")
        if not isinstance(channel_id, int):
            print(f"[ERROR] Invalid channel_id for company: {channel_id}")
            return

        # Fetch necessary data
        profile_data = fetch_data(profile_url)
        stock_data = fetch_data(stock_url).get("company_stock", {})
        detailed_data = fetch_data(detailed_url)

        if not profile_data or not stock_data or not detailed_data:
            print(f"[ERROR] Missing data for API key: {api_key}")
            return
        
        

        company_embed = await generate_company_embed(api_key, profile_url, stock_url, detailed_url)

        await post_all_embeds(api_key, channel_id, [(company_embed, None)])


    except Exception as e:
        print(f"[ERROR] Exception in post_company_update for API key '{api_key}': {e}")


def initialize_loyalty_tracking():
    if not os.path.exists(LOYALTY_TRACKING_FILE):
        save_json({}, LOYALTY_TRACKING_FILE)

def update_loyalty_tracking(api_key, emp_id, milestone):
    loyalty_data = get_company_data(api_key, LOYALTY_TRACKING_FILE)
    loyalty_data.setdefault(emp_id, [])
    if milestone not in loyalty_data[emp_id]:
        loyalty_data[emp_id].append(milestone)
        save_company_data(api_key, LOYALTY_TRACKING_FILE, loyalty_data)
        return True
    return False

def process_result(result):
    """Process result to extract position and requirements."""
    if not isinstance(result, dict):
        print(f"Error: Expected a dictionary but got {type(result).__name__}")
        return None, {}

    # Extract Position and Requirements
    position = result.get("Position", "Unknown Position")
    requirements = result.get("Requirements", {})

    # Skip unassigned or missing positions
    if position == "Unassigned" or not requirements:
        print(f"Skipping unassigned or missing position: {position}")
        return position, {}

    return position, requirements

async def generate_employee_embed(api_key, company_type, COMPANY_EMPLOYEES_URL):
    employee_data = fetch_data(COMPANY_EMPLOYEES_URL).get("company_employees", {})
    last_actions = get_company_data(api_key, LAST_ACTION_FILE)
    news_channel_id = get_channel_id(api_key, "news")
    news_channel = bot.get_channel(news_channel_id)

    bonus_channel_id = get_channel_id(api_key, "bonuses")
    bonus_channel = bot.get_channel(bonus_channel_id)

    if "employees" not in last_actions:
        last_actions["employees"] = {}

    embeds = []

    # Emoji mappings for stats
    stat_emojis = {
        "Manual Labor": "🔨",
        "Intelligence": "🧠",
        "Endurance": "💪",
    }

    for emp_id, details in employee_data.items():
        name = details.get("name", "Unknown")
        position = details.get("position", "N/A")
        loyalty = details.get("days_in_company", 0)
        wage = details.get("wage", "N/A")
        manual = details.get("manual_labor", 0)
        intelligence = details.get("intelligence", 0)
        endurance = details.get("endurance", 0)
        
        last_action = details.get("last_action", {}).get("relative", "N/A")
        effectiveness = details.get("effectiveness", {})
        name_link = f"[{name}](https://www.torn.com/profiles.php?XID={emp_id})"

        # Position update notification
        previous_position = last_actions["employees"].get(name, {}).get("Position", "N/A")
        if previous_position != position and previous_position != "N/A":
            if news_channel:
                embed = discord.Embed(
                    title="Position Update",
                    description=f"📢 **{name}** switched from **{previous_position}** to **{position}**.",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await news_channel.send(embed=embed)

        # Loyalty milestone notification
        if loyalty % 30 == 0 and loyalty > 0:
            if update_loyalty_tracking(api_key, emp_id, loyalty):
                if bonus_channel:
                    await bonus_channel.send(
                        f"🎉 {name_link} has reached {loyalty} days of loyalty! Consider issuing a bonus! 🎉"
                    )

        # Stats comparison
        positions = json.load(open(Company_Positions_File, "r"))
        result = get_business_position(positions, company_type, position)
        _, requirements = process_result(result)
        stat_comparison = []

        # Known stats
        known_stats = {
            "Manual Labor": manual,
            "Intelligence": intelligence,
            "Endurance": endurance,
        }

        # Compare stats with requirements
        for stat, required_value in requirements.items():
            current_value = known_stats.get(stat, 0)
            diff = current_value - required_value
            emoji = stat_emojis.get(stat, "")
            stat_comparison.append(f"{emoji} {stat}: {current_value:,} ({'+' if diff >= 0 else ''}{diff:,})")

        # Find the missing stat not in requirements
        missing_stat = next(
            (stat for stat in known_stats if stat not in requirements), None
        )
        if missing_stat:
            missing_stat_value = known_stats[missing_stat]
            emoji = stat_emojis.get(missing_stat, "")
            stat_comparison.append(f"{emoji} {missing_stat}: {missing_stat_value:,} (Not required)")

        # Add total stats to the end of the Stats field
        total_stat_value = sum(known_stats.values())
        stat_comparison.append(f"**Total Stats:** {total_stat_value:,}")

        # Update last actions
        last_actions["employees"][name] = {
            "Employee ID": emp_id,
            "last action": last_action,
            "Position": position,
            "Loyalty": loyalty,
            "Wage": wage,
            "Effectiveness": effectiveness,
            "Working Stats": known_stats,
        }

        # Build the embed
        embed = discord.Embed(
            title=name,
            url=f"https://www.torn.com/profiles.php?XID={emp_id}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="General Info",
            value=(f"**Position:** {position}\n"
                   f"**Loyalty:** {loyalty} days\n"
                   f"**Wage:** ${wage:,}\n"
                   f"**Last Online:** {last_action}"),
            inline=False
        )
        embed.add_field(
            name="Stats",
            value="\n".join(stat_comparison),  # Include missing stat and total stats
            inline=True
        )
        embed.add_field(
            name="Effectiveness",
            value=(f"**Settled in:** {effectiveness.get('settled_in', 'N/A')}\n"
                   f"**Merits:** {effectiveness.get('merits', 'N/A')}\n"
                   f"**Director Education:** {effectiveness.get('director_education', 'N/A')}\n"
                   f"**Management:** {effectiveness.get('management', 'N/A')}\n"
                   f"**Addiction:** {effectiveness.get('addiction', 'N/A')}\n"
                   f"**Inactivity:** {effectiveness.get('inactivity', 'N/A')}\n"
                   f"**Total Effectiveness:** {effectiveness.get('total', 'N/A')}")
        )
        embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        embeds.append(embed)

    # Save last actions to JSON
    update_last_actions(api_key, last_actions)
    return embeds

@tasks.loop(hours=1)
async def update_employee_stats(config, api_key, profile_url, employee_url, warnings_config):
    """
    Post or update the employee status report every hour.
    """
    try:
        channel_id = config.get("channel_id")
        if not isinstance(channel_id, int):
            print(f"[ERROR] Invalid channel_id for employees: {channel_id}")
            return

        target = await resolve_target(channel_id)
        if not target:
            print(f"[ERROR] Failed to resolve target for employee stats.")
            return

        company_data = fetch_data(profile_url)
        company_type = company_data.get("company", {}).get("company_type", "N/A")
        embeds = await generate_employee_embed(api_key, company_type, employee_url)
        if embeds:
            await send_or_edit_message(api_key, "employees", channel_id, embeds)
    except asyncio.CancelledError:
        print(f"[INFO] Task update_employee_stats for API key '{api_key}' was cancelled.")
    except Exception as e:
        print(f"[ERROR] Exception in update_employee_stats for API key '{api_key}': {e}")

def get_seen_applications(api_key):
    all_seen = load_json("applications_seen.json")
    return all_seen.get(api_key, {})

def save_seen_applications(api_key, applications):
    all_seen = load_json("applications_seen.json")
    all_seen[api_key] = applications
    save_json(all_seen, "applications_seen.json")

@tasks.loop(minutes=5)
async def check_applications(config, applications_url, api_key):
    try:
        seen_applications = get_seen_applications(api_key)
        channel_id = config.get("channel_id")

        if not isinstance(channel_id, int):
            print(f"[ERROR] Invalid channel_id for company: {channel_id}\nApplications.")
            return
        if not channel_id:
            print("[ERROR] No channel configured for applications.")
            return

        target = await resolve_target(channel_id)
        if not target:
            print(f"[ERROR] Failed to resolve target for applications. Channel ID: {channel_id}")
            return

        data = fetch_data(applications_url).get("applications", {})
        embeds_to_send = []

        if isinstance(data, list):
            for details in data:
                print(f"[Debug] in check apps: {details}")
        
        else:

            for app_id, details in data.items():
                if app_id in seen_applications:
                    continue

                user_id = details.get("userID", "N/A")
                name = details.get("name", "Unknown")
                level = details.get("level", "N/A")
                stats = details.get("stats", {})
                status = details.get("status", "N/A")
                expires = datetime.fromtimestamp(details.get("expires", 0)).strftime("%Y-%m-%d %H:%M:%S")
                message = details.get("message", "No message provided.")
                profile_link = f"https://www.torn.com/profiles.php?XID={user_id}"

                embed = discord.Embed(
                    title="New Application",
                    description=f"[{name}]({profile_link})",
                    color=get_application_status_color(status),
                )
                embed.add_field(name="Level", value=level, inline=True)
                embed.add_field(name="Manual Labor", value=stats.get("manual_labor", "N/A"), inline=True)
                embed.add_field(name="Intelligence", value=stats.get("intelligence", "N/A"), inline=True)
                embed.add_field(name="Endurance", value=stats.get("endurance", "N/A"), inline=True)
                embed.add_field(name="User Message", value=message, inline=False)
                embed.add_field(name="Status", value=status.capitalize(), inline=True)
                embed.add_field(name="Expires", value=expires, inline=True)
                embed.set_footer(text=f"Application ID: {app_id}")

                embeds_to_send.append(embed)
                seen_applications[app_id] = details

        if embeds_to_send:
            print(f"[INFO] Sending {len(embeds_to_send)} new application embeds.")
            await send_or_edit_message(api_key, "applications", channel_id, embeds_to_send)
        else:
            print("[INFO] No new applications to process.")

        save_seen_applications(api_key, seen_applications)
    except asyncio.CancelledError:
        print(f"[INFO] Task check_applications for API key {api_key} was cancelled.")
    except Exception as e:
        print(f"[ERROR] Exception in check_applications for API key {api_key}: {e}")
        stop_tasks_for_key(api_key)

@tasks.loop(hours=2)
async def process_company_news(api_key, news_config):
    """Check for new relevant news items and post them using the `send_or_edit_message` function."""
    NEWS_FILE = "news_log.json"  # To track seen news items
    NEWS_URL = f"https://api.torn.com/company/?key={api_key}&comment=TornAPI&selections=news"
    news_data = fetch_data(NEWS_URL).get("news", {})
    seen_news = get_company_data(api_key, NEWS_FILE)
    training_counts = get_company_data(api_key, "training_counts.json")
    news_channel_id = news_config.get("channel_id")

    if not isinstance(news_channel_id, int):
        print(f"Invalid channel_id for company: {news_channel_id}")
        return

    # Resolve the news target
    target = await resolve_target(news_channel_id)
    if not target:
        print(f"[ERROR] Failed to resolve target for news. Channel ID: {news_channel_id}")
        return

    print("[INFO] Processing company news...")
    embeds_to_send = []

    for news_id, details in news_data.items():
        # Skip already processed news
        if news_id in seen_news:
            continue

        raw_news_text = details["news"]
        news_text = clean_html(raw_news_text)
        timestamp = datetime.fromtimestamp(details["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        embed = None

        # Match day report using a regex
        day_report_match = re.search(r"(\w+) report: .*", news_text)
        if day_report_match:
            day = day_report_match.group(1)  # Extract the day (e.g., "Friday")
            embed = discord.Embed(
                title=f"{day} Report",
                description=news_text,
                color=discord.Color.gold(),
            )

        # Check for accepted applications
        application_match = re.search(
            r'<a href = http://www\.torn\.com/profiles\.php\?XID=\d+>(.*?)</a> has accepted <a href = http://www\.torn\.com/profiles\.php\?XID=\d+>(.*?)</a>\'s application to join the company',
            raw_news_text
        )
        if application_match:
            acceptor = application_match.group(1)
            applicant = application_match.group(2)
            embed = discord.Embed(
                title="Application Accepted",
                description=f"🎉 **{acceptor}** has accepted **{applicant}**'s application to join the company!",
                color=discord.Color.green()
            )

        # Check for company rating changes
        rating_match = re.search(r"the company has (increased|decreased) to rating (\d+)", news_text)
        if rating_match:
            action = rating_match.group(1)
            rating = int(rating_match.group(2))
            description = (
                f"🎉 Congratulations! The company rating has increased to {rating}!"
                if action == "increased"
                else f"😢 The company rating has decreased to {rating}. Let's improve!"
            )
            embed = discord.Embed(
                title="Company Rating Update",
                description=description,
                color=discord.Color.green() if action == "increased" else discord.Color.red(),
            )

        # Check for funds withdrawn or deposited
        if re.search(r"withdrawn\s+\$\S+\s+from the company funds", news_text):
            emoji = get_news_emoji("withdrawn from the company funds")
            embed = discord.Embed(
                title="Company Funds Update",
                description=f"{emoji} {news_text}",
                color=discord.Color.purple(),
            )
        if re.search(r"has made a deposit of \$\S+\s+to the company funds", news_text):
            emoji = get_news_emoji("has made a deposit into the company funds")
            embed = discord.Embed(
                title="Company Funds Update",
                description=f"{emoji} {news_text}",
                color=discord.Color.purple(),
            )

        # Handle training-related news
        if "has been trained by the director" in news_text:
            employee_name = extract_employee_name(raw_news_text)
            if employee_name:
                training_counts[employee_name] = training_counts.get(employee_name, 0) + 1
                save_company_data(api_key, "training_counts.json", training_counts)

        # Handle employee leaving or being fired
        if "has left the company" in news_text or "has been fired from the company" in news_text:
            emoji = get_news_emoji(news_text)
            embed = discord.Embed(
                title="Employee Departure",
                description=f"{emoji} {news_text}",
                color=discord.Color.red(),
            )

        # Add the embed to the list if created
        if embed:
            embed.set_footer(text=f"Posted: {timestamp}")
            embeds_to_send.append(embed)

        # Mark the news as seen
        seen_news[news_id] = details

    # Save the seen news
    save_company_data(api_key, NEWS_FILE, seen_news)

    # Post grouped training report if training occurred
    if training_counts:
        training_summary = "\n".join(
            [f"{name}: {count} times" for name, count in training_counts.items()]
        )
        training_embed = discord.Embed(
            title="Training Summary",
            description=f"📘 **Training by Director**:\n{training_summary}",
            color=discord.Color.blue(),
        )
        embeds_to_send.append(training_embed)
        # Reset training counts after sending
        save_company_data(api_key, "training_counts.json", {})

    # Send all collected embeds
    if embeds_to_send:
        print(f"[INFO] Sending {len(embeds_to_send)} news embeds.")
        await send_or_edit_message(api_key, "news", news_channel_id, embeds_to_send)
    else:
        print("[INFO] No new news to process.")



async def resolve_target(target_id):
    try:
        target = bot.get_channel(target_id)
        if target:
            print(f"Resolved target ID {target_id} as channel: {target.name}")
            return target

        user = await bot.fetch_user(target_id)
        if user:
            dm_channel = await user.create_dm()
            print(f"Resolved target ID {target_id} as user's DM: {dm_channel}")
            return dm_channel

    except discord.Forbidden:
        print(f"Permission denied to access target ID: {target_id}.")
    except discord.HTTPException as e:
        print(f"HTTP error resolving target ID {target_id}: {e}")
    except Exception as e:
        print(f"Unexpected error resolving target ID {target_id}: {e}")

    print(f"Failed to resolve target ID: {target_id}")
    return None

async def send_to_target(target_id, embed=None):
    """
    Sends a message or embed to the resolved target (channel or DM).
    """
    target = await resolve_target(target_id)
    if not target:
        print(f"Cannot send message: Target ID {target_id} could not be resolved.")
        return None

    try:
        if embed:
            return await target.send(embed=embed)
    except discord.Forbidden:
        print(f"Permission denied to send message to target ID {target_id}.")
    except discord.HTTPException as e:
        print(f"HTTP error sending to target ID {target_id}: {e}")
    except Exception as e:
        print(f"Unexpected error sending to target ID {target_id}: {e}")

    return None

@bot.command(name="test_target")
async def test_target(ctx, target_id: int):
    try:
        target = bot.get_channel(target_id)
        if target:
            await ctx.send(f"Target {target_id} resolved as a channel: {target.name}")
        else:
            user = await bot.fetch_user(target_id)
            if user:
                await ctx.send(f"Target {target_id} resolved as a user: {user.name}")
            else:
                await ctx.send(f"Target {target_id} could not be resolved.")
    except discord.Forbidden:
        await ctx.send(f"Permission denied for target ID: {target_id}.")
    except Exception as e:
        await ctx.send(f"Error resolving target {target_id}: {e}")

@bot.command(name="show_config")
async def show_config(ctx):
    config_data = load_json(CONFIG_FILE).get("api_keys", {})
    api_key = config_data.get(str(ctx.author.id))
    if not api_key:
        await ctx.send("No API key found for your user.")
    else:
        config = config_data.get(api_key, {})
        await ctx.send(f"Config for your API key: {config}")

async def send_or_edit_message(api_key, section, target_id, embeds, file=None):
    target = await resolve_target(target_id)
    if not target:
        print(f"[ERROR] Cannot resolve target for section '{section}', target ID: {target_id}.")
        return

    message_ids = get_message_ids(api_key, section) or []
    updated_message_ids = []

    try:
        for idx, embed in enumerate(embeds):
            if idx < len(message_ids):
                try:
                    message = await target.fetch_message(message_ids[idx])
                    if file:
                        # Re-send with file (delete and replace the message)
                        await message.delete()
                        with open(file.fp.name, 'rb') as reopened_file:  # Ensure file is reopened
                            discord_file = discord.File(reopened_file, filename=file.filename)
                            new_message = await target.send(embed=embed, file=discord_file)
                        updated_message_ids.append(new_message.id)
                    else:
                        # Edit existing message
                        await message.edit(embed=embed)
                        updated_message_ids.append(message.id)
                except discord.NotFound:
                    # If message not found, send a new one
                    if file:
                        with open(file.fp.name, 'rb') as reopened_file:
                            discord_file = discord.File(reopened_file, filename=file.filename)
                            new_message = await target.send(embed=embed, file=discord_file)
                    else:
                        new_message = await target.send(embed=embed)
                    updated_message_ids.append(new_message.id)
            else:
                # Send a new message
                if file:
                    with open(file.fp.name, 'rb') as reopened_file:
                        discord_file = discord.File(reopened_file, filename=file.filename)
                        new_message = await target.send(embed=embed, file=discord_file)
                else:
                    new_message = await target.send(embed=embed)
                updated_message_ids.append(new_message.id)

        # Delete extra messages
        for extra_id in message_ids[len(embeds):]:
            try:
                message = await target.fetch_message(extra_id)
                await message.delete()
            except discord.NotFound:
                print(f"[WARN] Message ID {extra_id} not found for deletion.")

        # Save updated message IDs
        save_message_ids(api_key, section, updated_message_ids)
        print(f"[SUCCESS] Updated messages for section '{section}' with IDs: {updated_message_ids}.")
    except Exception as e:
        print(f"[ERROR] Failed to send or edit messages for section '{section}': {e}")

# --------- EVENT HANDLERS ---------

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    validate_and_fix_config()
    api_keys = load_api_keys()

    for user_id, user_config in api_keys.items():
        api_key = user_config.get("api_key")
        if api_key:
            print(f"[INFO] Initializing for API key: {api_key}")
            initialize_profit_log(api_key)

    print("Initialization complete.")

bot.run(TOKEN)
