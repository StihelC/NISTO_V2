from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem, QMenu, QAction
from PyQt5.QtGui import QPen, QColor, QPainterPath, QFont, QBrush, QPainterPathStroker
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QObject, QRectF
import uuid
from constants import ConnectionTypes
import logging

class ConnectionSignals(QObject):
    """Signals for connection events."""
    selected = pyqtSignal(object)  # connection
    deleted = pyqtSignal(object)   # connection
    updated = pyqtSignal(object)   # connection

class EditableTextItem(QGraphicsTextItem):
    """A text item that can be edited and sends signals when editing finishes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.editing = False
        
        # Background appearance
        self.background_color = QColor(255, 255, 255, 220)  # Slightly transparent white
        self.background_padding = 4  # Padding around text
        
    def paint(self, painter, option, widget):
        """Paint a background rect behind the text."""
        # Draw background rectangle
        painter.save()
        painter.setBrush(self.background_color)
        painter.setPen(Qt.NoPen)  # No border for the background
        
        # Get text rect with padding
        rect = self.boundingRect()
        bg_rect = rect.adjusted(
            -self.background_padding, 
            -self.background_padding, 
            self.background_padding, 
            self.background_padding
        )
        
        # Draw rounded rectangle
        painter.drawRoundedRect(bg_rect, 3, 3)
        painter.restore()
        
        # Draw the text
        super().paint(painter, option, widget)
    
    # Cache the bounding rect for more efficient updates    
    def boundingRect(self):
        rect = super().boundingRect()
        # Include the background padding in the bounding rect
        return rect.adjusted(
            -self.background_padding, 
            -self.background_padding, 
            self.background_padding, 
            self.background_padding
        )
        
    def focusOutEvent(self, event):
        """Finish editing when focus is lost."""
        self.editing = False
        if self.parentItem() and hasattr(self.parentItem(), 'on_label_edited'):
            self.parentItem().on_label_edited(self.toPlainText())
        super().focusOutEvent(event)
        
    def keyPressEvent(self, event):
        """Handle Enter key to finish editing."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.clearFocus()
            event.accept()
        else:
            super().keyPressEvent(event)

class Connection(QGraphicsPathItem):
    """Represents a connection between two devices in the topology."""
    
    # Routing styles
    STYLE_STRAIGHT = 0
    STYLE_ORTHOGONAL = 1
    STYLE_CURVED = 2
    
    # Path update modes
    UPDATE_BOTH_ENDS = 0
    UPDATE_SOURCE = 1
    UPDATE_TARGET = 2
    
    def __init__(self, source_device, target_device, source_port=None, target_port=None):
        """Initialize a connection between two devices."""
        super().__init__()
        
        # Basic setup
        self.logger = logging.getLogger(__name__)
        self.id = str(uuid.uuid4())
        self.source_device = source_device
        self.target_device = target_device
        
        # Debug mode
        self.debug_selection = False
        
        # Initialize label immediately to avoid NoneType errors
        self.label = None
        
        self.logger.info(f"Creating connection between {source_device.name} and {target_device.name}")
        
        # Add to devices' connections list
        source_device.add_connection(self)
        target_device.add_connection(self)
        
        # Port positions
        self.source_port = source_port or source_device.get_nearest_port(target_device.get_center_position())
        self.target_port = target_port or target_device.get_nearest_port(source_device.get_center_position())
        self._source_port = self.source_port
        self._target_port = self.target_port
        
        # Store raw device positions
        self.source_pos = source_device.scenePos()
        self.target_pos = target_device.scenePos()
        
        # Visual properties
        self._label_text = "Link"  # Default label
        self.connection_type = "ethernet"  # Default type
        self.bandwidth = "1G"  # Default bandwidth
        self.latency = "0ms"  # Default latency
        
        # Add this properties dictionary for storing connection properties
        self.properties = {
            "Bandwidth": self.bandwidth,
            "Latency": self.latency,
            "Label": self._label_text
        }
        
        # Style properties
        self._line_width = 1  # Thinner visual lines
        self.line_width = 1
        self.line_color = QColor(70, 70, 70)
        self.line_style = Qt.SolidLine
        self._base_color = QColor(70, 70, 70)  # Default dark gray
        self._hover_color = QColor(0, 120, 215)  # Default bright blue
        self.selected_color = QColor(255, 140, 0)  # Orange
        self._text_color = QColor(40, 40, 40)  # Near black
        self._routing_style = self.STYLE_STRAIGHT
        self.routing_style = self.STYLE_STRAIGHT
        
        # Track state
        self.is_selected = False
        self.is_hover = False
        self._was_selected = False
        self.control_points = []
        
        # Create signals object
        self.signals = ConnectionSignals()
        
        # Configure selectable behavior
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setAcceptHoverEvents(True)
        
        # Set Z-value
        self.setZValue(-1)
        
        # Create the path
        self.update_path()
        
        # Now create the label
        self.create_label()
        
        # Setup listeners for device movement
        if hasattr(source_device, 'signals') and hasattr(source_device.signals, 'moved'):
            source_device.signals.moved.connect(self._handle_device_moved)
        
        if hasattr(target_device, 'signals') and hasattr(target_device.signals, 'moved'):
            target_device.signals.moved.connect(self._handle_device_moved)

    @property
    def label_text(self):
        """Get the label text."""
        return self._label_text
    
    @label_text.setter
    def label_text(self, value):
        """Set the label text and update the label."""
        # Ensure the value isn't a QPointF object
        if isinstance(value, QPointF):
            self.logger.warning(f"Attempted to set label_text to QPointF: {value}")
            return
            
        self._label_text = value
        
        # Update the label if it exists
        if self.label:
            self.label.setPlainText(self._label_text)
            self._update_label_position()
    
    def create_label(self):
        """Create or update the connection label."""
        if not self.label:
            self.label = QGraphicsTextItem(self)
            
            # Style the label
            self.label.setDefaultTextColor(self._text_color)
            font = QFont()
            font.setPointSize(8)
            self.label.setFont(font)
        
        # Set the text - safely
        if hasattr(self, '_label_text') and self._label_text and not isinstance(self._label_text, QPointF):
            self.label.setPlainText(self._label_text)
        else:
            # Default label
            self.label.setPlainText("Link")
        
        # Position the label
        self._update_label_position()
    
    def _connect_to_device_changes(self):
        """Connect to device signals to update when devices move."""
        if self.source_device and hasattr(self.source_device, 'signals'):
            if hasattr(self.source_device.signals, 'moved'):
                self.source_device.signals.moved.connect(self._on_device_moved)
        
        if self.target_device and hasattr(self.target_device, 'signals'):
            if hasattr(self.target_device.signals, 'moved'):
                self.target_device.signals.moved.connect(self._on_device_moved)

    def _on_device_moved(self, device):
        """Handle device movement by updating the connection path."""
        # Capture the old bounding rect before update
        old_rect = self.boundingRect()
        if self.label:
            old_rect = old_rect.united(
                self.label.boundingRect().adjusted(
                    -self.label.background_padding*2,
                    -self.label.background_padding*2,
                    self.label.background_padding*2,
                    self.label.background_padding*2
                ).translated(self.label.pos())
            )
        
        # Update the path
        self.update_path()
        
        # Make sure we update the scene with both old and new areas
        if self.scene():
            scene_rect = self.mapToScene(old_rect).boundingRect().united(
                self.mapToScene(self.boundingRect()).boundingRect()
            )
            # Add some margin
            scene_rect.adjust(-5, -5, 5, 5)
            self.scene().update(scene_rect)
    
    def _find_best_port(self, from_device, to_device):
        """Find the best connection port on from_device facing to_device."""
        # Get center of target device
        if hasattr(to_device, 'get_center_position'):
            target_center = to_device.get_center_position()
        else:
            target_center = to_device.scenePos()
            
        # Find nearest port on source device
        if hasattr(from_device, 'get_nearest_port'):
            return from_device.get_nearest_port(target_center)
            
        # Fall back to device position
        return from_device.scenePos()
    
    def update_path(self):
        """Update the connection path based on current device positions."""
        try:
            # Store current label text before updating
            current_label_text = None
            if hasattr(self, 'label') and self.label:
                current_label_text = self.label.toPlainText()
            elif hasattr(self, '_label_text'):
                current_label_text = self._label_text
            
            # Re-calculate ports in case devices moved
            if hasattr(self, '_find_best_port'):
                self._source_port = self._find_best_port(self.source_device, self.target_device)
                self._target_port = self._find_best_port(self.target_device, self.source_device)
            
            # Create path based on routing style
            path = QPainterPath()
            path.moveTo(self._source_port)
            
            if self.routing_style == self.STYLE_STRAIGHT:
                # Simple straight line
                path.lineTo(self._target_port)
                
            elif self.routing_style == self.STYLE_ORTHOGONAL:
                # Right-angle connections (Manhattan routing)
                sx, sy = self._source_port.x(), self._source_port.y()
                tx, ty = self._target_port.x(), self._target_port.y()
                
                # Determine direction based on relative positions
                dx, dy = tx - sx, ty - sy
                
                if abs(dx) > abs(dy):
                    # Horizontal dominant - go horizontally first
                    path.lineTo(sx + dx/2, sy)
                    path.lineTo(sx + dx/2, ty)
                else:
                    # Vertical dominant - go vertically first
                    path.lineTo(sx, sy + dy/2)
                    path.lineTo(tx, sy + dy/2)
                    
                path.lineTo(tx, ty)
                
            elif self.routing_style == self.STYLE_CURVED:
                # Bezier curve
                sx, sy = self._source_port.x(), self._source_port.y()
                tx, ty = self._target_port.x(), self._target_port.y()
                
                # Control points at 1/3 and 2/3 of the path
                dx, dy = tx - sx, ty - sy
                cp1 = QPointF(sx + dx/3, sy)
                cp2 = QPointF(tx - dx/3, ty)
                
                path.cubicTo(cp1, cp2, self._target_port)
            
            # Set the path
            self.setPath(path)
            
            # Ensure we preserve the label
            if not hasattr(self, 'label') or not self.label:
                self.create_label()
            
            # Always set the label text to preserve it
            if current_label_text:
                self._label_text = current_label_text  # Store in attribute
                self.label.setPlainText(current_label_text)  # Update the visual label
            
            # Update label position
            self._update_label_position()
            
        except Exception as e:
            self.logger.error(f"Error updating path: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _update_label_position(self):
        """Place label at center of connection."""
        try:
            # First check if label exists
            if not hasattr(self, 'label') or self.label is None:
                return
                
            # Get path center point - use safe access to path
            path = self.path()
            if path and not path.isEmpty():
                # Calculate center point of the path
                center_point = path.pointAtPercent(0.5)
                
                # Position the label precisely at the center, accounting for label size
                label_width = self.label.boundingRect().width()
                label_height = self.label.boundingRect().height()
                
                # Position label at center point, offset by half its dimensions
                self.label.setPos(
                    center_point.x() - label_width/2,
                    center_point.y() - label_height/2
                )
            else:
                # Fallback if no valid path exists
                if hasattr(self, '_source_port') and hasattr(self, '_target_port'):
                    # Use midpoint between source and target ports
                    mid_x = (self._source_port.x() + self._target_port.x()) / 2
                    mid_y = (self._source_port.y() + self._target_port.y()) / 2
                    
                    # Position label at this midpoint
                    label_width = self.label.boundingRect().width()
                    label_height = self.label.boundingRect().height()
                    
                    self.label.setPos(
                        mid_x - label_width/2,
                        mid_y - label_height/2
                    )
        except Exception as e:
            self.logger.error(f"Error updating label position: {str(e)}")
    
    def set_style_for_type(self, connection_type):
        """Set the visual style based on the connection type."""
        # Import constants if needed (in case this method is called directly)
        from constants import ConnectionTypes
        
        # Default style
        style = {
            'color': QColor(30, 30, 30),
            'style': Qt.SolidLine,
            'width': 2
        }
        
        # Style based on connection type
        if connection_type == ConnectionTypes.ETHERNET:
            style = {'color': QColor(0, 0, 0), 'style': Qt.SolidLine, 'width': 2}
        elif connection_type == ConnectionTypes.SERIAL:
            style = {'color': QColor(0, 0, 255), 'style': Qt.DashLine, 'width': 1.5}
        elif connection_type == ConnectionTypes.FIBER:
            style = {'color': QColor(0, 128, 0), 'style': Qt.SolidLine, 'width': 3}
        elif connection_type == ConnectionTypes.WIRELESS:
            style = {'color': QColor(128, 0, 128), 'style': Qt.DotLine, 'width': 1.5}
        elif connection_type == ConnectionTypes.GIGABIT_ETHERNET:
            style = {'color': QColor(50, 50, 50), 'style': Qt.SolidLine, 'width': 2.5}
        elif connection_type == ConnectionTypes.TEN_GIGABIT_ETHERNET:
            style = {'color': QColor(0, 100, 200), 'style': Qt.SolidLine, 'width': 3}
        elif connection_type == ConnectionTypes.FORTY_GIGABIT_ETHERNET:
            style = {'color': QColor(0, 150, 200), 'style': Qt.SolidLine, 'width': 3.5}
        elif connection_type == ConnectionTypes.HUNDRED_GIGABIT_ETHERNET:
            style = {'color': QColor(0, 200, 200), 'style': Qt.SolidLine, 'width': 4}
        elif connection_type == ConnectionTypes.FIBER_CHANNEL:
            style = {'color': QColor(200, 100, 0), 'style': Qt.SolidLine, 'width': 3}
        elif connection_type == ConnectionTypes.MPLS:
            style = {'color': QColor(100, 0, 100), 'style': Qt.DashDotLine, 'width': 2.5}
        elif connection_type == ConnectionTypes.POINT_TO_POINT:
            style = {'color': QColor(0, 0, 100), 'style': Qt.SolidLine, 'width': 2}
        elif connection_type == ConnectionTypes.VPN:
            style = {'color': QColor(0, 100, 0), 'style': Qt.DashDotDotLine, 'width': 2}
        elif connection_type == ConnectionTypes.SDWAN:
            style = {'color': QColor(0, 128, 128), 'style': Qt.DashDotLine, 'width': 2.5}
        elif connection_type == ConnectionTypes.SATELLITE:
            style = {'color': QColor(128, 0, 0), 'style': Qt.DotLine, 'width': 2}
        elif connection_type == ConnectionTypes.MICROWAVE:
            style = {'color': QColor(200, 0, 0), 'style': Qt.DotLine, 'width': 1.5}
        elif connection_type == ConnectionTypes.BLUETOOTH:
            style = {'color': QColor(0, 0, 200), 'style': Qt.DashDotLine, 'width': 1.5}
        elif connection_type == ConnectionTypes.CUSTOM:
            style = {'color': QColor(50, 50, 50), 'style': Qt.SolidLine, 'width': 2}
        
        # Store current connection type
        self.connection_type = connection_type
        
        # Apply style
        self.line_color = style['color']
        self.line_style = style['style']
        self.line_width = style['width']
        self._apply_style()
        
        # Update label text to match connection type if needed
        if hasattr(self, 'label_text'):
            # Import here to avoid circular import
            from constants import ConnectionTypes
            display_name = ConnectionTypes.DISPLAY_NAMES.get(connection_type, "Link")
            self.label_text = display_name
    
    def _apply_style(self):
        """Apply the current style settings."""
        pen = QPen()
        
        # Use selected color if selected
        if self.isSelected():
            pen.setColor(self.selected_color)
        else:
            pen.setColor(self.line_color)
        
        pen.setWidthF(self.line_width)
        pen.setStyle(self.line_style)
        pen.setCapStyle(Qt.RoundCap)
        
        self.setPen(pen)
    
    def create_label(self):
        """Create a text label for the connection."""
        if not self.label:
            self.label = EditableTextItem(self)
            
            # Use the stored label text, not a default value
            self.label.setPlainText(self.label_text)
            
            # Make the label more visible with a better background
            self.label.setDefaultTextColor(QColor(0, 0, 0))
            font = QFont()
            font.setBold(True)
            self.label.setFont(font)
            
            # Set background color with higher opacity for better visibility
            self.label.background_color = QColor(255, 255, 255, 220)
            self.label.background_padding = 5  # More padding around text
            
            # Set Z-value to be above the connection line
            self.label.setZValue(self.zValue() + 1)
            
            # Update position
            self._update_label_position()
            
            print(f"Created label with text: '{self.label_text}'")
    
    def on_label_edited(self, new_text):
        """Called when the label editing is finished."""
        if new_text != self.label_text:
            self.label_text = new_text
            self._update_label_position()  # Recenter based on new text size
            
            # If there's a signal for connection changes, emit it
            if hasattr(self.signals, 'changed'):
                self.signals.changed.emit(self)
    
    def set_routing_style(self, style):
        """Set the routing style (straight, orthogonal, curved)."""
        self.logger.debug(f"Setting routing style to {style} (was {self.routing_style})")
        
        # Convert string styles to integer constants for internal use
        if isinstance(style, str):
            style_map = {
                "direct": self.STYLE_STRAIGHT,
                "straight": self.STYLE_STRAIGHT,
                "orthogonal": self.STYLE_ORTHOGONAL,
                "curved": self.STYLE_CURVED
            }
            if style.lower() in style_map:
                style = style_map[style.lower()]
        
        # Check if style is a valid integer value
        if style not in (self.STYLE_STRAIGHT, self.STYLE_ORTHOGONAL, self.STYLE_CURVED):
            self.logger.warning(f"Invalid routing style: {style}, defaulting to STRAIGHT")
            style = self.STYLE_STRAIGHT
        
        # Only update if style actually changed
        if style != self.routing_style:
            self.routing_style = style
            self.update_path()
            
            # Force a more comprehensive scene update to ensure the line is visible
            if self.scene():
                # Get a larger update rectangle that includes both old and new paths
                update_rect = self.sceneBoundingRect().adjusted(-30, -30, 30, 30)
                self.scene().update(update_rect)
                
                # Force update on all views
                for view in self.scene().views():
                    view.viewport().update()
    
    def paint(self, painter, option, widget=None):
        """Custom painting with debugging information."""
        # Check if selected and update style if needed
        if self.isSelected() != self._was_selected:
            self._was_selected = self.isSelected()
            self._apply_style()
        
        # Store original pen
        original_pen = self.pen()
        
        # First draw a wider transparent path for hit detection
        hit_pen = QPen(Qt.transparent)
        hit_pen.setWidth(10)
        painter.setPen(hit_pen)
        painter.drawPath(self.path())
        
        # Then draw the visible line
        painter.setPen(original_pen)
        painter.drawPath(self.path())
        
        # Show debug visuals if enabled
        if self.debug_selection:
            debug_pen = QPen(QColor(255, 0, 0, 50))
            debug_pen.setWidth(1)
            painter.setPen(debug_pen)
            painter.setBrush(QBrush(QColor(255, 0, 0, 20)))
            
            # Draw a simple rectangle around the path instead of complex operations
            painter.drawRect(self.path().boundingRect().adjusted(-6, -6, 6, 6))
    
    def shape(self):
        """Return a shape for hit detection that's wider than the visible path."""
        # Create a wider path for better selection
        path = QPainterPath(self.path())
        
        # Create a wider stroke path for better hit detection
        pen = QPen()
        pen.setWidth(12)  # Much wider than visible line
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        
        # Create a stroker to expand the path
        stroker = QPainterPathStroker(pen)
        selection_shape = stroker.createStroke(path)
        
        return selection_shape
    
    def boundingRect(self):
        """Override to provide a larger bounding rectangle for selection."""
        rect = super().boundingRect()
        return rect.adjusted(-6, -6, 6, 6)
    
    def mousePressEvent(self, event):
        """Handle mouse press to improve selection."""
        if event.button() == Qt.LeftButton:
            # Select this connection
            self.setSelected(True)
            
            # Only clear other selections if not multi-selecting
            if not (event.modifiers() & Qt.ControlModifier) and not (event.modifiers() & Qt.ShiftModifier):
                # Temporarily store this selection
                was_selected = self.isSelected()
                
                # Clear other selections
                scene = self.scene()
                if scene:
                    scene.clearSelection()
                
                # Restore our selection
                self.setSelected(was_selected)
                
            event.accept()
        else:
            super().mousePressEvent(event)

    def itemChange(self, change, value):
        """Handle item changes like selection."""
        if change == QGraphicsItem.ItemSelectedChange:
            # Log selection changes
            if self.debug_selection:
                self.logger.info(f"Connection {self.id} selection changing to: {bool(value)}")
            
            # Emit signal when selection changes
            if value:
                self.signals.selected.emit(self)
            else:
                self.signals.selected.emit(self)
            
            # Update appearance
            self._apply_style()
        
        # Debug position change
        elif change == QGraphicsItem.ItemPositionHasChanged and self.debug_selection:
            self.logger.debug(f"Connection {self.id} position changed")
        
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        if self.debug_selection:
            self.logger.info(f"Hover enter on connection {self.id}")
        
        self.is_hover = True
        # Highlight connection on hover
        self.setPen(QPen(self.selected_color, self.line_width + 1, self.line_style))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        if self.debug_selection:
            self.logger.info(f"Hover leave on connection {self.id}")
        
        self.is_hover = False
        # Restore original appearance
        self._apply_style()
        super().hoverLeaveEvent(event)
    
    def delete(self):
        """Remove this connection."""
        # Store scene and path for later update
        scene = self.scene()
        path_rect = self.boundingRect()
        scene_path = self.mapToScene(path_rect).boundingRect().adjusted(-20, -20, 20, 20)
        
        # If we have a label, include its area in the update region
        if self.label and self.label.scene():
            label_rect = self.label.sceneBoundingRect()
            scene_path = scene_path.united(label_rect.adjusted(-5, -5, 5, 5))
        
        # Disconnect from devices
        if self.source_device:
            if hasattr(self.source_device, 'remove_connection'):
                self.source_device.remove_connection(self)
        
        if self.target_device:
            if hasattr(self.target_device, 'remove_connection'):
                self.target_device.remove_connection(self)
        
        # Emit signal before removal
        self.signals.deleted.emit(self)
        
        # Remove the label first to avoid dangling references
        if self.label and self.label.scene():
            scene.removeItem(self.label)
        
        # Remove from scene
        if scene:
            scene.removeItem(self)
            
            # Force update the affected area
            scene.update(scene_path)
            
            # Update all connected views
            for view in scene.views():
                view.viewport().update()
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        menu = QMenu()
        
        # Add "Edit Label" action
        edit_action = QAction("Edit Label", self.scene().views()[0])
        edit_action.triggered.connect(self._start_label_editing)
        menu.addAction(edit_action)
        
        # Add "Show Connection Info" action
        info_action = QAction("Connection Info", self.scene().views()[0])
        info_action.triggered.connect(self._show_connection_info)
        menu.addAction(info_action)
        
        # Add other possible actions
        delete_action = QAction("Delete Connection", self.scene().views()[0])
        delete_action.triggered.connect(self._delete_connection)
        menu.addAction(delete_action)
        
        # Show the menu at the event position
        menu.exec_(event.screenPos())
    
    def _show_connection_info(self):
        """Show a dialog with connection information."""
        from PyQt5.QtWidgets import QMessageBox
        
        # Get connection type display name
        from constants import ConnectionTypes
        conn_type_display = ConnectionTypes.DISPLAY_NAMES.get(
            self.connection_type, 
            "Unknown Connection Type"
        )
        
        # Build info message
        info = f"Connection Type: {conn_type_display}\n"
        info += f"Label: {self.label_text}\n"
        
        if self.bandwidth:
            info += f"Bandwidth: {self.bandwidth}\n"
        if self.latency:
            info += f"Latency: {self.latency}\n"
            
        info += f"Source Device: {self.source_device.name}\n"
        info += f"Target Device: {self.target_device.name}\n"
        
        # Show the info dialog
        QMessageBox.information(
            self.scene().views()[0], 
            "Connection Information",
            info
        )
    
    def _start_label_editing(self):
        """Start editing the connection label."""
        if self.label:
            self.label.editing = True
            self.label.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.label.setFocus()
    
    def _delete_connection(self):
        """Delete this connection."""
        # Disconnect from device signals
        if self.source_device and hasattr(self.source_device, 'signals'):
            if hasattr(self.source_device.signals, 'moved'):
                self.source_device.signals.moved.disconnect(self._on_device_moved)
        
        if self.target_device and hasattr(self.target_device, 'signals'):
            if hasattr(self.target_device.signals, 'moved'):
                self.target_device.signals.moved.disconnect(self._on_device_moved)
        
        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)
            
            # Notify the canvas that a connection was deleted (if signal exists)
            for view in self.scene().views():
                if hasattr(view, 'connection_deleted'):
                    view.connection_deleted.emit(self)

    def _handle_device_moved(self, device):
        """Handle when a device has moved and update the connection accordingly."""
        # Update the path when either device moves
        self.update_path()
        
        # Force update in the scene
        if self.scene():
            scene_path = self.mapToScene(self.boundingRect()).boundingRect()
            self.scene().update(scene_path)

    def update_label(self):
        """Update connection label text."""
        if hasattr(self, 'label_item') and self.label_item and hasattr(self, 'label_text'):
            self.label_item.setPlainText(self.label_text)