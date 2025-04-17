# commands.py
import discord
from discord.ext import commands
#from tasks.news_applications_training import TaskHandler
from helpers.news_management_utils import NewsManagementUtils
from helpers.employee_info_utils import EmployeeInfo
from helpers.training_utils import TrainingUtils
from helpers.company_utils import CompanyUtils
#from helpers.applications_management_utils import ApplicationsManagementUtils
from tasks.news_applications_training import initialize_tasks
from helpers.config_utils import ConfigUtils
from helpers.api_utils import ApiUtils
from helpers.loggers_utils import setup_logger
from tasks.utils import *
logger = setup_logger("CommandsLogger")
import os

config_utils = ConfigUtils(base_directory="./data/config/")
running_tasks = {}

def register_commands(bot):
    print(f'[Starting Commands]')

    @bot.command(name="list_employees")
    async def list_employees(ctx):
        """Lists all employees for the company."""
        
        config = await load_json_async(CONFIG_FILE)
        api_keys = config.get("api_keys", {})
        
        employee_list = []
        
        for api_key in api_keys.keys():
            company_utils = CompanyUtils(api_key)
            employee_data = company_utils.fetch_employee_data()
            
            for employee in employee_data.keys():
                employee_list.append(employee)

        employee_message = "**Company Employees:**\n" + "\n".join(employee_list)
        await ctx.send(employee_message)


    @bot.command(name="start")
    async def start_all_tasks(ctx):
        """
        Start all tasks for all API keys found in the config file.
        """
        await ctx.channel.send("Starting all tasks...")
        await initialize_tasks(bot)


    """@bot.command(name="dead")
    async def start_all_tasks_slash(ctx):
        
        #Start all tasks for all API keys in the config file.
        
        config_utils = ConfigUtils()
        api_keys = config_utils.get_json_key("config.json", "api_keys", {})
        

        if not api_keys:
            await ctx.send("No API keys found in the configuration file.")
            return

        for discord_id, key_config in api_keys.items():
            print(f"Debug: {discord_id}")

            
            api_key = config_utils.get_api_key_by_discord_id(discord_id)


            #api_key = ConfigUtils.get_api_key_by_discord_id(self=None, discord_id=discord_id)
            print(f"Debug: {api_key}")
            
            if api_key not in running_tasks:
                running_tasks[api_key] = {}
            urls = ApiUtils(api_key).generate_api_urls()

            # Start news task
            if "news" not in running_tasks[api_key]:
               
                manager = NewsManagementUtils(api_key)
                TaskHandler.news_task.change_interval(hours=1)
                TaskHandler.news_task.start(api_key, manager)
                running_tasks[api_key]["news"] = TaskHandler.news_task
                await ctx.send(f"Started news task for API key {api_key}.")

            # Start applications task
            if "applications" not in running_tasks[api_key]:

                profile_data = ApiUtils(api_key).fetch_data(urls['profile'])
                print(f"[DEBUG] Profile data: {profile_data}")
                profile_id = profile_data.get("company", {}).get("company_id", "")
                manager = ApplicationsManagementUtils(api_key)
                TaskHandler.applications_task.change_interval(minutes=5)
                TaskHandler.applications_task.start(api_key, manager)
                running_tasks[api_key]["applications"] = TaskHandler.applications_task
                await ctx.send(f"Started applications task for API key {api_key}.")

            # Start training task
            if "training" not in running_tasks[api_key]:
                manager = TrainingUtils(api_key)
                TaskHandler.training_task.change_interval(hours=1)
                TaskHandler.training_task.start(api_key, manager)
                running_tasks[api_key]["training"] = TaskHandler.training_task
                await ctx.send(f"Started training task for API key {api_key}.")

            # Start company task
            if "company" not in running_tasks[api_key]:
                manager = CompanyUtils(api_key)
                TaskHandler.company_task.change_interval(hours=1)
                TaskHandler.company_task.start(api_key, manager)
                running_tasks[api_key]["company"] = TaskHandler.company_task
                await ctx.send(f"Started company task for API key {api_key}.")
            
            #Start Employee Tasks
            if "employee" not in running_tasks[api_key]:
                manager = EmployeeInfo(api_key)
                TaskHandler.employee_task.change_interval(minutes=5)
                TaskHandler.employee_task.start(api_key, manager)
                running_tasks[api_key]["employees"] = TaskHandler.employee_task

        await ctx.send("All tasks started for all API keys.")"""

    @bot.command(name="stop")
    async def stop_all_tasks(ctx):
        """
        Stop all tasks for all API keys.
        """
        for api_key, tasks in running_tasks.items():
            for name, task in tasks.items():
                if task.is_running():
                    task.cancel()
            await ctx.send(f"Tasks stopped for API key {api_key}.")
        running_tasks.clear()
        await ctx.send("All tasks stopped for all API keys.")

    @bot.command(name="update_config")
    async def update_config(ctx, key: str, value: str):
        """
        Update the bot configuration.
        """
        config_utils.update_json_key("config.json", key, value)
        await ctx.send(f"Updated config key `{key}` to `{value}`.")

    @bot.command(name="list_tasks")
    async def list_tasks(ctx):
        """
        List all running tasks for each API key.
        """
        if not running_tasks:
            await ctx.send("No tasks are currently running.")
            return

        message = "Running Tasks:\n"
        for api_key, tasks in running_tasks.items():
            task_list = ", ".join(tasks.keys())
            message += f"- {api_key}: {task_list}\n"
        await ctx.send(message)

