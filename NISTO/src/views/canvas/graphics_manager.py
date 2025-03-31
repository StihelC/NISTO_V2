from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsRectItem, QGraphicsEllipseItem
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QPen, QColor, QBrush
import logging

class TemporaryGraphicsManager:
    """Manages temporary graphics items used for previews, dragging, etc."""
    
    def __init__(self, scene):
        """Initialize with a reference to the scene where items will be added."""
        self.scene = scene
        self.items = {}  # Dictionary to track created items by ID
        self.counter = 0  # Counter for generating unique IDs
        self.logger = logging.getLogger(__name__)
        
        # Default styles
        self.default_line_pen = QPen(QColor(100, 100, 255, 180), 2, Qt.DashLine)
        self.default_rect_pen = QPen(QColor(100, 100, 255, 180), 2, Qt.DashLine)
        self.default_rect_brush = QBrush(QColor(100, 100, 255, 40))
        self.default_ellipse_pen = QPen(QColor(100, 100, 255, 180), 2, Qt.DashLine)
        self.default_ellipse_brush = QBrush(QColor(100, 100, 255, 40))
    
    def add_line(self, start_point, end_point, pen=None):
        """Add a temporary line to the scene."""
        try:
            # Create line item
            line_item = QGraphicsLineItem(
                start_point.x(), start_point.y(), 
                end_point.x(), end_point.y()
            )
            
            # Set z-value to be on top
            line_item.setZValue(1000)  
            
            # Make line more visible - use solid bright blue line
            pen = QPen(QColor(50, 100, 255, 230), 3, Qt.SolidLine) 
            line_item.setPen(pen)
            
            # Add to scene and track
            self.scene.addItem(line_item)
            item_id = self._get_next_id()
            self.items[item_id] = line_item
            
            self.logger.debug(f"Created temporary line {item_id}")
            return item_id
        except Exception as e:
            self.logger.error(f"Error adding temporary line: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def update_line(self, item_id, start_point=None, end_point=None):
        """Update an existing temporary line."""
        try:
            line_item = self.items.get(item_id)
            if not line_item or not isinstance(line_item, QGraphicsLineItem):
                self.logger.error(f"Failed to update line: Item with ID {item_id} not found or not a line item")
                return False
                
            line = line_item.line()
            
            # Update points if provided
            if start_point:
                line.setP1(start_point)
            if end_point:
                line.setP2(end_point)
                
            # Set the new line
            line_item.setLine(line)
            return True
        except Exception as e:
            self.logger.error(f"Error updating temporary line: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def add_rect(self, rect, pen=None, brush=None):
        """
        Add a temporary rectangle to the scene.
        
        Args:
            rect (QRectF): Rectangle to add
            pen (QPen, optional): Pen for the outline
            brush (QBrush, optional): Brush for filling
            
        Returns:
            int: ID of the created rectangle item
        """
        # Create rectangle item
        rect_item = QGraphicsRectItem(rect)
        
        # Set pen and brush
        if pen is None:
            pen = self.default_rect_pen
        if brush is None:
            brush = self.default_rect_brush
            
        rect_item.setPen(pen)
        rect_item.setBrush(brush)
        
        # Add to scene and track
        self.scene.addItem(rect_item)
        item_id = self._get_next_id()
        self.items[item_id] = rect_item
        
        return item_id
    
    def update_rect(self, item_id, rect):
        """
        Update an existing temporary rectangle.
        
        Args:
            item_id (int): The ID of the rectangle to update
            rect (QRectF): New rectangle dimensions
            
        Returns:
            bool: True if the rectangle was updated, False otherwise
        """
        rect_item = self.items.get(item_id)
        if not rect_item or not isinstance(rect_item, QGraphicsRectItem):
            return False
            
        rect_item.setRect(rect)
        return True
    
    def add_ellipse(self, rect, pen=None, brush=None):
        """
        Add a temporary ellipse to the scene.
        
        Args:
            rect (QRectF): Rectangle that bounds the ellipse
            pen (QPen, optional): Pen for the outline
            brush (QBrush, optional): Brush for filling
            
        Returns:
            int: ID of the created ellipse item
        """
        # Create ellipse item
        ellipse_item = QGraphicsEllipseItem(rect)
        
        # Set pen and brush
        if pen is None:
            pen = self.default_ellipse_pen
        if brush is None:
            brush = self.default_ellipse_brush
            
        ellipse_item.setPen(pen)
        ellipse_item.setBrush(brush)
        
        # Add to scene and track
        self.scene.addItem(ellipse_item)
        item_id = self._get_next_id()
        self.items[item_id] = ellipse_item
        
        return item_id
    
    def update_ellipse(self, item_id, rect):
        """
        Update an existing temporary ellipse.
        
        Args:
            item_id (int): The ID of the ellipse to update
            rect (QRectF): New bounding rectangle
            
        Returns:
            bool: True if the ellipse was updated, False otherwise
        """
        ellipse_item = self.items.get(item_id)
        if not ellipse_item or not isinstance(ellipse_item, QGraphicsEllipseItem):
            return False
            
        ellipse_item.setRect(rect)
        return True
    
    def remove_item(self, item_id):
        """Remove a temporary item from the scene."""
        try:
            item = self.items.get(item_id)
            if not item:
                self.logger.warning(f"Cannot remove item {item_id}: not found")
                return False
                
            self.scene.removeItem(item)
            del self.items[item_id]
            self.logger.debug(f"Removed temporary item {item_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error removing item {item_id}: {str(e)}")
            return False
    
    def clear(self):
        """Remove all temporary items from the scene."""
        for item_id in list(self.items.keys()):
            self.remove_item(item_id)
    
    def _get_next_id(self):
        """Get the next unique ID for an item."""
        self.counter += 1
        return self.counter
