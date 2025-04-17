import discord
from datetime import datetime
from discord.ext import tasks
#from helpers.discord_utils import send_or_edit_message
#from helpers.discord_utils import DiscordUtils
from .utils import send_or_edit_message

from helpers.employee_info_utils import EmployeeInfo
from helpers.training_utils import TrainingUtils
#from .utils import *
from helpers.config_utils import ConfigUtils

config_utils = ConfigUtils(base_directory="./data")

COMPANY_POSITIONS_FILE = "./data/company_information/company_data.json"

async def generate_training_report(api_key):
    """
    Generate a detailed training report for employees.

    :param api_key: API key for the company.
    :return: A list of embeds for the training report and a dictionary of training needs.
    """
    training_utils = TrainingUtils()
    training_utils.initialize_training_data(api_key)
    employees = EmployeeInfo.fetch_employee_data(api_key)
    #employees = fetch_company_data(api_key, "employees")  # Fetch employee data from the API
    training_needs = training_utils.calculate_training_needs(api_key, employees)

    training_report_embeds = []
    for emp_id, needs in training_needs.items():
        employee = employees.get(emp_id, {})
        name = employee.get("name", "Unknown")
        position = employee.get("position", "Unassigned")
        embed = discord.Embed(
            title=f"Training Report: {name}",
            description=f"Position: {position}",
            color=discord.Color.orange()
        )
        for stat, deficit in needs.items():
            embed.add_field(name=stat, value=f"Needs: {deficit}", inline=False)
        embed.set_footer(text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        training_report_embeds.append(embed)

    return training_report_embeds, training_needs


@tasks.loop(hours=1)
async def training_task(api_key, bot):
    """
    Task to generate and post training reports.
    """
    training_report, training_needs = await generate_training_report(api_key)

    channel_id = await config_utils.get_json_key("config.json", f"api_keys.{api_key}.training.channel_id")
    if channel_id and training_report:
        await send_or_edit_message(bot, api_key, "training", channel_id, training_report)

        # Update training progress after posting
        training_utils = TrainingUtils()
        for emp_id, needs in training_needs.items():
            training_utils.update_training_progress(api_key, emp_id, needs)

async def start_training_task(bot, api_key, running_tasks):
    """
    Start the training task for a specific API key.
    """
    if "training" not in running_tasks:
        running_tasks["training"] = {}
    if api_key not in running_tasks["training"]:
        training_task_instance = training_task(api_key, bot)
        running_tasks["training"][api_key] = training_task_instance
        training_task_instance.start()
        print(f"Started training task for API key {api_key}.")


async def stop_training_task(api_key, running_tasks):
    """
    Stop the training task for a specific API key.
    """
    task = running_tasks.get("training", {}).pop(api_key, None)
    if task:
        task.cancel()
        print(f"Stopped training task for API key {api_key}.")

