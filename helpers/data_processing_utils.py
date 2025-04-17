import json
from .loggers_utils import setup_logger

logger = setup_logger("DataProcessing")

def filter_data(data, criteria):
    """
    Filter data based on given criteria.
    :param data: The data to filter (list of dicts or dict).
    :param criteria: A lambda or callable to evaluate filtering condition.
    :return: Filtered data.
    """
    try:
        logger.debug("Starting data filtering.")
        if isinstance(data, list):
            filtered = [item for item in data if criteria(item)]
        elif isinstance(data, dict):
            filtered = {k: v for k, v in data.items() if criteria(v)}
        else:
            logger.error("Invalid data format for filtering.")
            return None
        logger.info(f"Filtered data size: {len(filtered)}")
        return filtered
    except Exception as e:
        logger.exception("Error during data filtering.")
        return None

def aggregate_data(data, key, operation):
    """
    Aggregate data based on a key and operation.
    :param data: List of dictionaries.
    :param key: Key to aggregate on.
    :param operation: Aggregation operation ('sum', 'max', 'min', etc.).
    :return: Aggregated result or None if an error occurs.
    """
    try:
        logger.debug(f"Aggregating data with operation: {operation}")
        if operation == 'sum':
            return sum(item.get(key, 0) for item in data)
        elif operation == 'max':
            return max(item.get(key, float('-inf')) for item in data)
        elif operation == 'min':
            return min(item.get(key, float('inf')) for item in data)
        else:
            logger.error(f"Unsupported operation: {operation}")
            return None
    except Exception as e:
        logger.exception("Error during data aggregation.")
        return None

def transform_data(data, transformer):
    """
    Transform data using a given transformer function.
    :param data: List or dict of data.
    :param transformer: Callable to apply to each item.
    :return: Transformed data.
    """
    try:
        logger.debug("Transforming data.")
        if isinstance(data, list):
            return [transformer(item) for item in data]
        elif isinstance(data, dict):
            return {k: transformer(v) for k, v in data.items()}
        else:
            logger.error("Unsupported data format for transformation.")
            return None
    except Exception as e:
        logger.exception("Error during data transformation.")
        return None
