import logging
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QGraphicsItem

from .base_mode import DeviceInteractionMode, CanvasMode
from models.boundary import Boundary
from models.connection import Connection
from models.device import Device

class DeleteMode(DeviceInteractionMode):
    """Mode for deleting items from the canvas."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Delete the item that was clicked on."""
        if event.button() == Qt.LeftButton and item:
            self.logger.debug(f"DeleteMode: Attempting to delete {item.__class__.__name__}")
            
            # Find the top-level parent item if it's a device component
            top_item = item
            while top_item.parentItem():
                top_item = top_item.parentItem()
                self.logger.debug(f"DeleteMode: Found parent item {top_item.__class__.__name__}")
            
            # Check what kind of item we're dealing with
            if isinstance(top_item, Device) or self.is_device(top_item):
                self.logger.debug(f"DeleteMode: Deleting device {top_item}")
                self.canvas.delete_device_requested.emit(top_item)
            elif isinstance(top_item, Connection):
                self.logger.debug(f"DeleteMode: Deleting connection {top_item}")
                self.canvas.delete_connection_requested.emit(top_item)
            elif isinstance(top_item, Boundary):
                self.logger.debug(f"DeleteMode: Deleting boundary {top_item}")
                self.canvas.delete_boundary_requested.emit(top_item)
            else:
                self.logger.debug(f"DeleteMode: Deleting generic item {top_item}")
                self.canvas.delete_item_requested.emit(top_item)
                
            return True
        return False
        
    def cursor(self):
        """Use a special cursor for delete mode."""
        return Qt.ForbiddenCursor


class DeleteSelectedMode(CanvasMode):
    """Mode for deleting all selected items on the canvas."""
    
    def activate(self):
        """Called when this mode is activated."""
        super().activate()
        # When the mode is activated, immediately delete selected items
        selected_items = self.canvas.scene().selectedItems()
        if selected_items:
            self.canvas.delete_selected_requested.emit()
            # Automatically switch back to select mode after deletion
            from constants import Modes
            QTimer.singleShot(100, lambda: self.canvas.set_mode(Modes.SELECT))
        else:
            # If nothing is selected, show a hint and switch back to select mode
            self.canvas.statusMessage.emit("No items selected. Select items first and try again.")
            from constants import Modes
            QTimer.singleShot(100, lambda: self.canvas.set_mode(Modes.SELECT))
    
    def cursor(self):
        """Return the cursor to use in this mode."""
        return Qt.ForbiddenCursor
