from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsItem

# Import models needed for Device checks
from models.device import Device

class CanvasMode:
    """Base class for canvas interaction modes."""
    
    def __init__(self, canvas):
        """Initialize with a reference to the canvas."""
        self.canvas = canvas
        # Add name attribute with default value based on class name
        self.name = self.__class__.__name__

    def activate(self):
        """Called when the mode is activated."""
        pass
        
    def deactivate(self):
        """Called when the mode is deactivated."""
        pass
        
    def handle_mouse_press(self, event, scene_pos, item):
        """Handle mouse press event.
        
        Args:
            event: The mouse event
            scene_pos: The position in scene coordinates
            item: The item under the cursor (if any)
            
        Returns:
            bool: True if the event was handled, False to pass to default handler
        """
        return False
        
    def mouse_move_event(self, event):
        """Handle mouse move event.
        
        Args:
            event: The mouse event
            
        Returns:
            bool: True if the event was handled, False to pass to default handler
        """
        return False
        
    def mouse_release_event(self, event, scene_pos=None, item=None):
        """Handle mouse release event.
        
        Args:
            event: The mouse event
            scene_pos: The position in scene coordinates
            item: The item under the cursor (if any)
            
        Returns:
            bool: True if the event was handled, False to pass to default handler
        """
        return False
        
    def key_press_event(self, event):
        """Handle key press event.
        
        Args:
            event: The key event
            
        Returns:
            bool: True if the event was handled, False to pass to default handler
        """
        return False
    
    # Renamed to match what's called in mode_manager.py
    def mouse_press_event(self, event, scene_pos=None, item=None):
        """Handle mouse press event - compatibility method.
        
        This method exists to maintain compatibility with the mode_manager,
        and delegates to handle_mouse_press.
        """
        return self.handle_mouse_press(event, scene_pos, item)
        
    def cursor(self):
        """Return the cursor to use for this mode."""
        from PyQt5.QtCore import Qt
        return Qt.ArrowCursor


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

    def get_actual_device(self, item):
        """
        Get the device item from a potential child item.
        
        Args:
            item: The item to check
            
        Returns:
            The device if found, otherwise None
        """
        if not item:
            return None
            
        # If it's already a device, return it
        from models.device import Device
        if isinstance(item, Device):
            return item
            
        # Check if it's a child of a device
        if item.parentItem() and isinstance(item.parentItem(), Device):
            return item.parentItem()
            
        return None
