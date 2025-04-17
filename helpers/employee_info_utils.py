import os
import json
import asyncio
from datetime import datetime
from .loggers_utils import setup_logger
from .api_utils import ApiUtils
#from .file_utils_management import FileUtils
from .config_utils import ConfigUtils
#from .discord_interaction_utils import fetch_data  # Assuming this utility exists

# ---------------- CONFIGURE LOGGER ----------------
logger = setup_logger("Employee_Info")

# ---------------- EMPLOYEE MANAGEMENT ----------------


#logger = logging.getLogger("EmployeeInfo")

import logging
from helpers.api_utils import ApiUtils
#from helpers.file_utils_management import FileUtils
from tasks.utils import *
from helpers.config_utils import ConfigUtils

logger = logging.getLogger("EmployeeInfo")

class EmployeeInfo:
    EMPLOYEE_DATA_FILE = "./data/company_checker/Employee/employee_data.json"
    APPLICATIONS_DATA_FILE = "./data/company_checker/Applications/applications_data.json"
    TRAINING_DATA_FILE = "./data/company_checker/Training/training_data.json"

    def __init__(self, api_key):
        self.config_utils = ConfigUtils()
        self.api_key = api_key
        #self.company_id = company_id
        self.api_utils = ApiUtils(self.api_key) if self.api_key else None
        ensure_file_exists(self.EMPLOYEE_DATA_FILE, {})
        ensure_file_exists(self.APPLICATIONS_DATA_FILE, {})
        ensure_file_exists(self.TRAINING_DATA_FILE, {})

    async def fetch_employee_data(self):
        """
        Fetch employee data from the API and process it.
        """
        if not self.api_key:
            logger.error("API key not found for this Discord ID.")
            return {}
        
        url = self.api_utils.generate_api_urls()["employees"]
        data = self.api_utils.fetch_data(url)
        if not data or "error" in data:
            logger.error(f"Failed to fetch employee data for API key {self.api_key}.")
            return {}

        employee_data = data.get("company_employees", {})
        stored_data = await load_json_async(self.EMPLOYEE_DATA_FILE)
        stored_data[self.api_key] = employee_data
        await save_json_async(self.EMPLOYEE_DATA_FILE, stored_data)
        logger.info(f"Saved employee data for API key {self.api_key}.")
        return employee_data

    async def fetch_employee_applications(self):
        """
        Fetch employee applications from the API.
        """
        if not self.api_key:
            logger.error("API key not found for this Discord ID.")
            return {}
        
        url = self.api_utils.generate_api_urls()["applications"]
        data = self.api_utils.fetch_data(url)
        if not data or "error" in data:
            logger.error(f"Failed to fetch employee applications for API key {self.api_key}.")
            return {}
        
        applications_data = data.get("applications", {})
        stored_data = await load_json_async(self.APPLICATIONS_DATA_FILE)
        stored_data[self.api_key] = applications_data
        await save_json_async(self.APPLICATIONS_DATA_FILE, stored_data)
        logger.info(f"Saved applications data for API key {self.api_key}.")
        return applications_data
    
    async def fetch_training_data(self):
        """
        Fetch and store employee training data.
        """
        if not self.api_key:
            logger.error("API key not found for this Discord ID.")
            return {}
        
        url = self.api_utils.generate_api_urls()["training"]
        data = self.api_utils.fetch_data(url)
        if not data or "error" in data:
            logger.error(f"Failed to fetch training data for API key {self.api_key}.")
            return {}
        
        training_data = data.get("training", {})
        stored_data = await load_json_async(self.TRAINING_DATA_FILE)
        stored_data[self.api_key] = training_data
        await save_json_async(self.TRAINING_DATA_FILE, stored_data)
        logger.info(f"Saved training data for API key {self.api_key}.")
        return training_data
    
    def fetch_company_data(self):
        """
        Fetch company data from the API.
        """
        if not self.api_key:
            logger.error("API key not found for this Discord ID.")
            return {}
        
        url = self.api_utils.generate_api_urls()["profile"]
        data = self.api_utils.fetch_data(url)
        if not data or "error" in data:
            logger.error(f"Failed to fetch company data for API key {self.api_key}.")
            return {}
        return data.get("company_profile", {})
    
    def _get_api_key_from_config(self):
        """
        Retrieve the API key for the given Discord ID from the configuration file.
        """
        config_data = self.config_utils.load_json("config.json")
        api_key_data = config_data.get("api_keys", {}).get(str(self.discord_id), {})
        logger.debug(f"[Debug] API key data: {api_key_data}")

        if not api_key_data:
            logger.error(f"No API key found for Discord ID {self.discord_id}.")
            raise ValueError(f"No API key found for Discord ID {self.discord_id}.")

        return api_key_data.get("api_key")



    def load_employee_data(file_path):
        """
        Load employee data from a JSON file.

        :param file_path: Path to the employee data file.
        :return: Dictionary with employee data.
        """
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}. Returning empty data.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {file_path}: {e}")
            return {}

    def save_employee_data(file_path, data):
        """
        Save employee data to a JSON file.

        :param file_path: Path to the employee data file.
        :param data: Employee data to save.
        """
        try:
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {e}")

    def check_loyalty_milestones(employee, milestone_days=30):
        """
        Check if an employee has hit a loyalty milestone.

        :param employee: Employee data dictionary.
        :param milestone_days: Number of days to trigger milestones.
        :return: Boolean indicating if a milestone is reached.
        """
        loyalty = employee.get("days_in_company", 0)
        return loyalty > 0 and loyalty % milestone_days == 0
    
    
    def group_employees_by_position(employee_data):
        """
        Group employees by their positions.

        :param employee_data: Dictionary of employee data.
        :return: Dictionary with position as key and list of employees as value.
        """
        grouped = {}
        for emp_id, details in employee_data.items():
            position = details.get("position", "Unassigned")
            grouped.setdefault(position, []).append(details)
        return grouped

    async def generate_employee_embeds(api_key, employee_url, job_requirements):
        """
        Generate Discord embeds for employee information in position batches.

        :param api_key: API key for the company.
        :param employee_url: URL to fetch employee data.
        :param job_requirements: Dictionary of job requirements.
        :return: List of batched embeds grouped by position.
        """
        # Fetch and process data in one API call
        employee_data = await EmployeeInfo.fetch_employee_data(api_key, employee_url)
        if not employee_data:
            return []

        grouped_employees = EmployeeInfo.group_employees_by_position(employee_data)
        embeds = []

        for position, employees in grouped_employees.items():
            fields = []
            total_content_length = 0

            for details in employees:
                name = details["name"]
                stats = {
                    "Manual Labor": details["manual_labor"],
                    "Intelligence": details["intelligence"],
                    "Endurance": details["endurance"],
                }

                required_stats = job_requirements.get(position, {})
                improvements_needed = {}
                surplus_stats = {}

                for stat, required in required_stats.items():
                    current = stats.get(stat, 0)
                    if current < required:
                        improvements_needed[stat] = required - current
                    elif current > required:
                        surplus_stats[stat] = current - required

                missing_field = ", ".join(
                    [f"{stat}: -{value}" for stat, value in improvements_needed.items()]
                ) or "None"
                surplus_field = ", ".join(
                    [f"{stat}: +{value}" for stat, value in surplus_stats.items()]
                ) or "None"
                total_stats = sum(stats.values())

                field_content = (
                    f"**{name}**\n"
                    f"- Total Stats: {total_stats}\n"
                    f"- Missing Stats: {missing_field}\n"
                    f"- Surplus Stats: {surplus_field}"
                )

                # Check if adding this field exceeds Discord's character limit
                if total_content_length + len(field_content) > 2000:
                    embed = {
                        "title": f"{position} Batch",
                        "fields": fields,
                        "footer": {"text": f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
                    }
                    embeds.append(embed)
                    fields = []  # Start a new embed batch
                    total_content_length = 0

                fields.append({"name": name, "value": field_content, "inline": False})
                total_content_length += len(field_content)

            if fields:  # Add remaining fields for the position
                embed = {
                    "title": f"{position} Batch",
                    "fields": fields,
                    "footer": {"text": f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
                }
                embeds.append(embed)

        return embeds

    async def notify_loyalty_milestones(employees, milestone_days=30, notification_channel=None):
        """
        Notify about loyalty milestones for employees.

        :param employees: Dictionary of employee data.
        :param milestone_days: Number of days to trigger milestones.
        :param notification_channel: Async function to send notifications (e.g., a Discord channel).
        """
        for emp_id, employee in employees.items():
            if EmployeeInfo.check_loyalty_milestones(employee, milestone_days):
                name = employee.get("name", "Unknown")
                loyalty = employee.get("days_in_company", 0)
                message = f"🎉 {name} has reached {loyalty} days of loyalty!"
                logger.info(message)
                if notification_channel:
                    await notification_channel(message)

    async def evaluate_employee_stats(employees, job_requirements, notification_channel=None):
        """
        Evaluate employee stats against job requirements and notify if improvements are needed.

        :param employees: Dictionary of employee data.
        :param job_requirements: Dictionary of job requirements.
        :param notification_channel: Async function to send notifications.
        """
        for emp_id, employee in employees.items():
            position = employee.get("position", "Unassigned")
            stats = {
                "Manual Labor": employee.get("manual_labor", 0),
                "Intelligence": employee.get("intelligence", 0),
                "Endurance": employee.get("endurance", 0),
            }

            required_stats = job_requirements.get(position, {})
            improvements_needed = {}
            surplus_stats = {}

            for stat, required in required_stats.items():
                current = stats.get(stat, 0)
                if current < required:
                    improvements_needed[stat] = required - current
                elif current > required:
                    surplus_stats[stat] = current - required

            if improvements_needed or surplus_stats:
                name = employee.get("name", "Unknown")
                improvement_message = ", ".join(
                    [f"{stat}: -{value}" for stat, value in improvements_needed.items()]
                )
                surplus_message = ", ".join(
                    [f"{stat}: +{value}" for stat, value in surplus_stats.items()]
                )
                message = f"⚠️ {name} - Improvements: {improvement_message} | Surplus: {surplus_message}"
                logger.info(message)
                if notification_channel:
                    await notification_channel(message)

