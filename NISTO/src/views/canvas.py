from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsLineItem,
                           QGraphicsRectItem, QGraphicsItemGroup, QGraphicsItem, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF, QEvent, QTimer
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


class SelectionBox:
    """Represents a selection box for multiple item selection."""
    
    def __init__(self, scene):
        self.scene = scene
        self.start_pos = None
        self.current_rect = None
        self.rect_item = None
    
    def start(self, pos):
        """Start the selection box at the given position."""
        self.start_pos = pos
        self.create_rect(pos, pos)
    
    def update(self, pos):
        """Update the selection box with a new end position."""
        if self.start_pos:
            self.create_rect(self.start_pos, pos)
    
    def create_rect(self, start, end):
        """Create or update the selection rectangle."""
        # Remove existing rect if any
        if self.rect_item and self.rect_item.scene() == self.scene:
            self.scene.removeItem(self.rect_item)
        
        # Create new rect
        self.current_rect = QRectF(start, end).normalized()
        self.rect_item = QGraphicsRectItem(self.current_rect)
        
        # Style the rectangle
        pen = QPen(QColor(70, 130, 180), 1, Qt.SolidLine)  # Steel blue
        self.rect_item.setPen(pen)
        self.rect_item.setBrush(QBrush(QColor(70, 130, 180, 30)))  # Semi-transparent
        
        # Add to scene
        self.scene.addItem(self.rect_item)
    
    def finish(self, select_items=True):
        """Finish the selection process and optionally select items."""
        result = None
        if self.rect_item and self.current_rect:
            result = self.current_rect
        
        # Remove the rectangle
        if self.rect_item and self.rect_item.scene() == self.scene:
            self.scene.removeItem(self.rect_item)
        
        # Reset state
        self.start_pos = None
        self.current_rect = None
        self.rect_item = None
        
        return result


class SelectMode(CanvasMode):
    """Mode for selecting and manipulating devices and boundaries."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.selection_box = SelectionBox(canvas.scene())
        self.drag_started = False
        self.is_selecting_box = False
    
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
        
        # Handle left button press for potential box selection
        if event.button() == Qt.LeftButton:
            # If clicking on empty space, start box selection
            if not item:
                self.is_selecting_box = True
                self.selection_box.start(scene_pos)
                return True  # We're handling it
            
            # If shift is not pressed, clear selection and let Qt handle it
            if not (event.modifiers() & Qt.ShiftModifier):
                # Let default QGraphicsView selection behavior handle it
                pass
        
        # Let the default QGraphicsView selection behavior handle other cases
        return False
    
    def mouse_move_event(self, event):
        """Update selection box during drag."""
        if event.buttons() & Qt.LeftButton and self.is_selecting_box:
            scene_pos = self.canvas.mapToScene(event.pos())
            self.selection_box.update(scene_pos)
            return True
        return False
    
    def mouse_release_event(self, event):
        """Finalize selection on mouse release."""
        if event.button() == Qt.LeftButton and self.is_selecting_box:
            scene_pos = self.canvas.mapToScene(event.pos())
            
            # Finish the box selection
            selection_rect = self.selection_box.finish()
            
            if selection_rect:
                # Get items in the selection rectangle
                items = self.canvas.scene().items(selection_rect, Qt.IntersectsItemShape)
                
                # If not extending selection (shift not pressed), clear current selection
                if not (event.modifiers() & Qt.ShiftModifier):
                    self.canvas.scene().clearSelection()
                
                # Select all valid items in the selection rectangle
                for item in items:
                    if isinstance(item, (Device, Connection, Boundary)):
                        # Don't select temp graphics or helper items
                        if not item.parentItem():  # Only top-level items
                            item.setSelected(True)
            
            self.is_selecting_box = False
            return True
        
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
    """Mode for deleting items from the canvas by clicking on them."""
    
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


class DeleteSelectedMode(CanvasMode):
    """Mode for deleting all selected items on the canvas."""
    
    def activate(self):
        """Called when this mode is activated."""
        super().activate()
        # When the mode is activated, immediately delete selected items
        selected_items = self.canvas.scene().selectedItems()
        if selected_items:
            self.canvas.delete_selected_requested.emit()
            # Automatically switch back to select mode after deletion
            QTimer.singleShot(100, lambda: self.canvas.set_mode(Modes.SELECT))
        else:
            # If nothing is selected, show a hint and switch back to select mode
            self.canvas.statusMessage.emit("No items selected. Select items first and try again.")
            QTimer.singleShot(100, lambda: self.canvas.set_mode(Modes.SELECT))
    
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
                    # Show connection type dialog
                    from dialogs.connection_type_dialog import ConnectionTypeDialog
                    dialog = ConnectionTypeDialog(self.canvas.parent())
                    
                    if dialog.exec_():
                        # Get connection data
                        connection_data = dialog.get_connection_data()
                        
                        # Emit signal to the canvas with all necessary data
                        self.logger.debug(f"Creating connection from {self.source_device} to {device} with type {connection_data['type']}")
                        self.canvas.add_connection_requested.emit(
                            self.source_device, 
                            device,
                            connection_data
                        )
                
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
    add_connection_requested = pyqtSignal(object, object, object)  # source, target, connection_data
    delete_connection_requested = pyqtSignal(object)  # connection
    delete_boundary_requested = pyqtSignal(object)  # boundary
    delete_selected_requested = pyqtSignal()  # Signal for deleting all selected items
    statusMessage = pyqtSignal(str)  # Signal for status bar messages
    
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
        
        # Initialize zoom settings
        self.zoom_factor = 1.15  # Zoom in/out factor per step
        self.min_zoom = 0.1     # Minimum zoom level
        self.max_zoom = 5.0     # Maximum zoom level
        self.current_zoom = 1.0  # Current zoom level
        
        # Enable mouse tracking and wheel events
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Set rendering quality
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Set viewport update mode to get smoother updates
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
    
    def _setup_modes(self):
        """Initialize all available interaction modes."""
        # Use a dictionary to create modes
        mode_classes = {
            Modes.SELECT: SelectMode,
            Modes.ADD_DEVICE: AddDeviceMode,
            Modes.DELETE: DeleteMode,
            Modes.DELETE_SELECTED: DeleteSelectedMode,
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
        """Handle key press events."""
        # Handle delete key for selected items
        if event.key() == Qt.Key_Delete:
            selected_items = self.scene().selectedItems()
            if selected_items:
                # Emit signal to delete all selected items
                self.delete_selected_requested.emit()
                event.accept()
                return
        
        # If not handled above, pass to mode manager or parent
        if not self.mode_manager.handle_event("key_press_event", event):
            super().keyPressEvent(event)
    
    def scene(self):
        """Get the graphics scene."""
        return self._scene
    
    def contextMenuEvent(self, event):
        """Handle context menu events."""
        # Get item under cursor
        pos = event.pos()
        scene_pos = self.mapToScene(pos)
        item = self.scene().itemAt(scene_pos, self.transform())
        
        # Create the context menu
        menu = QMenu()
        
        if item:
            # Context menu for items
            from models.connection import Connection
            if isinstance(item, Connection):
                # Connection context menu
                self._create_connection_context_menu(menu, item)
            elif isinstance(item, Device):
                # Device context menu
                self._create_device_context_menu(menu, item)
            elif isinstance(item, Boundary):
                # Boundary context menu
                self._create_boundary_context_menu(menu, item)
            
            # Add delete option for any item
            menu.addSeparator()
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda: self._delete_item(item))
        else:
            # Context menu for empty canvas area
            self._create_canvas_context_menu(menu, scene_pos)
        
        if not menu.isEmpty():
            menu.exec_(event.globalPos())
            return
        
        # Default context menu if no specific menu
        super().contextMenuEvent(event)

    def _create_canvas_context_menu(self, menu, pos):
        """Create context menu for empty canvas area."""
        add_menu = menu.addMenu("Add")
        
        # Add device option
        add_device_action = add_menu.addAction("Device")
        add_device_action.triggered.connect(lambda: self.add_device_requested.emit(pos))
        
        # Add boundary option
        add_boundary_action = add_menu.addAction("Boundary")
        add_boundary_action.triggered.connect(lambda: self._start_boundary_at(pos))
        
        # Add connection option - disabled until implementation
        add_connection_action = add_menu.addAction("Connection")
        add_connection_action.triggered.connect(lambda: self._start_connection_at(pos))
        add_connection_action.setEnabled(False)  # Not directly possible without selecting source device
        
        # Menu options for selected items
        if self.scene().selectedItems():
            menu.addSeparator()
            delete_selected_action = menu.addAction("Delete Selected")
            delete_selected_action.triggered.connect(self.delete_selected_requested.emit)

    def _create_device_context_menu(self, menu, device):
        """Create context menu for devices."""
        # Add device-specific menu options
        edit_action = menu.addAction("Edit Device")
        edit_action.triggered.connect(lambda: self._edit_device(device))
        
        # Start connection from this device
        start_connection_action = menu.addAction("Create Connection")
        start_connection_action.triggered.connect(lambda: self._start_connection_from(device))

    def _create_boundary_context_menu(self, menu, boundary):
        """Create context menu for boundaries."""
        edit_action = menu.addAction("Edit Label")
        edit_action.triggered.connect(lambda: self._edit_boundary_label(boundary))
        
        # Add color submenu
        color_menu = menu.addMenu("Change Color")
        
        # Add some color options
        colors = [
            ("Blue", QColor(40, 120, 200, 80)),
            ("Green", QColor(40, 200, 120, 80)),
            ("Red", QColor(200, 40, 40, 80)),
            ("Yellow", QColor(200, 200, 40, 80)),
            ("Purple", QColor(120, 40, 200, 80))
        ]
        
        for name, color in colors:
            color_action = color_menu.addAction(name)
            color_action.triggered.connect(lambda checked, c=color: boundary.set_color(c))

    def _delete_item(self, item):
        """Delete a specific item."""
        # Store bounding rect for update
        update_rect = None
        if hasattr(item, 'sceneBoundingRect'):
            update_rect = item.sceneBoundingRect().adjusted(-20, -20, 20, 20)
        
        if isinstance(item, Device):
            self.delete_device_requested.emit(item)
        elif isinstance(item, Connection):
            self.delete_connection_requested.emit(item)
        elif isinstance(item, Boundary):
            self.delete_boundary_requested.emit(item)
        else:
            self.delete_item_requested.emit(item)
        
        # Force update of affected area
        if update_rect:
            self.scene().update(update_rect)
        
        # Force a complete viewport update
        self.viewport().update()

    def _edit_device(self, device):
        """Edit the selected device."""
        # This would be implemented to show the device dialog for editing
        from views.device_dialog import DeviceDialog
        dialog = DeviceDialog(self.parent(), device)
        dialog.exec_()

    def _edit_boundary_label(self, boundary):
        """Edit boundary label."""
        if hasattr(boundary, 'label'):
            boundary.label.start_editing()

    def _start_boundary_at(self, pos):
        """Start creating a boundary at position."""
        # Switch to boundary creation mode
        self.set_mode(Modes.ADD_BOUNDARY)
        
        # Get the mode instance and simulate a mouse press to start boundary
        boundary_mode = self.mode_manager.get_mode_instance(Modes.ADD_BOUNDARY)
        if boundary_mode:
            boundary_mode.start_pos = pos
            # We don't create the boundary immediately as it needs a release event with size

    def _start_connection_from(self, device):
        """Start creating a connection from a device."""
        # Switch to connection mode
        self.set_mode(Modes.ADD_CONNECTION)
        
        # Get the connection mode instance
        connection_mode = self.mode_manager.get_mode_instance(Modes.ADD_CONNECTION)
        if connection_mode:
            # Set the source device and start point
            connection_mode.source_device = device
            start_port = device.get_nearest_port(device.get_center_position())
            
            # Create the temporary line
            connection_mode.temp_line = QGraphicsLineItem(
                start_port.x(), start_port.y(),
                start_port.x(), start_port.y()
            )
            
            # Style the line
            pen = QPen(QColor(0, 120, 215), 2, Qt.DashLine)
            pen.setDashPattern([5, 3])
            pen.setCapStyle(Qt.RoundCap)
            connection_mode.temp_line.setPen(pen)
            connection_mode.temp_line.setZValue(1000)
            
            # Add to scene
            self.scene().addItem(connection_mode.temp_line)

    def _create_connection_context_menu(self, menu, connection):
        """Create context menu for a connection."""
        from models.connection import Connection
        
        # Connection style submenu
        style_menu = menu.addMenu("Routing Style")
        
        # Straight style
        straight_action = style_menu.addAction("Straight")
        straight_action.setCheckable(True)
        straight_action.setChecked(connection.routing_style == Connection.STYLE_STRAIGHT)
        straight_action.triggered.connect(
            lambda: connection.set_routing_style(Connection.STYLE_STRAIGHT))
        
        # Orthogonal style
        orthogonal_action = style_menu.addAction("Orthogonal")
        orthogonal_action.setCheckable(True)
        orthogonal_action.setChecked(connection.routing_style == Connection.STYLE_ORTHOGONAL)
        orthogonal_action.triggered.connect(
            lambda: connection.set_routing_style(Connection.STYLE_ORTHOGONAL))
        
        # Curved style
        curved_action = style_menu.addAction("Curved")
        curved_action.setCheckable(True)
        curved_action.setChecked(connection.routing_style == Connection.STYLE_CURVED)
        curved_action.triggered.connect(
            lambda: connection.set_routing_style(Connection.STYLE_CURVED))
        
        # Delete action
        menu.addSeparator()
        delete_action = menu.addAction("Delete Connection")
        delete_action.triggered.connect(lambda: self.delete_connection_requested.emit(connection))
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        # Get the current position of the mouse in scene coordinates
        mouse_pos = self.mapToScene(event.pos())
        
        # Calculate zoom factor based on wheel direction
        zoom_direction = 1 if event.angleDelta().y() > 0 else -1
        zoom_step = self.zoom_factor ** zoom_direction
        
        # Calculate new zoom level
        new_zoom = self.current_zoom * zoom_step
        
        # Enforce zoom limits
        if new_zoom < self.min_zoom:
            zoom_step = self.min_zoom / self.current_zoom
            new_zoom = self.min_zoom
        elif new_zoom > self.max_zoom:
            zoom_step = self.max_zoom / self.current_zoom
            new_zoom = self.max_zoom
        
        # Update current zoom level
        self.current_zoom = new_zoom
        
        # Scale the view
        self.scale(zoom_step, zoom_step)
        
        # Adjust the scene position to keep the mouse cursor in the same position
        new_pos = self.transform().map(mouse_pos)
        delta = new_pos - event.pos()
        self.translate(delta.x(), delta.y())
        
        # Log the zoom level
        self.logger.debug(f"Zoom level: {new_zoom:.2f}")
        
        # Update the view
        self.update()
    
    def zoom_in(self):
        """Zoom in on the canvas by a fixed step."""
        # Calculate new zoom level
        zoom_step = self.zoom_factor
        new_zoom = self.current_zoom * zoom_step
        
        # Enforce zoom limit
        if new_zoom > self.max_zoom:
            zoom_step = self.max_zoom / self.current_zoom
            new_zoom = self.max_zoom
        
        # Update current zoom level
        self.current_zoom = new_zoom
        
        # Apply zoom using scale
        self.scale(zoom_step, zoom_step)
        
        # Log the zoom level
        self.logger.debug(f"Zoom in: {new_zoom:.2f}")
        
        # Update the view
        self.update()
    
    def zoom_out(self):
        """Zoom out on the canvas by a fixed step."""
        # Calculate new zoom level
        zoom_step = 1.0 / self.zoom_factor
        new_zoom = self.current_zoom * zoom_step
        
        # Enforce zoom limit
        if new_zoom < self.min_zoom:
            zoom_step = self.min_zoom / self.current_zoom
            new_zoom = self.min_zoom
        
        # Update current zoom level
        self.current_zoom = new_zoom
        
        # Apply zoom using scale
        self.scale(zoom_step, zoom_step)
        
        # Log the zoom level
        self.logger.debug(f"Zoom out: {new_zoom:.2f}")
        
        # Update the view
        self.update()
    
    def reset_zoom(self):
        """Reset zoom level to 100%."""
        # Calculate zoom step to get back to 1.0
        zoom_step = 1.0 / self.current_zoom
        
        # Update current zoom level
        self.current_zoom = 1.0
        
        # Apply zoom using scale
        self.scale(zoom_step, zoom_step)
        
        # Log the zoom level
        self.logger.debug("Zoom reset to 1.0")
        
        # Update the view
        self.update()

