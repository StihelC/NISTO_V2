from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem, QFileDialog
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
    
    def __init__(self, name, device_type, properties=None, custom_icon_path=None):
        """Initialize a network device."""
        super().__init__()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Device properties
        self.id = str(uuid.uuid4())
        self.name = name
        self.device_type = device_type
        self.properties = self._init_properties(properties)
        
        # Path to custom icon if uploaded
        self.custom_icon_path = custom_icon_path
        self.logger.debug(f"Custom icon path set to: {self.custom_icon_path}")
        
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
        
        # List of connections attached to this device
        self.connections = []
        
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
        if self.custom_icon_path:
            self.logger.debug(f"Trying to load custom icon from: {self.custom_icon_path}")
            self._load_icon(self.custom_icon_path)
        else:
            icon_name = self.properties.get('icon', 'device.png')
            icon_paths = [
                f"icons/{icon_name}",
                f"resources/icons/{icon_name}",
                f"src/resources/icons/{icon_name}",
                f"../resources/icons/{icon_name}"
            ]
            for path in icon_paths:
                if os.path.exists(path):
                    self.logger.debug(f"Loading default icon from: {path}")
                    self._load_icon(path)
                    return
            self.logger.warning(f"No icon found for device type {self.device_type}")
    
    def _load_icon(self, path):
        """Load and set the icon from the given path, cropping to fit in the square."""
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            # Create a new pixmap with the exact device dimensions
            square_pixmap = QPixmap(self.width, self.height)
            square_pixmap.fill(Qt.transparent)  # Make it transparent
            
            # Calculate the source rectangle (center of the original image)
            src_width = min(pixmap.width(), pixmap.height())
            src_height = src_width  # Keep it square
            
            src_x = (pixmap.width() - src_width) // 2
            src_y = (pixmap.height() - src_height) // 2
            
            # Draw the center portion of the original image onto the square pixmap
            painter = QPainter(square_pixmap)
            painter.drawPixmap(
                0, 0, self.width, self.height,  # Destination rectangle
                pixmap,
                src_x, src_y, src_width, src_height  # Source rectangle
            )
            painter.end()
            
            # Use the cropped square pixmap
            self.icon_item = QGraphicsPixmapItem(square_pixmap, self)
            self.icon_item.setPos(0, 0)  # Position at top-left corner
            
            self.logger.debug(f"Successfully loaded and cropped icon from: {path}")
        else:
            self.logger.error(f"Failed to load icon from: {path}")
    
    def upload_custom_icon(self):
        """Open a file dialog to upload a custom icon."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Custom Icon", "", "Images (*.png *.xpm *.jpg)", options=options)
        if file_path:
            self.custom_icon_path = file_path
            self.logger.debug(f"Custom icon uploaded: {self.custom_icon_path}")
            self._try_load_icon()
            self.update()  # Force redraw
    
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
    
    def get_nearest_port(self, pos):
        """Get the nearest connection port to the given position."""
        # Create port positions
        center = self.mapToScene(QPointF(self.width / 2, self.height / 2))
        
        # Define ports at the middle of each side
        top = QPointF(center.x(), center.y() - self.height / 2)
        right = QPointF(center.x() + self.width / 2, center.y())
        bottom = QPointF(center.x(), center.y() + self.height / 2)
        left = QPointF(center.x() - self.width / 2, center.y())
        
        # Find nearest edge point
        ports = [top, right, bottom, left]
        nearest_port = None
        min_distance = float('inf')
        
        for port in ports:
            dx = port.x() - pos.x()
            dy = port.y() - pos.y()
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_port = port
        
        # Debug nearest port
        if nearest_port:
            self.logger.debug(f"Nearest port for {self.name}: ({nearest_port.x()}, {nearest_port.y()})")
            
        return nearest_port
    
    def get_center_position(self):
        """Get the center position of the device in scene coordinates."""
        rect = self.boundingRect()
        return self.mapToScene(rect.center())
    
    def _distance(self, p1, p2):
        """Calculate distance between two points."""
        return ((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2) ** 0.5
    
    def setProperty(self, name, value):
        """Set a custom property."""
        if name == 'show_connection_points':
            self._show_connection_points = value
            self.update()  # Force redraw
        else:
            # Store in properties dict
            self.properties[name] = value
    
    def add_connection(self, connection):
        """Add a connection to this device's connections list."""
        if connection not in self.connections:
            self.connections.append(connection)
    
    def remove_connection(self, connection):
        """Remove a connection from this device's connections list."""
        if connection in self.connections:
            self.connections.remove(connection)
    
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
    
    def delete(self):
        """Clean up resources before deletion."""
        # Store scene and bounding rect before removal for later update
        scene = self.scene()
        update_rect = self.sceneBoundingRect().adjusted(-10, -10, 10, 10)
        
        # Remove the text label if it exists
        if hasattr(self, 'text_item') and self.text_item:
            if self.text_item.scene():
                self.scene().removeItem(self.text_item)
            self.text_item = None
        
        # Remove the icon if it exists
        if hasattr(self, 'icon_item') and self.icon_item:
            if self.icon_item.scene():
                self.scene().removeItem(self.icon_item)
            self.icon_item = None
        
        # Disconnect all signals
        if hasattr(self, 'signals'):
            if hasattr(self.signals, 'deleted'):
                self.signals.deleted.emit(self)
        
        # Clean up connections
        connections_to_remove = list(self.connections)  # Create a copy to avoid modification during iteration
        for connection in connections_to_remove:
            if hasattr(connection, 'delete'):
                connection.delete()
        
        # Force update the scene area after deletion
        if scene:
            scene.update(update_rect)
            # Force update on all views
            for view in scene.views():
                view.viewport().update()

    def update_name(self):
        """Update device name display after name change."""
        if hasattr(self, 'text_item'):
            self.text_item.setPlainText(self.name)
            
            # Center the text if needed
            if hasattr(self, 'width'):
                text_width = self.text_item.boundingRect().width()
                text_x = (self.width - text_width) / 2
                self.text_item.setPos(text_x, self.height + 5)

    def update_color(self):
        """Update device visual appearance after color change."""
        if hasattr(self, 'color'):
            # Set the color in properties dict
            if hasattr(self, 'properties'):
                self.properties['color'] = self.color
            
            # Update the visual appearance
            if hasattr(self, 'rect_item'):
                brush = QBrush(self.color)
                self.rect_item.setBrush(brush)
                
                # Force redraw
                self.update()