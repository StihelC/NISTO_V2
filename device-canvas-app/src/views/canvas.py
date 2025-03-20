from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsLineItem,
                           QGraphicsRectItem, QGraphicsItemGroup)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen  # Ensure QPen is imported
from models.device import Device
from models.boundary import Boundary

class TemporaryGraphicsManager:
    """Class to manage temporary graphics items for preview purposes."""
    
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
    
    def clear(self):
        """Remove all temporary items from the scene."""
        for item in self.temp_items:
            if item.scene() == self.scene:
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


class AddDeviceMode(CanvasMode):
    """Mode for adding devices to the canvas."""
    
    def handle_mouse_press(self, event, scene_pos, item):
        self.canvas.add_device_requested.emit(scene_pos)
        return True
    
    def cursor(self):
        return Qt.CrossCursor


class DeleteMode(CanvasMode):
    """Mode for deleting items from the canvas."""
    
    def handle_mouse_press(self, event, scene_pos, item):
        if item:
            if self.is_device(item):
                self.canvas.delete_device_requested.emit(item)
                return True
            elif isinstance(item, Boundary):
                self.canvas.delete_boundary_requested.emit(item)
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
        self.temp_line = None
    
    def handle_mouse_press(self, event, scene_pos, item):
        # Check if we clicked on a device
        if isinstance(item, Device):
            if not self.source_device:
                # First click - select source device
                self.source_device = item
                self.start_temp_line(item.get_port_position())
            else:
                # Second click - create connection if target is a device
                if item != self.source_device:
                    self.canvas.add_connection_requested.emit(self.source_device, item)
                
                # Clean up and reset
                self.clean_up()
            return True
        elif self.source_device:
            # Clicked somewhere else after selecting source - cancel
            self.clean_up()
            return True
        return False
    
    def mouse_move_event(self, event):
        if self.source_device and self.temp_line:
            # Update temporary line endpoint
            current_pos = self.canvas.mapToScene(event.pos())
            self.update_temp_line(current_pos)
            event.accept()
            return True
        return False
    
    def start_temp_line(self, start_pos):
        """Start drawing a temporary connection line."""
        self.temp_line = QGraphicsLineItem(start_pos.x(), start_pos.y(), start_pos.x(), start_pos.y())
        self.temp_line.setPen(QPen(QColor(0, 0, 0, 180), 2, Qt.DashLine))
        self.canvas.scene().addItem(self.temp_line)
    
    def update_temp_line(self, end_pos):
        """Update the temporary connection line endpoint."""
        if self.temp_line:
            line = self.temp_line.line()
            self.temp_line.setLine(line.x1(), line.y1(), end_pos.x(), end_pos.y())
    
    def clean_up(self):
        """Clean up temporary items and reset state."""
        if self.temp_line and self.temp_line in self.canvas.scene().items():
            self.canvas.scene().removeItem(self.temp_line)
        self.source_device = None
        self.temp_line = None
    
    def deactivate(self):
        self.clean_up()
    
    def cursor(self):
        if self.source_device:
            # Change cursor when we've selected a source device
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
    delete_boundary_requested = pyqtSignal(object)

    # Mode constants
    MODE_SELECT = "select"
    MODE_ADD_DEVICE = "add_device"
    MODE_DELETE = "delete"
    MODE_ADD_BOUNDARY = "add_boundary"
    MODE_ADD_CONNECTION = "add_connection"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create a scene to hold the items
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # List to store devices
        self.devices = []
        
        # List to store boundaries
        self.boundaries = []
        
        # Setup rendering hints
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # Set scene rectangle
        self._scene.setSceneRect(-2000, -2000, 4000, 4000)
        
        # Setup appearance
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Mouse tracking
        self.setMouseTracking(True)
        
        # Set up modes
        self._setup_modes()
        self.set_mode(self.MODE_SELECT)
    
    def _setup_modes(self):
        """Initialize all available interaction modes."""
        self.modes = {
            self.MODE_SELECT: SelectMode(self),
            self.MODE_ADD_DEVICE: AddDeviceMode(self),
            self.MODE_DELETE: DeleteMode(self),
            self.MODE_ADD_BOUNDARY: AddBoundaryMode(self),
            self.MODE_ADD_CONNECTION: AddConnectionMode(self)
        }
        self.current_mode = None
    
    def set_mode(self, mode):
        """Set the current interaction mode."""
        if mode not in self.modes:
            print(f"Warning: Unknown mode '{mode}'")
            mode = self.MODE_SELECT
            
        # Deactivate current mode if exists
        if self.current_mode:
            self.modes[self.current_mode].deactivate()
            
        # Activate new mode
        self.current_mode = mode
        self.modes[mode].activate()
        self.setCursor(self.modes[mode].cursor())
    
    def mousePressEvent(self, event):
        """Handle mouse press events using the current mode."""
        if self.current_mode:
            if self.modes[self.current_mode].mouse_press_event(event):
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events using the current mode."""
        if self.current_mode:
            if self.modes[self.current_mode].mouse_move_event(event):
                return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events using the current mode."""
        if self.current_mode:
            if self.modes[self.current_mode].mouse_release_event(event):
                return
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events using the current mode."""
        if self.current_mode:
            if self.modes[self.current_mode].key_press_event(event):
                return
        super().keyPressEvent(event)
    
    def scene(self):
        """Get the graphics scene."""
        return self._scene