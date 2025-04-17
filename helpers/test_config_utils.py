import unittest
import os
from config_utils import ConfigUtils

class TestConfigUtils(unittest.TestCase):

    def setUp(self):
        self.test_directory = "./test_data"
        os.makedirs(self.test_directory, exist_ok=True)
        self.config_utils = ConfigUtils(base_directory=self.test_directory)

        # Create sample JSON files for testing
        self.valid_filename = "valid_config.json"
        self.invalid_filename = "invalid_config.json"
        self.missing_keys_filename = "missing_keys_config.json"
        self.test_save_filename = "test_save.json"

        # Valid JSON content
        valid_content = {
            "api_keys": "test_key",
            "company_settings": {"setting1": "value1"},
            "logging": {"level": "DEBUG"}
        }
        self.config_utils.save_json(self.valid_filename, valid_content)

        # Invalid JSON content
        with open(self.config_utils._get_file_path(self.invalid_filename), "w") as file:
            file.write("{invalid_json: true,}")  # Corrupted JSON

        # Missing keys JSON content
        missing_keys_content = {
            "api_keys": "test_key",
            "logging": {"level": "DEBUG"}
        }
        self.config_utils.save_json(self.missing_keys_filename, missing_keys_content)

    def tearDown(self):
        for filename in os.listdir(self.test_directory):
            os.remove(os.path.join(self.test_directory, filename))
        os.rmdir(self.test_directory)

    def test_load_json_valid(self):
        data = self.config_utils.load_json(self.valid_filename)
        self.assertIn("api_keys", data)

    def test_load_json_invalid(self):
        data = self.config_utils.load_json(self.invalid_filename)
        self.assertEqual(data, {})

    def test_save_json(self):
        test_data = {"key": "value"}
        self.config_utils.save_json(self.test_save_filename, test_data)
        saved_data = self.config_utils.load_json(self.test_save_filename)
        self.assertEqual(saved_data, test_data)

    def test_validate_config_valid(self):
        required_keys = ["api_keys", "company_settings", "logging"]
        is_valid, missing = self.config_utils.validate_config(self.valid_filename, required_keys)
        self.assertTrue(is_valid)
        self.assertEqual(missing, [])

    def test_validate_config_missing_keys(self):
        required_keys = ["api_keys", "company_settings", "logging"]
        is_valid, missing = self.config_utils.validate_config(self.missing_keys_filename, required_keys)
        self.assertFalse(is_valid)
        self.assertIn("company_settings", missing)

    def test_update_json_key(self):
        test_key = "new_key"
        test_value = "new_value"
        self.config_utils.update_json_key(self.valid_filename, test_key, test_value)
        data = self.config_utils.load_json(self.valid_filename)
        self.assertIn(test_key, data)
        self.assertEqual(data[test_key], test_value)

    def test_get_json_key_existing(self):
        key = "api_keys"
        value = self.config_utils.get_json_key(self.valid_filename, key)
        self.assertEqual(value, "test_key")

    def test_get_json_key_missing(self):
        key = "non_existent_key"
        default_value = "default"
        value = self.config_utils.get_json_key(self.valid_filename, key, default_value)
        self.assertEqual(value, default_value)

if __name__ == "__main__":
    unittest.main()
