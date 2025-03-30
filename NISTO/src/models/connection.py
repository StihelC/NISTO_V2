from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem, QMenu, QAction
from PyQt5.QtGui import QPen, QColor, QPainterPath, QFont, QBrush
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QObject, QRectF
import uuid
from constants import ConnectionTypes

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
    """A connection between two devices."""
    
    # Line styles
    STYLE_SOLID = Qt.SolidLine
    STYLE_DASHED = Qt.DashLine
    STYLE_DOTTED = Qt.DotLine
    
    # Connection styles
    STYLE_STRAIGHT = 0
    STYLE_ORTHOGONAL = 1
    STYLE_CURVED = 2
    
    def __init__(self, source_device, target_device, connection_type=None, label=None, bandwidth=None, latency=None):
        super().__init__()
        
        # Create signals object
        self.signals = ConnectionSignals()
        
        # Store device references
        self.source_device = source_device
        self.target_device = target_device
        
        # Register this connection with the devices
        if hasattr(source_device, 'add_connection'):
            source_device.add_connection(self)
        if hasattr(target_device, 'add_connection'):
            target_device.add_connection(self)
        
        # Generate a unique ID
        self.id = str(uuid.uuid4())
        
        # Store source and target ports (scene coordinates)
        self._source_port = self._find_best_port(source_device, target_device)
        self._target_port = self._find_best_port(target_device, source_device)
        
        # Set connection properties
        self.connection_type = connection_type or ConnectionTypes.ETHERNET
        self.label_text = label or "Link"  # Default label text
        self.bandwidth = bandwidth or ""
        self.latency = latency or ""
        
        # Visual properties
        self.routing_style = self.STYLE_STRAIGHT  # Default routing style
        self.line_width = 2
        self.line_color = QColor(30, 30, 30)
        self.line_style = Qt.SolidLine
        self.selected_color = QColor(255, 140, 0)  # Orange
        self._was_selected = False
        
        # Set style based on connection type
        self.set_style_for_type(self.connection_type)
        
        # Always create a label (with default text if none provided)
        self.label = None
        self.create_label()
            
        # Update path
        self.update_path()
        
        # Make selectable and ensure it accepts mouse events
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)  # Can receive keyboard focus
        self.setAcceptHoverEvents(True)  # Will receive hover events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)  # Accept mouse buttons
        
        # Connect to device position changes
        self._connect_to_device_changes()
    
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
        # Re-calculate ports in case devices moved
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
        
        # Always update label position when path changes
        self._update_label_position()
    
    def _update_label_position(self):
        """Place label at center of connection."""
        if not self.label:
            return
            
        # Get path center point
        path_length = self.path().length()
        center_point = self.path().pointAtPercent(0.5)
        
        # Position the label precisely at the center
        label_width = self.label.boundingRect().width()
        label_height = self.label.boundingRect().height()
        
        self.label.setPos(
            center_point.x() - label_width/2,
            center_point.y() - label_height/2
        )
        
        # Only show editing UI when editing
        if not getattr(self.label, 'editing', False):
            self.label.setTextInteractionFlags(Qt.NoTextInteraction)
    
    def set_style_for_type(self, connection_type):
        """Set the visual style based on the connection type."""
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
        
        # Apply style
        self.line_color = style['color']
        self.line_style = style['style']
        self.line_width = style['width']
        self._apply_style()
    
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
        self.routing_style = style
        self.update_path()
    
    def paint(self, painter, option, widget=None):
        """Custom painting."""
        # Check if selected and update style if needed
        if self.isSelected() != self._was_selected:
            self._was_selected = self.isSelected()
            self._apply_style()
        
        # Call the parent paint method
        super().paint(painter, option, widget)
    
    def itemChange(self, change, value):
        """Handle item changes like selection."""
        if change == QGraphicsItem.ItemSelectedChange:
            # Emit signal when selection changes
            if value:
                self.signals.selected.emit(self)
            else:
                self.signals.selected.emit(self)
            
            # Update appearance
            self._apply_style()
        
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        # Highlight connection on hover
        self.setPen(QPen(self.selected_color, self.line_width + 1, self.line_style))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        # Restore original appearance
        self._apply_style()
        super().hoverLeaveEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Allow editing the label text on double-click."""
        # Always start editing the label on double-click anywhere on the connection
        self._start_label_editing()
        super().mouseDoubleClickEvent(event)
    
    def delete(self):
        """Remove this connection."""
        # Disconnect from devices
        if self.source_device:
            if hasattr(self.source_device, 'remove_connection'):
                self.source_device.remove_connection(self)
        
        if self.target_device:
            if hasattr(self.target_device, 'remove_connection'):
                self.target_device.remove_connection(self)
        
        # Emit signal before removal
        self.signals.deleted.emit(self)
        
        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)
    
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