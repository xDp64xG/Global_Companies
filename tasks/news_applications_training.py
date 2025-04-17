import asyncio
import json
import os
#from .utils import load_json, save_json, generate_api_urls
from .company_task import post_company_update, monitor_company_funds
from .employee_task import update_employee_stats
from .applications_task import check_applications
from .news_task import process_company_news, scheduled_news_task
from discord.ext import tasks
from .training_task import start_training_task
from .utils import *

CONFIG_FILE = "./data/config/config.json"

async def ensure_json_file(file_path, default_data={}):
    """Ensure a JSON file exists, creating it with default data if missing."""
    try:
        if not os.path.exists(file_path):
            await save_json_async(default_data, file_path)
    except Exception as e:
        print(f"[ERROR] Failed to create {file_path}: {e}")


async def initialize_tasks(bot):
    """Initialize tasks based on the latest configuration, ensuring all API keys have active tasks."""
    config = await load_json_async(CONFIG_FILE)
    api_keys = config.get("api_keys", {})

    for user_id, user_config in api_keys.items():
        api_key = user_config.get("api_key")
        if not api_key:
            continue

        print(f"[INFO] Starting tasks for API key: {api_key}")

        company_config = user_config.get("company", {})
        employees_config = user_config.get("employees", {})
        applications_config = user_config.get("applications", {})
        news_config = user_config.get("news", {})
        training_config = user_config.get("training", {})

        urls = generate_api_urls(api_key)
        print(f"URLS: {urls}")

        # Ensure each API key has its own independent task
        if not post_company_update.is_running():
            post_company_update.start(bot, company_config, api_key, urls)

        if not update_employee_stats.is_running():
            update_employee_stats.start(bot, employees_config, api_key, urls.get("employees"), urls.get("profile"))

        if not check_applications.is_running():
            check_applications.start(bot, applications_config, api_key, urls.get("applications"))

        if not scheduled_news_task.is_running():
            scheduled_news_task.start(bot, api_key, news_config, urls)

        if not monitor_company_funds.is_running():
            monitor_company_funds.start(bot, api_key, news_config, urls.get("detailed"))


async def initialize_tasks2(bot):
    """Initialize tasks based on the latest configuration, ensuring they don't restart unnecessarily."""
    config = await load_json_async(CONFIG_FILE)
    api_keys = config.get("api_keys", {})
    
    for user_id, user_config in api_keys.items():
        api_key = user_config.get("api_key")
        if not api_key:
            continue
        
        print(f"[INFO] Starting tasks for API key: {api_key}")
        
        company_config = user_config.get("company", {})
        employees_config = user_config.get("employees", {})
        applications_config = user_config.get("applications", {})
        news_config = user_config.get("news", {})

        urls = generate_api_urls(api_key)
        print(f"URLS: {urls}")
        profile_url = urls.get("profile")
        detailed_url = urls.get("detailed")
        stock_url = urls.get("stock")
        employees_url = urls.get("employees")
        applications_url = urls.get("applications")
        news_url = urls.get("news")

        
        if not post_company_update.is_running():
            post_company_update.start(bot, company_config, api_key, urls)
        
        if not update_employee_stats.is_running():
            update_employee_stats.start(bot, employees_config, api_key, employees_url, detailed_url)
        
        if not check_applications.is_running():
            check_applications.start(bot, applications_config, api_key, applications_url)
        
        if not scheduled_news_task.is_running():
            scheduled_news_task.start(bot, api_key, news_config, urls)
        
        if not monitor_company_funds.is_running():
            monitor_company_funds.start(bot, api_key, news_config, detailed_url)
        
        """if not start_training_task.is_running():
            start_training_task.start(api_key)"""
    
@tasks.loop(minutes=10)
async def refresh_tasks():
    """Refresh tasks dynamically based on config updates."""
    print("[INFO] Refreshing tasks to match latest config.json")
    await initialize_tasks()
    
async def main():
    """Main entry point to initialize tasks, ensuring missing JSON files are created."""
    print("[INFO] Initializing all tasks...")
    
    await ensure_json_file("company_checker/Applications/applications_seen.json", {})
    await ensure_json_file("company_checker/News/news_log.json", {})
    await ensure_json_file("company_checker/Employee/employee_data.json", {})
    await ensure_json_file("data/config/config.json", {"api_keys": {}})
    
    await initialize_tasks()
    refresh_tasks.start()

if __name__ == "__main__":
    asyncio.run(main())