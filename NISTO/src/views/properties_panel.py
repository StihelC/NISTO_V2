from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QPushButton, QScrollArea, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class PropertiesPanel(QWidget):
    """A panel for displaying and editing properties of selected items."""
    
    # Signals for property changes
    name_changed = pyqtSignal(str)
    z_value_changed = pyqtSignal(float)
    device_property_changed = pyqtSignal(str, object)
    connection_property_changed = pyqtSignal(str, object)
    boundary_property_changed = pyqtSignal(str, object)
    change_icon_requested = pyqtSignal(object)  # New signal for icon change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.current_item = None
        self.boundary_devices = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI elements."""
        main_layout = QVBoxLayout(self)
        
        # Scrollable area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # Title for the panel
        title = QLabel("Properties")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.content_layout.addWidget(title)
        
        # Create sections
        self.general_group = self._create_general_section()
        self.device_group = self._create_device_section()
        self.connection_group = self._create_connection_section()
        self.boundary_group = self._create_boundary_section()
        
        # Add sections to layout
        self.content_layout.addWidget(self.general_group)
        self.content_layout.addWidget(self.device_group)
        self.content_layout.addWidget(self.connection_group)
        self.content_layout.addWidget(self.boundary_group)
        self.content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_general_section(self):
        """Create the general properties section."""
        group = QGroupBox("General")
        layout = QFormLayout(group)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(
            lambda: self.name_changed.emit(self.name_edit.text())
        )
        layout.addRow("Name:", self.name_edit)
        
        # Z-Index (layer) control
        self.z_index_spin = QSpinBox()
        self.z_index_spin.setRange(-100, 100)
        self.z_index_spin.valueChanged.connect(
            lambda value: self.z_value_changed.emit(float(value))
        )
        layout.addRow("Layer (Z-Index):", self.z_index_spin)
        
        # Remove color picker section
        
        return group
    
    def _create_device_section(self):
        """Create the device-specific properties section."""
        group = QGroupBox("Device Properties")
        layout = QFormLayout(group)
        
        # Device type 
        self.device_type_label = QLabel()
        layout.addRow("Type:", self.device_type_label)
        
        # Add button to change device icon
        self.change_icon_button = QPushButton("Change Icon")
        self.change_icon_button.clicked.connect(self._on_change_icon_clicked)
        layout.addRow("Icon:", self.change_icon_button)
        
        # Custom properties table
        self.device_props_table = QTableWidget(0, 2)
        self.device_props_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.device_props_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.device_props_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.device_props_table.setMinimumHeight(100)
        layout.addRow(self.device_props_table)
        
        # Connect to slot that handles property changes
        self.device_props_table.cellChanged.connect(self._on_device_property_changed)
        
        return group
    
    def _create_connection_section(self):
        """Create the connection-specific properties section."""
        group = QGroupBox("Connection Properties")
        layout = QFormLayout(group)
        
        # Connection type
        self.connection_type_combo = QComboBox()
        layout.addRow("Type:", self.connection_type_combo)
        
        # Source device
        self.connection_source_label = QLabel()
        layout.addRow("Source:", self.connection_source_label)
        
        # Target device
        self.connection_target_label = QLabel()
        layout.addRow("Target:", self.connection_target_label)
        
        # Line style selection
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["Straight", "Orthogonal", "Curved"])
        self.line_style_combo.currentTextChanged.connect(
            lambda text: self.connection_property_changed.emit("line_style", text)
        )
        layout.addRow("Line Style:", self.line_style_combo)
        
        # Connection properties
        self.connection_props_table = QTableWidget(0, 2)
        self.connection_props_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.connection_props_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.connection_props_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.connection_props_table.setMinimumHeight(100)
        layout.addRow(self.connection_props_table)
        
        # Connect to slot that handles property changes
        self.connection_props_table.cellChanged.connect(self._on_connection_property_changed)
        
        return group
    
    def _create_boundary_section(self):
        """Create the boundary-specific properties section."""
        group = QGroupBox("Boundary Information")
        layout = QFormLayout(group)
        
        # Show contained devices
        self.boundary_devices_table = QTableWidget(0, 1)
        self.boundary_devices_table.setHorizontalHeaderLabels(["Contained Devices"])
        self.boundary_devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.boundary_devices_table.setMinimumHeight(100)
        layout.addRow(self.boundary_devices_table)
        
        return group
    
    def display_item_properties(self, item):
        """Update the panel with the selected item's properties."""
        # Clear previous item data
        self.current_item = item
        
        # Hide all sections initially
        self.general_group.hide()
        self.device_group.hide()
        self.connection_group.hide()
        self.boundary_group.hide()
        
        if not item:
            return
        
        # Show general section for all items
        self.general_group.show()
        
        # Update the general properties
        if hasattr(item, 'name'):
            self.name_edit.setText(item.name)
        
        # Set z-index value
        self.z_index_spin.setValue(int(item.zValue()))
        
        # Remove color preview update
        
        # Show specific section based on item type
        from models.device import Device
        from models.connection import Connection
        from models.boundary import Boundary
        
        if isinstance(item, Device):
            self._display_device_properties(item)
        elif isinstance(item, Connection):
            self._display_connection_properties(item)
        elif isinstance(item, Boundary):
            self._display_boundary_properties(item)
    
    def _display_device_properties(self, device):
        """Display device-specific properties."""
        self.device_group.show()
        
        # Show device type
        self.device_type_label.setText(device.device_type)
        
        # Disconnect signal to prevent firing while updating
        self.device_props_table.cellChanged.disconnect(self._on_device_property_changed)
        
        # Clear and repopulate properties table
        self.device_props_table.setRowCount(0)
        
        if hasattr(device, 'properties'):
            row = 0
            for key, value in device.properties.items():
                self.device_props_table.insertRow(row)
                
                # Skip color as it's handled in general section
                if key == 'color':
                    continue
                    
                # Add property name
                key_item = QTableWidgetItem(key)
                key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Make property name read-only
                self.device_props_table.setItem(row, 0, key_item)
                
                # Add property value (convert to string if needed)
                value_str = str(value) if not isinstance(value, str) else value
                self.device_props_table.setItem(row, 1, QTableWidgetItem(value_str))
                
                row += 1
        
        # Reconnect signal
        self.device_props_table.cellChanged.connect(self._on_device_property_changed)
    
    def _display_connection_properties(self, connection):
        """Display connection-specific properties."""
        self.connection_group.show()
        
        # Show source and target
        if hasattr(connection, 'source_device'):
            self.connection_source_label.setText(connection.source_device.name)
        
        if hasattr(connection, 'target_device'):
            self.connection_target_label.setText(connection.target_device.name)
        
        # Set connection type
        if hasattr(connection, 'connection_type'):
            self.connection_type_combo.blockSignals(True)
            self.connection_type_combo.clear()
            
            # Import ConnectionTypes constants
            from constants import ConnectionTypes
            
            # Use the DISPLAY_NAMES dictionary to populate connection types
            for conn_type, display_name in ConnectionTypes.DISPLAY_NAMES.items():
                self.connection_type_combo.addItem(display_name, conn_type)
            
            # Find and select the current connection type
            current_type = connection.connection_type
            index = self.connection_type_combo.findData(current_type)
            if index >= 0:
                self.connection_type_combo.setCurrentIndex(index)
            self.connection_type_combo.blockSignals(False)
        
        # Set line style
        if hasattr(connection, 'routing_style'):
            self.line_style_combo.blockSignals(True)
            
            # Map integer constants to UI strings
            style_map = {
                0: "Straight",   # STYLE_STRAIGHT
                1: "Orthogonal", # STYLE_ORTHOGONAL
                2: "Curved"      # STYLE_CURVED
            }
            
            # Get the style name for the current style
            style_name = style_map.get(connection.routing_style, "Straight")
            self.line_style_combo.setCurrentText(style_name)
            self.line_style_combo.blockSignals(False)
        
        # Disconnect signal to prevent firing while updating
        self.connection_props_table.cellChanged.disconnect(self._on_connection_property_changed)
        
        # Clear and repopulate properties table
        self.connection_props_table.setRowCount(0)
        
        # Add connection properties
        props = []
        if hasattr(connection, 'bandwidth'):
            props.append(("Bandwidth", connection.bandwidth))
        if hasattr(connection, 'latency'):
            props.append(("Latency", connection.latency))
        if hasattr(connection, 'label_text'):
            props.append(("Label", connection.label_text))
        
        for row, (key, value) in enumerate(props):
            self.connection_props_table.insertRow(row)
            
            # Add property name
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Make property name read-only
            self.connection_props_table.setItem(row, 0, key_item)
            
            # Add property value
            value_str = str(value) if value is not None else ""
            self.connection_props_table.setItem(row, 1, QTableWidgetItem(value_str))
        
        # Reconnect signal
        self.connection_props_table.cellChanged.connect(self._on_connection_property_changed)
    
    def _display_boundary_properties(self, boundary):
        """Display boundary-specific properties."""
        self.boundary_group.show()
        
        # Clear the devices table
        self.boundary_devices_table.setRowCount(0)
        
        # Find devices that are contained within this boundary
        if self.boundary_devices:
            for row, device in enumerate(self.boundary_devices):
                self.boundary_devices_table.insertRow(row)
                self.boundary_devices_table.setItem(row, 0, QTableWidgetItem(device.name))
    
    def set_boundary_contained_devices(self, devices):
        """Set the list of devices contained within the selected boundary."""
        self.boundary_devices = devices
        
        # If a boundary is currently selected, update its display
        if self.current_item and self.boundary_group.isVisible():
            self._display_boundary_properties(self.current_item)
    
    def _on_device_property_changed(self, row, column):
        """Handle changes in device property table."""
        if column == 1:  # Only care about value column
            key = self.device_props_table.item(row, 0).text()
            value = self.device_props_table.item(row, 1).text()
            self.device_property_changed.emit(key, value)
    
    def _on_connection_property_changed(self, row, column):
        """Handle changes in connection property table."""
        if column == 1:  # Only care about value column
            key = self.connection_props_table.item(row, 0).text()
            value = self.connection_props_table.item(row, 1).text()
            self.connection_property_changed.emit(key, value)
    
    def _on_change_icon_clicked(self):
        """Handle click on change icon button."""
        if self.current_item:
            self.change_icon_requested.emit(self.current_item)
