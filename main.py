import sys
import json # For loading the example file
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt
from json_editor_widget import JsonEditorWidget # Uncommented and correctly imported

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON Editor Test Application")
        self.setGeometry(100, 100, 900, 700) # Adjusted size

        self.json_editor = JsonEditorWidget()

        # Create a central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.json_editor)

        # Example: Load a JSON file at startup (e.g., example1.json)
        try:
            with open("example1.json", 'r') as f:
                json_data = json.load(f)
            self.json_editor.load_json_from_dict(json_data)
            print("Successfully loaded example1.json into the widget.")
        except FileNotFoundError:
            print("Error: example1.json not found. Make sure it's in the correct path.")
            # Optionally, show a message in the widget or main window
            # from PySide6.QtGui import QStandardItem # Import QStandardItem if using this optional code
            # self.json_editor.model.invisibleRootItem().appendRow([QStandardItem("Error"), QStandardItem("example1.json not found")])
        except json.JSONDecodeError:
            print("Error: example1.json contains invalid JSON.")
            # Optionally, show a message
        except Exception as e:
            print(f"An unexpected error occurred while loading example1.json: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
