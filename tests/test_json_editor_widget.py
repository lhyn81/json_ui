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
