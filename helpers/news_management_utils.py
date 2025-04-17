
from datetime import datetime
from .loggers_utils import setup_logger
from .api_utils import ApiUtils
#from .file_utils_management import FileUtils

from tasks.utils import *

logger = setup_logger("NewsManagement")

class NewsManagementUtils:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_utils = ApiUtils(api_key)
        self.news_data_dir = "./data/company_checker/News/news_log.json"
        ensure_file_exists(self.news_data_dir, "news_data")

    def fetch_company_news(self):
        try:
            url = self.api_utils.generate_api_urls()["news"]
            data = self.api_utils.fetch_data(url)
            return data.get("news", {})
        except Exception as e:
            logger.exception(f"Failed to fetch company news for API key {self.api_key}: {e}")
            return {}

    def filter_relevant_news(self, news_data):
        relevant_news = []
        for news_id, details in news_data.items():
            news_text = details.get("news", "").lower()
            timestamp = details.get("timestamp", 0)
            if "rating" in news_text or "has been trained" in news_text:
                relevant_news.append({
                    "title": "Relevant News",
                    "description": news_text.capitalize(),
                    "timestamp": datetime.utcfromtimestamp(timestamp)
                })
        logger.info(f"Filtered {len(relevant_news)} relevant news items.")
        return relevant_news
