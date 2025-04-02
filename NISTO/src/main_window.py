from PyQt5.QtWidgets import QMainWindow, QAction, QToolBar
from PyQt5.QtGui import QIcon
import os
from controllers.bulk_device_controller import BulkDeviceController
from controllers.bulk_property_controller import BulkPropertyController

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        # ...existing code...
        
        # After creating device_controller
        self.bulk_device_controller = BulkDeviceController(
            self.canvas,
            self.device_controller,
            self.event_bus,
            self.undo_redo_manager
        )
        
        self.bulk_property_controller = BulkPropertyController(
            self.canvas,
            self.device_controller,
            self.event_bus,
            self.undo_redo_manager
        )
        
        # ...existing code...
    
    def _create_menus(self):
        """Create the application menus."""
        # ...existing code...
        
        # Device menu
        devices_menu = self.menuBar().addMenu("&Devices")
        
        add_device_action = QAction("&Add Device...", self)
        add_device_action.setStatusTip("Add a new device to the canvas")
        add_device_action.triggered.connect(self._on_add_device_requested)
        devices_menu.addAction(add_device_action)
        
        bulk_add_action = QAction("Add &Multiple Devices...", self)
        bulk_add_action.setStatusTip("Add multiple different devices in bulk")
        bulk_add_action.triggered.connect(self._on_bulk_add_device_requested)
        devices_menu.addAction(bulk_add_action)
        
        # Add separator
        devices_menu.addSeparator()
        
        # Add bulk edit option
        bulk_edit_action = QAction("&Edit Selected Devices...", self)
        bulk_edit_action.setStatusTip("Edit properties of multiple selected devices")
        bulk_edit_action.triggered.connect(self._on_edit_selected_devices)
        devices_menu.addAction(bulk_edit_action)
        
        # ...existing code...
    
    def _create_toolbars(self):
        """Create the application toolbars."""
        # ...existing code...
        
        # Add bulk device button to the device toolbar
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icons", "bulk_add.png")
        if not os.path.exists(icon_path):
            # Use a fallback icon if the bulk_add.png doesn't exist
            bulk_device_button = QAction("Add Multiple", self)
        else:
            bulk_device_button = QAction(QIcon(icon_path), "Add Multiple", self)
            
        bulk_device_button.setToolTip("Add multiple different devices at once")
        bulk_device_button.triggered.connect(self._on_bulk_add_device_requested)
        
        # Find the device toolbar or create it
        if hasattr(self, 'device_toolbar'):
            self.device_toolbar.addAction(bulk_device_button)
        else:
            self.device_toolbar = self.addToolBar("Device Tools")
            self.device_toolbar.addAction(bulk_device_button)
        
        # Add bulk edit button
        bulk_edit_button = QAction("Edit Multiple", self)
        bulk_edit_button.setToolTip("Edit properties of selected devices")
        bulk_edit_button.triggered.connect(self._on_edit_selected_devices)
        self.device_toolbar.addAction(bulk_edit_button)
        
        # ...existing code...
    
    def _on_bulk_add_device_requested(self):
        """Show dialog to add multiple devices in bulk."""
        # Get the center of the current view as default position
        view_center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
        self.bulk_device_controller.show_bulk_add_dialog(view_center)
    
    def _on_edit_selected_devices(self):
        """Show dialog to edit properties of selected devices."""
        self.bulk_property_controller.edit_selected_devices()
    
    # ...existing code...
