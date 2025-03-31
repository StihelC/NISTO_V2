import logging
from PyQt5.QtCore import Qt
from views.canvas.modes.base_mode import CanvasMode

class AddDeviceMode(CanvasMode):
    """Mode for adding devices to the canvas."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Add a device at the clicked position."""
        if event.button() == Qt.LeftButton:
            self.logger.debug(f"AddDeviceMode: Adding device at {scene_pos.x():.1f}, {scene_pos.y():.1f}")
            self.canvas.add_device_requested.emit(scene_pos)
            return True
        return False
        
    def cursor(self):
        """Use crosshair cursor for device placement."""
        return Qt.CrossCursor
