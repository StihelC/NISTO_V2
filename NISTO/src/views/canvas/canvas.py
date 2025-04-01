from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QMenu, 
    QGraphicsItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QEvent, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor

import logging
from constants import Modes

# Import our modularized components
from .graphics_manager import TemporaryGraphicsManager
from .selection_box import SelectionBox
from .mode_manager import CanvasModeManager

# Import modes
from .modes.select_mode import SelectMode
from .modes.add_device_mode import AddDeviceMode
from .modes.delete_mode import DeleteMode, DeleteSelectedMode
from .modes.add_boundary_mode import AddBoundaryMode
from .modes.add_connection_mode import AddConnectionMode

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
    selection_changed = pyqtSignal(list)  # Signal for selection changes
    
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
        
        # Event bus reference (will be set externally)
        self.event_bus = None
        
        # Drag tracking variables
        self._drag_start_pos = None
        self._drag_item = None
        
        # Variables for canvas dragging (panning)
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        
        # Set rendering hints for better quality
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # Set scene rectangle to support large networks (10,000+ devices)
        self._scene.setSceneRect(-50000, -50000, 100000, 100000)
        
        # Setup appearance
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Mouse tracking
        self.setMouseTracking(True)
        
        # Initialize helper components
        self.temp_graphics = TemporaryGraphicsManager(self._scene)
        
        # Setup mode manager
        self.mode_manager = CanvasModeManager(self)
        
        # Set up modes
        self._setup_modes()
        
        # Set initial mode
        self.set_mode(Modes.SELECT)
        
        # Initialize zoom settings with more conservative limits
        self.zoom_factor = 1.15  # Zoom in/out factor per step
        self.min_zoom = 0.05     # Minimum zoom level (5%)
        self.max_zoom = 2.5      # Maximum zoom level (250%)
        self.current_zoom = 1.0  # Current zoom level (100%)
        self.initial_transform = self.transform()  # Store initial transform
        
        # Store the initial viewport center point
        self.home_position = QPointF(0, 0)  # Default center of the view
        
        # Enable wheel events
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Set viewport update mode to get smoother updates
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Enhanced rubber band selection setup with stronger styling
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Set a more visible rubber band style - use QSS that's guaranteed to work
        self.setStyleSheet("""
            QGraphicsView {
                selection-background-color: rgba(0, 100, 255, 50);
            }
        """)
        
        # Variable to track if rubber band selection is active
        self._rubber_band_active = False
    
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
            try:
                mode = mode_class(self)
                self.mode_manager.register_mode(mode_id, mode)
            except Exception as e:
                self.logger.error(f"Failed to initialize mode {mode_class.__name__}: {e}")
    
    def set_mode(self, mode):
        """Set the current interaction mode."""
        return self.mode_manager.set_mode(mode)
    
    def get_item_at(self, pos):
        """Get item at the given view position."""
        scene_pos = self.mapToScene(pos)
        return self.scene().itemAt(scene_pos, self.transform())
    
    def mousePressEvent(self, event):
        """Handle mouse press events with improved device dragging support."""
        try:
            # Handle middle button or shift+left click for panning
            if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier):
                self._is_panning = True
                self._pan_start_x = event.x()
                self._pan_start_y = event.y()
                self.setCursor(Qt.ClosedHandCursor)
                self.setDragMode(QGraphicsView.NoDrag)
                event.accept()
                return
                
            # If space is held for temp pan mode
            if hasattr(self, '_temp_pan_mode') and self._temp_pan_mode:
                self._is_panning = True
                self._pan_start_x = event.x()
                self._pan_start_y = event.y()
                self.setCursor(Qt.ClosedHandCursor)
                self.setDragMode(QGraphicsView.NoDrag)
                event.accept()
                return
                
            # Get item at click position
            scene_pos = self.mapToScene(event.pos())
            item = self.get_item_at(event.pos())
            
            # Special case for empty clicks in select mode
            if not item and event.button() == Qt.LeftButton and self.mode_manager.current_mode == Modes.SELECT:
                # Clear selection and prepare for rubber band
                if not (event.modifiers() & Qt.ControlModifier):
                    self.scene().clearSelection()
                
                # Important: Use NoDrag first to reset any existing drag state
                self.setDragMode(QGraphicsView.NoDrag)
                # Now set rubber band mode
                self.setDragMode(QGraphicsView.RubberBandDrag)
                
                # Let Qt handle the rubber band natively
                super().mousePressEvent(event)
                return
            
            # Let the mode manager handle the event
            handled = self.mode_manager.handle_event("mouse_press_event", event, scene_pos, item)
            
            # If it wasn't handled by our mode, let Qt handle it for built-in rubber band selection
            if not handled:
                super().mousePressEvent(event)
                
        except Exception as e:
            self.logger.error(f"Error in mousePressEvent: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        try:
            # Handle canvas panning
            if self._is_panning:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (event.x() - self._pan_start_x))
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (event.y() - self._pan_start_y))
                self._pan_start_x = event.x()
                self._pan_start_y = event.y()
                event.accept()
                return
            
            # Let the mode manager handle the event first
            if not self.mode_manager.handle_event("mouse_move_event", event):
                # If the mode didn't handle it, pass to default implementation
                super().mouseMoveEvent(event)
                
        except Exception as e:
            self.logger.error(f"Error in mouseMoveEvent: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        # End canvas panning
        if self._is_panning:
            if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier):
                self._is_panning = False
                self.setCursor(Qt.ArrowCursor)
                self.setDragMode(QGraphicsView.RubberBandDrag)  # Restore rubber band mode
                event.accept()
                return
        
        # Reset rubber band selection tracking
        if hasattr(self, '_rubber_band_active') and self._rubber_band_active and event.button() == Qt.LeftButton:
            self._rubber_band_active = False
            self.logger.debug("Rubber band selection complete")
        
        # Track item movements for undo/redo
        if hasattr(self, '_drag_start_pos') and hasattr(self, '_drag_item'):
            if self._drag_item and self._drag_start_pos:
                current_pos = self._drag_item.scenePos()
                if current_pos != self._drag_start_pos:
                    # Calculate actual item position difference
                    dx = current_pos.x() - self._drag_start_pos.x()
                    dy = current_pos.y() - self._drag_start_pos.y()
                    
                    # Add movement to undo/redo history if available
                    if hasattr(self, 'event_bus') and self.event_bus:
                        # Publish move event for controllers to handle
                        self.event_bus.emit('item.moved', 
                            item=self._drag_item, 
                            old_pos=self._drag_start_pos,
                            new_pos=current_pos
                        )
                    
                    # Reset drag tracking variables
                    self._drag_start_pos = None
                    self._drag_item = None
        
        # Let the active mode handle the event
        scene_pos = self.mapToScene(event.pos())
        item = self.get_item_at(event.pos())
        handled = self.mode_manager.handle_event("mouse_release_event", event, scene_pos, item)
        if not handled:
            super().mouseReleaseEvent(event)
        
        # After mouse release, always ensure we're in rubber band drag mode if in select mode
        if self.mode_manager.current_mode == Modes.SELECT:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # After handling mouse release, emit selection changed signal
        self.selection_changed.emit(self.scene().selectedItems())
        
    def keyPressEvent(self, event):
        """Handle key press events."""
        # If space bar is pressed, switch to pan mode temporarily
        if event.key() == Qt.Key_Space:
            self.setCursor(Qt.OpenHandCursor)
            self._temp_pan_mode = True
            event.accept()
            return
            
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
            
    def keyReleaseEvent(self, event):
        """Handle key release events."""
        # If space bar is released, exit pan mode
        if event.key() == Qt.Key_Space and hasattr(self, '_temp_pan_mode'):
            self.setCursor(Qt.ArrowCursor)
            self._temp_pan_mode = False
            event.accept()
            return
            
        super().keyReleaseEvent(event)
    
    def get_item_at(self, pos):
        """Get item at the given view position."""
        scene_pos = self.mapToScene(pos)
        return self.scene().itemAt(scene_pos, self.transform())
        
    def scene(self):
        """Get the graphics scene."""
        return self._scene
    
    def zoom_in(self):
        """Zoom in on the canvas view."""
        if self.current_zoom < self.max_zoom:
            self.scale(self.zoom_factor, self.zoom_factor)
            self.current_zoom *= self.zoom_factor
            self.statusMessage.emit(f"Zoom: {int(self.current_zoom * 100)}%")
    
    def zoom_out(self):
        """Zoom out on the canvas view."""
        if self.current_zoom > self.min_zoom:
            factor = 1.0 / self.zoom_factor
            self.scale(factor, factor)
            self.current_zoom *= factor
            self.statusMessage.emit(f"Zoom: {int(self.current_zoom * 100)}%")
    
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.setTransform(self.initial_transform)
        self.current_zoom = 1.0
        self.statusMessage.emit("Zoom: 100%")
        
    def set_home_position(self, pos):
        """Set the home position for the canvas."""
        self.home_position = pos
    
    def reset_view(self):
        """Reset the view to the home position with 100% zoom."""
        self.reset_zoom()
        self.centerOn(self.home_position)
        self.statusMessage.emit("View reset to home position")
    
    def set_devices_draggable(self, draggable):
        """Make all devices draggable or not."""
        for device in self.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, draggable)
            device.setFlag(QGraphicsItem.ItemIsSelectable, True)  # Always keep selectable

    def diagnostics(self):
        """Print diagnostic information about current canvas state."""
        self.logger.debug("======= CANVAS DIAGNOSTICS =======")
        self.logger.debug(f"Devices: {len(self.devices)}")
        self.logger.debug(f"Connections: {len(self.connections)}")
        self.logger.debug(f"Boundaries: {len(self.boundaries)}")
        self.logger.debug(f"Drag mode: {self.dragMode()}")
        
        # Check current mode
        current_mode = None
        if hasattr(self, 'mode_manager') and hasattr(self.mode_manager, 'current_mode_instance'):
            current_mode = self.mode_manager.current_mode_instance.__class__.__name__ if self.mode_manager.current_mode_instance else None
        self.logger.debug(f"Current mode: {current_mode}")
        
        # Check selected items
        selected = self.scene().selectedItems()
        self.logger.debug(f"Selected items: {len(selected)}")
        
        # Device check - verify movable flag for all devices
        for i, device in enumerate(self.devices):
            is_movable = bool(device.flags() & QGraphicsItem.ItemIsMovable)
            is_selectable = bool(device.flags() & QGraphicsItem.ItemIsSelectable)
            self.logger.debug(f"Device {i} ({device.name}): movable={is_movable}, selectable={is_selectable}")
        
        self.logger.debug("================================")
