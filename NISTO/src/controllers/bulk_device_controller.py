import logging
import math
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QLabel, 
    QSpinBox, QComboBox, QDialogButtonBox, QGroupBox, QCheckBox,
    QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
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
        # Set window title with coordinates info
        dialog.setWindowTitle(f"Add Multiple Devices at ({int(position.x())}, {int(position.y())})")
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get device data from the dialog
            device_data = dialog.get_device_data()
            if device_data:
                device_count = len(device_data)
                self.logger.info(f"Creating {device_count} devices from bulk add dialog")
                self._bulk_add_devices(device_data)
                
                # Show success message
                if self.event_bus:
                    self.event_bus.emit("status_message", f"Added {device_count} devices successfully")
            else:
                self.logger.warning("No devices were selected in bulk add dialog")
    
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
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)  # Increased height for more options
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # General controls
        layout.addWidget(QLabel("<b>Create multiple devices at once</b>"))
        
        # Device selection section
        device_group = QGroupBox("Device Selection")
        device_layout = QVBoxLayout(device_group)
        
        # Grid layout for device types
        grid_layout = QGridLayout()
        
        # Add entries for each device type
        self.device_counts = {}
        row = 0
        
        # Get device types from DeviceTypes class attributes
        device_types = [attr for attr in dir(DeviceTypes) 
                       if not attr.startswith('__') and isinstance(getattr(DeviceTypes, attr), str)]
        
        for device_type in device_types:
            if device_type == "GENERIC":
                continue  # Skip generic type
            
            # Get the actual string value from the DeviceTypes class
            type_value = getattr(DeviceTypes, device_type)
                
            # Label with device type
            label = QLabel(device_type.title())
            grid_layout.addWidget(label, row, 0)
            
            # Spin box for count
            count_spin = QSpinBox()
            count_spin.setRange(0, 100)
            count_spin.setValue(0)
            grid_layout.addWidget(count_spin, row, 1)
            
            # Store reference to spin box with the type value
            self.device_counts[type_value] = count_spin
            
            row += 1
        
        device_layout.addLayout(grid_layout)
        layout.addWidget(device_group)
        
        # Layout options in a group box
        layout_group = QGroupBox("Layout Options")
        layout_options = QVBoxLayout(layout_group)
        
        layout_label = QLabel("Select a network layout pattern:")
        layout_options.addWidget(layout_label)
        
        self.layout_type = QComboBox()
        self.layout_type.addItems([
            "Grid", 
            "Horizontal Line", 
            "Vertical Line", 
            "Circle", 
            "Star", 
            "Bus",
            "DMZ (Perimeter Defense)",
            "Defense-in-Depth Layers",
            "Segmented Network",
            "Zero Trust Microsegmentation",
            "SCADA/ICS Architecture"
        ])
        self.layout_type.currentIndexChanged.connect(self._update_layout_description)
        layout_options.addWidget(self.layout_type)
        
        # Add a description label for the selected layout
        self.layout_description = QLabel("Arrange devices in a grid pattern")
        self.layout_description.setWordWrap(True)
        self.layout_description.setStyleSheet("color: #555; font-style: italic;")
        layout_options.addWidget(self.layout_description)
        
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
        
        layout_options.addLayout(spacing_layout)
        layout.addWidget(layout_group)
        
        # Enhanced device naming options
        naming_group = QGroupBox("Device Naming")
        naming_layout = QVBoxLayout(naming_group)
        
        # Naming scheme selection
        scheme_layout = QHBoxLayout()
        scheme_layout.addWidget(QLabel("Naming Scheme:"))
        
        self.naming_scheme = QComboBox()
        self.naming_scheme.addItems(["Type-Number", "Prefix-Number", "Custom Pattern"])
        self.naming_scheme.currentIndexChanged.connect(self._update_naming_options)
        scheme_layout.addWidget(self.naming_scheme)
        
        naming_layout.addLayout(scheme_layout)
        
        # Custom prefix input for Prefix-Number scheme
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Custom Prefix:"))
        
        self.custom_prefix = QLineEdit("Device")
        prefix_layout.addWidget(self.custom_prefix)
        
        naming_layout.addLayout(prefix_layout)
        
        # Custom pattern with help text
        pattern_layout = QVBoxLayout()
        pattern_help = QLabel("Pattern variables: {type}, {index}, {count}")
        pattern_help.setStyleSheet("color: gray; font-style: italic;")
        pattern_layout.addWidget(pattern_help)
        
        self.naming_pattern = QLineEdit("{type}{index}")
        pattern_layout.addWidget(self.naming_pattern)
        
        naming_layout.addLayout(pattern_layout)
        
        # Starting index option
        start_index_layout = QHBoxLayout()
        start_index_layout.addWidget(QLabel("Start Numbering From:"))
        
        self.start_index = QSpinBox()
        self.start_index.setRange(0, 1000)
        self.start_index.setValue(1)  # Default starting from 1
        start_index_layout.addWidget(self.start_index)
        
        naming_layout.addLayout(start_index_layout)
        
        # Add a preview of device names based on current settings
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("<b>Name Preview:</b>"))
        
        self.name_preview = QLabel("Router1, Router2, ...")
        self.name_preview.setStyleSheet("font-style: italic; color: #666;")
        preview_layout.addWidget(self.name_preview)
        
        naming_layout.addLayout(preview_layout)
        
        # Add a button to update the preview
        update_preview = QPushButton("Update Preview")
        update_preview.clicked.connect(self._update_name_preview)
        naming_layout.addWidget(update_preview)
        
        layout.addWidget(naming_group)
        
        # Default properties section
        props_group = QGroupBox("Default Properties")
        props_layout = QVBoxLayout(props_group)
        
        # Property table
        self.props_table = QTableWidget(0, 2)
        self.props_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.props_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.props_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        props_layout.addWidget(self.props_table)
        
        # Add common properties button
        add_prop_button = QPushButton("Add Property")
        add_prop_button.clicked.connect(self._add_property_row)
        props_layout.addWidget(add_prop_button)
        
        layout.addWidget(props_group)
        
        # Initialize with some common properties
        self._add_common_properties()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initial update of naming options
        self._update_naming_options(0)
        self._update_name_preview()
    
    def _update_naming_options(self, index):
        """Update visibility of naming options based on selected scheme."""
        scheme = self.naming_scheme.currentText()
        
        # Show/hide relevant widgets based on naming scheme
        if scheme == "Type-Number":
            self.custom_prefix.setVisible(False)
            self.naming_pattern.setVisible(False)
            pattern_visible = False
        elif scheme == "Prefix-Number":
            self.custom_prefix.setVisible(True)
            self.naming_pattern.setVisible(False)
            pattern_visible = False
        else:  # Custom Pattern
            self.custom_prefix.setVisible(False)
            self.naming_pattern.setVisible(True)
            pattern_visible = True
        
        # Find and update visibility of the pattern help label
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QLabel):
                if "Pattern variables" in item.widget().text():
                    item.widget().setVisible(pattern_visible)
    
    def _update_layout_description(self):
        """Update the description text based on selected layout."""
        layout_type = self.layout_type.currentText()
        
        descriptions = {
            "Grid": "Arrange devices in a grid pattern (rows and columns)",
            "Horizontal Line": "Place devices in a single horizontal line",
            "Vertical Line": "Place devices in a single vertical line",
            "Circle": "Arrange devices in a circular pattern",
            "Star": "Place one device in the center with others around it (hub and spoke)",
            "Bus": "Arrange devices along a horizontal bus line (linear network)",
            "DMZ (Perimeter Defense)": "Create a DMZ architecture with internal, DMZ, and external zones",
            "Defense-in-Depth Layers": "Arrange devices in tiered security layers (onion model)",
            "Segmented Network": "Create a segmented network with separate security domains",
            "Zero Trust Microsegmentation": "Implement a zero trust architecture with microsegments",
            "SCADA/ICS Architecture": "Industrial control system layout with zones and conduits"
        }
        
        self.layout_description.setText(descriptions.get(layout_type, "Select a layout pattern"))
    
    def _update_name_preview(self):
        """Update the name preview based on current settings."""
        # Find out which device type has a non-zero count
        preview_device_type = None
        preview_count = 0
        
        for device_type, spin_box in self.device_counts.items():
            if spin_box.value() > 0:
                preview_device_type = device_type
                preview_count = spin_box.value()
                break
        
        if not preview_device_type:
            self.name_preview.setText("No devices selected")
            return
        
        # Generate preview names
        scheme = self.naming_scheme.currentText()
        start_idx = self.start_index.value()
        type_name = preview_device_type.split('.')[-1].title() if '.' in preview_device_type else preview_device_type.title()
        
        preview_names = []
        count = min(3, preview_count)  # Show at most 3 examples
        
        for i in range(count):
            idx = start_idx + i
            
            if scheme == "Type-Number":
                name = f"{type_name}{idx}"
            elif scheme == "Prefix-Number":
                prefix = self.custom_prefix.text()
                name = f"{prefix}{idx}"
            else:  # Custom Pattern
                pattern = self.naming_pattern.text()
                name = pattern.replace("{type}", type_name)
                name = name.replace("{index}", str(idx))
                name = name.replace("{count}", str(preview_count))
            
            preview_names.append(name)
        
        # Add ellipsis if there are more devices
        if preview_count > count:
            preview_names.append("...")
        
        self.name_preview.setText(", ".join(preview_names))
    
    def _add_property_row(self):
        """Add a new property row to the property table."""
        row = self.props_table.rowCount()
        self.props_table.insertRow(row)
        
        # Property name cell
        prop_name = QTableWidgetItem("")
        prop_name.setFlags(prop_name.flags() | Qt.ItemIsEditable)
        self.props_table.setItem(row, 0, prop_name)
        
        # Property value cell
        prop_value = QTableWidgetItem("")
        prop_value.setFlags(prop_value.flags() | Qt.ItemIsEditable)
        self.props_table.setItem(row, 1, prop_value)
    
    def _add_common_properties(self):
        """Add some common properties to the property table."""
        common_props = [
            ("location", "Main Office"),
            ("priority", "Medium"),
            ("status", "Active")
        ]
        
        for prop_name, prop_value in common_props:
            row = self.props_table.rowCount()
            self.props_table.insertRow(row)
            
            name_item = QTableWidgetItem(prop_name)
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.props_table.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(prop_value)
            value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)
            self.props_table.setItem(row, 1, value_item)
    
    def get_properties(self):
        """Get the properties defined in the properties table."""
        props = {}
        for row in range(self.props_table.rowCount()):
            name_item = self.props_table.item(row, 0)
            value_item = self.props_table.item(row, 1)
            
            if name_item and value_item:
                name = name_item.text().strip()
                value = value_item.text().strip()
                
                if name:  # Only add if property name is not empty
                    props[name] = value
        
        return props
    
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
        
        # Get default properties for all created devices
        default_props = self.get_properties()
        
        # Calculate positions based on layout
        layout_type = self.layout_type.currentText()
        h_spacing = self.h_spacing.value()
        v_spacing = self.v_spacing.value()
        
        # Get naming scheme settings
        naming_scheme = self.naming_scheme.currentText()
        custom_prefix = self.custom_prefix.text()
        naming_pattern = self.naming_pattern.text()
        start_idx = self.start_index.value()
        
        device_index = start_idx
        
        # Create device data for each type
        for device_type, spin_box in self.device_counts.items():
            count = spin_box.value()
            if count == 0:
                continue
            
            # Readable type name for naming
            type_name = device_type.split('.')[-1].title() if '.' in device_type else device_type.title()
            
            for i in range(count):
                # Calculate position
                if layout_type == "Grid":
                    row = (device_index - start_idx) // 5
                    col = (device_index - start_idx) % 5
                    pos = QPointF(
                        self.position.x() + col * h_spacing,
                        self.position.y() + row * v_spacing
                    )
                elif layout_type == "Horizontal Line":
                    pos = QPointF(
                        self.position.x() + (device_index - start_idx) * h_spacing,
                        self.position.y()
                    )
                elif layout_type == "Vertical Line":
                    pos = QPointF(
                        self.position.x(),
                        self.position.y() + (device_index - start_idx) * v_spacing
                    )
                elif layout_type == "Circle":
                    radius = max(h_spacing, v_spacing) * 1.5
                    angle = (2 * math.pi / total_devices) * (device_index - start_idx)
                    pos = QPointF(
                        self.position.x() + radius * math.cos(angle),
                        self.position.y() + radius * math.sin(angle)
                    )
                elif layout_type == "Star":
                    # Star layout - one device in the center, others around in a circle
                    if i == 0:  # First device is at the center
                        pos = QPointF(self.position.x(), self.position.y())
                    else:
                        # Other devices are in a circle around the center
                        # Use a smaller count for angle calculation (excluding the central node)
                        star_count = total_devices - 1
                        star_idx = (device_index - start_idx) - 1  # Adjust index for star pattern
                        radius = max(h_spacing, v_spacing) * 1.2
                        angle = (2 * math.pi / star_count) * star_idx
                        pos = QPointF(
                            self.position.x() + radius * math.cos(angle),
                            self.position.y() + radius * math.sin(angle)
                        )
                elif layout_type == "Bus":
                    # Bus layout - devices arranged in a line with equal vertical spacing
                    # First device position
                    if i == 0:
                        pos = QPointF(
                            self.position.x() - (h_spacing * (count - 1) / 2),
                            self.position.y()
                        )
                    else:
                        # Subsequent devices are placed horizontally with equal spacing
                        pos = QPointF(
                            self.position.x() - (h_spacing * (count - 1) / 2) + (i * h_spacing),
                            self.position.y()
                        )
                elif layout_type == "DMZ (Perimeter Defense)":
                    # DMZ architecture with three zones: internal, DMZ, and external
                    zone_count = 3  # Fixed zones
                    zone_devices = total_devices // zone_count
                    
                    # Determine which zone this device belongs to
                    current_index = device_index - start_idx
                    zone = 0
                    if current_index < zone_devices:
                        zone = 0  # Internal zone
                    elif current_index < 2 * zone_devices:
                        zone = 1  # DMZ
                    else:
                        zone = 2  # External zone
                        
                    # Position within zone
                    zone_position = current_index % zone_devices
                    
                    # Calculate vertical position (columns within zones)
                    col = zone_position % 3
                    row = zone_position // 3
                    
                    pos = QPointF(
                        self.position.x() + (zone * 3 * h_spacing) + (col * h_spacing),
                        self.position.y() + row * v_spacing
                    )
                
                elif layout_type == "Defense-in-Depth Layers":
                    # Concentric security layers (3-5 layers)
                    max_layers = 4
                    devices_per_layer = total_devices // max_layers
                    
                    # Determine which layer this device belongs to
                    current_index = device_index - start_idx
                    layer = current_index // devices_per_layer
                    if layer >= max_layers:
                        layer = max_layers - 1
                        
                    # Position within layer
                    layer_position = current_index % devices_per_layer
                    devices_in_current_layer = min(devices_per_layer, total_devices - layer * devices_per_layer)
                    
                    # Calculate angle for this device in the layer
                    angle = (2 * math.pi / devices_in_current_layer) * layer_position
                    
                    # Radius increases with layer
                    radius = (layer + 1) * max(h_spacing, v_spacing)
                    
                    pos = QPointF(
                        self.position.x() + radius * math.cos(angle),
                        self.position.y() + radius * math.sin(angle)
                    )
                
                elif layout_type == "Segmented Network":
                    # Create 3-4 network segments with devices in each
                    segments = 4
                    devices_per_segment = max(1, total_devices // segments)
                    
                    # Determine which segment this device belongs to
                    current_index = device_index - start_idx
                    segment = current_index // devices_per_segment
                    if segment >= segments:
                        segment = segments - 1
                        
                    # Position within segment
                    segment_position = current_index % devices_per_segment
                    
                    # Layout as a grid within each segment
                    segment_cols = 2
                    col = segment_position % segment_cols
                    row = segment_position // segment_cols
                    
                    pos = QPointF(
                        self.position.x() - (h_spacing * 2) + (segment * 3 * h_spacing) + (col * h_spacing),
                        self.position.y() - (v_spacing * 2) + (row * v_spacing)
                    )
                
                elif layout_type == "Zero Trust Microsegmentation":
                    # Create microsegments (small clusters) with devices
                    segments = 5
                    devices_per_segment = max(1, total_devices // segments)
                    
                    # Determine which microsegment this device belongs to
                    current_index = device_index - start_idx
                    segment = current_index // devices_per_segment
                    if segment >= segments:
                        segment = segments - 1
                        
                    # Position within microsegment as small clusters
                    segment_position = current_index % devices_per_segment
                    
                    # Calculate angle for this device in a small circle
                    angle = (2 * math.pi / devices_per_segment) * segment_position
                    
                    # Position the microsegment clusters in a larger circle
                    segment_angle = (2 * math.pi / segments) * segment
                    segment_radius = max(h_spacing, v_spacing) * 3
                    
                    # Center position for this microsegment
                    segment_x = self.position.x() + segment_radius * math.cos(segment_angle)
                    segment_y = self.position.y() + segment_radius * math.sin(segment_angle)
                    
                    # Position within microsegment (small circle)
                    inner_radius = h_spacing * 0.8
                    pos = QPointF(
                        segment_x + inner_radius * math.cos(angle),
                        segment_y + inner_radius * math.sin(angle)
                    )
                
                elif layout_type == "SCADA/ICS Architecture":
                    # ICS layout with control zones (enterprise, DMZ, control, field)
                    zones = 4  # Fixed zones: Enterprise, DMZ, Control, Field
                    devices_per_zone = max(1, total_devices // zones)
                    
                    # Determine which zone this device belongs to
                    current_index = device_index - start_idx
                    zone = current_index // devices_per_zone
                    if zone >= zones:
                        zone = zones - 1
                        
                    # Position within zone
                    zone_position = current_index % devices_per_zone
                    zone_cols = 2
                    
                    col = zone_position % zone_cols
                    row = zone_position // zone_cols
                    
                    # Different zones are placed vertically (top: enterprise, bottom: field)
                    pos = QPointF(
                        self.position.x() - h_spacing + (col * h_spacing),
                        self.position.y() - v_spacing * 3 + (zone * 2.5 * v_spacing) + (row * v_spacing)
                    )
                
                # Generate name based on scheme
                if naming_scheme == "Type-Number":
                    name = f"{type_name}{device_index}"
                elif naming_scheme == "Prefix-Number":
                    name = f"{custom_prefix}{device_index}"
                else:  # Custom Pattern
                    name = naming_pattern
                    name = name.replace("{type}", type_name)
                    name = name.replace("{index}", str(device_index))
                    name = name.replace("{count}", str(total_devices))
                
                # Add device data with properties
                device_data.append((name, device_type, pos, default_props.copy()))
                device_index += 1
        
        return device_data
