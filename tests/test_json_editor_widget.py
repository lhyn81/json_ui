import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Adjust path to import JsonEditorWidget from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Conditional import for QApplication for testing environments
QApplication = None
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QStandardItemModel
    from PySide6.QtCore import QModelIndex
except ImportError:
    print("PySide6 components not found, running tests without them where possible.")
    QStandardItemModel = None # Placeholder if not available
    QModelIndex = None # Placeholder

from json_editor_widget import JsonEditorWidget, KeyFilterProxyModel


# Global app instance, created only if QApplication is available and not already running
# Ensure sys.argv exists for QApplication, default to empty list if not (e.g. in some test runners)
app_instance = None
if QApplication:
    try:
        app_instance = QApplication.instance()
        if not app_instance:
            app_instance = QApplication(sys.argv if hasattr(sys, 'argv') else []) # Ensure sys.argv is passed
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
        # Ensure QMessageBox is properly mocked on the class for the duration of the test.
        with patch.object(JsonEditorWidget, 'QMessageBox', MagicMock()) as mock_msg_box:
            self.assertTrue(self.widget.load_json_from_string(json_string))
            self.assertEqual(self.widget.to_dict(), expected_dict)


    def test_load_json_from_string_invalid(self):
        print("\nRunning: test_load_json_from_string_invalid")
        json_string = '{"name": "Test", "value": 123,}' # Invalid trailing comma
        with patch.object(JsonEditorWidget, 'QMessageBox', MagicMock()) as mock_msg_box:
            self.assertFalse(self.widget.load_json_from_string(json_string))
            # Optionally, check that QMessageBox.critical was called
            mock_msg_box.critical.assert_called_once()

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
            # Ensure the class attribute exists for mocking, even if it's just a MagicMock
            if not hasattr(JsonEditorWidget, 'QMessageBox'):
                JsonEditorWidget.QMessageBox = MagicMock()


class TestJsonEditorWidgetUIActions(unittest.TestCase):
    def setUp(self):
        """Set up the test environment for UI action tests."""
        # Ensure a QApplication instance exists.
        global app_instance
        if QApplication and not app_instance:
            try:
                app_instance = QApplication(sys.argv if hasattr(sys, 'argv') else [])
            except Exception as e:
                # This might happen if sys.argv is not suitable or if it's run in an env
                # where QApplication cannot be initialized (e.g. no display server and no headless platform plugin)
                print(f"Failed to create QApplication for TestJsonEditorWidgetUIActions: {e}")
                # Depending on the tests, this might be a critical failure.
                # For now, we'll allow tests to proceed, but they might fail if they strictly need QApplication.
        self.widget = JsonEditorWidget()

    @patch.object(JsonEditorWidget, 'tree_view', MagicMock())
    def test_handle_expand_all(self):
        print("\nRunning: test_handle_expand_all")
        self.widget.handle_expand_all()
        self.widget.tree_view.expandAll.assert_called_once()

    @patch.object(JsonEditorWidget, 'tree_view', MagicMock())
    def test_handle_collapse_all(self):
        print("\nRunning: test_handle_collapse_all")
        self.widget.handle_collapse_all()
        self.widget.tree_view.collapseAll.assert_called_once()

    @patch('json_editor_widget.QMessageBox.information')
    def test_handle_consistency_check(self, mock_qmessagebox_information):
        print("\nRunning: test_handle_consistency_check")
        self.widget.handle_consistency_check()
        mock_qmessagebox_information.assert_called_once_with(
            self.widget, 
            "Consistency Check", 
            "Feature not yet implemented."
        )


if __name__ == '__main__':
    # unittest.mock.patch is used, so ensure unittest.mock is imported
    # from unittest import mock # Already handled by 'from unittest.mock import patch, MagicMock'

    # The following block for ensuring JsonEditorWidget.QMessageBox exists is good practice
    # if tests are run directly and the widget's module might not perfectly handle its own imports
    # in a test-only context (though ideally the module itself should be robust).
    if not hasattr(JsonEditorWidget, 'QMessageBox'):
        try:
            from PySide6.QtWidgets import QMessageBox
            JsonEditorWidget.QMessageBox = QMessageBox
        except ImportError:
            print("Warning: PySide6.QtWidgets.QMessageBox not found for __main__ guard, using MagicMock.")
            JsonEditorWidget.QMessageBox = MagicMock()

class TestKeyFilterProxyModel(unittest.TestCase):
    def setUp(self):
        global app_instance
        if QApplication and not app_instance:
            try:
                app_instance = QApplication(sys.argv if hasattr(sys, 'argv') else [])
            except Exception as e:
                print(f"Failed to create QApplication for TestKeyFilterProxyModel: {e}")
        
        self.editor_widget = JsonEditorWidget() # For _populate_tree_recursive and _format_value_for_display
        self.source_model = QStandardItemModel()
        self.proxy_model = KeyFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)

    def _populate_source_model(self, data_dict):
        self.source_model.clear() # Clear previous data
        # JsonEditorWidget._populate_tree_recursive expects parent_item, not parent_index
        self.editor_widget._populate_tree_recursive(data_dict, self.source_model.invisibleRootItem())

    def _get_visible_items(self, model_to_check, parent_index=QModelIndex()):
        """
        Traverses the proxy model and returns a nested list/dict structure 
        representing the visible items.
        Format: [('key', 'value'), ('parent_key', '(dict)', [('child_key', 'child_value')])]
        """
        visible_items = []
        if not model_to_check: return visible_items

        for row in range(model_to_check.rowCount(parent_index)):
            key_index = model_to_check.index(row, 0, parent_index)
            value_index = model_to_check.index(row, 1, parent_index)
            
            if not key_index.isValid():
                continue

            key_text = model_to_check.data(key_index)
            value_text = model_to_check.data(value_index) # This is the display value, e.g. "(dict)" or formatted primitive

            # Check for children in the proxy model
            if model_to_check.hasChildren(key_index):
                children = self._get_visible_items(model_to_check, key_index)
                visible_items.append((key_text, value_text, children))
            else:
                visible_items.append((key_text, value_text))
        return visible_items

    def test_filter_parent_match(self):
        print("\nRunning: test_filter_parent_match")
        data = {"parent": {"child_leaf": "value1", "child_obj": {"grandchild": "value2"}}, "other_parent": "value3"}
        self._populate_source_model(data)
        
        self.proxy_model.set_filter_text("parent")
        
        visible = self._get_visible_items(self.proxy_model)
        
        expected = [
            ("parent", "(dict)", [
                ("child_leaf", self.editor_widget._format_value_for_display("value1")),
                ("child_obj", "(dict)", [
                    ("grandchild", self.editor_widget._format_value_for_display("value2"))
                ])
            ])
        ]
        self.assertEqual(visible, expected, "Parent match filtering failed.")
        
        # Check that "other_parent" is not at the root
        root_keys = [item[0] for item in visible]
        self.assertNotIn("other_parent", root_keys, "'other_parent' should not be visible at root.")

    def test_filter_child_match_deeply_nested(self):
        print("\nRunning: test_filter_child_match_deeply_nested")
        data = {"user": {"name": "John", "details": {"age": 30, "city": "New York"}}, "config": {"enabled": True}}
        self._populate_source_model(data)
        
        self.proxy_model.set_filter_text("city")
        
        visible = self._get_visible_items(self.proxy_model)
        
        expected = [
            ("user", "(dict)", [
                # name and details are visible because 'user' is an ancestor of 'city'
                ("name", self.editor_widget._format_value_for_display("John")), 
                ("details", "(dict)", [
                    # age is visible because 'details' is an ancestor of 'city'
                    ("age", self.editor_widget._format_value_for_display(30)),    
                    ("city", self.editor_widget._format_value_for_display("New York"))
                ])
            ])
        ]
        self.assertEqual(visible, expected, "Deep child match filtering failed.")
        root_keys = [item[0] for item in visible]
        self.assertNotIn("config", root_keys, "'config' should not be visible at root.")

    def test_filter_sibling_of_matched_child(self):
        print("\nRunning: test_filter_sibling_of_matched_child")
        data = {"parent_key": {"child_match": "value_m", "child_sibling": "value_s"}}
        self._populate_source_model(data)
        
        self.proxy_model.set_filter_text("child_match")
        visible = self._get_visible_items(self.proxy_model)
        
        expected = [
            ("parent_key", "(dict)", [
                ("child_match", self.editor_widget._format_value_for_display("value_m")),
                # child_sibling is visible because parent_key (ancestor) is shown due to child_match
                ("child_sibling", self.editor_widget._format_value_for_display("value_s")) 
            ])
        ]
        self.assertEqual(visible, expected, "Sibling of matched child filtering failed.")

    def test_filter_no_match(self):
        print("\nRunning: test_filter_no_match")
        data = {"key1": "value1", "key2": "value2"}
        self._populate_source_model(data)
        
        self.proxy_model.set_filter_text("nonexistent")
        visible = self._get_visible_items(self.proxy_model)
        
        self.assertEqual(visible, [], "No match filtering should result in empty list.")

    def test_filter_empty_text(self):
        print("\nRunning: test_filter_empty_text")
        data = {"key1": "value1", "key2": {"subkey": "subvalue"}}
        self._populate_source_model(data)
        
        self.proxy_model.set_filter_text("") # Empty filter
        visible = self._get_visible_items(self.proxy_model)
        
        expected = [
            ("key1", self.editor_widget._format_value_for_display("value1")),
            ("key2", "(dict)", [
                ("subkey", self.editor_widget._format_value_for_display("subvalue"))
            ])
        ]
        self.assertEqual(visible, expected, "Empty filter text should show all items.")
    
    unittest.main()

```
