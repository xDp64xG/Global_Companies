import requests
import time
import logging

logger = logging.getLogger("API_Interaction")

class ApiUtils:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = f"https://api.torn.com/company/?key={api_key}&comment=Project_Glo_Co_Bot"

    def generate_api_urls(self):
        #self.base_url = f"https://api.torn.com/company/?key={api_key}&comment=Project_Glo_Co_Bot"
        return {
            "profile": f"{self.base_url}&selections=profile",
            "stock": f"{self.base_url}&selections=stock",
            "employees": f"{self.base_url}&selections=employees",
            "detailed": f"{self.base_url}&selections=detailed",
            "applications": f"{self.base_url}&selections=applications",
            "news": f"{self.base_url}&selections=news",
        }

    def fetch_data(self, url, max_retries=3, delay=1):
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
