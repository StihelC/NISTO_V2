from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsItem

# Import models needed for Device checks
from models.device import Device

class CanvasMode:
    """Base class for canvas interaction modes using template method pattern."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        # Add a name attribute for easier identification
        self.name = self.__class__.__name__
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Template method for mouse press - override in subclasses."""
        return False
    
    def mouse_press_event(self, event):
        """Handle mouse press event with common logic."""
        if event.button() == Qt.LeftButton:
            scene_pos = self.canvas.mapToScene(event.pos())
            item = self.canvas.scene().itemAt(scene_pos, self.canvas.transform())
            if self.handle_mouse_press(event, scene_pos, item):
                event.accept()
                return True
        return False
    
    def mouse_move_event(self, event):
        """Handle mouse move event in this mode."""
        return False
    
    def mouse_release_event(self, event, scene_pos=None, item=None):
        """Handle mouse release event in this mode."""
        return False
    
    def key_press_event(self, event):
        """Handle key press event in this mode."""
        return False
    
    def cursor(self):
        """Return the cursor to use in this mode."""
        return Qt.ArrowCursor
    
    def activate(self):
        """Called when this mode is activated."""
        # By default, make devices non-draggable in every mode
        self.set_devices_draggable(False)
    
    def deactivate(self):
        """Called when this mode is deactivated."""
        pass
    
    def set_devices_draggable(self, draggable):
        """Helper to set draggability for all devices."""
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, draggable)


class DeviceInteractionMode(CanvasMode):
    """Base class for modes that interact with devices."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        
    def is_device(self, item):
        """Check if the item is a device."""
        return isinstance(item, Device)
    
    def get_device_at_position(self, pos):
        """Get a device at the given scene position."""
        item = self.canvas.scene().itemAt(pos, self.canvas.transform())
        if self.is_device(item):
            return item
        return None
