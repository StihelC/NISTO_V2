from PyQt5.QtWidgets import QMainWindow, QDialog, QMessageBox, QAction
from PyQt5.QtCore import QPointF, QTimer, Qt
from PyQt5.QtGui import QColor  # Removed QKeySequence import as it's not used
import logging

from .canvas import Canvas
from constants import Modes
from controllers.menu_manager import MenuManager
from controllers.device_controller import DeviceController
from controllers.connection_controller import ConnectionController
from controllers.boundary_controller import BoundaryController
from controllers.clipboard_manager import ClipboardManager
from utils.event_bus import EventBus
from models.device import Device
from models.connection import Connection
from models.boundary import Boundary

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NISTO")
        self.setGeometry(100, 100, 800, 600)

        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Create canvas
        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Connect status message signal
        self.canvas.statusMessage.connect(self.statusBar().showMessage)
        
        # Create event bus for communication between components
        self.event_bus = EventBus()
        
        # Initialize controllers
        self.device_controller = DeviceController(self.canvas, self.event_bus)
        self.connection_controller = ConnectionController(self.canvas, self.event_bus)
        self.boundary_controller = BoundaryController(self.canvas, self.event_bus)
        
        # Initialize clipboard manager
        self.clipboard_manager = ClipboardManager(
            self.canvas, 
            self.device_controller,
            self.connection_controller,
            self.event_bus
        )
        
        # Create menu manager
        self.menu_manager = MenuManager(self, self.canvas, self.event_bus)
        self.menu_manager.create_toolbar()
        
        # Initialize command_manager with a None value to avoid attribute errors
        self.command_manager = None
        
        # Create file menu with save/load actions
        self._create_file_menu()
        
        # Don't create edit menu here - it will be created in main.py after command_manager is set
        # self._create_edit_menu()  <-- Comment out or remove this line
        
        # Create view menu
        self._create_view_menu()
        
        # Set up keyboard shortcuts
        self._setup_shortcuts()
        
        # Connect canvas signals to controllers
        self.connect_signals()
        
        # Set initial mode
        self.set_mode(Modes.SELECT)

    def _create_file_menu(self):
        """Create the File menu with save/load actions."""
        file_menu = self.menuBar().addMenu("File")
        
        # Save canvas action
        save_action = QAction("Save Canvas", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_canvas)
        file_menu.addAction(save_action)
        
        # Load canvas action
        load_action = QAction("Load Canvas", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_canvas)
        file_menu.addAction(load_action)
        
        # Exit action
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _create_edit_menu(self):
        """Create the Edit menu with clipboard and undo/redo actions."""
        edit_menu = self.menuBar().addMenu("Edit")
        
        # Only add undo/redo actions if command_manager is initialized
        if self.command_manager:
            # Undo action
            undo_action = QAction("Undo", self)
            undo_action.setShortcut("Ctrl+Z")
            undo_action.triggered.connect(self.command_manager.undo)
            undo_action.setEnabled(self.command_manager.can_undo())
            self.undo_action = undo_action
            edit_menu.addAction(undo_action)
            
            # Redo action
            redo_action = QAction("Redo", self)
            redo_action.setShortcut("Ctrl+Y")
            redo_action.triggered.connect(self.command_manager.redo)
            redo_action.setEnabled(self.command_manager.can_redo())
            self.redo_action = redo_action
            edit_menu.addAction(redo_action)
            
            # Add separator after undo/redo
            edit_menu.addSeparator()
            
            # Connect to undo/redo manager signals for updates
            self.command_manager.undo_redo_manager.stack_changed.connect(self._update_undo_redo_actions)
        
        # Cut action
        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.clipboard_manager.cut_selected)
        edit_menu.addAction(cut_action)
        
        # Copy action
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.clipboard_manager.copy_selected)
        edit_menu.addAction(copy_action)
        
        # Paste action
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.clipboard_manager.paste)
        edit_menu.addAction(paste_action)
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.on_delete_selected_requested)
        edit_menu.addAction(delete_action)

    def _update_undo_redo_actions(self):
        """Update the undo/redo actions based on state."""
        if self.command_manager and hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(self.command_manager.can_undo())
            self.undo_action.setText(self.command_manager.get_undo_text())
            
        if self.command_manager and hasattr(self, 'redo_action'):
            self.redo_action.setEnabled(self.command_manager.can_redo())
            self.redo_action.setText(self.command_manager.get_redo_text())

    def _create_view_menu(self):
        """Create the View menu."""
        view_menu = self.menuBar().addMenu("&View")
        
        # Zoom In action - Fix shortcut
        zoom_in_action = QAction("Zoom In", self)
        # Using equals sign for plus to avoid issues with Qt shortcut parsing
        zoom_in_action.setShortcut("Ctrl+=")  # This works for both Ctrl++ and Ctrl+=
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        # Zoom Out action
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        # Reset Zoom action
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        view_menu.addAction(reset_zoom_action)  # FIX: This was a bug - should be reset_zoom_action
        
        view_menu.addSeparator()
        
        return view_menu
    
    def _setup_shortcuts(self):
        """Set up additional keyboard shortcuts."""
        # These shortcuts work globally in the main window
        
        # Delete key for deleting selected items
        # This function is already handled by the canvas and mode system
        pass

    def connect_signals(self):
        """Connect canvas signals to appropriate controller handlers."""
        self.canvas.add_device_requested.connect(self.device_controller.on_add_device_requested)
        self.canvas.delete_device_requested.connect(self.device_controller.on_delete_device_requested)
        self.canvas.add_boundary_requested.connect(self.boundary_controller.on_add_boundary_requested)
        self.canvas.add_connection_requested.connect(self.connection_controller.on_add_connection_requested)
        self.canvas.delete_connection_requested.connect(self.connection_controller.on_delete_connection_requested)
        self.canvas.delete_boundary_requested.connect(self.boundary_controller.on_delete_boundary_requested)
        self.canvas.delete_item_requested.connect(self.on_delete_item_requested)
        self.canvas.delete_selected_requested.connect(self.on_delete_selected_requested)
    
    def set_mode(self, mode):
        """Set the current interaction mode."""
        self.canvas.set_mode(mode)
        self.logger.info(f"Mode changed to: {mode}")
        # Update menu/toolbar to reflect current mode
        self.menu_manager.update_mode_actions(mode)
        
    def on_delete_item_requested(self, item):
        """Handle request to delete a non-specific item."""
        if item:
            self.logger.info(f"Deleting item of type {type(item).__name__}")
            self.canvas.scene().removeItem(item)
    
    def on_delete_selected_requested(self):
        """Handle request to delete all selected items."""
        selected_items = self.canvas.scene().selectedItems()
        
        if not selected_items:
            return
        
        try:
            self.logger.info(f"Attempting to delete {len(selected_items)} selected items")
            
            # Group items by type to handle deletion in the correct order
            connections = [item for item in selected_items if isinstance(item, Connection)]
            devices = [item for item in selected_items if isinstance(item, Device)]
            boundaries = [item for item in selected_items if isinstance(item, Boundary)]
            
            # Use composite command to handle undo/redo for multiple items
            if hasattr(self, 'command_manager') and self.command_manager:
                from controllers.commands import CompositeCommand
                composite_cmd = CompositeCommand(description=f"Delete {len(selected_items)} Selected Items")
                composite_cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                using_commands = True
            else:
                composite_cmd = None
                using_commands = False
            
            # Delete connections first to avoid references to deleted devices
            self.logger.info(f"Deleting {len(connections)} connections")
            for connection in connections:
                if using_commands:
                    from controllers.commands import DeleteConnectionCommand
                    cmd = DeleteConnectionCommand(self.connection_controller, connection)
                    cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                    composite_cmd.add_command(cmd)
                else:
                    self.connection_controller._delete_connection(connection)
            
            # Delete devices
            self.logger.info(f"Deleting {len(devices)} devices")
            for device in devices:
                if using_commands:
                    from controllers.commands import DeleteDeviceCommand
                    cmd = DeleteDeviceCommand(self.device_controller, device)
                    cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                    composite_cmd.add_command(cmd)
                else:
                    self.device_controller._delete_device(device)
            
            # Delete boundaries
            self.logger.info(f"Deleting {len(boundaries)} boundaries")
            for boundary in boundaries:
                if using_commands:
                    from controllers.commands import DeleteBoundaryCommand
                    cmd = DeleteBoundaryCommand(self.boundary_controller, boundary)
                    composite_cmd.add_command(cmd)
                else:
                    self.boundary_controller.on_delete_boundary_requested(boundary)
            
            # Push the composite command if we're using undo/redo
            if composite_cmd and composite_cmd.commands:
                self.logger.info(f"Pushing composite delete command with {len(composite_cmd.commands)} actions")
                self.command_manager.undo_redo_manager.push_command(composite_cmd)
                
            # Force a complete update of the canvas
            self.canvas.viewport().update()
            
            self.logger.info(f"Deleted {len(connections)} connections, {len(devices)} devices, and {len(boundaries)} boundaries")
        except Exception as e:
            self.logger.error(f"Error in delete_selected: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def keyPressEvent(self, event):
        """Handle key press events."""
        # Let the canvas and its modes handle the key first
        if self.canvas.scene().focusItem():
            # If an item has focus, let Qt's standard event handling work
            super().keyPressEvent(event)
            return
            
        # Handle keyboard shortcuts using key combinations directly
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.copy_selected()
            event.accept()
        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.paste()
            event.accept()
        elif event.key() == Qt.Key_X and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.cut_selected()
            event.accept()
        else:
            # Pass to parent for default handling
            super().keyPressEvent(event)
    
    def save_canvas(self):
        """Save the current canvas to a file."""
        from views.file_dialog import SaveCanvasDialog
        
        success, message = SaveCanvasDialog.save_canvas(self, self.canvas)
        if success:
            self.logger.info("Canvas saved successfully")
        else:
            self.logger.warning(f"Canvas save failed: {message}")

    def load_canvas(self):
        """Load a canvas from a file."""
        from views.file_dialog import LoadCanvasDialog
        
        success, message = LoadCanvasDialog.load_canvas(self, self.canvas)
        if success:
            self.logger.info("Canvas loaded successfully")
        else:
            self.logger.warning(f"Canvas load failed: {message}")