import logging
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPixmapItem
from PyQt5.QtGui import QPen, QColor

from views.canvas.modes.base_mode import DeviceInteractionMode
from models.device import Device

class AddConnectionMode(DeviceInteractionMode):
    """Mode for adding connections between devices."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
        self.source_device = None
        self.temp_line = None
        self.hover_device = None
    
    def activate(self):
        """Called when this mode is activated."""
        super().activate()
        self.logger.debug("AddConnectionMode: Activated")
        # Clear any existing temp line to ensure clean state
        if self.temp_line is not None:
            try:
                self.canvas.temp_graphics.remove_item(self.temp_line)
            except:
                pass
            self.temp_line = None
        
        self.canvas.statusMessage.emit("Click on a device to start creating a connection")
    
    def is_device(self, item):
        """Check if the item is a device with better type checking."""
        # Try direct isinstance check
        if isinstance(item, Device):
            return True
        
        # Check if it's in the canvas devices list
        if item in self.canvas.devices:
            return True
            
        # Check parent item if this is a child component
        if item and item.parentItem() and item.parentItem() in self.canvas.devices:
            return True
            
        return False
    
    def get_actual_device(self, item):
        """Get the actual Device object from any item that might be part of a device."""
        if not item:
            return None
            
        # If it's already a Device, return it
        if isinstance(item, Device):
            return item
            
        # If it's in the canvas devices list
        if item in self.canvas.devices:
            return item
            
        # If it's a child item (like icon or text label)
        if item.parentItem():
            parent = item.parentItem()
            # Check if parent is a device
            if isinstance(parent, Device) or parent in self.canvas.devices:
                return parent
            
        # Last resort - check all devices to see if this is a child component
        for device in self.canvas.devices:
            if item in device.childItems():
                return device
                
        return None
    
    def get_device_at_position(self, pos):
        """Get a device at the given scene position with better detection."""
        # First try direct hit testing
        item = self.canvas.scene().itemAt(pos, self.canvas.transform())
        
        # Get the actual device object
        device = self.get_actual_device(item)
        if device:
            return device
            
        # Try checking all devices for proximity if no direct hit
        min_distance = 20  # Max distance to consider a hit
        closest_device = None
        
        for device in self.canvas.devices:
            center = device.get_center_position() if hasattr(device, 'get_center_position') else device.scenePos()
            dx = center.x() - pos.x()
            dy = center.y() - pos.y()
            distance = (dx*dx + dy*dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_device = device
                
        return closest_device
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Handle selecting source and target devices for connection."""
        if event.button() == Qt.LeftButton:
            device = self.get_device_at_position(scene_pos)
            
            # If no source device selected yet
            if not self.source_device:
                if device:
                    self.source_device = device
                    self.logger.debug(f"AddConnectionMode: Selected source device {device}")
                    
                    # Make sure we have a name attribute for the status message
                    device_name = getattr(device, 'name', 'Device')
                    self.canvas.statusMessage.emit(f"Selected {device_name} as source. Click on another device to connect.")
                    
                    # Force the scene to update to show ports
                    self.canvas.viewport().update()
                    return True
                    
            # If we already have a source device, try to connect to target
            elif device and device != self.source_device:
                self.logger.debug(f"AddConnectionMode: Connecting {self.source_device} to {device}")
                # Create empty connection data dictionary
                connection_data = {
                    'type': 'ethernet',  # Default connection type
                    'label': '',         # No label by default
                    'bandwidth': '',     # No bandwidth specification
                    'latency': ''        # No latency specification
                }
                
                self.canvas.add_connection_requested.emit(self.source_device, device, connection_data)
                
                # Reset state
                self.source_device = None
                if self.temp_line is not None:
                    try:
                        self.canvas.temp_graphics.remove_item(self.temp_line)
                    except:
                        pass
                    self.temp_line = None
                
                self.canvas.statusMessage.emit("Connection created. Click on a device to start a new connection.")
                return True
                
            # Reset if clicking on empty space
            elif not device:
                self.source_device = None
                if self.temp_line is not None:
                    try:
                        self.canvas.temp_graphics.remove_item(self.temp_line)
                    except:
                        pass
                    self.temp_line = None
                
                self.canvas.statusMessage.emit("Connection cancelled. Click on a device to start again.")
                return True
                
        return False
        
    def mouse_move_event(self, event):
        """Update temporary connection line while drawing."""
        # First check for devices under the cursor for hover highlighting
        scene_pos = self.canvas.mapToScene(event.pos())
        hover_device = self.get_device_at_position(scene_pos)
        
        # Update hover device if changed
        if hover_device != self.hover_device:
            self.hover_device = hover_device
            self.canvas.viewport().update()  # Force redraw to show connection points

        # Draw temporary connection line if we have a source device
        if self.source_device:
            # Get center position of the source device
            source_pos = self.get_device_center(self.source_device)
            
            # Debug the positions occasionally
            if event.pos().x() % 200 == 0 and event.pos().y() % 200 == 0:
                self.logger.debug(f"AddConnectionMode: Drawing preview line from {source_pos.x():.1f},{source_pos.y():.1f} to {scene_pos.x():.1f},{scene_pos.y():.1f}")
            
            try:
                # Update existing line or create a new one
                if self.temp_line is not None:
                    result = self.canvas.temp_graphics.update_line(self.temp_line, source_pos, scene_pos)
                    if not result:
                        # If update failed, recreate the line
                        self.logger.debug(f"AddConnectionMode: Line update failed, recreating line")
                        try:
                            self.canvas.temp_graphics.remove_item(self.temp_line)
                        except:
                            pass
                        self.temp_line = self.canvas.temp_graphics.add_line(source_pos, scene_pos)
                else:
                    self.temp_line = self.canvas.temp_graphics.add_line(source_pos, scene_pos)
                    self.logger.debug(f"AddConnectionMode: Created new temp line with ID {self.temp_line}")
            except Exception as e:
                self.logger.error(f"Error updating temporary line: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                
            return True
        
        return False
    
    def get_device_center(self, device):
        """Get the center position of a device with better error handling."""
        try:
            # Try get_center_position method first
            if hasattr(device, 'get_center_position'):
                return device.get_center_position()
            
            # Try scenePos + bounding rect center
            if hasattr(device, 'scenePos') and hasattr(device, 'boundingRect'):
                pos = device.scenePos()
                rect = device.boundingRect()
                return QPointF(
                    pos.x() + rect.width() / 2,
                    pos.y() + rect.height() / 2
                )
                
            # Last resort: just use scene position
            return device.scenePos()
            
        except Exception as e:
            self.logger.error(f"Error getting device center: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Return scene position as fallback
            return device.scenePos()
        
    def deactivate(self):
        """Clean up when mode is deactivated."""
        super().deactivate()
        self.source_device = None
        self.hover_device = None
        
        # Remove temporary line
        if self.temp_line is not None:
            self.logger.debug(f"AddConnectionMode: Removing temp_line {self.temp_line} during deactivate")
            try:
                self.canvas.temp_graphics.remove_item(self.temp_line)
            except Exception as e:
                self.logger.error(f"Failed to remove temp_line: {e}")
            self.temp_line = None
            
    def cursor(self):
        """Use pointer cursor for connection mode."""
        if self.source_device:
            return Qt.CrossCursor  # Shows we're in connecting state
        return Qt.PointingHandCursor
