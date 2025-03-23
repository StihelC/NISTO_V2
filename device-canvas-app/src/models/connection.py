from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem
from PyQt5.QtGui import QPen, QColor, QPainterPath, QFont, QBrush
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QObject, QRectF
import uuid
from constants import ConnectionTypes

class ConnectionSignals(QObject):
    """Signals for connection events."""
    selected = pyqtSignal(object)  # connection
    deleted = pyqtSignal(object)   # connection
    updated = pyqtSignal(object)   # connection

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
    
    def __init__(self, source_device, target_device, connection_type=None, label=None):
        super().__init__()
        
        # Create signals object
        self.signals = ConnectionSignals()
        
        # Store device references
        self.source_device = source_device
        self.target_device = target_device
        
        # Generate a unique ID
        self.id = str(uuid.uuid4())
        
        # Store source and target ports (scene coordinates)
        self._source_port = self._find_best_port(source_device, target_device)
        self._target_port = self._find_best_port(target_device, source_device)
        
        # Set connection properties
        self.connection_type = connection_type or ConnectionTypes.ETHERNET
        self.label_text = label or ""
        self.bandwidth = ""
        self.latency = ""
        
        # Visual properties
        self.routing_style = self.STYLE_STRAIGHT  # Default routing style
        self.line_width = 2
        self.line_color = QColor(30, 30, 30)
        self.line_style = Qt.SolidLine
        self.selected_color = QColor(255, 140, 0)  # Orange
        self._was_selected = False
        
        # Set style based on connection type
        self.set_style_for_type(self.connection_type)
        
        # Create label if text provided
        self.label = None
        if self.label_text:
            self.create_label()
            
        # Update path
        self.update_path()
        
        # Make selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Connect to device position changes
        self._connect_to_device_changes()
    
    def _connect_to_device_changes(self):
        """Connect to device position changes to update connection path."""
        # This requires devices to emit signals when they move
        if hasattr(self.source_device, 'signals') and hasattr(self.source_device.signals, 'moved'):
            self.source_device.signals.moved.connect(self.update_path)
        if hasattr(self.target_device, 'signals') and hasattr(self.target_device.signals, 'moved'):
            self.target_device.signals.moved.connect(self.update_path)
    
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
            
        elif self.STYLE_CURVED:
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
        
        # Update label position if needed
        if self.label:
            self._update_label_position()
    
    def _update_label_position(self):
        """Place label at center of connection."""
        if not self.label:
            return
            
        # Get path center point
        path_length = self.path().length()
        center_point = self.path().pointAtPercent(0.5)
        
        # Position label slightly above the path
        label_offset = QPointF(-self.label.boundingRect().width()/2, -self.label.boundingRect().height())
        self.label.setPos(center_point + label_offset)
    
    def set_style_for_type(self, connection_type):
        """Set the visual style based on the connection type."""
        if connection_type == ConnectionTypes.ETHERNET:
            # Ethernet - solid black line
            self.line_color = QColor(0, 0, 0)
            self.line_style = Qt.SolidLine
            self.line_width = 2
        elif connection_type == ConnectionTypes.SERIAL:
            # Serial - blue dashed line
            self.line_color = QColor(0, 0, 255)
            self.line_style = Qt.DashLine
            self.line_width = 1.5
        elif connection_type == ConnectionTypes.FIBER:
            # Fiber - green solid line, thicker
            self.line_color = QColor(0, 128, 0)
            self.line_style = Qt.SolidLine
            self.line_width = 3
        elif connection_type == ConnectionTypes.WIRELESS:
            # Wireless - purple dotted line
            self.line_color = QColor(128, 0, 128)
            self.line_style = Qt.DotLine
            self.line_width = 1.5
        else:
            # Default style
            self.line_color = QColor(0, 0, 0)
            self.line_style = Qt.SolidLine
            self.line_width = 2
        
        # Apply style
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
            self.label = QGraphicsTextItem(self)
            self.label.setPlainText(self.label_text)
            
            # Set Z-value to be above the connection line
            self.label.setZValue(self.zValue() + 1)
            
            # Update position
            self._update_label_position()
    
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
    
    def delete(self):
        """Remove this connection."""
        # Disconnect from devices
        if self.source_device:
            self.source_device.remove_connection(self)
        
        if self.target_device:
            self.target_device.remove_connection(self)
        
        # Emit signal before removal
        self.signals.deleted.emit(self)
        
        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)