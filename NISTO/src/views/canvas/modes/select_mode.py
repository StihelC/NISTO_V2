import logging
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QGraphicsItem

from views.canvas.modes.base_mode import CanvasMode
from models.boundary import Boundary
from models.device import Device
from models.connection import Connection

class SelectMode(CanvasMode):
    """Mode for selecting and manipulating devices and boundaries."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
        self.mouse_press_pos = None
        self.drag_started = False
        self.click_item = None
        self.drag_threshold = 5  # Minimum drag distance to consider it a drag
        self.name = "Select Mode"  # Add explicit name for this mode
    
    def activate(self):
        """Enable dragging when select mode is active."""
        self.logger.debug("SelectMode: Activated")
        
        # Clear any selection boxes that might be lingering
        self.canvas.viewport().update()
        
        # Ensure we're in rubber band drag mode
        self.canvas.setDragMode(self.canvas.RubberBandDrag)
        
        # Make sure rubber band selection is visible and uses a larger selection area
        self.canvas.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        
        # Make all devices draggable and selectable
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, True)
            device.setFlag(QGraphicsItem.ItemIsSelectable, True)
            
            # Make sure all child items are also draggable
            for child in device.childItems():
                child.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        # Make all connections selectable and focusable
        for connection in self.canvas.connections:
            connection.setFlag(QGraphicsItem.ItemIsSelectable, True)
            connection.setFlag(QGraphicsItem.ItemIsFocusable, True)
        
        # Make all boundaries selectable
        for boundary in self.canvas.boundaries:
            boundary.setFlag(QGraphicsItem.ItemIsSelectable, True)
            boundary.setFlag(QGraphicsItem.ItemIsMovable, True)
    
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
            # Log for debugging
            self.logger.debug(f"Mouse press in select mode at {scene_pos.x()}, {scene_pos.y()}")
            
            # Check if we clicked on a selectable item
            selectable_item = None
            
            # Check for device or child of device
            if isinstance(item, Device) or (item and item.parentItem() and isinstance(item.parentItem(), Device)):
                selectable_item = item if isinstance(item, Device) else item.parentItem()
                # ...existing code for device selection...
            # Check for connection
            elif isinstance(item, Connection):
                selectable_item = item
                # ...existing code for connection selection...
            # Check for boundary
            elif isinstance(item, Boundary):
                selectable_item = item
                # ...existing code for boundary selection...
            
            # If we found a selectable item
            if selectable_item:
                self.click_item = selectable_item
                
                # If Shift is not pressed, clear selection first
                if not (event.modifiers() & Qt.ShiftModifier) and not selectable_item.isSelected():
                    self.canvas.scene().clearSelection()
                
                # Select the item
                selectable_item.setSelected(True)
                
                # Emit selection changed signal
                self.canvas.selection_changed.emit(self.canvas.scene().selectedItems())
                
                # Only set NoDrag mode for devices (connections can't be dragged)
                if isinstance(selectable_item, Device):
                    self.canvas.setDragMode(self.canvas.NoDrag)
                
                return True  # Event handled
            else:
                # Clicked on empty space - don't handle it here
                # Let the Canvas class handle it directly for rubber band selection
                return False
        
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
                    self.logger.debug("Started rubber band selection")
            
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
            selected_items = self.canvas.scene().selectedItems()
            self.logger.debug(f"Selection complete: {len(selected_items)} items selected")
            self.canvas.selection_changed.emit(selected_items)
            
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
