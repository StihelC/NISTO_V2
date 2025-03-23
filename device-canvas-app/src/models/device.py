from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QPixmap, QColor, QPen, QBrush, QPainterPath, QPainter
from PyQt5.QtCore import QRectF, Qt, QPointF, QObject, pyqtSignal
import uuid
import os
import logging
from constants import DeviceTypes

class DeviceSignals(QObject):
    """Signals emitted by devices."""
    selected = pyqtSignal(object, bool)  # device, is_selected
    moved = pyqtSignal(object)  # device
    double_clicked = pyqtSignal(object)  # device
    deleted = pyqtSignal(object)  # device

class Device(QGraphicsItem):
    """Represents a network device in the topology."""
    
    # Device properties organized by type
    DEVICE_PROPERTIES = {
        DeviceTypes.ROUTER: {
            'icon': 'router.png',
            'color': QColor(200, 120, 60),  # Orange-brown
            'routing_protocol': 'OSPF',
            'forwarding_table': {}
        },
        DeviceTypes.SWITCH: {
            'icon': 'switch.png',
            'color': QColor(60, 120, 200),  # Blue
            'ports': 24,
            'managed': True,
            'vlan_support': True
        },
        DeviceTypes.FIREWALL: {
            'icon': 'firewall.png',
            'color': QColor(200, 60, 60),  # Red
            'rules': [],
            'inspection_type': 'stateful'
        },
        DeviceTypes.SERVER: {
            'icon': 'server.png',
            'color': QColor(60, 160, 60),  # Green
            'services': [],
            'os': 'Linux'
        },
        DeviceTypes.WORKSTATION: {
            'icon': 'workstation.png',
            'color': QColor(150, 120, 180),  # Purple
            'os': 'Windows'
        },
        DeviceTypes.CLOUD: {
            'icon': 'cloud.png',
            'color': QColor(100, 160, 220),  # Light blue
            'provider': 'AWS'
        },
        DeviceTypes.GENERIC: {
            'icon': 'device.png',
            'color': QColor(150, 150, 150)  # Gray
        }
    }
    
    def __init__(self, name, device_type, properties=None):
        """Initialize a network device."""
        super().__init__()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Device properties
        self.id = str(uuid.uuid4())
        self.name = name
        self.device_type = device_type
        self.properties = self._init_properties(properties)
        
        # Create signals object
        self.signals = DeviceSignals()
        
        # Set flags for interactivity
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Set Z value to be above connections
        self.setZValue(10)
        
        # Size settings
        self.width = 60
        self.height = 60
        
        # Track selection state
        self.is_selected = False
        
        # Track connection points visibility
        self._show_connection_points = False
        
        # Create child items
        self._create_visuals()
    
    def _init_properties(self, custom_properties=None):
        """Initialize the device properties based on type and custom values."""
        # Get default properties for this device type
        default_props = self.DEVICE_PROPERTIES.get(self.device_type, self.DEVICE_PROPERTIES[DeviceTypes.GENERIC]).copy()
        
        # Override with custom properties if provided
        if custom_properties:
            default_props.update(custom_properties)
        
        return default_props
    
    def _create_visuals(self):
        """Create the visual representation of the device."""
        # Create background rectangle
        self.rect_item = QGraphicsRectItem(0, 0, self.width, self.height, self)
        
        # Set the visual appearance based on device type
        device_color = self.properties.get('color', QColor(150, 150, 150))
        
        # Create a visually distinct appearance with gradient or solid color
        brush = QBrush(device_color)
        self.rect_item.setBrush(brush)
        self.rect_item.setPen(QPen(Qt.black, 1))
        
        # Add text for the device name
        self.text_item = QGraphicsTextItem(self.name, self)
        # Center the text
        text_width = self.text_item.boundingRect().width()
        text_x = (self.width - text_width) / 2
        self.text_item.setPos(text_x, self.height + 5)  # Position below rectangle
        
        # Try to load the icon as a separate item
        self.icon_item = None
        self._try_load_icon()
    
    def _try_load_icon(self):
        """Try to load an icon for the device type."""
        try:
            # Get icon name from properties
            icon_name = self.properties.get('icon', 'device.png')
            
            # Possible icon locations
            icon_paths = [
                f"icons/{icon_name}",
                f"resources/icons/{icon_name}",
                f"src/resources/icons/{icon_name}",
                f"../resources/icons/{icon_name}"
            ]
            
            for path in icon_paths:
                if os.path.exists(path):
                    pixmap = QPixmap(path)
                    if not pixmap.isNull():
                        # Create icon item
                        self.icon_item = QGraphicsPixmapItem(pixmap, self)
                        # Scale the icon to fit
                        icon_scale = min(self.width / pixmap.width(), self.height / pixmap.height()) * 0.7
                        self.icon_item.setScale(icon_scale)
                        # Center the icon
                        icon_width = pixmap.width() * icon_scale
                        icon_height = pixmap.height() * icon_scale
                        icon_x = (self.width - icon_width) / 2
                        icon_y = (self.height - icon_height) / 2
                        self.icon_item.setPos(icon_x, icon_y)
                        return
                        
            self.logger.warning(f"No icon found for device type {self.device_type}")
        except Exception as e:
            self.logger.error(f"Error loading device icon: {str(e)}")
    
    def boundingRect(self):
        """Return the bounding rectangle of the device."""
        # Include space for text below
        return QRectF(0, 0, self.width, self.height + 20)
    
    def shape(self):
        """Return a more precise shape for hit detection."""
        path = QPainterPath()
        path.addRect(0, 0, self.width, self.height)  # Just the main rectangle, not the text
        return path
    
    def paint(self, painter, option, widget=None):
        """Paint the device with connection points if needed."""
        # Most painting is handled by child items, but we draw connection points here
        
        # Check if we need to show connection points
        showing_points = self._show_connection_points
        
        # Also show connection points when in connection mode
        if not showing_points and self.scene():
            from constants import Modes
            canvas = self._get_canvas()
            if canvas and hasattr(canvas, 'mode_manager'):
                mode_mgr = canvas.mode_manager
                if hasattr(mode_mgr, 'get_current_mode') and mode_mgr.current_mode == Modes.ADD_CONNECTION:
                    showing_points = True
                    
                    # Check if this device is being hovered in connection mode
                    if hasattr(mode_mgr, 'get_mode_instance'):
                        mode = mode_mgr.get_mode_instance()
                        is_hovered = hasattr(mode, 'hover_device') and mode.hover_device == self
        
        # Draw selection indicator
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 140, 0), 2))  # Orange selection
            painter.drawRect(-2, -2, self.width + 4, self.height + 4)
        
        # Draw connection points if needed
        if showing_points:
            painter.save()
            
            # Use a lighter color if this device is being hovered in connection mode
            is_hovered = False
            canvas = self._get_canvas()
            if canvas and hasattr(canvas, 'mode_manager'):
                if hasattr(canvas.mode_manager, 'get_mode_instance'):
                    mode = canvas.mode_manager.get_mode_instance()
                    is_hovered = hasattr(mode, 'hover_device') and mode.hover_device == self
            
            if is_hovered:
                # Highlighted port appearance
                painter.setPen(QPen(QColor(65, 105, 225), 2))  # Royal blue
                painter.setBrush(QBrush(QColor(65, 105, 225, 100)))
                radius = 6
            else:
                # Normal port appearance
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.setBrush(QBrush(QColor(200, 200, 200, 150)))
                radius = 4
            
            # Draw each port
            for port in self.get_connection_ports():
                painter.drawEllipse(port, radius, radius)
                
            painter.restore()
    
    def _get_canvas(self):
        """Helper method to get the canvas that contains this device."""
        if not self.scene():
            return None
        
        # Try to get parent, which should be the canvas
        parent = self.scene().views()[0] if self.scene().views() else None
        return parent
    
    def get_connection_ports(self):
        """Get all available connection ports as local coordinates."""
        # Define 8 compass points around the device
        center_x = self.width / 2
        center_y = self.height / 2
        
        ports = [
            QPointF(center_x, 0),                # N
            QPointF(self.width, 0),              # NE
            QPointF(self.width, center_y),       # E
            QPointF(self.width, self.height),    # SE
            QPointF(center_x, self.height),      # S
            QPointF(0, self.height),             # SW
            QPointF(0, center_y),                # W
            QPointF(0, 0)                        # NW
        ]
        
        return ports
    
    def get_nearest_port(self, scene_pos):
        """Get the nearest connection point to the given scene position."""
        # Convert scene position to local coordinates
        local_pos = self.mapFromScene(scene_pos)
        
        # Get all connection ports
        ports = self.get_connection_ports()
        
        # Find closest port
        closest_port = ports[0]
        min_distance = self._distance(local_pos, ports[0])
        
        for port in ports[1:]:
            distance = self._distance(local_pos, port)
            if distance < min_distance:
                min_distance = distance
                closest_port = port
        
        # Convert back to scene coordinates
        return self.mapToScene(closest_port)
    
    def _distance(self, p1, p2):
        """Calculate distance between two points."""
        return ((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2) ** 0.5
    
    def get_center_position(self):
        """Get the center position of the device in scene coordinates."""
        center = QPointF(self.width / 2, self.height / 2)
        return self.mapToScene(center)
    
    def setProperty(self, name, value):
        """Set a custom property."""
        if name == 'show_connection_points':
            self._show_connection_points = value
            self.update()  # Force redraw
        else:
            # Store in properties dict
            self.properties[name] = value
    
    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Item is about to move
            pass
        elif change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            # Item has moved
            if hasattr(self.signals, 'moved'):
                self.signals.moved.emit(self)
        elif change == QGraphicsItem.ItemSelectedChange:
            # Selection state is about to change
            self.is_selected = bool(value)
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            # Selection state has changed
            if hasattr(self.signals, 'selected'):
                self.signals.selected.emit(self, self.isSelected())
            
        return super().itemChange(change, value)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click events."""
        if hasattr(self.signals, 'double_clicked'):
            self.signals.double_clicked.emit(self)
        super().mouseDoubleClickEvent(event)