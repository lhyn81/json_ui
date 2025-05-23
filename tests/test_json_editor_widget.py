import unittest
import sys
import os
import json

# Adjust path to import JsonEditorWidget from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Conditional import for QApplication for testing environments
QApplication = None
try:
    from PySide6.QtWidgets import QApplication
except ImportError:
    print("PySide6.QtWidgets.QApplication not found, running tests without it where possible.")

from json_editor_widget import JsonEditorWidget


# Global app instance, created only if QApplication is available and not already running
app_instance = None
if QApplication:
    try:
        app_instance = QApplication.instance()
        if not app_instance:
            app_instance = QApplication(sys.argv if hasattr(sys, 'argv') else [])
    except Exception as e:
        print(f"Failed to create QApplication for tests: {e}")


class TestJsonEditorWidgetDataLogic(unittest.TestCase):

    def setUp(self):
        self.widget = JsonEditorWidget()

    def test_parse_value_from_display(self):
        print("\nRunning: test_parse_value_from_display")
        parse = self.widget._parse_value_from_display
        self.assertEqual(parse("null"), None, "Parsing 'null'")
        self.assertEqual(parse("true"), True, "Parsing 'true'")
        self.assertEqual(parse("false"), False, "Parsing 'false'")
        self.assertEqual(parse("123"), 123, "Parsing integer '123'")
        self.assertEqual(parse("-456"), -456, "Parsing negative integer '-456'")
        self.assertEqual(parse("3.14"), 3.14, "Parsing float '3.14'")
        self.assertEqual(parse("-0.5"), -0.5, "Parsing negative float '-0.5'")
        self.assertEqual(parse("Hello"), "Hello", "Parsing string 'Hello'")
        self.assertEqual(parse(""), None, "Parsing empty string to None") # Changed from "" to None as per typical JSON editor behavior

    def test_format_value_for_display(self):
        print("\nRunning: test_format_value_for_display")
        format_val = self.widget._format_value_for_display
        self.assertEqual(format_val(None), "null", "Formatting None")
        self.assertEqual(format_val(True), "true", "Formatting True")
        self.assertEqual(format_val(False), "false", "Formatting False")
        self.assertEqual(format_val(123), "123", "Formatting integer 123")
        self.assertEqual(format_val(3.14), "3.14", "Formatting float 3.14")
        self.assertEqual(format_val("Hello"), "Hello", "Formatting string 'Hello'")

    def _test_load_and_to_dict_conversion(self, test_data, test_name):
        print(f"\nRunning: {test_name}")
        self.widget.load_json_from_dict(test_data)
        converted_data = self.widget.to_dict()
        self.assertEqual(converted_data, test_data, f"Data mismatch for {test_name}")

    def test_simple_dict_conversion(self):
        data = {"key1": "value1", "key2": 100, "key3": True, "key4": None}
        self._test_load_and_to_dict_conversion(data, "test_simple_dict_conversion")

    def test_nested_dict_conversion(self):
        data = {
            "name": "John Doe", "age": 30,
            "address": {"street": "123 Main St", "city": "Anytown"}
        }
        self._test_load_and_to_dict_conversion(data, "test_nested_dict_conversion")

    def test_list_conversion(self):
        data = {"items": [1, "two", False, None, {"nested_key": "nested_val"}]}
        self._test_load_and_to_dict_conversion(data, "test_list_conversion")

    def test_complex_structure_conversion(self):
        # Using example2.json content for a comprehensive test
        complex_data = {
            "projectName": "Data Visualizer", "version": 1.2, "isActive": True,
            "settings": {
                "theme": "dark",
                "notifications": {"email": True, "sms": False},
                "ports": [8080, 8081, 9000],
                "allowed_hosts": []
            },
            "contributors": [
                {"id": 101, "name": "Alice", "roles": ["developer", "reviewer"], "contact": None},
                {"id": 102, "name": "Bob", "roles": ["designer"], "contact": {"email": "bob@example.com"}}
            ],
            "emptyObject": {}, "emptyList": [],
            "matrix": [[1,2,3],[4,5,6]],
            "description": "A sample configuration file with various data types and structures."
        }
        self._test_load_and_to_dict_conversion(complex_data, "test_complex_structure_conversion")

    def test_root_list_conversion(self):
        data = [{"item1": "value1"}, {"item2": 200}, 3, "four", None, True, [], {}]
        self._test_load_and_to_dict_conversion(data, "test_root_list_conversion")

    def test_empty_root_object(self):
        data = {}
        self._test_load_and_to_dict_conversion(data, "test_empty_root_object")

    def test_empty_root_list(self):
        data = []
        self._test_load_and_to_dict_conversion(data, "test_empty_root_list")

    def test_load_json_from_string_valid(self):
        print("\nRunning: test_load_json_from_string_valid")
        json_string = '{"name": "Test", "value": 123}'
        expected_dict = {"name": "Test", "value": 123}
        # Mock QMessageBox to prevent UI pop-ups during tests
        original_qmessagebox = JsonEditorWidget.QMessageBox if hasattr(JsonEditorWidget, 'QMessageBox') else None
        JsonEditorWidget.QMessageBox = unittest.mock.MagicMock()
        
        try:
            self.assertTrue(self.widget.load_json_from_string(json_string))
            self.assertEqual(self.widget.to_dict(), expected_dict)
        finally:
            if original_qmessagebox:
                 JsonEditorWidget.QMessageBox = original_qmessagebox # Restore
            elif hasattr(JsonEditorWidget, 'QMessageBox'): # Clean up if we added it
                 del JsonEditorWidget.QMessageBox


    def test_load_json_from_string_invalid(self):
        print("\nRunning: test_load_json_from_string_invalid")
        json_string = '{"name": "Test", "value": 123,}' # Invalid trailing comma
        original_qmessagebox = JsonEditorWidget.QMessageBox if hasattr(JsonEditorWidget, 'QMessageBox') else None
        JsonEditorWidget.QMessageBox = unittest.mock.MagicMock()
        
        try:
            self.assertFalse(self.widget.load_json_from_string(json_string))
            # Optionally, check that QMessageBox.critical was called
            JsonEditorWidget.QMessageBox.critical.assert_called_once()
        finally:
            if original_qmessagebox:
                JsonEditorWidget.QMessageBox = original_qmessagebox
            elif hasattr(JsonEditorWidget, 'QMessageBox'):
                 del JsonEditorWidget.QMessageBox

    # --- Tests for Consistency Check Logic ---

    def _perform_consistency_check_logic(self, list_of_objects_data):
        # Helper function to simulate the core logic of handle_consistency_check
        # list_of_objects_data should be a list of dictionaries,
        # e.g., [{"item_name": "Obj0", "data": {"a":1, "b":2}}, {"item_name": "Obj1", "data": {"a":1, "c":3}}]
        
        if not list_of_objects_data or len(list_of_objects_data) < 2:
            return True, [] # Consistent if less than 2 objects

        first_object_keys = set(list_of_objects_data[0]["data"].keys())
        report_messages = []
        consistent = True

        for i in range(1, len(list_of_objects_data)):
            current_obj_item_name = list_of_objects_data[i]["item_name"]
            current_obj_keys = set(list_of_objects_data[i]["data"].keys())

            missing_keys = sorted(list(first_object_keys - current_obj_keys))
            extra_keys = sorted(list(current_obj_keys - first_object_keys))

            if missing_keys:
                consistent = False
                report_messages.append(f"{current_obj_item_name} missing: {', '.join(missing_keys)}")
            if extra_keys:
                consistent = False
                report_messages.append(f"{current_obj_item_name} extra: {', '.join(extra_keys)}")
        return consistent, report_messages, sorted(list(first_object_keys))


    def test_consistency_check_consistent_objects(self):
        print("\nRunning: test_consistency_check_consistent_objects")
        objects = [
            {"item_name": "Obj0", "data": {"name": "Alice", "age": 30, "city": "New York"}},
            {"item_name": "Obj1", "data": {"name": "Bob", "age": 24, "city": "London"}},
            {"item_name": "Obj2", "data": {"name": "Charlie", "age": 35, "city": "Paris"}}
        ]
        consistent, messages, _ = self._perform_consistency_check_logic(objects)
        self.assertTrue(consistent, "Objects should be consistent.")
        self.assertEqual(len(messages), 0, "There should be no inconsistency messages.")

    def test_consistency_check_missing_keys(self):
        print("\nRunning: test_consistency_check_missing_keys")
        objects = [
            {"item_name": "Obj0", "data": {"name": "Alice", "age": 30, "city": "New York"}},
            {"item_name": "Obj1", "data": {"name": "Bob", "city": "London"}}, # Missing 'age'
        ]
        consistent, messages, ref_keys = self._perform_consistency_check_logic(objects)
        self.assertFalse(consistent, "Objects should be inconsistent.")
        self.assertIn("Obj1 missing: age", messages[0])
        self.assertEqual(ref_keys, ["age", "city", "name"])


    def test_consistency_check_extra_keys(self):
        print("\nRunning: test_consistency_check_extra_keys")
        objects = [
            {"item_name": "Obj0", "data": {"name": "Alice", "age": 30}},
            {"item_name": "Obj1", "data": {"name": "Bob", "age": 24, "city": "London"}}, # Extra 'city'
        ]
        consistent, messages, ref_keys = self._perform_consistency_check_logic(objects)
        self.assertFalse(consistent, "Objects should be inconsistent.")
        self.assertIn("Obj1 extra: city", messages[0])
        self.assertEqual(ref_keys, ["age", "name"])

    def test_consistency_check_mixed_issues(self):
        print("\nRunning: test_consistency_check_mixed_issues")
        objects = [
            {"item_name": "Obj0", "data": {"id":1, "name": "Alice", "age": 30, "country": "USA"}},
            {"item_name": "Obj1", "data": {"id":2, "name": "Bob", "city": "London"}}, # Missing age, country. Extra city.
            {"item_name": "Obj2", "data": {"id":3, "name": "Charlie", "age": 35, "status": "active"}} # Missing country. Extra status.
        ]
        consistent, messages, ref_keys = self._perform_consistency_check_logic(objects)
        self.assertFalse(consistent, "Objects should be inconsistent.")
        self.assertEqual(ref_keys, ["age", "country", "id", "name"])
        
        # Check messages - order might vary if an object has both missing and extra,
        # but for a single object the message should be predictable based on sorted keys.
        # Obj1: missing age, country; extra city
        self.assertTrue(any("Obj1 missing: age, country" in m or "Obj1 missing: country, age" in m for m in messages))
        self.assertTrue(any("Obj1 extra: city" in m for m in messages))
        
        # Obj2: missing country; extra status
        self.assertTrue(any("Obj2 missing: country" in m for m in messages))
        self.assertTrue(any("Obj2 extra: status" in m for m in messages))


    def test_consistency_check_empty_and_one_object(self):
        print("\nRunning: test_consistency_check_empty_and_one_object")
        objects_empty = []
        consistent, messages = self._perform_consistency_check_logic(objects_empty)
        self.assertTrue(consistent)
        self.assertEqual(len(messages), 0)

        objects_one = [{"item_name": "Obj0", "data": {"name": "Alice"}}]
        consistent, messages = self._perform_consistency_check_logic(objects_one)
        self.assertTrue(consistent)
        self.assertEqual(len(messages), 0)

    def test_consistency_check_identical_objects(self):
        print("\nRunning: test_consistency_check_identical_objects")
        objects = [
            {"item_name": "Obj0", "data": {"key1": "val1", "key2": "val2"}},
            {"item_name": "Obj1", "data": {"key1": "val1", "key2": "val2"}},
        ]
        consistent, messages, _ = self._perform_consistency_check_logic(objects)
        self.assertTrue(consistent)
        self.assertEqual(len(messages), 0)

    def test_consistency_check_different_order_same_keys(self):
        print("\nRunning: test_consistency_check_different_order_same_keys")
        objects = [
            {"item_name": "Obj0", "data": {"key1": "val1", "key2": "val2"}},
            {"item_name": "Obj1", "data": {"key2": "val2", "key1": "val1"}}, # Order is different
        ]
        consistent, messages, _ = self._perform_consistency_check_logic(objects)
        self.assertTrue(consistent) # Set comparison is order-agnostic
        self.assertEqual(len(messages), 0)


if __name__ == '__main__':
    # Need to import mock for the QMessageBox patching
    from unittest import mock # Moved import here
    # Also, JsonEditorWidget itself uses QMessageBox, so it needs to be available or mocked there too.
    # The test code imports JsonEditorWidget.QMessageBox, so it implies it should exist on the class.
    # Let's add it to JsonEditorWidget if not already there for testability or ensure mock handles it.
    # For simplicity, the test code will mock it directly on the class.
    if not hasattr(JsonEditorWidget, 'QMessageBox'): # Ensure the attribute exists for mocking
        # This is a fallback for the test environment.
        # Proper solution is that JsonEditorWidget.py handles its QMessageBox import and usage consistently.
        try:
            from PySide6.QtWidgets import QMessageBox 
            JsonEditorWidget.QMessageBox = QMessageBox
        except ImportError:
            # If PySide6 isn't available at all, this mock won't save direct calls in widget
            print("Warning: PySide6.QtWidgets.QMessageBox not found, mock may not cover all usage if widget calls it directly.")
            JsonEditorWidget.QMessageBox = mock.MagicMock() # Provide a mock if not importable


    unittest.main()

```
