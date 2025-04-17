import json
from tasks.utils import load_json, save_json, get_json_key, save_json_key, validate_json_structure

TEST_JSON_PATH = "test_json.json"
TEST_JSON_DATA = {"key1": "value1", "key2": {"nested_key": "nested_value"}}

def test_json_handling():
    print("🔍 Running JSON Handling Tests...")

    # Test saving JSON
    try:
        save_json(TEST_JSON_DATA, TEST_JSON_PATH)
        print("✅ save_json() passed.")
    except Exception as e:
        print(f"❌ save_json() failed: {e}")

    # Test loading JSON
    try:
        loaded_data = load_json(TEST_JSON_PATH)
        assert isinstance(loaded_data, dict), "Loaded JSON is not a dictionary."
        print("✅ load_json() passed.")
    except Exception as e:
        print(f"❌ load_json() failed: {e}")

    # Test getting a JSON key
    try:
        test_value = get_json_key(TEST_JSON_PATH, "key2", {})
        assert isinstance(test_value, dict), "get_json_key() returned incorrect type."
        print("✅ get_json_key() passed.")
    except Exception as e:
        print(f"❌ get_json_key() failed: {e}")

    # Test validating JSON structure
    try:
        is_valid = validate_json_structure(loaded_data, {"key1": str, "key2": dict})
        assert is_valid, "JSON structure validation failed."
        print("✅ validate_json_structure() passed.")
    except Exception as e:
        print(f"❌ validate_json_structure() failed: {e}")

if __name__ == "__main__":
    test_json_handling()
