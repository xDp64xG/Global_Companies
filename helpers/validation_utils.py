# ---------------- VALIDATION UTILITIES ----------------

def validate_api_key(api_key):
    """
    Validate that the provided API key is a non-empty string.

    :param api_key: The API key to validate.
    :return: Tuple (bool, str), where bool indicates validity and str contains an error message if invalid.
    """
    if not isinstance(api_key, str) or not api_key.strip():
        return False, "API key must be a non-empty string."
    return True, None

def validate_channel_id(channel_id):
    """
    Validate that the channel ID is a positive integer.

    :param channel_id: The channel ID to validate.
    :return: Tuple (bool, str), where bool indicates validity and str contains an error message if invalid.
    """
    if not isinstance(channel_id, int) or channel_id <= 0:
        return False, "Channel ID must be a positive integer."
    return True, None

def validate_url(url):
    """
    Validate that the provided string is a valid URL.

    :param url: The URL to validate.
    :return: Tuple (bool, str), where bool indicates validity and str contains an error message if invalid.
    """
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return False, "Invalid URL format. Must start with 'http://' or 'https://'."
    return True, None

def validate_date_format(date_str, date_format="%Y-%m-%d"):
    """
    Validate that the date string matches the specified format.

    :param date_str: The date string to validate.
    :param date_format: The expected date format (default is '%Y-%m-%d').
    :return: Tuple (bool, str), where bool indicates validity and str contains an error message if invalid.
    """
    from datetime import datetime

    try:
        datetime.strptime(date_str, date_format)
        return True, None
    except ValueError:
        return False, f"Date must be in the format {date_format}."

# Example Usage:
# valid, error = validate_api_key("my_api_key")
# if not valid:
#     print(f"Validation Error: {error}")
