import sys
from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow
from utils.event_bus import EventBus
from controllers.device_controller import DeviceController
from controllers.connection_controller import ConnectionController
from controllers.boundary_controller import BoundaryController
from controllers.command_manager import CommandManager

def main():
    app = QApplication(sys.argv)
    
    # Create the main window
    main_window = MainWindow()
    
    # Get references to objects initialized in the main window
    canvas = main_window.canvas
    event_bus = main_window.event_bus
    
    # Create command manager and connect it to controllers
    command_manager = CommandManager(event_bus)
    
    # Save reference to command manager in main window
    main_window.command_manager = command_manager
    
    # Get references to controllers already created in the main window
    device_controller = main_window.device_controller
    connection_controller = main_window.connection_controller
    boundary_controller = main_window.boundary_controller
    
    # Register controllers with the event bus
    event_bus.register_controller('device_controller', device_controller)
    event_bus.register_controller('connection_controller', connection_controller)
    event_bus.register_controller('boundary_controller', boundary_controller)
    
    # Update controllers with undo_redo_manager
    device_controller.undo_redo_manager = command_manager.undo_redo_manager
    boundary_controller.undo_redo_manager = command_manager.undo_redo_manager
    connection_controller.undo_redo_manager = command_manager.undo_redo_manager
    
    # Update command manager with controller references
    command_manager.set_controllers(
        device_controller=device_controller,
        boundary_controller=boundary_controller,
        connection_controller=connection_controller
    )
    
    # Connect event_bus to the canvas for item_moved events
    canvas.event_bus = event_bus
    
    # Create edit menu with undo/redo functionality after command_manager is set
    # This ensures we only have one Edit menu with undo/redo functionality
    main_window._create_edit_menu()
    
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()