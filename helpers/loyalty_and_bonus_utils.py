# loyalty_bonuses_utils.py

from loggers_utils import setup_logger
from file_utils import load_json, save_json

LOYALTY_FILE = "loyalty_tracking.json"
logger = setup_logger("LoyaltyBonuses")

def track_loyalty(api_key, employee_id, days):
    loyalty_data = load_json(LOYALTY_FILE).get(api_key, {})
    milestones = loyalty_data.setdefault(employee_id, [])
    if days in milestones:
        logger.info(f"Loyalty milestone {days} already tracked for {employee_id}.")
        return False
    milestones.append(days)
    save_json(LOYALTY_FILE, {api_key: loyalty_data})
    logger.info(f"Loyalty milestone {days} tracked for {employee_id}.")
    return True
