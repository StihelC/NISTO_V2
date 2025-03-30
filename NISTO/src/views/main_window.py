from PyQt5.QtWidgets import QMainWindow, QDialog, QMessageBox
from PyQt5.QtCore import QPointF, QTimer
from PyQt5.QtGui import QColor
import logging

from .canvas import Canvas
from constants import Modes
from controllers.menu_manager import MenuManager
from controllers.device_controller import DeviceController
from controllers.connection_controller import ConnectionController
from controllers.boundary_controller import BoundaryController
from utils.event_bus import EventBus

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
        
        # Create event bus for communication between components
        self.event_bus = EventBus()
        
        # Initialize controllers
        self.device_controller = DeviceController(self.canvas, self.event_bus)
        self.connection_controller = ConnectionController(self.canvas, self.event_bus)
        self.boundary_controller = BoundaryController(self.canvas, self.event_bus)
        
        # Create menu manager
        self.menu_manager = MenuManager(self, self.canvas, self.event_bus)
        self.menu_manager.create_toolbar()
        
        # Connect canvas signals to controllers
        self.connect_signals()
        
        # Set initial mode
        self.set_mode(Modes.SELECT)

    def connect_signals(self):
        """Connect canvas signals to appropriate controller handlers."""
        self.canvas.add_device_requested.connect(self.device_controller.on_add_device_requested)
        self.canvas.delete_device_requested.connect(self.device_controller.on_delete_device_requested)
        self.canvas.add_boundary_requested.connect(self.boundary_controller.on_add_boundary_requested)
        self.canvas.add_connection_requested.connect(self.connection_controller.on_add_connection_requested)
        self.canvas.delete_connection_requested.connect(self.connection_controller.on_delete_connection_requested)
        self.canvas.delete_boundary_requested.connect(self.boundary_controller.on_delete_boundary_requested)
        self.canvas.delete_item_requested.connect(self.on_delete_item_requested)
    
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