import logging
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor

from views.canvas.modes.base_mode import CanvasMode
from ..graphics_manager import TemporaryGraphicsManager

class AddBoundaryMode(CanvasMode):  # Changed class name from BoundaryMode to AddBoundaryMode
    """Mode for adding boundaries to the canvas."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
        self.start_pos = None
        self.current_rect = None
        self.is_drawing = False
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Start drawing a boundary."""
        if event.button() == Qt.LeftButton:
            self.start_pos = scene_pos
            self.is_drawing = True
            self.logger.debug(f"AddBoundaryMode: Starting boundary at {scene_pos.x():.1f}, {scene_pos.y():.1f}")
            return True
        return False
        
    def mouse_move_event(self, event):
        """Update boundary preview while drawing."""
        if self.is_drawing and self.start_pos:
            scene_pos = self.canvas.mapToScene(event.pos())
            rect = QRectF(self.start_pos, scene_pos)
            
            # Show preview rectangle
            if self.current_rect:
                self.canvas.temp_graphics.update_rect(self.current_rect, rect)
            else:
                self.current_rect = self.canvas.temp_graphics.add_rect(rect)
                
            return True
        return False
        
    def mouse_release_event(self, event, scene_pos=None, item=None):
        """Finish drawing the boundary."""
        if self.is_drawing and event.button() == Qt.LeftButton and self.start_pos and scene_pos:
            rect = QRectF(self.start_pos, scene_pos).normalized()
            
            # Only create if the rectangle has some size
            if rect.width() > 10 and rect.height() > 10:
                self.logger.debug(f"AddBoundaryMode: Created boundary {rect.x():.1f},{rect.y():.1f} {rect.width():.1f}x{rect.height():.1f}")
                self.canvas.add_boundary_requested.emit(rect)
                
            # Clean up temporary graphics
            if self.current_rect:
                self.canvas.temp_graphics.remove_item(self.current_rect)
                self.current_rect = None
                
            # Reset state
            self.is_drawing = False
            self.start_pos = None
            return True
            
        return False
        
    def cursor(self):
        """Use crosshair cursor for boundary drawing."""
        return Qt.CrossCursor
