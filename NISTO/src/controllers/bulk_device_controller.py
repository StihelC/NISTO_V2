import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QPushButton, QLabel, QSpinBox, QComboBox, QDialogButtonBox
from PyQt5.QtCore import QPointF, Qt

from models.device import Device
from constants import DeviceTypes
from controllers.commands import Command, CompositeCommand

class BulkAddDevicesCommand(Command):
    """Command for adding multiple devices at once."""
    
    def __init__(self, device_controller, devices):
        """Initialize the command.
        
        Args:
            device_controller: The device controller to use for operations
            devices: List of (name, type, position, properties) tuples for devices to add
        """
        super().__init__("Add Multiple Devices")
        self.device_controller = device_controller
        self.device_data = devices
        self.created_devices = []
        
    def execute(self):
        """Execute the command by creating all devices."""
        self.created_devices = []
        
        for name, device_type, position, properties in self.device_data:
            device = self.device_controller._create_device(name, device_type, position, properties)
            self.created_devices.append(device)
            
        return True
        
    def undo(self):
        """Undo the command by removing all created devices."""
        for device in self.created_devices:
            self.device_controller._delete_device(device)
            
        self.created_devices = []
        return True


class BulkDeviceController:
    """Controller for bulk device operations."""
    
    def __init__(self, canvas, device_controller, event_bus, undo_redo_manager=None):
        """Initialize the bulk device controller.
        
        Args:
            canvas: The canvas to operate on
            device_controller: The device controller for creating individual devices
            event_bus: Event bus for broadcasting events
            undo_redo_manager: Undo/redo manager for command pattern support
        """
        self.canvas = canvas
        self.device_controller = device_controller
        self.event_bus = event_bus
        self.undo_redo_manager = undo_redo_manager
        self.logger = logging.getLogger(__name__)
    
    def show_bulk_add_dialog(self, position=None):
        """Show a dialog to add multiple devices at once.
        
        Args:
            position: Optional starting position for the first device
        """
        dialog = BulkDeviceAddDialog(position)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get device data from the dialog
            device_data = dialog.get_device_data()
            if device_data:
                self._bulk_add_devices(device_data)
    
    def _bulk_add_devices(self, device_data):
        """Add multiple devices at once.
        
        Args:
            device_data: List of (name, type, position, properties) tuples
        """
        self.logger.info(f"Adding {len(device_data)} devices in bulk")
        
        # Use command pattern if undo/redo manager is available
        if self.undo_redo_manager:
            cmd = BulkAddDevicesCommand(self.device_controller, device_data)
            self.undo_redo_manager.push_command(cmd)
        else:
            # Add devices directly without undo support
            for name, device_type, position, properties in device_data:
                self.device_controller._create_device(name, device_type, position, properties)
        
        # Notify that multiple devices were added
        if self.event_bus:
            self.event_bus.emit("bulk_devices_added", len(device_data))


class BulkDeviceAddDialog(QDialog):
    """Dialog for adding multiple devices in bulk."""
    
    def __init__(self, position=None, parent=None):
        """Initialize the dialog.
        
        Args:
            position: Optional starting position for the first device
            parent: Parent widget
        """
        super().__init__(parent)
        self.position = position or QPointF(0, 0)
        self.setWindowTitle("Add Multiple Devices")
        self.setMinimumWidth(450)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # General controls
        layout.addWidget(QLabel("<b>Create multiple devices at once</b>"))
        
        # Grid layout for device types
        grid_layout = QGridLayout()
        
        # Add entries for each device type
        self.device_counts = {}
        row = 0
        
        for device_type in DeviceTypes:
            if device_type == DeviceTypes.GENERIC:
                continue  # Skip generic type
                
            # Label with device type
            label = QLabel(device_type.title())
            grid_layout.addWidget(label, row, 0)
            
            # Spin box for count
            count_spin = QSpinBox()
            count_spin.setRange(0, 100)
            count_spin.setValue(0)
            grid_layout.addWidget(count_spin, row, 1)
            
            # Store reference to spin box
            self.device_counts[device_type] = count_spin
            
            row += 1
        
        layout.addLayout(grid_layout)
        
        # Layout options
        layout.addWidget(QLabel("<b>Layout Options</b>"))
        
        self.layout_type = QComboBox()
        self.layout_type.addItems(["Grid", "Horizontal Line", "Vertical Line", "Circle"])
        layout.addWidget(self.layout_type)
        
        # Spacing controls
        spacing_layout = QGridLayout()
        spacing_layout.addWidget(QLabel("Horizontal Spacing:"), 0, 0)
        
        self.h_spacing = QSpinBox()
        self.h_spacing.setRange(10, 500)
        self.h_spacing.setValue(100)
        spacing_layout.addWidget(self.h_spacing, 0, 1)
        
        spacing_layout.addWidget(QLabel("Vertical Spacing:"), 1, 0)
        
        self.v_spacing = QSpinBox()
        self.v_spacing.setRange(10, 500)
        self.v_spacing.setValue(100)
        spacing_layout.addWidget(self.v_spacing, 1, 1)
        
        layout.addLayout(spacing_layout)
        
        # Device naming
        layout.addWidget(QLabel("<b>Device Naming</b>"))
        
        self.naming_prefix = QComboBox()
        self.naming_prefix.addItems(["Type", "Custom Prefix"])
        self.naming_prefix.setEditable(True)
        layout.addWidget(self.naming_prefix)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_device_data(self):
        """Get the device data from the dialog inputs.
        
        Returns:
            List of (name, type, position, properties) tuples
        """
        device_data = []
        total_devices = 0
        
        # Count total devices to create
        for device_type, spin_box in self.device_counts.items():
            total_devices += spin_box.value()
        
        # If no devices selected, return empty list
        if total_devices == 0:
            return []
        
        # Calculate positions based on layout
        layout_type = self.layout_type.currentText()
        h_spacing = self.h_spacing.value()
        v_spacing = self.v_spacing.value()
        
        # Choose naming scheme
        naming_prefix = self.naming_prefix.currentText()
        
        device_index = 1
        
        # Create device data for each type
        for device_type, spin_box in self.device_counts.items():
            count = spin_box.value()
            if count == 0:
                continue
                
            for i in range(count):
                # Calculate position
                if layout_type == "Grid":
                    row = (device_index - 1) // 5
                    col = (device_index - 1) % 5
                    pos = QPointF(
                        self.position.x() + col * h_spacing,
                        self.position.y() + row * v_spacing
                    )
                elif layout_type == "Horizontal Line":
                    pos = QPointF(
                        self.position.x() + (device_index - 1) * h_spacing,
                        self.position.y()
                    )
                elif layout_type == "Vertical Line":
                    pos = QPointF(
                        self.position.x(),
                        self.position.y() + (device_index - 1) * v_spacing
                    )
                elif layout_type == "Circle":
                    import math
                    radius = max(h_spacing, v_spacing) * 1.5
                    angle = (2 * math.pi / total_devices) * (device_index - 1)
                    pos = QPointF(
                        self.position.x() + radius * math.cos(angle),
                        self.position.y() + radius * math.sin(angle)
                    )
                
                # Generate name
                if naming_prefix == "Type":
                    name = f"{device_type.title()}{device_index}"
                else:
                    name = f"{naming_prefix}{device_index}"
                
                # Add device data
                device_data.append((name, device_type, pos, None))
                device_index += 1
        
        return device_data
