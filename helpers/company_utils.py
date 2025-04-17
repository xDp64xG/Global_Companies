import discord
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
#from .file_utils_management import FileUtils
#from tasks.utils import ensure_file_exists, load_json, save_json
from tasks.utils import *
from .api_utils import *
from .data_processing_utils import aggregate_data  # ✅ Import aggregation function

import logging

logger = logging.getLogger("CompanyUtils")


#PROFIT_TRACKING_FILE = "profit_tracking.json"
LAST_COUNTED_DATE = "last_counted_date.json"
CURRENT_STOCK_FILE = "./data/company_checker/Stocks/current_stock.json"
STOCK_LOG_FILE = "./data/company_checker/Stocks/daily_stock_log.json"
PROFIT_LOG_FILE = "./data/company_checker/Profits/profit_log.json"
PROFIT_TRACKING_FILE = "./data/company_checker/Profits/profit_tracking.json"

DEFAULT_FILE_CONTENT = {
    "employee_data": {},
    "training_data": {"employees": []},
    "stock_data": {"records": []},
    "profit_data": {"logs": []},
    "applications_data": {"applications": []},
    "news_data": {"news": []}
}

class CompanyUtils:
    
    def __init__(self, api_key):
        self.api_key = api_key
        ensure_file_exists(PROFIT_LOG_FILE, "profit_data")
        #ensure_file_exists()
        ensure_file_exists(STOCK_LOG_FILE, "stock_data")
        ensure_file_exists(CURRENT_STOCK_FILE, "stock_data")

        #FileUtils
        #FileUtils.ensure_file_exists(CURRENT_STOCK_FILE, "stock_data")

    async def get_company_data(api_key, file):
        data = await load_json_async(file)
        if isinstance(api_key, dict):
            print(f"[ERROR] Invalid API key type: {type(api_key)} - {api_key}")
            return {}
        return data.get(api_key, {})

    async def fetch_company_data(self, co_id):
        """
        Fetch company data for a specific API key.
        """
        company_data = await load_json_async("./data/company_information/company_data.json").get(co_id, {})
        logger.info(f"Fetched company data for API key: {self.api_key}")
        return company_data

    async def initialize_profit_tracking(api_key):
        """Initialize the profit tracking for a specific API key if it does not exist."""
        profit_tracking = await CompanyUtils.get_company_data(api_key, PROFIT_TRACKING_FILE)
        if not profit_tracking:
            print(f"[DEBUG] Initializing profit tracking for API Key {api_key}.")
            await CompanyUtils.save_company_data(api_key, PROFIT_TRACKING_FILE, {"entries": []})



    async def update_profit_tracking(self, current_profit=None, current_customers=None, is_daily_update=False):
        """Update profit tracking for a specific API key and compute statistics."""
        
        profit_tracking = await load_json_async(PROFIT_TRACKING_FILE)
        profit_log = await load_json_async(PROFIT_LOG_FILE)

        today_date = datetime.now().strftime("%Y-%m-%d")

        if self.api_key not in profit_tracking:
            profit_tracking[self.api_key] = {"entries": []}

        if self.api_key not in profit_log:
            profit_log[self.api_key] = {"entries": []}

        # Check if today's data is already logged
        if is_daily_update and not any(entry["date"] == today_date for entry in profit_log[self.api_key]["entries"]):
            if current_profit is not None and current_customers is not None:
                new_entry = {
                    "date": today_date,
                    "profit": current_profit,
                    "customers": current_customers
                }
                profit_tracking[self.api_key]["entries"].append(new_entry)
                profit_log[self.api_key]["entries"].append(new_entry)

                await save_json_async(profit_tracking, PROFIT_TRACKING_FILE)
                await save_json_async(profit_log, PROFIT_LOG_FILE)

                print(f"[INFO] Logged profit data for {self.api_key}: {new_entry}")

        # Compute aggregated statistics
        profit_entries = profit_log[self.api_key]["entries"]

        return {
            "total_days": len(profit_entries),
            "total_profit": aggregate_data(profit_entries, "profit", "sum"),
            "average_profit": aggregate_data(profit_entries, "profit", "sum") / len(profit_entries) if profit_entries else 0,
            "highest_profit": aggregate_data(profit_entries, "profit", "max"),
            "lowest_profit": aggregate_data(profit_entries, "profit", "min"),
            "highest_customers": aggregate_data(profit_entries, "customers", "max"),
            "lowest_customers": aggregate_data(profit_entries, "customers", "min"),
        }
    
    async def update_last_counted_date(api_key):
        last_counted = await CompanyUtils.get_company_data(api_key, LAST_COUNTED_DATE)
        today = datetime.now().strftime("%Y-%m-%d")
        last_counted["last_counted"] = today
        await CompanyUtils.save_company_data(api_key, LAST_COUNTED_DATE, last_counted)

    async def should_count_day(api_key):
        last_counted = await CompanyUtils.get_company_data(api_key, LAST_COUNTED_DATE).get("last_counted", "")
        today = datetime.now().strftime("%Y-%m-%d")
        return today != last_counted
    
    async def save_company_data(api_key, file, new_data):
        """Save data for a specific API key."""
        data = await load_json_async(file)
        data[api_key] = new_data
        await save_json_async(data, file)

    async def fetch_stock_data(self):
        """
        Fetch stock data for a specific API key.
        """
        stock_data = await load_json_async(CURRENT_STOCK_FILE)
        stocks = stock_data.get(self.api_key, {})
        #stock_data = await load_json_async(CURRENT_STOCK_FILE).get(self.api_key, {})
        logger.info(f"Fetched stock data for API key: {self.api_key}")
        print(f"[DEBUG] Stock data for {self.api_key}: {stocks}")
        return stocks

    def build_company_embed(self, company_data):
        """Build a complete Discord embed for company details."""
        
        embed = discord.Embed(
            title=f"📊 {company_data.get('name', 'Company Info')}",
            description=f"Details for {company_data.get('name', 'N/A')}",
            color=discord.Color.blue(),
        )

        embed.add_field(name="🏢 Company Funds", value=f"${company_data.get('funds', 0):,}", inline=True)
        embed.add_field(name="📈 Popularity", value=f"{company_data.get('popularity', 0):,}", inline=True)
        embed.add_field(name="📊 Efficiency", value=f"{company_data.get('efficiency', 0):,}", inline=True)
        embed.add_field(name="🌱 Environment", value=f"{company_data.get('environment', 0):,}", inline=True)
        
        stock_metrics = company_data.get("stock_metrics", {})
        for stock_name, stock_value in stock_metrics.items():
            embed.add_field(name=f"📦 {stock_name}", value=f"{stock_value:,}", inline=True)

        return embed


    async def initialize_stock_log(self):
        """
        Initialize the stock log for a specific API key.
        """
        stock_log = await load_json_async(STOCK_LOG_FILE)
        if self.api_key not in stock_log:
            logger.info(f"Initializing stock log for API key: {self.api_key}")
            stock_log[self.api_key] = {"entries": []}
            await save_json_async(stock_log, STOCK_LOG_FILE)  # ✅ Correct

    async def log_daily_stock(self, stock_data):
        """Log daily stock data before trying to generate a stock graph."""

        await self.initialize_stock_log()  # Await properly

        stock_log = await load_json_async(STOCK_LOG_FILE)
        today_date = datetime.now().strftime("%Y-%m-%d")

        if self.api_key not in stock_log:
            stock_log[self.api_key] = {"entries": []}

        if not stock_data or not isinstance(stock_data, dict):
            logger.error(f"[Stock] Data is empty or invalid for {self.api_key}: {stock_data}")
            return

        if any(entry["date"] == today_date for entry in stock_log[self.api_key]["entries"]):
            logger.info(f"[Stock] Already logged for {self.api_key} today.")
            return

        new_entry = {
            "date": today_date,
            "stock_data": stock_data
        }

        stock_log[self.api_key]["entries"].append(new_entry)
        await save_json_async(stock_log, STOCK_LOG_FILE)

        logger.info(f"[Stock] Logged stock data for {self.api_key}.")


    def generate_stock_graph(self):
        """Generate a stock graph only if stock data exists."""

        data = self.prepare_graph_data(STOCK_LOG_FILE)

        if not data:
            print(f"[ERROR] No valid stock data found for graphing. Skipping stock graph generation.")
            return None

        return self.generate_graph(data, "Stock Metrics", f"./data/company_checker/Stocks/stock_graph_{self.api_key}.png")


    async def prepare_graph_data(self, file_path):
        log_data = await load_json_async(file_path).get(self.api_key, {}).get("entries", [])
        
        organized_data = {}
        for entry in log_data:
            if "date" not in entry:
                print(f"[ERROR] Missing 'date' key in entry: {entry}")
                continue  # Skip invalid entries

            date = entry["date"]

            # Ensure correct key selection for stocks vs. profits
            data = entry.get("stock_data", None) if file_path == STOCK_LOG_FILE else entry.get("profit", None)

            if not isinstance(data, dict):
                print(f"[WARNING] Skipping entry with invalid data format: {data}")
                continue  # Skip invalid entries

            for item, value in data.items():
                if item not in organized_data:
                    organized_data[item] = {"dates": [], "values": []}
                organized_data[item]["dates"].append(date)
                organized_data[item]["values"].append(value if isinstance(value, (int, float)) else 0)

        return organized_data


    def generate_graph(self, data, title, filename):
        plt.figure(figsize=(14, 8))
        data_exists = False  # Track if valid data exists

        for item, details in data.items():
            if not details["dates"]:
                print(f"[WARNING] No dates found for {item}. Skipping plot.")
                continue

            try:
                dates = [datetime.strptime(d, "%Y-%m-%d") for d in details["dates"] if d != "Unknown Date"]
                if dates:  # Ensure valid dates exist
                    plt.plot(dates, details["values"], label=item)
                    data_exists = True  # Mark that we have data
            except ValueError as e:
                print(f"[ERROR] Date formatting issue: {e}")
                continue

        if not data_exists:
            print(f"[WARNING] No valid data found for {title}. Skipping graph generation.")
            return None

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gcf().autofmt_xdate()

        if plt.gca().lines:
            plt.legend()

        plt.title(title)
        plt.savefig(filename)
        plt.close()

        print(f"[INFO] {title} graph saved as {filename}")
        return filename

    
    async def generate_graphs(self):
        #stock_url = urls.get("stock")
        #profile_url = urls.get('profile')
        stock_graph = await self.generate_stock_graph()
        profit_graph = await self.generate_profit_graph()
        return stock_graph, profit_graph


    
    async def generate_profit_graph(self):
        data = await self.prepare_graph_data(PROFIT_LOG_FILE)
        return self.generate_graph(data, "Profit Metrics", f"./data/company_checker/Profits/profit_graph_{self.api_key}.png")
