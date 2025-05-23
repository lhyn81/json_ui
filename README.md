# PySide6 JSON Editor Widget

A custom PySide6 widget for displaying, editing, and managing JSON-like data. This widget allows users to explore, modify, add, remove, and save JSON objects and arrays through a graphical tree interface.

## Features

*   **Tree View Display**: Hierarchical display of JSON data (objects and arrays).
*   **Key Filtering**: Real-time filtering of tree items by key using a filter input field.
*   **Load, Save, and Save As**:
    *   Load JSON data from `.json` files.
    *   "Save" the current JSON structure to its original file or prompt for a new file if unsaved.
    *   "Save As..." to save the current JSON structure to a new user-specified file.
    *   Window title updates to reflect the currently open file.
*   **In-Place Editing**:
    *   Edit keys (for objects) and values directly in the tree.
    *   Automatic type conversion feedback (e.g., "true" becomes `true`).
*   **Structural Modifications**:
    *   **Add Item**: Add new key-value pairs to objects or new elements to arrays using a dedicated dialog that allows specifying the key (if applicable), value, and data type.
    *   **Remove Item**: Delete selected items (keys from objects or elements from arrays).
*   **Consistency Check**:
    *   Verify if all objects within a selected array share the same set of keys.
    *   Reports missing or extra keys for each inconsistent object.
*   **View Controls**:
    *   **Expand All**: Fully expand all nodes in the tree.
    *   **Collapse All**: Fully collapse all nodes in the tree.
*   **Data Type Handling**: Supports common JSON data types: strings, numbers (integers/floats), booleans, null, objects, and arrays.
*   **Type Preservation**: Maintains distinction between empty objects (`{}`) and empty lists (`[]`) during load/save operations.

## Project Structure

*   `main.py`: The main application to run and test the `JsonEditorWidget`.
*   `json_editor_widget.py`: Contains the core `JsonEditorWidget` class.
*   `example1.json`: An example JSON file (as provided in the initial requirement).
*   `example2.json`: A more complex example JSON file demonstrating various data structures.
*   `tests/`: Contains unit tests for the widget's data logic.
    *   `test_json_editor_widget.py`: Unit tests for data parsing, formatting, loading, and conversion.

## Prerequisites

*   Python 3.x
*   PySide6 (`pip install pyside6`)

## How to Run

1.  Ensure Python 3 and PySide6 are installed.
2.  Clone this repository or download the source files.
3.  Navigate to the root directory of the project.
4.  Run the main application:
    ```bash
    python main.py
    ```
    This will open a window displaying the JSON editor, pre-loaded with `example1.json`. You can then use the "Load JSON" button to open other files like `example2.json`.

## How to Run Tests

1.  Navigate to the root directory of the project.
2.  Run the unit tests:
    ```bash
    python -m unittest discover tests
    ```
    or directly:
    ```bash
    python tests/test_json_editor_widget.py
    ```

## Future Considerations / Potential Enhancements

*   More sophisticated validation for keys and values during editing.
*   Drag-and-drop support for reordering items.
*   Context menu for actions (add, remove, change type) directly on tree items.
*   Better visual distinction for different data types in the tree.
*   Support for very large JSON files (virtualized tree view).
*   Undo/Redo functionality.
