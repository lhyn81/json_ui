import sys
import json
import os # Added for os.path.basename
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
    QVBoxLayout, # Ensuring QVBoxLayout is directly available
    QFormLayout, 
    QLineEdit, 
    QDialogButtonBox,
    QLabel,
    QComboBox,
    QHBoxLayout # Added for filter layout
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QSortFilterProxyModel # Added QSortFilterProxyModel


class KeyFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""

    def set_filter_text(self, text):
        self.filter_text = text.lower()
        self.invalidateFilter() # Trigger a re-filter

    def filterAcceptsRow(self, source_row, source_parent_index):
        if not self.filter_text: # No filter, accept all
            return True

        source_model = self.sourceModel()
        
        # Get the QStandardItem for the key in the current row
        key_item_index = source_model.index(source_row, 0, source_parent_index)
        if not key_item_index.isValid():
            return False # Should not happen with valid model

        key_item = source_model.itemFromIndex(key_item_index)
        if not key_item:
             return False # Should not happen

        # Check if the current item's key matches
        current_key_text = key_item.text().lower()
        key_matches = self.filter_text in current_key_text
        
        if key_matches:
            return True # Current item's key matches, show it and its children

        # If key doesn't match, check if any children match (so parent is visible)
        if source_model.hasChildren(key_item_index):
            for i in range(source_model.rowCount(key_item_index)):
                if self.filterAcceptsRow(i, key_item_index): # Recursive call for children
                    return True
        
        return False # Neither current key nor any children keys match


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

        self.proxy_model = KeyFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.proxy_model) # Use proxy model
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows) # Corrected enum
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.DoubleClicked | QTreeView.EditTrigger.EditKeyPressed) # Corrected enum
        self.model.itemChanged.connect(self.on_item_changed)
        self._is_programmatic_change = False
        self.current_file_path = None # Added for tracking current file

        # Layout
        main_layout = QVBoxLayout(self)

        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by key...")
        self.filter_input.textChanged.connect(self.proxy_model.set_filter_text)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.filter_input)
        main_layout.addLayout(filter_layout)

        main_layout.addWidget(self.tree_view)

        # Buttons
        self.load_button = QPushButton("Load JSON")
        self.save_button = QPushButton("Save") # New name
        self.save_as_button = QPushButton("Save As...")
        self.add_item_button = QPushButton("Add Item")
        self.remove_item_button = QPushButton("Remove Item")
        self.consistency_check_button = QPushButton("Check Consistency")
        self.expand_all_button = QPushButton("Expand All") # New button
        self.collapse_all_button = QPushButton("Collapse All") # New button

        button_layout = QHBoxLayout() 
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.save_as_button) 
        button_layout.addWidget(self.add_item_button)
        button_layout.addWidget(self.remove_item_button)
        button_layout.addWidget(self.consistency_check_button)
        button_layout.addWidget(self.expand_all_button) # Added to layout
        button_layout.addWidget(self.collapse_all_button) # Added to layout
        main_layout.addLayout(button_layout)

        # Connect signals for buttons
        self.load_button.clicked.connect(self.handle_load_json)
        self.save_button.clicked.connect(self.handle_save) 
        self.save_as_button.clicked.connect(self.handle_save_as)
        self.add_item_button.clicked.connect(self.handle_add_item)
        self.remove_item_button.clicked.connect(self.handle_remove_item)
        self.consistency_check_button.clicked.connect(self.handle_consistency_check)
        self.expand_all_button.clicked.connect(self.handle_expand_all) # New connection
        self.collapse_all_button.clicked.connect(self.handle_collapse_all) # New connection
        
        self.update_window_title() # Initial call

        # self.setLayout(main_layout) # QVBoxLayout was already passed self

    def handle_expand_all(self):
        self.tree_view.expandAll()

    def handle_collapse_all(self):
        self.tree_view.collapseAll()

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
                    self.current_file_path = file_path # Add this line
                    self.update_window_title() # Add this call
                # else: # load_json_from_string returned False, indicating an error it already reported.
            except FileNotFoundError:
                QMessageBox.critical(self, "Error", f"File not found: {file_path}")
            # json.JSONDecodeError is handled by load_json_from_string, but if it were direct:
            # except json.JSONDecodeError as e:
            #     QMessageBox.critical(self, "Error", f"Invalid JSON file: {e.msg}") # Corrected to e.msg
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def handle_save(self): # Renamed from handle_save_json
        if self.current_file_path:
            try:
                data_dict = self.to_dict()
                json_string = json.dumps(data_dict, indent=4, ensure_ascii=False)
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(json_string)
                QMessageBox.information(self, "Success", f"JSON file saved to {self.current_file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save JSON file: {e}")
        else:
            # If no current path, behave like "Save As"
            self.handle_save_as()

    def handle_save_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File As...",
            self.current_file_path if self.current_file_path else "",  # Start directory or last path
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                data_dict = self.to_dict()
                json_string = json.dumps(data_dict, indent=4, ensure_ascii=False)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json_string)
                self.current_file_path = file_path # Update current path
                self.update_window_title() # Update window title
                QMessageBox.information(self, "Success", f"JSON file saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save JSON file: {e}")
                
    def update_window_title(self):
        window = self.window() # Gets the top-level window containing this widget
        if window: # Check if widget is part of a window
            # Attempt to find a base title. This might need adjustment if main.py changes its title logic.
            # For now, assume a generic base or retrieve if possible.
            # A more robust way might be to pass the base title or a callback from main.py.
            base_title = "JSON Editor" 
            # Check if the current window title already contains "JSON Editor" to avoid duplication
            # This is a simple check; more sophisticated state management might be needed for complex title scenarios
            current_window_title = window.windowTitle()
            if "JSON Editor" in current_window_title and "-" in current_window_title:
                # Try to extract the original base title part if it was set like "Base - File"
                base_title = current_window_title.split(" - ")[0]


            if self.current_file_path:
                file_name = os.path.basename(self.current_file_path)
                window.setWindowTitle(f"{base_title} - {file_name}")
            else:
                window.setWindowTitle(f"{base_title} - New File")

    def handle_consistency_check(self):
        QMessageBox.information(self, "Consistency Check", "Feature not yet implemented.")

    def handle_add_item(self):
        proxy_current_index = self.tree_view.currentIndex()
        # Map proxy index to source index for model operations
        current_index = self.proxy_model.mapToSource(proxy_current_index) if proxy_current_index.isValid() else proxy_current_index

        parent_item = None
        parent_type = "dict" # Default to dict if adding to root or no selection

        if current_index.isValid(): # Use the mapped source_index
            # Get item from the source model
            selected_item = self.model.itemFromIndex(current_index) 
            if not selected_item: # Should not happen if index is valid and mapped
                parent_item = self.model.invisibleRootItem()
                parent_type = self._get_stored_type_info(parent_item) or "dict"
            else:
                potential_parent = selected_item
                if selected_item.column() == 1: # Selected a value cell
                    parent_row_key_item = selected_item.parent().child(selected_item.row(), 0) if selected_item.parent() else None
                    if parent_row_key_item and (parent_row_key_item.hasChildren() or self._get_stored_type_info(parent_row_key_item) in ["list", "dict"]):
                         potential_parent = parent_row_key_item
                    elif selected_item.parent():
                        potential_parent = selected_item.parent()

                stored_type = self._get_stored_type_info(potential_parent)
                if potential_parent.hasChildren() or stored_type in ["list", "dict"]:
                    parent_item = potential_parent
                    parent_type = stored_type if stored_type in ["list", "dict"] else "dict"
                elif potential_parent.parent():
                    parent_item = potential_parent.parent()
                    stored_type_on_parent = self._get_stored_type_info(parent_item)
                    parent_type = stored_type_on_parent if stored_type_on_parent in ["list", "dict"] else "dict"
                else: 
                    parent_item = self.model.invisibleRootItem()
                    root_type = self._get_stored_type_info(parent_item)
                    parent_type = root_type if root_type in ["list", "dict"] else "dict"
        else: # No selection or invalid mapped index, add to root
            parent_item = self.model.invisibleRootItem()
            root_type = self._get_stored_type_info(parent_item)
            parent_type = root_type if root_type in ["list", "dict"] else "dict"
            if not root_type and parent_item.rowCount() == 0:
                 self._store_type_info(parent_item, "dict")
                 parent_type = "dict"


        dialog = AddItemDialog(parent_type, self)
        if dialog.exec() == QDialog.Accepted: 
            try:
                key, value = dialog.get_data()
                key_text = key
                if parent_type == "list":
                    key_text = str(parent_item.rowCount()) 
                
                if parent_type == "dict" and not key_text:
                    QMessageBox.warning(self, "Add Item", "Key cannot be empty for an object.")
                    return

                if parent_type == "dict":
                    for i in range(parent_item.rowCount()):
                        if parent_item.child(i, 0) and parent_item.child(i, 0).text() == key_text:
                            QMessageBox.warning(self, "Add Item", f"Key '{key_text}' already exists.")
                            return

                key_item = QStandardItem(key_text)
                if parent_type == "list":
                    key_item.setEditable(False) 
                else:
                    key_item.setEditable(True) 
                    key_item.setData(key_text, Qt.UserRole + 2) 

                value_item = None 
                if isinstance(value, (dict, list)):
                    value_item = QStandardItem(f"({type(value).__name__})") 
                    value_item.setEditable(False)
                    self._store_type_info(key_item, "dict" if isinstance(value, dict) else "list")
                    self._populate_tree_recursive(value, key_item) 
                else:
                    value_item = QStandardItem(self._format_value_for_display(value))
                    value_item.setEditable(True)
                
                parent_item.appendRow([key_item, value_item])

                # Expansion logic: use mapFromSource for the view
                source_parent_idx_for_view = parent_item.index()
                if parent_item != self.model.invisibleRootItem():
                    proxy_parent_idx_for_view = self.proxy_model.mapFromSource(source_parent_idx_for_view)
                    if proxy_parent_idx_for_view.isValid():
                        self.tree_view.expand(proxy_parent_idx_for_view)
                else: # If adding to root, expand the new item itself (key_item)
                    source_key_item_idx = key_item.index()
                    proxy_key_item_idx = self.proxy_model.mapFromSource(source_key_item_idx)
                    if proxy_key_item_idx.isValid():
                        self.tree_view.expand(proxy_key_item_idx)

            except ValueError as e:
                QMessageBox.critical(self, "Add Item Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Add Item Error", f"An unexpected error occurred: {e}")

    def handle_remove_item(self):
        proxy_current_index = self.tree_view.currentIndex()
        if not proxy_current_index.isValid():
            QMessageBox.information(self, "Remove Item", "Please select an item to remove.")
            return

        # Map to source for model operations
        source_current_index = self.proxy_model.mapToSource(proxy_current_index)
        if not source_current_index.isValid(): # Should not happen if proxy index was valid
            QMessageBox.warning(self, "Remove Item", "Could not map selected item for removal.")
            return

        selected_item = self.model.itemFromIndex(source_current_index)
        if not selected_item: # Should also not happen
            QMessageBox.warning(self, "Remove Item", "Selected item not found in source model.")
            return
        
        parent_item = selected_item.parent() # This is a source model parent
        item_row_to_remove = selected_item.row()

        if parent_item: # Parent is a QStandardItem from the source model
            parent_item.removeRow(item_row_to_remove)
            if self._get_stored_type_info(parent_item) == "list":
                for i in range(parent_item.rowCount()):
                    item_at_new_index = parent_item.child(i, 0) 
                    if item_at_new_index: 
                        item_at_new_index.setText(str(i))
        else: # Top-level item (child of invisibleRootItem)
            self.model.removeRow(item_row_to_remove) # Remove from source model's root
            if self._get_stored_type_info(self.model.invisibleRootItem()) == "list":
                 for i in range(self.model.rowCount()): 
                    item_at_new_index = self.model.item(i, 0) 
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
