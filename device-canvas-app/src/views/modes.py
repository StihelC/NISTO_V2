from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QColor

class CanvasMode:
    """Base class for canvas interaction modes."""
    
    def __init__(self, canvas):
        self.canvas = canvas
    
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
    
    def mouse_release_event(self, event):
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
        pass
    
    def deactivate(self):
        """Called when this mode is deactivated."""
        pass


class SelectMode(CanvasMode):
    """Mode for selecting and manipulating devices."""
    
    def handle_mouse_press(self, event, scene_pos, item):
        # Let the default QGraphicsView selection behavior handle it
        return False
    
    def cursor(self):
        return Qt.ArrowCursor
