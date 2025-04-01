import logging
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QGraphicsItem

from views.canvas.modes.base_mode import CanvasMode
from models.boundary import Boundary
from models.device import Device

class SelectMode(CanvasMode):
    """Mode for selecting and manipulating devices and boundaries."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
        self.mouse_press_pos = None
        self.drag_started = False
        self.click_item = None
        self.drag_threshold = 5  # Minimum drag distance to consider it a drag
    
    def activate(self):
        """Enable dragging when select mode is active."""
        self.logger.debug("SelectMode: Activated")
        
        # Set rubber band selection mode
        self.canvas.setDragMode(self.canvas.RubberBandDrag)
        
        # Make all devices draggable and selectable
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, True)
            device.setFlag(QGraphicsItem.ItemIsSelectable, True)
            
            # Make sure all child items are also draggable
            for child in device.childItems():
                child.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        # Make all connections selectable
        for connection in self.canvas.connections:
            connection.setFlag(QGraphicsItem.ItemIsSelectable, True)
            connection.setFlag(QGraphicsItem.ItemIsFocusable, True)
    
    def deactivate(self):
        """Disable dragging when leaving select mode."""
        self.logger.debug("SelectMode: Deactivated")
        
        # Disable dragging for all devices
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, False)
        
        # We intentionally keep connections selectable even in other modes
        # so they can be selected by clicking directly on them
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Handle mouse button press events."""
        self.mouse_press_pos = scene_pos
        self.drag_started = False
        
        # For double clicks on boundaries, start editing the label
        if event.type() == QEvent.MouseButtonDblClick and isinstance(item, Boundary):
            if hasattr(item, 'label') and item.label:
                item.label.start_editing()
                return True
        
        # Handle left button press for potential drag or selection
        if event.button() == Qt.LeftButton:
            # Find if we clicked on a device or part of a device
            device = None
            if isinstance(item, Device):
                device = item
            elif item and item.parentItem() and isinstance(item.parentItem(), Device):
                device = item.parentItem()
            
            if device:
                self.click_item = device
                
                # If Shift is not pressed, clear selection first
                if not (event.modifiers() & Qt.ShiftModifier) and not device.isSelected():
                    self.canvas.scene().clearSelection()
                    
                # Select the device
                device.setSelected(True)
                
                # Switch to NoDrag mode for item dragging
                self.canvas.setDragMode(self.canvas.NoDrag)
                
                # Return False to let Qt's default implementation handle the drag
                return False
                
            else:
                # Clicked on empty space - prepare for rubber band selection
                if not (event.modifiers() & Qt.ShiftModifier):
                    self.canvas.scene().clearSelection()
                
                # Make sure we're in rubber band mode
                self.canvas.setDragMode(self.canvas.RubberBandDrag)
                return True  # We'll handle this event
        
        return False
    
    def mouse_move_event(self, event):
        """Handle mouse move events for selection box and dragging."""
        if event.buttons() & Qt.LeftButton and self.mouse_press_pos:
            # Get current scene position
            scene_pos = self.canvas.mapToScene(event.pos())
            
            # Calculate distance moved
            dx = scene_pos.x() - self.mouse_press_pos.x()
            dy = scene_pos.y() - self.mouse_press_pos.y()
            dist = (dx*dx + dy*dy) ** 0.5
            
            # If we've moved far enough to consider it a drag
            if dist > self.drag_threshold and not self.drag_started:
                self.drag_started = True
                
                # Set drag mode based on whether we're dragging a device or creating selection box
                if self.click_item:
                    # Ensure proper drag mode for device dragging
                    self.canvas.setDragMode(self.canvas.NoDrag)
                else:
                    # Use rubber band mode for selection box
                    self.canvas.setDragMode(self.canvas.RubberBandDrag)
            
            return True
        
        return False
    
    def mouse_release_event(self, event, scene_pos=None, item=None):
        """Handle mouse release to complete selection box or drag operation."""
        if event.button() == Qt.LeftButton and self.mouse_press_pos:
            # Reset state variables
            self.mouse_press_pos = None
            self.drag_started = False
            
            # Always switch back to rubber band selection mode for next operation
            self.canvas.setDragMode(self.canvas.RubberBandDrag)
            
            # Clear reference to clicked item
            self.click_item = None
            
            # Notify about selection changes
            self.canvas.selection_changed.emit(self.canvas.scene().selectedItems())
            
            return True
        
        return False
    
    def key_press_event(self, event):
        """Handle key press events for selection operations."""
        # Handle Ctrl+A for select all
        if event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            for item in self.canvas.scene().items():
                if item.isVisible() and (item in self.canvas.devices or item in self.canvas.boundaries):
                    item.setSelected(True)
            
            # Emit selection changed signal
            self.canvas.selection_changed.emit(self.canvas.scene().selectedItems())
            return True
            
        # Handle Escape key to clear selection
        if event.key() == Qt.Key_Escape:
            self.canvas.scene().clearSelection()
            # Emit selection changed signal
            self.canvas.selection_changed.emit([])
            return True
            
        return False
