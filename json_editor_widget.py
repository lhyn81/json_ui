import sys
import json
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout, # Added QHBoxLayout import
    QTreeView,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QInputDialog, 
    QDialog, 
    QVBoxLayout as QVBoxLayoutDialog, # Alias to avoid conflict if used elsewhere, though QVBoxLayout is already imported
    QFormLayout, 
    QLineEdit, 
    QDialogButtonBox,
    QLabel,
    QComboBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt


class AddItemDialog(QDialog):
    def __init__(self, parent_type, parent=None): # parent_type can be 'dict' or 'list'
        super().__init__(parent)
        self.setWindowTitle("Add New Item")
        # Use QVBoxLayoutDialog alias if there's a naming conflict, otherwise direct QVBoxLayout is fine.
        # Assuming QVBoxLayout from main imports is sufficient if this class is in same file.
        # For clarity, let's use the specific import if it was meant to be distinct,
        # but standard practice would reuse the existing QVBoxLayout import.
        # The prompt used QVBoxLayout directly, so I will too.
        layout = QVBoxLayout(self) # Uses the existing QVBoxLayout import
        
        self.form_layout = QFormLayout()
        self.key_label = QLabel("Key:")
        self.key_edit = QLineEdit()
        self.value_label = QLabel("Value:")
        self.value_edit = QLineEdit()
        self.type_label = QLabel("Value Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["String", "Integer", "Float", "Boolean (true/false)", "Null (null)", "Empty Object ({})", "Empty List ([])"])

        if parent_type == "list":
            self.key_edit.setPlaceholderText("(auto-generated index)")
            self.key_edit.setEnabled(False)
        
        self.form_layout.addRow(self.key_label, self.key_edit)
        self.form_layout.addRow(self.value_label, self.value_edit)
        self.form_layout.addRow(self.type_label, self.type_combo)
        
        layout.addLayout(self.form_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_data(self):
        key = self.key_edit.text() if self.key_edit.isEnabled() else None
        value_text = self.value_edit.text()
        selected_type = self.type_combo.currentText()
        
        value = None
        if selected_type == "String":
            value = value_text
        elif selected_type == "Integer":
            try: value = int(value_text)
            except ValueError: raise ValueError("Invalid integer value")
        elif selected_type == "Float":
            try: value = float(value_text)
            except ValueError: raise ValueError("Invalid float value")
        elif selected_type == "Boolean (true/false)":
            if value_text.lower() == "true": value = True
            elif value_text.lower() == "false": value = False
            else: raise ValueError("Invalid boolean value (use 'true' or 'false')")
        elif selected_type == "Null (null)":
            value = None
        elif selected_type == "Empty Object ({})":
            value = {}
        elif selected_type == "Empty List ([])":
            value = []
        return key, value

class JsonEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JSON Editor Widget")
        # self.setGeometry(0, 0, 600, 400) # Size will be managed by layout/main window

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Key', 'Value'])

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows) # Corrected enum
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.DoubleClicked | QTreeView.EditTrigger.EditKeyPressed) # Corrected enum
        self.model.itemChanged.connect(self.on_item_changed)
        self._is_programmatic_change = False

        # Layout
        main_layout = QVBoxLayout(self) # Changed variable name for clarity
        main_layout.addWidget(self.tree_view)

        # Buttons
        self.load_button = QPushButton("Load JSON")
        self.save_button = QPushButton("Save JSON")
        self.add_item_button = QPushButton("Add Item")
        self.remove_item_button = QPushButton("Remove Item")

        button_layout = QHBoxLayout() 
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.add_item_button)
        button_layout.addWidget(self.remove_item_button)
        main_layout.addLayout(button_layout)

        # Connect signals for buttons
        self.load_button.clicked.connect(self.handle_load_json)
        self.save_button.clicked.connect(self.handle_save_json)
        self.add_item_button.clicked.connect(self.handle_add_item)
        self.remove_item_button.clicked.connect(self.handle_remove_item)

        # self.setLayout(main_layout) # QVBoxLayout was already passed self

    def _store_type_info(self, item, data_type):
        # Helper to store original type (list or dict) for empty collections
        # or for distinguishing between list and dict if keys are all numeric
        item.setData(data_type, Qt.UserRole + 1)

    def _get_stored_type_info(self, item):
        return item.data(Qt.UserRole + 1)

    def load_json_from_string(self, json_string):
        '''Loads JSON data from a string.'''
        try:
            data = json.loads(json_string)
            self.load_json_from_dict(data) # Call the dict loader
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Load Error", f"Invalid JSON string: {e}")
            return False
        return True

    def load_json_from_dict(self, data_dict):
        '''Loads JSON data from a Python dictionary.'''
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Key', 'Value'])
        self._populate_tree_recursive(data_dict, self.model.invisibleRootItem())
        self.tree_view.expandAll() # Expand all items by default
        self.tree_view.resizeColumnToContents(0)
        self.tree_view.resizeColumnToContents(1)

    def _populate_tree_recursive(self, data, parent_item):
        '''Recursively populates the tree model with JSON data.'''
        if isinstance(data, dict):
            self._store_type_info(parent_item, "dict")
            for key, value in data.items():
                key_item = QStandardItem(str(key))
                key_item.setEditable(True) 
                # Store original key to handle edits correctly if needed later
                key_item.setData(str(key), Qt.UserRole + 2) 


                if isinstance(value, (dict, list)):
                    # For parent nodes, value column can show type or be empty
                    value_item = QStandardItem(f"({type(value).__name__})")
                    value_item.setEditable(False)
                    self._store_type_info(key_item, type(value).__name__) # Store type for children
                    parent_item.appendRow([key_item, value_item])
                    self._populate_tree_recursive(value, key_item)
                else:
                    value_item = QStandardItem(self._format_value_for_display(value))
                    value_item.setEditable(True)
                    parent_item.appendRow([key_item, value_item])
        elif isinstance(data, list):
            self._store_type_info(parent_item, "list")
            for index, item in enumerate(data):
                # Index item (acts as key for lists)
                index_item = QStandardItem(str(index))
                index_item.setEditable(False) # Array indices are not user-editable

                if isinstance(item, (dict, list)):
                    value_item = QStandardItem(f"({type(item).__name__})")
                    value_item.setEditable(False)
                    self._store_type_info(index_item, type(item).__name__) # Store type for children
                    parent_item.appendRow([index_item, value_item])
                    self._populate_tree_recursive(item, index_item)
                else:
                    value_item = QStandardItem(self._format_value_for_display(item))
                    value_item.setEditable(True)
                    parent_item.appendRow([index_item, value_item])
    
    def _format_value_for_display(self, value):
        if value is None:
            return "null"
        if isinstance(value, bool):
            return str(value).lower()
        return str(value)

    def to_dict(self):
        '''Converts the current data in the tree model back to a Python dictionary or list.'''
        root_item = self.model.invisibleRootItem()
        if root_item.rowCount() == 0:
            return {} # Or perhaps determine root type if necessary

        # Check the type of the first child's "key" to guess if root is list or dict
        # This assumes a non-empty JSON. For empty root, load_json_from_dict should store root type.
        # For simplicity, we'll assume the root type is determined by its children's structure
        # or the type of the data initially loaded.
        # A more robust way is to store the root type info on invisibleRootItem() when loading.

        # We will determine the type based on the children of the invisible root.
        # The _populate_tree_recursive stores type info on the parent_item of the children.
        # So, for the actual root data, we need to inspect its children.
        
        # If invisibleRootItem has children, it means the JSON is not empty.
        # The _populate_tree_recursive adds children to key_item for dicts/lists,
        # or directly to parent_item for the initial call.
        # Let's try to determine the root structure.
        
        # Simplified: assume it's an object if the first actual item added to invisibleRootItem
        # was populated as a dictionary. This is tricky without storing root type explicitly.
        # The _to_dict_recursive will handle the actual conversion for children.

        if root_item.rowCount() > 0:
            # Peek at the first item to see if its children form a list or dict
            # This is still a bit heuristic.
            # The structure of _populate_tree_recursive means the invisibleRootItem's children
            # are the top-level keys of a dictionary, or indices of a list if the root was a list.
            
            # Check if the root itself was marked as a list or dict during population
            # (this requires _populate_tree_recursive to mark invisibleRootItem if root is list/dict)
            # For now, _populate_tree_recursive is called with invisibleRootItem and the data.
            # So, invisibleRootItem would get type info for the *root* data.
            
            root_type_hint = self._get_stored_type_info(root_item)

            if root_type_hint == "list":
                return self._to_list_recursive(root_item)
            else: # Default to dict if not specified or other type
                return self._to_dict_recursive(root_item) 
        return {} # Default for empty or undetermined


    def _to_dict_recursive(self, parent_item):
        dct = {}
        for i in range(parent_item.rowCount()):
            key_item = parent_item.child(i, 0)
            if not key_item: continue

            key = key_item.text()
            
            # Check if this key_item itself has children (it's a parent of a nested structure)
            # or if it's a simple key-value pair.
            if key_item.hasChildren():
                # The children of key_item form the nested structure.
                # We need to determine if these children form a list or a dict.
                child_container_type = self._get_stored_type_info(key_item)
                if child_container_type == "list":
                    dct[key] = self._to_list_recursive(key_item)
                else: # Default to dict
                    dct[key] = self._to_dict_recursive(key_item)
            else:
                # This is a simple key-value pair. Value is in the second column.
                value_item = parent_item.child(i, 1)
                if value_item:
                    dct[key] = self._parse_value_from_display(value_item.text())
        return dct

    def _to_list_recursive(self, parent_item):
        lst = []
        for i in range(parent_item.rowCount()):
            # For lists, the "key" item (child at col 0) holds the index.
            # The actual content (value or nested structure) is associated with this index_item.
            index_item = parent_item.child(i, 0) 
            if not index_item: continue

            if index_item.hasChildren():
                # Nested structure within the list item
                child_container_type = self._get_stored_type_info(index_item)
                if child_container_type == "list":
                    lst.append(self._to_list_recursive(index_item))
                else: # Default to dict
                    lst.append(self._to_dict_recursive(index_item))
            else:
                # Simple value in the list. Value is in the second column.
                value_item = parent_item.child(i, 1)
                if value_item:
                    lst.append(self._parse_value_from_display(value_item.text()))
        return lst

    def _parse_value_from_display(self, value_str):
        '''Attempts to parse a string value from display into Python types.'''
        if value_str == "null":
            return None
        if value_str == "true":
            return True
        if value_str == "false":
            return False
        try:
            return int(value_str)
        except ValueError:
            pass
        try:
            return float(value_str)
        except ValueError:
            pass
        return value_str # Return as string if no other type matches

    def on_item_changed(self, item):
        # Avoid recursion if setText itself triggers itemChanged
        if hasattr(self, '_is_programmatic_change') and self._is_programmatic_change:
            return

        parent_text = "Root"
        parent_item = item.parent() # This is the QStandardItem representing the parent key/index or invisibleRoot
        
        if parent_item and parent_item != self.model.invisibleRootItem():
            # Try to get the key/index text of the parent item itself.
            # If parent_item is an item generated for a key (e.g. "address"), its text is "address".
            # If parent_item is an item generated for a list index (e.g. "0"), its text is "0".
            # This is the item that *contains* the changed item 'item'.
            parent_display_text = parent_item.text() # This might be empty if it's a value cell of a container.
                                                     # Or it's the key if parent_item is a key item.

            # Let's clarify: 'item' is the QStandardItem that changed.
            # 'item.parent()' is the QStandardItem that is the logical parent in the tree.
            # e.g. if {"key": "value"} is changed, 'item' is for "value", item.parent() is for "key".
            # if ["item0", "item1"] item1 is changed, 'item' is for "item1", item.parent() is for "0" (index item).
            
            # The goal is to log the key or index under which the change occurred.
            actual_parent_container_item = item.parent() # This is the item whose children are being modified or is the key itself.
            
            if actual_parent_container_item: # If item is not a top-level key.
                if actual_parent_container_item == self.model.invisibleRootItem():
                     parent_text = "RootObject/Array"
                else:
                     # The item that changed (item) is either a key (col 0) or value (col 1).
                     # Its parent (actual_parent_container_item) is the item for the key/index of the container
                     # *if* the changed item is part of a nested structure.
                     # Example: {"outer_key": {"inner_key": "value"}}
                     # If "value" changes: item is "value", parent is "inner_key".
                     # If "inner_key" changes: item is "inner_key", parent is "outer_key".

                     # If 'item' is a value (col 1), its direct parent in model is the key/index item.
                     # If 'item' is a key (col 0), its direct parent is the key/index item of the level above.
                     
                     # Let's use the item's own row and its sibling key item for context if it's a value.
                     if item.column() == 1: # Value changed
                         key_sibling_item = actual_parent_container_item.child(item.row(), 0)
                         if key_sibling_item:
                             parent_text = f"Under Key/Index: '{key_sibling_item.text()}'"
                         else: # Should not happen in current structure
                             parent_text = "Under Unknown Key/Index"
                     elif item.column() == 0: # Key changed
                         # The parent of this key item is the container it belongs to.
                         grandparent_item = actual_parent_container_item.parent()
                         if grandparent_item and grandparent_item != self.model.invisibleRootItem():
                             parent_text = f"In Container Key/Index: '{actual_parent_container_item.text()}' (Key itself is changing)"
                         elif actual_parent_container_item == self.model.invisibleRootItem():
                             parent_text = "RootObject/Array (Key itself is changing)"
                         else: # Key is a child of some other key/index
                             parent_text = f"In Container Key/Index: '{actual_parent_container_item.text()}' (Key itself is changing)"


        print(f"Item changed: '{item.text()}' at (row:{item.row()}, col:{item.column()}). Context: {parent_text}")


        # If a value is changed (column 1)
        if item.column() == 1:
            try:
                self._is_programmatic_change = True
                
                current_text = item.text()
                parsed_value = self._parse_value_from_display(current_text)
                formatted_value = self._format_value_for_display(parsed_value)
                
                if current_text != formatted_value:
                    item.setText(formatted_value)
                    print(f"  Value re-formatted: '{current_text}' -> '{formatted_value}'")
                
            finally:
                self._is_programmatic_change = False
        elif item.column() == 0: # A key was changed
            # Could add logic here if needed, e.g. to update stored original key for rename tracking
            # item.setData(item.text(), Qt.UserRole + 2) # Example: update stored key
            pass

    def handle_load_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load JSON File",
            "",  # Start directory
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_string = f.read()
                # We already have a method that takes a string
                if self.load_json_from_string(json_string): # load_json_from_string handles its own error messages for parsing
                    QMessageBox.information(self, "Success", "JSON file loaded successfully.")
                # else: # load_json_from_string returned False, indicating an error it already reported.
            except FileNotFoundError:
                QMessageBox.critical(self, "Error", f"File not found: {file_path}")
            # json.JSONDecodeError is handled by load_json_from_string, but if it were direct:
            # except json.JSONDecodeError as e:
            #     QMessageBox.critical(self, "Error", f"Invalid JSON file: {e.msg}") # Corrected to e.msg
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def handle_save_json(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            "",  # Start directory
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                data_dict = self.to_dict()
                json_string = json.dumps(data_dict, indent=4, ensure_ascii=False)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json_string)
                QMessageBox.information(self, "Success", "JSON file saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save JSON file: {e}")

    def handle_add_item(self):
        current_index = self.tree_view.currentIndex()
        parent_item = None
        parent_type = "dict" # Default to dict if adding to root or no selection

        if current_index.isValid():
            selected_item = self.model.itemFromIndex(current_index)
            # If selected item is a key of a container, its children are the container's items.
            # If selected item is a value of a container, its parent is the key.
            # We want to add to the container represented by selected_item (if it's a key)
            # or to the container selected_item belongs to.

            # Determine the actual item that will be the parent for the new child.
            # And determine if it's a list or a dictionary.
            potential_parent = selected_item
            if selected_item.column() == 1: # Selected a value cell
                # Try to get the key item associated with this value cell's row
                parent_row_key_item = selected_item.parent().child(selected_item.row(), 0) if selected_item.parent() else None
                if parent_row_key_item and (parent_row_key_item.hasChildren() or self._get_stored_type_info(parent_row_key_item) in ["list", "dict"]):
                     potential_parent = parent_row_key_item # The key item is the container
                elif selected_item.parent(): # Selected a simple value, its parent (the key item's parent) is the container
                    potential_parent = selected_item.parent()
                # else: selected_item has no parent, should not happen for a value cell if model is structured.

            stored_type = self._get_stored_type_info(potential_parent)
            if potential_parent.hasChildren() or stored_type in ["list", "dict"]: # It's a container or marked as one
                parent_item = potential_parent
                parent_type = stored_type if stored_type in ["list", "dict"] else "dict" # Fallback
            elif potential_parent.parent(): # It's a child item, so add to its parent container
                parent_item = potential_parent.parent()
                stored_type_on_parent = self._get_stored_type_info(parent_item)
                parent_type = stored_type_on_parent if stored_type_on_parent in ["list", "dict"] else "dict"
            else: # No clear parent container from selection, add to root
                parent_item = self.model.invisibleRootItem()
                root_type = self._get_stored_type_info(parent_item)
                parent_type = root_type if root_type in ["list", "dict"] else "dict"
        else: # No selection, add to root
            parent_item = self.model.invisibleRootItem()
            root_type = self._get_stored_type_info(parent_item)
            parent_type = root_type if root_type in ["list", "dict"] else "dict"
            if not root_type and parent_item.rowCount() == 0: # If root is empty and untyped, assume dict
                 self._store_type_info(parent_item, "dict")


        dialog = AddItemDialog(parent_type, self)
        if dialog.exec() == QDialog.Accepted: # Use QDialog.DialogCode.Accepted for PySide6
            try:
                key, value = dialog.get_data()
                
                key_text = key
                if parent_type == "list":
                    key_text = str(parent_item.rowCount()) # Index for list
                
                if parent_type == "dict" and not key_text: # Ensure key_text is not None or empty
                    QMessageBox.warning(self, "Add Item", "Key cannot be empty for an object.")
                    return

                # Prevent duplicate keys in dict
                if parent_type == "dict":
                    for i in range(parent_item.rowCount()):
                        if parent_item.child(i, 0) and parent_item.child(i, 0).text() == key_text:
                            QMessageBox.warning(self, "Add Item", f"Key '{key_text}' already exists.")
                            return

                key_item = QStandardItem(key_text)
                if parent_type == "list":
                    key_item.setEditable(False) # List indices are not editable
                else:
                    key_item.setEditable(True) # Dict keys are editable
                    key_item.setData(key_text, Qt.UserRole + 2) # Store original key for editing tracking

                value_item = None # Must define value_item
                if isinstance(value, (dict, list)):
                    value_item = QStandardItem(f"({type(value).__name__})") # Display type
                    value_item.setEditable(False)
                    self._store_type_info(key_item, "dict" if isinstance(value, dict) else "list")
                    self._populate_tree_recursive(value, key_item) # Populate children
                else:
                    value_item = QStandardItem(self._format_value_for_display(value))
                    value_item.setEditable(True)
                
                parent_item.appendRow([key_item, value_item])
                if parent_item != self.model.invisibleRootItem(): # Don't try to expand invisible root
                    self.tree_view.expand(parent_item.index())
                else: # If adding to root, expand the new item if it's a container
                    self.tree_view.expand(key_item.index())


            except ValueError as e:
                QMessageBox.critical(self, "Add Item Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Add Item Error", f"An unexpected error occurred: {e}")

    def handle_remove_item(self):
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            QMessageBox.information(self, "Remove Item", "Please select an item to remove.")
            return

        selected_item = self.model.itemFromIndex(current_index)
        
        parent_item = selected_item.parent()
        item_row_to_remove = selected_item.row()

        if parent_item:
            parent_item.removeRow(item_row_to_remove)
            # Check if the parent was a list to re-index
            if self._get_stored_type_info(parent_item) == "list":
                for i in range(parent_item.rowCount()):
                    item_at_new_index = parent_item.child(i, 0) # Key/Index item
                    if item_at_new_index: 
                        item_at_new_index.setText(str(i))
        else: # It's a top-level item (child of invisibleRootItem)
            self.model.removeRow(item_row_to_remove)
            # Check if root itself is a list to re-index (less common for root to be list, but possible)
            if self._get_stored_type_info(self.model.invisibleRootItem()) == "list":
                 for i in range(self.model.rowCount()): # Iterate root items
                    item_at_new_index = self.model.item(i, 0) # Key/Index item
                    if item_at_new_index:
                        item_at_new_index.setText(str(i))


# Example usage for direct testing of the widget
if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = JsonEditorWidget()

    sample_json_data = {
        "name": "John Doe",
        "age": 30,
        "isStudent": False,
        "address": {
            "street": "123 Main St",
            "city": "Anytown"
        },
        "courses": [
            {"title": "History", "credits": 3, "details": {"level": "100", "optional_attrs": [None, "extra"]}},
            {"title": "Math", "credits": 4, "details": {"level": "200"}}
        ],
        "metadata": None,
        "empty_obj": {},
        "empty_list": [],
        "list_of_lists": [[1,2],[3,4]]
    }
    
    editor.load_json_from_dict(sample_json_data)
    editor.show()
    
    # Test to_dict conversion
    # Wait for the event loop to start before calling to_dict if it relies on UI updates.
    # For now, this direct call might be okay if model is populated synchronously.
    # Converted_data = editor.to_dict()
    # print("\nConverted back to dict/list:")
    # print(json.dumps(Converted_data, indent=4))
    # print("\nOriginal dict/list:")
    # print(json.dumps(sample_json_data, indent=4))
    
    # A simple visual test for now. Full assertion would require careful comparison.
    # print("Data matches original:", Converted_data == sample_json_data)

    sys.exit(app.exec())
