from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPen, QColor, QBrush

class SelectionBox:
    """
    Helper class to draw and track rubber-band selection boxes.
    Manages the visual representation of a selection area.
    """
    
    def __init__(self, scene):
        """Initialize with a reference to the scene."""
        self.scene = scene
        self.start_point = None
        self.current_rect = None
        self.selection_rect_item = None
        
        # Style for the selection box
        self.pen = QPen(QColor(70, 130, 180), 1, Qt.DashLine)
        self.brush = QBrush(QColor(70, 130, 180, 40))
    
    def start(self, start_point):
        """Start drawing a selection box from the given point."""
        self.start_point = start_point
        
        # Create the initial rectangle item if it doesn't exist
        if not self.selection_rect_item:
            self.selection_rect_item = QGraphicsRectItem(QRectF(start_point, start_point))
            self.selection_rect_item.setPen(self.pen)
            self.selection_rect_item.setBrush(self.brush)
            self.scene.addItem(self.selection_rect_item)
        else:
            # If it exists, just update its position
            self.selection_rect_item.setRect(QRectF(start_point, start_point))
            self.selection_rect_item.show()
    
    def update(self, current_point):
        """Update the selection box to the current mouse position."""
        if not self.start_point or not self.selection_rect_item:
            return
            
        # Calculate the rect between start and current point
        rect = QRectF(self.start_point, current_point).normalized()
        self.current_rect = rect
        
        # Update the visual rect item
        self.selection_rect_item.setRect(rect)
    
    def end(self):
        """Finish the selection operation and return the final rect."""
        final_rect = self.current_rect
        
        # Hide the selection rect
        if self.selection_rect_item:
            self.selection_rect_item.hide()
            
        # Reset state
        self.start_point = None
        self.current_rect = None
        
        return final_rect
    
    def cancel(self):
        """Cancel the current selection operation."""
        if self.selection_rect_item:
            self.selection_rect_item.hide()
            
        self.start_point = None
        self.current_rect = None
    
    def __del__(self):
        """Clean up when the object is deleted."""
        if self.selection_rect_item and self.scene:
            self.scene.removeItem(self.selection_rect_item)
