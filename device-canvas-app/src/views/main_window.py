from PyQt5.QtWidgets import (QMainWindow, QToolBar, QAction, QFileDialog, 
                           QMessageBox, QMenu, QActionGroup, QDialog,
                           QGraphicsLineItem, QGraphicsItem)
from PyQt5.QtCore import QPointF, QRectF, QTimer, Qt
from PyQt5.QtGui import QColor, QPen
import logging
import math
from .canvas import Canvas
from constants import Modes, DeviceTypes, ConnectionTypes
from models.device import Device
from .device_dialog import DeviceDialog
from models.boundary import Boundary
from models.connection import Connection

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Device Canvas Application")
        self.setGeometry(100, 100, 800, 600)

        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)

        # Initialize device counter for generating unique names
        self.device_counter = 0
        
        # Connect signals
        self.connect_signals()
        
        self.create_toolbar()
    
    def connect_signals(self):
        """Connect signals to handlers."""
        # Connect canvas signals to handlers
        self.canvas.add_device_requested.connect(self.on_add_device_requested)
        self.canvas.delete_device_requested.connect(self.on_delete_device_requested)
        self.canvas.delete_item_requested.connect(self.on_delete_item_requested)
        self.canvas.add_boundary_requested.connect(self.on_add_boundary_requested)
        self.canvas.add_connection_requested.connect(self.on_add_connection_requested)
        self.canvas.delete_connection_requested.connect(self.on_delete_connection_requested)
        self.canvas.delete_boundary_requested.connect(self.on_delete_boundary_requested)
    
    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Create an action group for mutually exclusive mode buttons
        mode_group = QActionGroup(self)
        
        # Mode selection actions
        self.mode_actions = {}
        
        # Select mode
        select_action = QAction("Select", self)
        select_action.setCheckable(True)
        select_action.setChecked(True)  # Default mode
        select_action.triggered.connect(lambda: self.set_mode(Modes.SELECT))
        mode_group.addAction(select_action)
        toolbar.addAction(select_action)
        self.mode_actions[Modes.SELECT] = select_action
        
        # Add device mode
        add_device_action = QAction("Add Device", self)
        add_device_action.setCheckable(True)
        add_device_action.triggered.connect(lambda: self.set_mode(Modes.ADD_DEVICE))
        mode_group.addAction(add_device_action)
        toolbar.addAction(add_device_action)
        self.mode_actions[Modes.ADD_DEVICE] = add_device_action
        
        # Add connection mode
        add_connection_action = QAction("Add Connection", self)
        add_connection_action.setCheckable(True)
        add_connection_action.triggered.connect(lambda: self.set_mode(Modes.ADD_CONNECTION))
        mode_group.addAction(add_connection_action)
        toolbar.addAction(add_connection_action)
        self.mode_actions[Modes.ADD_CONNECTION] = add_connection_action
        
        # Add boundary mode
        add_boundary_action = QAction("Add Boundary", self)
        add_boundary_action.setCheckable(True)
        add_boundary_action.triggered.connect(lambda: self.set_mode(Modes.ADD_BOUNDARY))
        mode_group.addAction(add_boundary_action)
        toolbar.addAction(add_boundary_action)
        self.mode_actions[Modes.ADD_BOUNDARY] = add_boundary_action
        
        # Delete mode
        delete_action = QAction("Delete", self)
        delete_action.setCheckable(True)
        delete_action.triggered.connect(lambda: self.set_mode(Modes.DELETE))
        mode_group.addAction(delete_action)
        toolbar.addAction(delete_action)
        self.mode_actions[Modes.DELETE] = delete_action
        
        toolbar.addSeparator()

        # Device quick-add actions
        devices_menu = QMenu("Quick Add Device", self)
        
        # Add actions for each device type
        for device_type in [DeviceTypes.ROUTER, DeviceTypes.SWITCH, DeviceTypes.SERVER, DeviceTypes.FIREWALL]:
            action = QAction(device_type.title(), self)
            action.triggered.connect(lambda checked, dt=device_type: self.add_device(device_type=dt))
            devices_menu.addAction(action)
        
        add_device_btn = toolbar.addAction("Quick Add")
        add_device_btn.setMenu(devices_menu)

        # Add this to the create_toolbar method
        test_action = QAction("Test Graphics", self)
        test_action.triggered.connect(self.canvas.test_temporary_graphics)
        toolbar.addAction(test_action)

        test_line = QAction("Test Connection Line", self)
        test_line.triggered.connect(self.test_connection_line)
        toolbar.addAction(test_line)

        # Add to create_toolbar method
        show_bounds = QAction("Show Device Bounds", self)
        show_bounds.triggered.connect(self.show_device_bounds)
        toolbar.addAction(show_bounds)

        test_devices = QAction("Create Test Devices", self)
        test_devices.triggered.connect(self.create_test_devices)
        toolbar.addAction(test_devices)

        connection_points = QAction("Toggle Connection Points", self)
        connection_points.triggered.connect(lambda: self.toggle_connection_points())
        toolbar.addAction(connection_points)

    def set_mode(self, mode):
        """Set the current interaction mode."""
        self.canvas.set_mode(mode)
        self.logger.info(f"Mode changed to: {mode}")
    
    def on_add_device_requested(self, pos):
        """Handle request to add a new device at the specified position."""
        try:
            # Show dialog to get device details
            dialog = DeviceDialog(self)
            if dialog.exec_() != QDialog.Accepted:
                return
            
            # Get the data from dialog
            device_data = dialog.get_device_data()
            
            # Generate name if empty
            if not device_data['name']:
                self.device_counter += 1
                device_data['name'] = f"Device{self.device_counter}"
            
            # Create the device
            device = Device(
                device_data['name'],
                device_data['type'],
                device_data['properties']
            )
            
            # Position the device
            device.setPos(pos)
            
            # Add to scene
            self.canvas.scene().addItem(device)
            self.canvas.devices.append(device)
            
            # Connect device signals if the handler exists
            if hasattr(self, 'on_device_selected'):
                device.signals.selected.connect(self.on_device_selected)
            
            self.logger.info(f"Added device: {device_data['name']}, type: {device_data['type']} at position {pos.x()}, {pos.y()}")
            
        except Exception as e:
            import traceback
            self.logger.error(f"Error adding device: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to add device: {str(e)}")

    def on_delete_device_requested(self, device):
        """Handle request to delete a specific device."""
        if device:
            self.logger.info(f"Deleting device '{device.name}' (ID: {device.id})")
            
            # Remove from scene
            self.canvas.scene().removeItem(device)
            
            # Remove from devices list
            if device in self.canvas.devices:
                self.canvas.devices.remove(device)
    
    def on_delete_item_requested(self, item):
        """Handle request to delete a non-device item."""
        if item:
            self.logger.info(f"Deleting item of type {type(item).__name__}")
            self.canvas.scene().removeItem(item)
    
    def on_add_boundary_requested(self, rect):
        """Handle request to add a boundary region."""
        self.logger.info(f"Adding boundary at {rect}")
        self.create_boundary(rect)
    
    def on_add_connection_requested(self, source_device, target_device):
        """Handle request to add a connection between two devices."""
        try:
            # Create a new connection
            from models.connection import Connection
            from constants import ConnectionTypes
            
            connection = Connection(source_device, target_device, ConnectionTypes.ETHERNET)
            
            # Add to scene
            self.canvas.scene().addItem(connection)
            self.canvas.connections.append(connection)
            
            # Connect signals if needed
            # connection.signals.selected.connect(...)
            
            self.logger.info(f"Added connection from {source_device.name} to {target_device.name}")
            
        except Exception as e:
            import traceback
            self.logger.error(f"Error adding connection: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to add connection: {str(e)}")

    def create_device(self, name, device_type, position, properties=None):
        """Create a device with the given parameters."""
        try:
            self.logger.info(f"Creating device '{name}' of type '{device_type}'")
            
            # If no name provided, generate one
            if not name:
                self.device_counter += 1
                name = f"Device {self.device_counter}"
            
            # Create device object
            device = Device(name, device_type)
            device.setPos(position)
            
            # Set custom properties if provided
            if properties:
                for key, value in properties.items():
                    device.update_property(key, value)
            
            # Connect signals
            device.signals.position_changed.connect(self._on_device_moved)
            device.signals.selection_changed.connect(self._on_device_selection_changed)
            
            # Add to scene
            scene = self.canvas.scene()
            if scene:
                scene.addItem(device)
                
                # Add to devices list
                self.canvas.devices.append(device)
                
                self.logger.info(f"Device '{name}' added at position ({position.x()}, {position.y()})")
                return device
            else:
                self.logger.error("No scene available to add device")
                self.show_error("Canvas scene not initialized")
        
        except Exception as e:
            self.logger.error(f"Error creating device: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Failed to create device: {str(e)}")
        
        return None

    def add_device(self, device_type=None):
        """Quick-add a device of the specified type at the center of the view."""
        try:
            # Generate device name
            self.device_counter += 1
            name = f"Device {self.device_counter}"
            
            # Default to router if no type specified
            if not device_type:
                device_type = DeviceTypes.ROUTER
            
            # Calculate center position
            view_center = self.canvas.viewport().rect().center()
            scene_pos = self.canvas.mapToScene(view_center)
            
            # Create the device
            device = self.create_device(name, device_type, scene_pos)
            return device
            
        except Exception as e:
            self.logger.error(f"Error adding device: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Failed to add device: {str(e)}")
            return None

    def _on_device_moved(self, device):
        """Handle device position changes."""
        if device:
            pos = device.pos()
            self.logger.debug(f"Device '{device.name}' moved to ({pos.x()}, {pos.y()})")
    
    def _on_device_selection_changed(self, device, selected):
        """Handle device selection changes."""
        if device:
            status = "selected" if selected else "deselected"
            self.logger.debug(f"Device '{device.name}' {status}")

    def show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self, "Error", message)

    def create_boundary(self, rect, name=None, color=None):
        """Create a boundary with the given parameters."""
        try:
            # Generate a name if not provided
            if not name:
                # Use counter for unique naming
                if not hasattr(self, 'boundary_counter'):
                    self.boundary_counter = 0
                self.boundary_counter += 1
                name = f"Zone {self.boundary_counter}"
            
            # Default color if none provided
            if not color:
                color = QColor(40, 120, 200, 80)
            
            # Create boundary object
            boundary = Boundary(rect, name, color)
            
            # Add to scene
            scene = self.canvas.scene()
            if scene:
                scene.addItem(boundary)
                
                # Store boundary if needed
                if not hasattr(self.canvas, "boundaries"):
                    self.canvas.boundaries = []
                self.canvas.boundaries.append(boundary)
                
                self.logger.info(f"Boundary '{name}' added at {rect}")
                return boundary
            else:
                self.logger.error("No scene available to add boundary")
        
        except Exception as e:
            self.logger.error(f"Error creating boundary: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Failed to create boundary: {str(e)}")
        
        return None

    def on_delete_boundary_requested(self, boundary):
        """Handle request to delete a specific boundary."""
        if boundary:
            self.logger.info(f"Deleting boundary '{boundary.name}'")
            
            # Use the boundary's delete method to ensure label is removed too
            boundary.delete()
            
            # Remove from scene
            self.canvas.scene().removeItem(boundary)
            
            # Remove from boundaries list
            if boundary in self.canvas.boundaries:
                self.canvas.boundaries.remove(boundary)

    def create_connection(self, source_device, target_device, connection_type=None, label=None):
        """Create a connection between two devices."""
        try:
            # Check if connection already exists
            existing = self._find_existing_connection(source_device, target_device)
            if existing:
                self.logger.info(f"Connection already exists between {source_device.name} and {target_device.name}")
                return existing
            
            # Create the connection
            connection = Connection(source_device, target_device, connection_type, label)
            
            # Add to scene
            self.canvas.scene().addItem(connection)
            
            # Store connection if needed
            if not hasattr(self.canvas, "connections"):
                self.canvas.connections = []
            self.canvas.connections.append(connection)
            
            self.logger.info(f"Connection created between {source_device.name} and {target_device.name}")
            return connection
        
        except Exception as e:
            self.logger.error(f"Error creating connection: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Failed to create connection: {str(e)}")
        
        return None

    def _find_existing_connection(self, device1, device2):
        """Check if a connection already exists between two devices."""
        if hasattr(self.canvas, "connections"):
            for conn in self.canvas.connections:
                if ((conn.source_device == device1 and conn.target_device == device2) or
                    (conn.source_device == device2 and conn.target_device == device1)):
                    return conn
        return None

    def on_delete_connection_requested(self, connection):
        """Handle request to delete a connection."""
        if connection:
            self.logger.info(f"Deleting connection between {connection.source_device.name} and {connection.target_device.name}")
            
            # Use the connection's delete method to clean up references
            connection.delete()
            
            # Remove from connections list
            if hasattr(self.canvas, "connections") and connection in self.canvas.connections:
                self.canvas.connections.remove(connection)

    def test_connection_line(self):
        """Test the temporary connection line display."""
        # Check if we have devices to work with
        if not self.canvas.devices:
            self.logger.warning("No devices available for testing connection line")
            return
        
        # Get scene and first device position
        scene = self.canvas.scene()
        start_pos = self.canvas.devices[0].pos()
        
        # Create a temporary line
        temp_line = QGraphicsLineItem(start_pos.x(), start_pos.y(), start_pos.x(), start_pos.y())
        
        # Style the line
        pen = QPen(QColor(0, 120, 215), 2, Qt.DashLine)
        pen.setDashPattern([5, 5])
        pen.setCapStyle(Qt.RoundCap)
        temp_line.setPen(pen)
        temp_line.setZValue(1000)
        
        # Add to scene
        scene.addItem(temp_line)
        
        self.logger.info(f"Created test line starting at {start_pos.x()}, {start_pos.y()}")
        
        # Set up animation
        self.animation_counter = 0
        self.animation_timer = QTimer()
        
        def animate_line():
            self.animation_counter += 1
            angle = self.animation_counter / 30.0 * math.pi
            
            # Move endpoint in a circle
            radius = 100
            end_x = start_pos.x() + radius * math.cos(angle)
            end_y = start_pos.y() + radius * math.sin(angle)
            
            # Update line
            temp_line.setLine(start_pos.x(), start_pos.y(), end_x, end_y)
            
            # Stop after completing a circle
            if self.animation_counter >= 60:  # ~360 degrees
                self.animation_timer.stop()
                scene.removeItem(temp_line)
                self.logger.info("Test line animation completed")
        
        # Start animation
        self.animation_timer.timeout.connect(animate_line)
        self.animation_timer.start(50)  # 50ms interval

    def create_test_devices(self):
        """Create test devices for debugging connection mode."""
        from models.device import Device
        from constants import DeviceTypes
        from PyQt5.QtCore import QPointF
        
        # Clear existing devices first
        for device in list(self.canvas.devices):
            self.canvas.scene().removeItem(device)
        self.canvas.devices.clear()
        
        # Create two test devices at known positions
        positions = [
            QPointF(-100, 0),   # Left
            QPointF(100, 0)     # Right
        ]
        
        device_types = [DeviceTypes.ROUTER, DeviceTypes.SWITCH]
        
        for i, (pos, dev_type) in enumerate(zip(positions, device_types)):
            device_name = f"TestDevice{i}"
            device = Device(device_name, dev_type)
            device.setPos(pos)
            
            # Make sure it's selectable
            device.setFlag(QGraphicsItem.ItemIsSelectable, True)
            device.setFlag(QGraphicsItem.ItemIsMovable, True)
            
            # Add to scene
            self.canvas.scene().addItem(device)
            self.canvas.devices.append(device)
            
            self.logger.info(f"Created test device: {device_name} at {pos.x()}, {pos.y()}")
        
        # Switch to connection mode
        from constants import Modes
        self.set_mode(Modes.ADD_CONNECTION)
        self.logger.info("Switched to connection mode")

    def show_device_bounds(self):
        """Show the bounding rectangles of all devices for debugging."""
        from PyQt5.QtWidgets import QGraphicsRectItem
        from PyQt5.QtGui import QPen, QColor, QBrush
        from PyQt5.QtCore import Qt
        
        # Remove any existing debug visualizations
        for item in self.canvas.scene().items():
            if hasattr(item, 'isDebugRect') and item.isDebugRect:
                self.canvas.scene().removeItem(item)
        
        # Create and show bounds for each device
        for i, device in enumerate(self.canvas.devices):
            # Get scene bounding rect
            rect = device.sceneBoundingRect()
            
            # Create a rect item to show the bounds
            debug_rect = QGraphicsRectItem(rect)
            debug_rect.setPen(QPen(QColor(255, 0, 0, 128), 1, Qt.DashLine))
            debug_rect.setBrush(QBrush(QColor(255, 0, 0, 30)))
            debug_rect.setZValue(900)  # Below temp connection but above other items
            debug_rect.isDebugRect = True  # Custom property to identify
            
            # Add to scene
            self.canvas.scene().addItem(debug_rect)
            
            self.logger.info(f"Device {i} bounds: ({rect.x()}, {rect.y()}, {rect.width()}x{rect.height()})")
        
        # Auto-remove after 5 seconds
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(5000, lambda: self.clear_debug_visuals())

    def clear_debug_visuals(self):
        """Clear all debug visualizations."""
        for item in self.canvas.scene().items():
            if hasattr(item, 'isDebugRect') and item.isDebugRect:
                self.canvas.scene().removeItem(item)

    def toggle_connection_points(self, visible=None):
        """Toggle visibility of connection points on all devices."""
        if visible is None:
            # Toggle current state
            if not hasattr(self, '_show_connection_points'):
                self._show_connection_points = False
            visible = not self._show_connection_points
            self._show_connection_points = visible
        
        # Apply to all devices
        for device in self.canvas.devices:
            device.setProperty('show_connection_points', visible)
        
        self.logger.info(f"Connection points {'shown' if visible else 'hidden'}")
        
        # Force redraw
        self.canvas.viewport().update()

    def on_device_selected(self, device, is_selected):
        """Handle device selection changes."""
        try:
            if is_selected:
                self.logger.debug(f"Device selected: {device.name}")
                # Update UI or show properties if needed
                # For example, you might want to show the device properties in a panel
            else:
                self.logger.debug(f"Device deselected: {device.name}")
                # Handle deselection if necessary
        except Exception as e:
            self.logger.error(f"Error handling device selection: {str(e)}")