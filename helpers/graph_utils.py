import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from .file_utils_management import FileUtils
import logging

logger = logging.getLogger("GraphUtils")

STOCK_LOG_FILE = "/data/company_checker/Stocks/daily_stock_log.json"

class GraphUtils:
    def __init__(self, api_key):
        self.api_key = api_key

    def prepare_graph_data(self):
        log_data = FileUtils.load_json(STOCK_LOG_FILE).get(self.api_key, {}).get("entries", [])
        organized_data = {}
        for entry in log_data:
            date = entry["date"]
            stock_data = entry.get("stock_data", {})
            for item, details in stock_data.items():
                if item not in organized_data:
                    organized_data[item] = {"dates": [], "values": []}
                organized_data[item]["dates"].append(date)
                organized_data[item]["values"].append(details.get("sold_amount", 0))
        return organized_data

    def generate_stock_graph(self):
        data = self.prepare_graph_data()
        plt.figure(figsize=(14, 8))
        for item, details in data.items():
            dates = [datetime.strptime(d, "%Y-%m-%d") for d in details["dates"]]
            plt.plot(dates, details["values"], label=item)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gcf().autofmt_xdate()
        plt.legend()
        filename = f"/data/graphs/stock_graph_{self.api_key}.png"
        plt.savefig(filename)
        plt.close()
        logger.info(f"Stock graph saved as {filename}")
        return filename
    
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from .file_utils_management import FileUtils
import logging

logger = logging.getLogger("GraphUtils")

STOCK_LOG_FILE = "/data/company_checker/Stocks/daily_stock_log.json"

class GraphUtils:
    def __init__(self, api_key):
        self.api_key = api_key

    def prepare_graph_data(self):
        log_data = FileUtils.load_json(STOCK_LOG_FILE).get(self.api_key, {}).get("entries", [])
        organized_data = {}
        for entry in log_data:
            date = entry["date"]
            stock_data = entry.get("stock_data", {})
            for item, details in stock_data.items():
                if item not in organized_data:
                    organized_data[item] = {"dates": [], "values": []}
                organized_data[item]["dates"].append(date)
                organized_data[item]["values"].append(details.get("sold_amount", 0))
        return organized_data

    def generate_stock_graph(self):
        data = self.prepare_graph_data()
        plt.figure(figsize=(14, 8))
        for item, details in data.items():
            dates = [datetime.strptime(d, "%Y-%m-%d") for d in details["dates"]]
            plt.plot(dates, details["values"], label=item)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gcf().autofmt_xdate()
        plt.legend()
        filename = f"/data/graphs/stock_graph_{self.api_key}.png"
        plt.savefig(filename)
        plt.close()
        logger.info(f"Stock graph saved as {filename}")
        return filename



import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from .file_utils_management import FileUtils
import logging

logger = logging.getLogger("GraphUtils")

CURRENT_STOCK_FILE = "/data/company_checker/current_stock.json"
STOCK_LOG_FILE = "/data/company_checker/Stocks/daily_stock_log.json"

class GraphUtils:
    def __init__(self, api_key):
        self.api_key = api_key

    def prepare_graph_data(self, file_path):
        log_data = FileUtils.load_json(file_path).get(self.api_key, {}).get("entries", [])
        organized_data = {}
        for entry in log_data:
            date = entry["date"]
            data = entry.get("stock_data", {}) if file_path == STOCK_LOG_FILE else entry.get("profit_data", {})
            for item, details in data.items():
                if item not in organized_data:
                    organized_data[item] = {"dates": [], "values": []}
                organized_data[item]["dates"].append(date)
                organized_data[item]["values"].append(details.get("value", 0))
        return organized_data

    def generate_graph(self, data, title, filename):
        plt.figure(figsize=(14, 8))
        for item, details in data.items():
            dates = [datetime.strptime(d, "%Y-%m-%d") for d in details["dates"]]
            plt.plot(dates, details["values"], label=item)

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gcf().autofmt_xdate()
        plt.title(title)
        plt.legend()
        plt.savefig(filename)
        plt.close()
        logger.info(f"{title} graph saved as {filename}")
        return filename

    def generate_stock_graph(self):
        data = self.prepare_graph_data(STOCK_LOG_FILE)
        return self.generate_graph(data, "Stock Metrics", f"/data/company_checker/Stocks/stock_graph_{self.api_key}.png")
