from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem, QFileDialog
from PyQt5.QtGui import QPixmap, QColor, QPen, QBrush, QPainterPath, QPainter, QFont
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

class Device(QGraphicsPixmapItem):
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
        
        # Initialize component variables
        self.label = None
        self.image = None
        self.box = None
        self.rect_item = None
        self.text_item = None
        self.icon_item = None
        
        # Create child items
        self._create_visuals()
        
        # Set up parent-child relationships
        if self.text_item:
            self.text_item.setParentItem(self)
        if self.icon_item:
            self.icon_item.setParentItem(self)
        if self.rect_item:
            self.rect_item.setParentItem(self)
        
        # Make device children non-movable by default
        # This ensures that device components can't be moved separately
        for child in self.childItems():
            child.setFlag(QGraphicsItem.ItemIsSelectable, False)
            child.setFlag(QGraphicsItem.ItemIsMovable, False)
            child.setAcceptedMouseButtons(Qt.NoButton)
        
        # Initialize display properties dictionary
        self.display_properties = {}
        
        # Create property labels
        self.property_labels = {}
    
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
        
        # Create text item for the name
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText(self.name)
        
        # Center the text
        text_width = self.text_item.boundingRect().width()
        text_x = (self.width - text_width) / 2
        self.text_item.setPos(text_x, self.height + 5)  # Position below rectangle
        
        # Try to load the icon as a separate item
        self._try_load_icon()
    
    def _try_load_icon(self):
        """Try to load an icon for the device type or name from multiple possible locations."""
        # First check for custom icon path (highest priority)
        if self.custom_icon_path and os.path.exists(self.custom_icon_path):
            self.logger.info(f"ICON DEBUG: Loading custom icon from: {self.custom_icon_path}")
            if self._load_icon(self.custom_icon_path):
                return True
        
        # Log the current working directory to help with debugging path issues
        cwd = os.getcwd()
        self.logger.info(f"ICON DEBUG: Current working directory: {cwd}")
        
        # Get all possible icon folders
        icon_folders = self._get_icon_directories()
        self.logger.info(f"ICON DEBUG: Searching in icon folders: {icon_folders}")
        
        # Search for device type icons first with multiple case variations
        type_variations = [
            self.device_type.lower(),
            self.device_type,
            self.device_type.upper(),
            self.device_type.capitalize()
        ]
        
        # Try each type variation with each icon folder
        for folder in icon_folders:
            for type_var in type_variations:
                icon_path = os.path.join(folder, f"{type_var}.png")
                self.logger.info(f"ICON DEBUG: Checking type icon at: {icon_path}")
                if os.path.exists(icon_path):
                    self.logger.info(f"ICON DEBUG: Found type icon at: {icon_path}")
                    if self._load_icon(icon_path):
                        return True

        # Try the icon name specified in properties
        icon_name = self.properties.get('icon', 'device.png')
        if icon_name:
            for folder in icon_folders:
                icon_path = os.path.join(folder, icon_name)
                self.logger.info(f"ICON DEBUG: Checking property icon at: {icon_path}")
                if os.path.exists(icon_path):
                    self.logger.info(f"ICON DEBUG: Found property icon at: {icon_path}")
                    if self._load_icon(icon_path):
                        return True
        
        # Try device name-based icons
        if self._try_load_icon_by_name(self.name):
            return True
        
        # Try default "generic" icon as last resort
        for folder in icon_folders:
            default_icon = os.path.join(folder, "device.png")
            if os.path.exists(default_icon):
                self.logger.info(f"ICON DEBUG: Using default icon: {default_icon}")
                if self._load_icon(default_icon):
                    return True
        
        self.logger.warning(f"ICON DEBUG: No icon found for device {self.name} of type {self.device_type}")
        return False

    def _get_icon_directories(self):
        """Get all possible icon directories, relative to different references."""
        import sys
        import os.path
        
        # Start with current directory and known relative paths
        icon_dirs = ["icons"]
        
        # Add application directory and its relative paths
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logger.info(f"ICON DEBUG: Application directory: {app_dir}")
        
        # Add all possible icon locations relative to the app directory
        icon_dirs.extend([
            os.path.join(app_dir, "icons"),
            os.path.join(app_dir, "resources", "icons"),
            os.path.join(app_dir, "src", "resources", "icons"),
            os.path.join(app_dir, "src", "icons"),
            # For development environments, try a few levels up
            os.path.join(app_dir, "..", "resources", "icons"),
            os.path.join(app_dir, "..", "icons"),
        ])
        
        # Filter to only directories that actually exist
        existing_dirs = [d for d in icon_dirs if os.path.isdir(d)]
        
        # If we found no existing directories, return the theoretical ones anyway
        return existing_dirs if existing_dirs else icon_dirs

    def _try_load_icon_by_name(self, name):
        """Try to load an icon that matches the device name."""
        # Normalize name (lowercase, remove spaces)
        normalized_name = name.lower().replace(" ", "_")
        
        # Check for different image formats
        extensions = ['.png', '.jpg', '.jpeg', '.svg', '.webp']
        
        # Get all possible icon folders
        icon_folders = self._get_icon_directories()
        
        # Try each combination of folder, name variation, and extension
        name_variations = [
            normalized_name,
            name,
            name.lower(),
        ]
        
        for folder in icon_folders:
            for name_var in name_variations:
                for ext in extensions:
                    path = os.path.join(folder, f"{name_var}{ext}")
                    if os.path.exists(path):
                        self.logger.info(f"ICON DEBUG: Found matching icon at {path}")
                        if self._load_icon(path):
                            return True
        
        return False

    def _load_icon(self, path):
        """Load and set the icon from the given path, preserving quality."""
        self.logger.info(f"ICON DEBUG: Attempting to load icon from: {path}")
        
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.logger.info(f"ICON DEBUG: Successfully loaded pixmap from {path}, size: {pixmap.width()}x{pixmap.height()}")
            
            # Create a new pixmap with the exact device dimensions
            square_pixmap = QPixmap(self.width, self.height)
            square_pixmap.fill(Qt.transparent)  # Make it transparent
            
            # Calculate aspect ratio to maintain proportions
            src_width = pixmap.width()
            src_height = pixmap.height()
            
            if src_width == 0 or src_height == 0:
                self.logger.error(f"ICON DEBUG: Invalid image dimensions in {path}: {src_width}x{src_height}")
                return False
                
            aspect_ratio = src_width / src_height
            
            # Determine target dimensions while maintaining aspect ratio
            if aspect_ratio >= 1:  # Wider than tall
                dest_width = self.width
                dest_height = int(self.width / aspect_ratio)
                dest_x = 0
                dest_y = (self.height - dest_height) // 2
            else:  # Taller than wide
                dest_height = self.height
                dest_width = int(self.height * aspect_ratio)
                dest_y = 0
                dest_x = (self.width - dest_width) // 2
            
            self.logger.info(f"ICON DEBUG: Scaled size: {dest_width}x{dest_height}, position: ({dest_x},{dest_y})")
            
            # Draw the image with high quality
            painter = QPainter(square_pixmap)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            
            # Draw the image centered with proper aspect ratio
            painter.drawPixmap(
                dest_x, dest_y, dest_width, dest_height,
                pixmap
            )
            painter.end()
            
            # Check if we already have an icon item and remove it
            if hasattr(self, 'icon_item') and self.icon_item:
                self.logger.info("ICON DEBUG: Removing existing icon item before adding new one")
                if self.icon_item.scene():
                    self.scene().removeItem(self.icon_item)
            
            # Use the properly scaled pixmap
            self.icon_item = QGraphicsPixmapItem(square_pixmap, self)
            self.icon_item.setPos(0, 0)  # Position at top-left corner
            
            # Make sure icon is visible
            self.icon_item.setZValue(1)  # Put icon above the background rectangle
            
            self.logger.info(f"ICON DEBUG: Successfully created icon_item")
            return True
        else:
            self.logger.error(f"ICON DEBUG: Failed to load icon from: {path}, pixmap is null")
            return False
    
    def upload_custom_icon(self):
        """Open a file dialog to upload a custom high-resolution icon."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            None, 
            "Select High-Resolution Icon", 
            "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)", 
            options=options
        )
        if file_path:
            self.custom_icon_path = file_path
            self.logger.debug(f"Custom high-resolution icon uploaded: {self.custom_icon_path}")
            # Remove existing icon if any
            if hasattr(self, 'icon_item') and self.icon_item:
                if self.icon_item.scene():
                    self.scene().removeItem(self.icon_item)
                self.icon_item = None
            # Load the new icon with high quality
            self._load_icon(self.custom_icon_path)
            self.update()  # Force redraw
            return True
        return False
    
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
        return ((p1.x() - p2.x()) ** 2 + (p2.y() - p2.y()) ** 2) ** 0.5
    
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
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events to keep all components together."""
        # Call the base implementation to handle the actual dragging
        super().mouseMoveEvent(event)
        
        # Make sure all child items stay aligned with the device
        # This is redundant but ensures integrity in case something goes wrong
        for child in self.childItems():
            # Special handling for text_item (label) which should remain at its position below the device
            if child == self.text_item:
                # Ensure label stays centered under the device
                text_width = child.boundingRect().width()
                text_x = (self.width - text_width) / 2
                child.setPos(text_x, self.height + 5)
            # All other children should be at 0,0 relative to device
            elif child.pos() != QPointF(0, 0):
                child.setPos(QPointF(0, 0))
        
        # Emit signal that device has moved
        if hasattr(self, 'signals'):
            self.signals.moved.emit(self)
        
        # Update connections
        self.update_connections()

    def update_connections(self):
        """Update all connections attached to this device."""
        for connection in self.connections:
            try:
                # Use hasattr to safely check for the update_path method
                if hasattr(connection, 'update_path'):
                    connection.update_path()
                # For compatibility with older code that might use different method names
                elif hasattr(connection, '_update_path'):
                    connection._update_path()
            except Exception as e:
                self.logger.error(f"Error updating connection: {str(e)}")

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
            
            # Update property positions as name might have changed size
            self.update_property_labels()

    def update_color(self):
        """Update device visual appearance after color change."""
        if hasattr(self, 'color'):
            # Store the color in the properties dictionary
            if hasattr(self, 'properties'):
                self.properties['color'] = self.color
            
            # Update the visual appearance with the new color
            if hasattr(self, 'rect_item'):
                # Create a new brush with the updated color
                brush = QBrush(self.color)
                self.rect_item.setBrush(brush)
                
                # Use black border regardless of color for consistency
                self.rect_item.setPen(QPen(Qt.black, 1))
                
                # Force a redraw of the device
                if self.scene():
                    update_rect = self.sceneBoundingRect().adjusted(-5, -5, 5, 5)
                    self.scene().update(update_rect)
                
                self.update()  # This calls the Qt update method
                
                self.logger.debug(f"Device '{self.name}' color updated to {self.color.name()}")

    def center_pos(self):
        """Get the center position of the device in scene coordinates."""
        return self.get_center_position()

    def setFlag(self, flag, enabled):
        """Override setFlag to properly propagate flags to child items."""
        # Call the base implementation first
        super().setFlag(flag, enabled)
        
        # Only handle ItemIsMovable flag
        if flag == QGraphicsItem.ItemIsMovable:
            # Apply the same flag to all child items
            for child in self.childItems():
                # Use setFlag directly instead of setFlags
                child.setFlag(QGraphicsItem.ItemIsMovable, enabled)

    def update_property_labels(self):
        """Update the property labels displayed under the device icon."""
        # Remove all existing property labels
        for label in self.property_labels.values():
            scene = label.scene()
            if scene:
                scene.removeItem(label)
        self.property_labels.clear()
        
        # Get properties to display
        display_props = []
        for prop, show in self.display_properties.items():
            if show and prop in self.properties:
                display_props.append((prop, str(self.properties[prop])))
        
        # If no properties to display, just return
        if not display_props:
            return
        
        # Start positioning from the bottom of the device plus the name label height
        # First, calculate where the name text ends
        name_bottom = self.height + self.text_item.boundingRect().height() + 5
        
        # Create new labels for selected properties
        for i, (prop, value) in enumerate(display_props):
            label = QGraphicsTextItem(self)
            # Show only the value without the property name
            label.setPlainText(f"{value}")
            label.setFont(QFont("Arial", 8))
            
            # Center the label horizontally
            x_pos = (self.width - label.boundingRect().width()) / 2
            
            # Position each property below the name, with spacing between properties
            # Add additional offset to ensure it's below both the device and name
            y_pos = name_bottom + (i * (label.boundingRect().height() + 2))
            
            label.setPos(x_pos, y_pos)
            self.property_labels[prop] = label