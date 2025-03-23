from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsLineItem,
                           QGraphicsRectItem, QGraphicsItemGroup, QGraphicsItem)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF, QEvent
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen  # Ensure QPen is imported
import logging
from models.device import Device
from models.boundary import Boundary
from models.connection import Connection
from controllers.mode_manager import ModeManager
from constants import Modes

class TemporaryGraphicsManager:
    """Helper class to manage temporary graphics items during interactions."""
    
    def __init__(self, scene):
        self.scene = scene
        self.temp_items = []
    
    def add_temp_rect(self, rect, pen=None, brush=None):
        """Add a temporary rectangle to the scene."""
        if pen is None:
            pen = QPen(QColor(0, 0, 255, 180), 2, Qt.DashLine)
        
        if brush is None:
            brush = QBrush(QColor(0, 0, 255, 50))
        
        rect_item = QGraphicsRectItem(rect)
        rect_item.setPen(pen)
        rect_item.setBrush(brush)
        self.scene.addItem(rect_item)
        self.temp_items.append(rect_item)
        return rect_item
    
    def add_temp_line(self, start_pos, end_pos=None, style=Qt.DashLine, color=QColor(0, 0, 0, 180), width=2):
        """Add a temporary line to the scene."""
        end_pos = end_pos or start_pos  # If no end_pos provided, use start_pos
        
        # Create a line item
        line = QGraphicsLineItem(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
        
        # Style the line
        pen = QPen(color, width, style)
        pen.setCapStyle(Qt.RoundCap)  # Rounded ends look better
        line.setPen(pen)
        
        # Add to scene and track it
        self.scene.addItem(line)
        self.temp_items.append(line)
        return line
    
    def update_line(self, line, end_pos):
        """Update the endpoint of a temporary line."""
        if line in self.temp_items:
            line_obj = line.line()
            line.setLine(line_obj.x1(), line_obj.y1(), end_pos.x(), end_pos.y())
    
    def clear(self):
        """Remove all temporary items from the scene."""
        for item in self.temp_items:
            if item.scene() == self.scene:  # Check if item is still in the scene
                self.scene.removeItem(item)
        self.temp_items.clear()

# Strategy pattern for canvas modes
class CanvasMode:
    """Base class for canvas interaction modes using template method pattern."""
    
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
    
    def is_device(self, item):
        """Check if an item is a device."""
        return isinstance(item, Device)
    
    def get_device_at_position(self, pos):
        """Get a device at the given scene position."""
        item = self.canvas.scene().itemAt(pos, self.canvas.transform())
        if self.is_device(item):
            return item
        return None


class SelectMode(CanvasMode):
    """Mode for selecting and manipulating devices and boundaries."""
    
    def activate(self):
        """Enable dragging when select mode is active."""
        self.set_devices_draggable(True)
    
    def deactivate(self):
        """Disable dragging when leaving select mode."""
        self.set_devices_draggable(False)
    
    def handle_mouse_press(self, event, scene_pos, item):
        # For double clicks on boundaries, start editing the label
        if event.type() == QEvent.MouseButtonDblClick and isinstance(item, Boundary):
            if item.label:
                item.label.start_editing()
                return True
        # Let the default QGraphicsView selection behavior handle it
        return False
    
    def cursor(self):
        return Qt.ArrowCursor


class AddDeviceMode(CanvasMode):
    """Mode for adding devices to the canvas."""
    
    def handle_mouse_press(self, event, scene_pos, item):
        self.canvas.add_device_requested.emit(scene_pos)
        return True
    
    def cursor(self):
        return Qt.CrossCursor


class DeleteMode(DeviceInteractionMode):
    """Mode for deleting items from the canvas."""
    
    def handle_mouse_press(self, event, scene_pos, item):
        if item:
            if self.is_device(item):
                self.canvas.delete_device_requested.emit(item)
                return True
            elif isinstance(item, Boundary):
                self.canvas.delete_boundary_requested.emit(item)
                return True
            elif isinstance(item, Connection):
                self.canvas.delete_connection_requested.emit(item)
                return True
            else:
                # For other item types
                self.canvas.delete_item_requested.emit(item)
                return True
        return False
    
    def cursor(self):
        return Qt.ForbiddenCursor


class AddBoundaryMode(CanvasMode):
    """Mode for adding boundary regions to the canvas."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.start_pos = None
        self.temp_graphics = TemporaryGraphicsManager(canvas.scene())
        self.current_rect = None
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Handle first click to start boundary creation."""
        self.start_pos = scene_pos
        return True
    
    def mouse_move_event(self, event):
        if event.buttons() & Qt.LeftButton and self.start_pos:
            current_pos = self.canvas.mapToScene(event.pos())
            
            # Remove previous rectangle
            self.temp_graphics.clear()
            
            # Create updated rectangle
            rect = QRectF(self.start_pos, current_pos).normalized()
            self.current_rect = self.temp_graphics.add_temp_rect(rect)
            
            return True
        return False
    
    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton and self.start_pos:
            end_pos = self.canvas.mapToScene(event.pos())
            rect = QRectF(self.start_pos, end_pos).normalized()
            
            # Only create boundary if it has a reasonable size
            min_size = 20  # Minimum size in scene units
            if rect.width() > min_size and rect.height() > min_size:
                # Clean up temp graphics and emit signal with the final rect
                self.temp_graphics.clear()
                self.canvas.add_boundary_requested.emit(rect)
            else:
                # If too small, just clean up without creating
                self.temp_graphics.clear()
                
            self.start_pos = None
            return True
        return False
    
    def deactivate(self):
        self.temp_graphics.clear()
        self.start_pos = None
    
    def cursor(self):
        return Qt.CrossCursor


class AddConnectionMode(CanvasMode):
    """Mode for creating connections between devices."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.source_device = None
        self.hover_device = None  # Track device under cursor
        self.temp_line = None
        self.logger = logging.getLogger(__name__)
    
    def activate(self):
        """Called when this mode is activated."""
        # Make devices non-draggable in this mode
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, False)
            
        # Force update to show connection points
        self.canvas.viewport().update()
        
        self.logger.debug("Connection mode activated")
    
    def deactivate(self):
        """Called when this mode is deactivated."""
        self.clean_up()
        
        # Force update to hide connection points
        self.canvas.viewport().update()
        
        self.logger.debug("Connection mode deactivated")
    
    def is_device(self, item):
        """Check if an item is a device."""
        return isinstance(item, Device)
    
    def get_device_at_position(self, pos):
        """Get a device at the given scene position."""
        # Try direct hit test
        item = self.canvas.scene().itemAt(pos, self.canvas.transform())
        if self.is_device(item):
            return item
            
        # If that fails, check all devices manually
        for device in self.canvas.devices:
            if device.sceneBoundingRect().contains(pos):
                return device
                
        return None
    
    def mouse_press_event(self, event):
        """Handle mouse press event."""
        if event.button() != Qt.LeftButton:
            return False
        
        # Get the position in scene coordinates
        scene_pos = self.canvas.mapToScene(event.pos())
        
        # Check if we clicked on a device
        device = self.get_device_at_position(scene_pos)
        
        if device:
            if not self.source_device:
                # First click - set source device
                self.source_device = device
                
                # Get the nearest port to where we clicked
                start_port = device.get_nearest_port(scene_pos)
                
                # Create a temporary line for preview
                self.temp_line = QGraphicsLineItem(
                    start_port.x(), start_port.y(), 
                    start_port.x(), start_port.y()
                )
                
                # Make the line visually distinctive
                pen = QPen(QColor(0, 120, 215), 2, Qt.DashLine)
                pen.setDashPattern([5, 3])  # 5px dash, 3px gap
                pen.setCapStyle(Qt.RoundCap)
                self.temp_line.setPen(pen)
                
                # Make sure it's on top of other items
                self.temp_line.setZValue(1000) 
                
                # Add to scene
                self.canvas.scene().addItem(self.temp_line)
                
                self.logger.debug(f"Started connection from device: {device}")
                return True
            else:
                # Second click - finalize connection
                if device != self.source_device:
                    # Emit signal to the canvas to create the connection
                    # Don't call add_connection directly on the device
                    self.logger.debug(f"Creating connection from {self.source_device} to {device}")
                    self.canvas.add_connection_requested.emit(self.source_device, device)
                
                # Clean up temporary items
                self.clean_up()
                return True
        elif self.source_device:
            # Clicked somewhere else - cancel the operation
            self.logger.debug("Connection cancelled")
            self.clean_up()
            return True
        
        return False
    
    def mouse_move_event(self, event):
        """Update line position during mouse movement."""
        current_pos = self.canvas.mapToScene(event.pos())
        
        # Check if hovering over a device
        hover_device = self.get_device_at_position(current_pos)
        if hover_device != self.hover_device:
            # Device under cursor changed
            self.hover_device = hover_device
            self.canvas.viewport().update()  # Force redraw to update connection points
        
        if self.source_device and self.temp_line:
            # Get the start position from the existing line
            line = self.temp_line.line()
            start_pos = QPointF(line.x1(), line.y1())
            
            # Update end position
            end_pos = current_pos
            
            # If hovering over a potential target device, snap to nearest port
            if hover_device and hover_device != self.source_device:
                end_pos = hover_device.get_nearest_port(current_pos)
            
            # Update the line
            self.temp_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            return True
            
        return False
    
    def clean_up(self):
        """Clean up temporary items and reset state."""
        if self.temp_line:
            self.canvas.scene().removeItem(self.temp_line)
            self.temp_line = None
        
        self.source_device = None
        self.hover_device = None
    
    def key_press_event(self, event):
        """Handle key press events."""
        # Cancel with Escape key
        if event.key() == Qt.Key_Escape and self.source_device:
            self.logger.debug("Connection cancelled with Escape key")
            self.clean_up()
            return True
        return False
    
    def cursor(self):
        """Return the appropriate cursor for this mode."""
        if self.source_device:
            return Qt.PointingHandCursor
        return Qt.CrossCursor


class Canvas(QGraphicsView):
    """Canvas widget for displaying and interacting with network devices."""
    
    # Signals for different actions
    add_device_requested = pyqtSignal(QPointF)
    delete_device_requested = pyqtSignal(object)
    delete_item_requested = pyqtSignal(object)
    add_boundary_requested = pyqtSignal(object)  # QRectF
    add_connection_requested = pyqtSignal(object, object)  # source, target
    delete_connection_requested = pyqtSignal(object)  # connection
    delete_boundary_requested = pyqtSignal(object)  # boundary
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Create a scene to hold the items
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # Lists to store items
        self.devices = []
        self.boundaries = []
        self.connections = []
        
        # Set rendering hints for better quality
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # Set scene rectangle (optional, can be adjusted)
        self._scene.setSceneRect(-2000, -2000, 4000, 4000)
        
        # Setup appearance
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Mouse tracking
        self.setMouseTracking(True)
        
        # Setup mode manager
        self.mode_manager = ModeManager(self)
        
        # Set up modes
        self._setup_modes()
        
        # Set initial mode
        self.set_mode(Modes.SELECT)
    
    def _setup_modes(self):
        """Initialize all available interaction modes."""
        # Use a dictionary to create modes
        mode_classes = {
            Modes.SELECT: SelectMode,
            Modes.ADD_DEVICE: AddDeviceMode,
            Modes.DELETE: DeleteMode,
            Modes.ADD_BOUNDARY: AddBoundaryMode,
            Modes.ADD_CONNECTION: AddConnectionMode
        }
        
        # Create and register each mode with the manager
        for mode_id, mode_class in mode_classes.items():
            mode = mode_class(self)
            self.mode_manager.register_mode(mode_id, mode)
    
    def set_mode(self, mode):
        """Set the current interaction mode."""
        self.mode_manager.set_mode(mode)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        try:
            # Debug print
            print(f"Canvas: mousePressEvent at {event.pos()}")
            
            if not self.mode_manager.handle_event("mouse_press_event", event):
                super().mousePressEvent(event)
        except Exception as e:
            import traceback
            self.logger.error(f"Error in mousePressEvent: {str(e)}")
            traceback.print_exc()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        try:
            # Only debug occasionally to avoid console spam
            if event.pos().x() % 100 == 0 and event.pos().y() % 100 == 0:
                print(f"Canvas: mouseMoveEvent at {event.pos()}")
                
            if not self.mode_manager.handle_event("mouse_move_event", event):
                super().mouseMoveEvent(event)
        except Exception as e:
            import traceback
            self.logger.error(f"Error in mouseMoveEvent: {str(e)}")
            traceback.print_exc()
    
    def mouseReleaseEvent(self, event):
        if not self.mode_manager.handle_event("mouse_release_event", event):
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        if not self.mode_manager.handle_event("key_press_event", event):
            super().keyPressEvent(event)
    
    def scene(self):
        """Get the graphics scene."""
        return self._scene
    
    def test_temporary_graphics(self):
        """Test method to verify temporary graphics are working."""
        temp_graphics = TemporaryGraphicsManager(self.scene())
        
        # Create a line from center to right
        center = QPointF(0, 0)
        right = QPointF(200, 0)
        line = temp_graphics.add_temp_line(center, right, 
                                          color=QColor(255, 0, 0, 200),
                                          width=5)
        
        # Schedule removal after 3 seconds
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(3000, temp_graphics.clear)