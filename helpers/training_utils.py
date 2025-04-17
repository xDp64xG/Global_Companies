
from datetime import datetime
from .loggers_utils import setup_logger
#from .file_utils_management import FileUtils
from tasks.utils import *
from .config_utils import ConfigUtils

logger = setup_logger("TrainingUtils")

TRAINING_FILE = "./data/company_checker/Training/training_data.json"
POSITIONS_FILE = "./data/company_information/company_data.json"

class TrainingUtils:
    async def __init__(self, api_key):
        self.api_key = api_key
        ensure_file_exists(TRAINING_FILE, "training_data")

    async def initialize_training_data(self):
        self.training_file = TRAINING_FILE
        training_data = await load_json_async(self.training_file) or {}

        if self.api_key not in training_data:
            training_data[self.api_key] = {}

        await save_json_async(self.training_file, training_data)

    async def calculate_training_needs(self, employees):
        training_needs = {}
        positions = await load_json_async(POSITIONS_FILE)

        for emp_id, details in employees.items():
            position = details.get("position", "Unassigned")
            stats = {
                "Manual Labor": details.get("manual_labor", 0),
                "Intelligence": details.get("intelligence", 0),
                "Endurance": details.get("endurance", 0),
            }
            required_stats = positions.get(position, {})
            for stat, required_value in required_stats.items():
                current_value = stats.get(stat, 0)
                if current_value < required_value:
                    training_needs.setdefault(emp_id, {}).update({
                        stat: required_value - current_value
                    })
        logger.info(f"Training needs calculated for API key: {self.api_key}")
        return training_needs

    async def update_training_progress(self, api_key, emp_id, stats_trained):
        training_data = await load_json_async(TRAINING_FILE)
        api_training = training_data.setdefault(api_key, {})
        emp_training = api_training.setdefault(emp_id, {})

        for stat, value in stats_trained.items():
            emp_training[stat] = emp_training.get(stat, 0) + value

        await save_json_async(TRAINING_FILE, training_data)
        logger.info(f"Training progress updated for employee {emp_id} under API key {api_key}.")
