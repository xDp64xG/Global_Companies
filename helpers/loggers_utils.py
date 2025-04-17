import logging

# ---------------- CONFIGURE LOGGING ----------------

def setup_logger(name, log_file="app_debug.log", level=logging.DEBUG):
    """
    Set up a logger with a specific name and file.

    :param name: Name of the logger.
    :param log_file: File to write logs to.
    :param level: Logging level (e.g., DEBUG, INFO, WARNING).
    :return: Configured logger instance.
    """
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Set up logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Example Usage:
# logger = setup_logger("API_Interaction")
# logger.info("Logger configured successfully.")
