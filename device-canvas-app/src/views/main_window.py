from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction, QFileDialog, QMessageBox, QMenu, QActionGroup
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QColor
import logging
from .canvas import Canvas
from models.device import Device
from .device_dialog import DeviceDialog
from models.boundary import Boundary

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
        """Connect canvas signals to handlers."""
        self.canvas.add_device_requested.connect(self.on_add_device_requested)
        self.canvas.delete_device_requested.connect(self.on_delete_device_requested)
        self.canvas.delete_item_requested.connect(self.on_delete_item_requested)
        self.canvas.add_boundary_requested.connect(self.on_add_boundary_requested)
        self.canvas.add_connection_requested.connect(self.on_add_connection_requested)
        
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
        select_action.triggered.connect(lambda: self.set_mode(Canvas.MODE_SELECT))
        mode_group.addAction(select_action)
        toolbar.addAction(select_action)
        self.mode_actions[Canvas.MODE_SELECT] = select_action
        
        # Add device mode
        add_device_action = QAction("Add Device", self)
        add_device_action.setCheckable(True)
        add_device_action.triggered.connect(lambda: self.set_mode(Canvas.MODE_ADD_DEVICE))
        mode_group.addAction(add_device_action)
        toolbar.addAction(add_device_action)
        self.mode_actions[Canvas.MODE_ADD_DEVICE] = add_device_action
        
        # Add connection mode
        add_connection_action = QAction("Add Connection", self)
        add_connection_action.setCheckable(True)
        add_connection_action.triggered.connect(lambda: self.set_mode(Canvas.MODE_ADD_CONNECTION))
        mode_group.addAction(add_connection_action)
        toolbar.addAction(add_connection_action)
        self.mode_actions[Canvas.MODE_ADD_CONNECTION] = add_connection_action
        
        # Add boundary mode
        add_boundary_action = QAction("Add Boundary", self)
        add_boundary_action.setCheckable(True)
        add_boundary_action.triggered.connect(lambda: self.set_mode(Canvas.MODE_ADD_BOUNDARY))
        mode_group.addAction(add_boundary_action)
        toolbar.addAction(add_boundary_action)
        self.mode_actions[Canvas.MODE_ADD_BOUNDARY] = add_boundary_action
        
        # Delete mode
        delete_action = QAction("Delete", self)
        delete_action.setCheckable(True)
        delete_action.triggered.connect(lambda: self.set_mode(Canvas.MODE_DELETE))
        mode_group.addAction(delete_action)
        toolbar.addAction(delete_action)
        self.mode_actions[Canvas.MODE_DELETE] = delete_action
        
        toolbar.addSeparator()

        # Device quick-add actions
        devices_menu = QMenu("Quick Add Device", self)
        
        # Add actions for each device type
        for device_type in [Device.ROUTER, Device.SWITCH, Device.SERVER, Device.FIREWALL]:
            action = QAction(device_type.title(), self)
            action.triggered.connect(lambda checked, dt=device_type: self.add_device(device_type=dt))
            devices_menu.addAction(action)
        
        add_device_btn = toolbar.addAction("Quick Add")
        add_device_btn.setMenu(devices_menu)

    def set_mode(self, mode):
        """Set the current interaction mode."""
        self.canvas.set_mode(mode)
        self.logger.info(f"Mode changed to: {mode}")
    
    def on_add_device_requested(self, position):
        """Handle request to add a device at a specific position."""
        # Show device dialog
        dialog = DeviceDialog(self)
        if dialog.exec_():
            # Get device data from dialog
            data = dialog.get_device_data()
            if data:
                # Create the device with the provided data
                device = self.create_device(
                    name=data['name'], 
                    device_type=data['device_type'],
                    position=position,
                    properties=data['properties']
                )
                
                # Stay in add device mode to allow adding more devices
                # Or switch to select mode if preferred:
                # self.set_mode(Canvas.MODE_SELECT)

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
        """Handle request to add a connection between devices."""
        if source_device and target_device:
            self.logger.info(f"Adding connection from {source_device.name} to {target_device.name}")
            # Implement connection creation here
            # For example: self.create_connection(source_device, target_device)

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
                device_type = Device.ROUTER
            
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