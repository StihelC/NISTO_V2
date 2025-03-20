from PyQt5.QtCore import QPointF, pyqtSignal, Qt, QObject
from PyQt5.QtWidgets import (QGraphicsItemGroup, QGraphicsItem, QGraphicsTextItem,
                           QGraphicsRectItem, QGraphicsEllipseItem)
from PyQt5.QtGui import QPixmap, QFont, QPen, QBrush, QColor
import uuid

# Create a QObject-based class for signals
class DeviceSignals(QObject):
    position_changed = pyqtSignal(object)
    selection_changed = pyqtSignal(object, bool)

class Device(QGraphicsItemGroup):
    """Unified device class for network topology.
    
    This class handles both the data model and visual representation of network devices.
    """
    
    # Device type constants
    ROUTER = "router"
    SWITCH = "switch"
    SERVER = "server"
    FIREWALL = "firewall"
    CLOUD = "cloud"
    WORKSTATION = "workstation"
    GENERIC = "generic"
    
    # Visual appearance constants
    DEFAULT_RECT_SIZE = 80
    PORT_SIZE = 12
    LABEL_FONT_SIZE = 10
    TYPE_FONT_SIZE = 8
    BORDER_WIDTH = 2
    
    # Colors for different device types
    DEVICE_COLORS = {
        ROUTER: QColor(200, 200, 255),     # Light blue for routers
        SWITCH: QColor(200, 255, 200),     # Light green for switches
        SERVER: QColor(255, 200, 200),     # Light red for servers
        FIREWALL: QColor(255, 200, 100),   # Orange for firewalls
        CLOUD: QColor(230, 230, 255),      # Very light blue for cloud
        WORKSTATION: QColor(220, 220, 220),# Light gray for workstations
        GENERIC: QColor(240, 240, 240)     # Light gray for generic devices
    }
    
    # Device type properties
    DEVICE_PROPERTIES = {
        ROUTER: {
            'forwarding_table': {},
            'routing_protocol': 'OSPF',
            'icon': 'router.png',
        },
        SWITCH: {
            'vlan_support': True,
            'port_count': 24,
            'switching_capacity': '48 Gbps',
            'icon': 'switch.png',
        },
        SERVER: {
            'cpu': '4 cores',
            'memory': '16 GB',
            'storage': '1 TB',
            'os': 'Linux',
            'icon': 'server.png',
        },
        FIREWALL: {
            'inspection_type': 'Stateful',
            'throughput': '1 Gbps',
            'icon': 'firewall.png',
        },
        CLOUD: {
            'provider': 'Generic',
            'region': 'Default',
            'icon': 'cloud.png',
        },
        WORKSTATION: {
            'os': 'Windows',
            'cpu': '2 cores',
            'memory': '8 GB',
            'icon': 'workstation.png',
        },
        GENERIC: {
            'description': 'Generic network device',
            'icon': 'generic_device.png',
        }
    }
    
    def __init__(self, name, device_type):
        """Initialize a device."""
        super().__init__()
        
        # Create signals object
        self.signals = DeviceSignals()
        
        # Generate a unique ID
        self.id = str(uuid.uuid4())[:8]
        
        # Store basic properties
        self.name = name
        self.device_type = device_type.lower()
        self.connections = []
        
        # Copy properties from the device type template
        if self.device_type in self.DEVICE_PROPERTIES:
            self.properties = self.DEVICE_PROPERTIES[self.device_type].copy()
        else:
            self.device_type = self.GENERIC  # Fallback to generic
            self.properties = self.DEVICE_PROPERTIES[self.GENERIC].copy()
        
        # Define a single connection port
        self.port = {"position": QPointF(0, 0), "connections": []}
        
        # Visual components (will be set in _create_visual)
        self.rect_item = None
        self.name_item = None
        self.type_item = None
        self.port_visual = None
        
        # Set flags for interaction
        self.setFlag(QGraphicsItemGroup.ItemIsSelectable, True)
        self.setFlag(QGraphicsItemGroup.ItemIsMovable, True)
        self.setFlag(QGraphicsItemGroup.ItemSendsGeometryChanges, True)
        
        # Create visual representation
        self._create_visual()
        
        print(f"DEBUG: Device '{name}' of type '{device_type}' created with ID: {self.id}")
    
    def _create_visual(self):
        """Create the visual representation of the device."""
        try:
            rect_size = self.DEFAULT_RECT_SIZE
            
            # Create the device body (rectangle)
            self.rect_item = QGraphicsRectItem(-rect_size/2, -rect_size/2, rect_size, rect_size)
            self.rect_item.setPen(QPen(QColor(0, 0, 0), self.BORDER_WIDTH))
            
            # Set color based on device type
            color = self.DEVICE_COLORS.get(self.device_type, self.DEVICE_COLORS[self.GENERIC])
            self.rect_item.setBrush(QBrush(color))
            self.addToGroup(self.rect_item)
            
            # Add device name text
            self.name_item = QGraphicsTextItem(self.name)
            self.name_item.setFont(QFont("Arial", self.LABEL_FONT_SIZE))
            self.name_item.setPos(-self.name_item.boundingRect().width()/2, -rect_size/2 - 25)
            self.addToGroup(self.name_item)
            
            # Add device type text
            self.type_item = QGraphicsTextItem(self.device_type)
            self.type_item.setFont(QFont("Arial", self.TYPE_FONT_SIZE))
            self.type_item.setPos(-self.type_item.boundingRect().width()/2, rect_size/2 + 5)
            self.addToGroup(self.type_item)
            
            # Add single connection port (centered)
            self._init_port()
            
            print(f"DEBUG: Visual components created for device {self.name}")
            
        except Exception as e:
            print(f"ERROR: Failed to create visual for device: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _init_port(self):
        """Initialize the single connection port for the device."""
        try:
            port_size = self.PORT_SIZE
            
            # Create a small circle for the port at the center
            self.port_visual = QGraphicsEllipseItem(
                -port_size/2, 
                -port_size/2,
                port_size, 
                port_size
            )
            self.port_visual.setPen(QPen(Qt.black, 1))
            self.port_visual.setBrush(QBrush(QColor(100, 100, 100)))
            
            # Store the visual component in the port data
            self.port["visual"] = self.port_visual
            
            # Add port to the item group
            self.addToGroup(self.port_visual)
            
            # Make port invisible by default - will show when selected
            self.port_visual.setVisible(False)
            
            print(f"DEBUG: Initialized connection port for device {self.name}")
        
        except Exception as e:
            print(f"ERROR: Failed to initialize port: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def itemChange(self, change, value):
        """Handle item changes like selection and position."""
        if change == QGraphicsItemGroup.ItemPositionHasChanged:
            # Emit signal when position changes
            self.signals.position_changed.emit(self)
            
            # Update all connections
            for connection in self.connections:
                if hasattr(connection, 'update_position'):
                    connection.update_position()
            
        elif change == QGraphicsItemGroup.ItemSelectedChange:
            # Emit signal when selection changes
            self.signals.selection_changed.emit(self, bool(value))
            
            # Show/hide port based on selection
            if value:
                self.show_port()
            else:
                self.hide_port()
            
        return super().itemChange(change, value)
    
    def show_port(self):
        """Make connection port visible."""
        if self.port_visual:
            self.port_visual.setVisible(True)
    
    def hide_port(self):
        """Hide connection port."""
        if self.port_visual:
            self.port_visual.setVisible(False)
    
    def update_property(self, key, value):
        """Update a device property."""
        self.properties[key] = value
        print(f"DEBUG: Updated property '{key}' to '{value}' for device {self.name}")
    
    def add_connection(self, connection):
        """Add a connection to this device."""
        if connection not in self.connections:
            self.connections.append(connection)
            self.port["connections"].append(connection)
            print(f"DEBUG: Added connection to device {self.name}. Total connections: {len(self.connections)}")
    
    def remove_connection(self, connection):
        """Remove a connection from this device."""
        if connection in self.connections:
            self.connections.remove(connection)
            if connection in self.port["connections"]:
                self.port["connections"].remove(connection)
            print(f"DEBUG: Removed connection from device {self.name}. Remaining connections: {len(self.connections)}")
    
    def get_port_position(self):
        """Get the scene position of the connection port."""
        return self.mapToScene(self.port["position"])
    
    def update_name(self, new_name):
        """Update the device name."""
        self.name = new_name
        if self.name_item:
            self.name_item.setPlainText(new_name)
            # Recenter the text
            self.name_item.setPos(-self.name_item.boundingRect().width()/2, self.name_item.y())
        print(f"DEBUG: Updated device name to '{new_name}'")