import sys
import logging
from PyQt5.QtWidgets import QApplication

from views.main_window import MainWindow
from controllers.command_manager import CommandManager
from controllers.undo_redo_manager import UndoRedoManager

# Configure logging to show ONLY needed information (remove DEBUG level)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = MainWindow()
    
    # Setup command manager after window is created
    # Pass the event_bus from main_window to UndoRedoManager
    undo_redo_manager = UndoRedoManager(main_window.event_bus)
    
    # Pass both undo_redo_manager and event_bus to CommandManager
    command_manager = CommandManager(undo_redo_manager, main_window.event_bus)
    main_window.command_manager = command_manager
    
    # Now that command_manager is set up, create the properties controller
    main_window.setup_properties_controller()
    
    # Setup controllers with undo/redo manager
    main_window.device_controller.undo_redo_manager = undo_redo_manager
    main_window.connection_controller.undo_redo_manager = undo_redo_manager
    main_window.boundary_controller.undo_redo_manager = undo_redo_manager
    
    # Create edit menu (requires command_manager to be set)
    main_window._create_edit_menu()
    
    # Show window
    main_window.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()