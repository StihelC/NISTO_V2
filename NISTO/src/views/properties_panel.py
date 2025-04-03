from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QPushButton, QScrollArea, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QPlainTextEdit, QSpacerItem, QSizePolicy, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPalette

class PropertiesPanel(QWidget):
    """A panel for displaying and editing properties of selected items."""
    
    # Signals for property changes
    name_changed = pyqtSignal(str)
    z_value_changed = pyqtSignal(float)
    device_property_changed = pyqtSignal(str, object)
    connection_property_changed = pyqtSignal(str, object)
    boundary_property_changed = pyqtSignal(str, object)
    change_icon_requested = pyqtSignal(object)
    property_display_toggled = pyqtSignal(str, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.current_item = None
        self.boundary_devices = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI elements."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # Scrollable area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        
        # Title for the panel
        title = QLabel("Properties")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
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
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        layout.setVerticalSpacing(8)
        
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
        
        return group
    
    def _create_device_section(self):
        """Create the device-specific properties section."""
        group = QGroupBox("Device Properties")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        layout.setVerticalSpacing(8)
        
        # Device type 
        self.device_type_label = QLabel()
        layout.addRow("Type:", self.device_type_label)
        
        # Add button to change device icon
        self.change_icon_button = QPushButton("Change Icon")
        self.change_icon_button.setStyleSheet("QPushButton { padding: 4px 8px; }")
        self.change_icon_button.clicked.connect(self._on_change_icon_clicked)
        layout.addRow("Icon:", self.change_icon_button)
        
        # Display options group
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout(display_group)
        display_layout.setSpacing(6)
        self.display_checkboxes = {}
        
        # We'll populate these checkboxes dynamically when a device is selected
        display_layout.addWidget(QLabel("Show properties under icon:"))
        
        layout.addRow(display_group)
        
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
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        layout.setVerticalSpacing(8)
        
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
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        layout.setVerticalSpacing(8)
        
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
        
        # Clear previous properties
        self.device_props_table.setRowCount(0)
        
        # Clear any existing display option checkboxes
        for checkbox in self.display_checkboxes.values():
            checkbox.setParent(None)
        self.display_checkboxes.clear()
        
        # Find the display group within the device group
        display_group = self._get_display_options_group()
        
        if hasattr(device, 'properties'):
            # Create and configure grid layout for checkboxes
            grid_layout = QGridLayout()
            grid_layout.setHorizontalSpacing(10)
            grid_layout.setVerticalSpacing(8)
            
            # Add the grid layout to the display group
            if display_group:
                self._reset_layout(display_group)
                
                # Add instructions label
                display_group.setLayout(QVBoxLayout())
                display_group.layout().addWidget(QLabel("Show properties under icon:"))
                display_group.layout().addLayout(grid_layout)
            
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
                
                # Create display option checkbox
                if display_group:
                    checkbox = QCheckBox(key)
                    # Set checked status based on device's display_properties
                    if hasattr(device, 'display_properties') and key in device.display_properties:
                        checkbox.setChecked(device.display_properties[key])
                    checkbox.toggled.connect(lambda checked, k=key: self.property_display_toggled.emit(k, checked))
                    self.display_checkboxes[key] = checkbox
                    
                    # Add to grid, 3 columns
                    grid_col = row % 3
                    grid_row = row // 3
                    grid_layout.addWidget(checkbox, grid_row, grid_col)
                
                row += 1
        
        # Reconnect signal
        self.device_props_table.cellChanged.connect(self._on_device_property_changed)
    
    def _get_display_options_group(self):
        """Helper method to find the Display Options group within the device group."""
        for i in range(self.device_group.layout().count()):
            item = self.device_group.layout().itemAt(i)
            if (item and item.widget() and 
                isinstance(item.widget(), QGroupBox) and 
                item.widget().title() == "Display Options"):
                return item.widget()
        return None
    
    def _reset_layout(self, widget):
        """Safely reset a widget's layout by removing all child widgets."""
        old_layout = widget.layout()
        if (old_layout):
            # Take ownership of items before deleting layout
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    # Handle nested layouts if any
                    for i in range(item.layout().count()):
                        nested_item = item.layout().itemAt(i)
                        if nested_item.widget():
                            nested_item.widget().setParent(None)
    
    def _display_connection_properties(self, connection):
        """Update the panel with connection-specific properties."""
        self.connection_group.show()
        
        # Disconnect signal to prevent firing while updating
        self.connection_props_table.cellChanged.disconnect(self._on_connection_property_changed)
        
        # Clear previous properties
        self.connection_props_table.setRowCount(0)
        
        # Set routing style in combo box
        if hasattr(connection, 'routing_style'):
            style_index = {
                connection.STYLE_STRAIGHT: 0,
                connection.STYLE_ORTHOGONAL: 1,
                connection.STYLE_CURVED: 2
            }.get(connection.routing_style, 0)
            self.line_style_combo.setCurrentIndex(style_index)
        
        # Display core connection properties
        properties = []
        
        # Check if connection has properties dictionary
        if hasattr(connection, 'properties') and connection.properties:
            # Use the properties dictionary
            for key, value in connection.properties.items():
                properties.append((key, str(value) if value is not None else ""))
        else:
            # Fallback to individual attributes if properties dict doesn't exist
            if hasattr(connection, 'bandwidth'):
                properties.append(("Bandwidth", connection.bandwidth if connection.bandwidth else ""))
            if hasattr(connection, 'latency'):
                properties.append(("Latency", connection.latency if connection.latency else ""))
            if hasattr(connection, '_label_text'):
                properties.append(("Label", connection._label_text if connection._label_text else ""))
            properties.append(("Type", connection.connection_type if hasattr(connection, 'connection_type') else "ethernet"))
            
            # Add source and target info
            if hasattr(connection, 'source_device') and connection.source_device:
                properties.append(("Source", connection.source_device.name))
            if hasattr(connection, 'target_device') and connection.target_device:
                properties.append(("Target", connection.target_device.name))
        
        # Add all properties to table
        for i, (key, value) in enumerate(properties):
            self.connection_props_table.insertRow(i)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Make property name read-only
            self.connection_props_table.setItem(i, 0, key_item)
            self.connection_props_table.setItem(i, 1, QTableWidgetItem(str(value)))
        
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
    
    def show_multiple_devices(self, devices):
        """Show common properties for multiple selected devices."""
        # Clear current content
        self.clear()
        self.current_item = None  # Clear current item reference
        
        # Create main layout with sections
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # Create heading
        device_count = len(devices)
        heading = QLabel(f"<b>{device_count} Devices Selected</b>")
        heading.setStyleSheet("font-size: 14px; color: #2c3e50;")
        heading.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(heading)
        
        # Add device names for reference
        devices_list = [device.name for device in devices[:5]]
        if len(devices) > 5:
            devices_list.append(f"...and {len(devices) - 5} more")
            
        device_names = QLabel(", ".join(devices_list))
        device_names.setWordWrap(True)
        device_names.setAlignment(Qt.AlignCenter)
        device_names.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        main_layout.addWidget(device_names)
        
        # Horizontal line separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ecf0f1;")
        main_layout.addWidget(line)
        
        # Collect common property names across all selected devices
        common_props = self._get_common_properties(devices)
        
        if not common_props:
            # No common editable properties
            no_props_label = QLabel("No common editable properties")
            no_props_label.setAlignment(Qt.AlignCenter)
            no_props_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
            main_layout.addWidget(no_props_label)
            self.content_layout.addWidget(main_container)
            return
        
        # Create properties section
        properties_group = QGroupBox("Common Properties")
        properties_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        properties_layout = QFormLayout(properties_group)
        properties_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        properties_layout.setVerticalSpacing(8)
        
        # Add common properties
        for prop_name in common_props:
            # Skip color properties for now
            if prop_name.lower() == 'color':
                continue
                
            # Handle QColor and other unhashable types
            values = []
            same_values = True
            first_value = None
            
            for i, device in enumerate(devices):
                if not hasattr(device, 'properties'):
                    continue
                    
                value = device.properties.get(prop_name, "")
                
                if isinstance(value, QColor):
                    # Convert QColor to string representation for comparison
                    value_str = f"rgba({value.red()},{value.green()},{value.blue()},{value.alpha()})"
                    values.append(value_str)
                    
                    if i == 0:
                        first_value = value_str
                    elif value_str != first_value:
                        same_values = False
                else:
                    # For regular hashable values
                    values.append(value)
                    
                    if i == 0:
                        first_value = value
                    elif value != first_value:
                        same_values = False
            
            # Format the property name nicely
            readable_name = prop_name.replace('_', ' ').title()
            
            # Create the appropriate widget based on property type
            if prop_name.lower() in ["description", "notes"]:
                # Multi-line text field for descriptions
                widget = QPlainTextEdit()
                widget.setMaximumHeight(80)  # Limit height
                if same_values and values:
                    widget.setPlainText(str(values[0]))
                else:
                    widget.setPlaceholderText("Multiple values - will be updated for all devices")
                    widget.setStyleSheet("font-style: italic;")
                    
                widget.textChanged.connect(lambda editor=widget, name=prop_name: 
                                         self._emit_property_change(name, editor.toPlainText()))
            else:
                # Regular line edit for most properties
                widget = QLineEdit()
                if same_values and values:
                    widget.setText(str(values[0]))
                else:
                    widget.setPlaceholderText("Multiple values - will be updated for all")
                    widget.setStyleSheet("font-style: italic; color: #95a5a6;")
                    
                widget.textChanged.connect(lambda text, name=prop_name: 
                                         self._emit_property_change(name, text))
            
            # Add to the form layout with a label
            properties_layout.addRow(readable_name + ":", widget)
        
        main_layout.addWidget(properties_group)
        
        # Create separate display options section with improved layout
        display_group = QGroupBox("Display Settings")
        display_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        display_layout = QVBoxLayout(display_group)
        
        display_label = QLabel("Show properties under device icons:")
        display_label.setStyleSheet("margin-bottom: 8px;")
        display_layout.addWidget(display_label)
        
        # Create a grid layout for checkboxes with better spacing
        checkbox_grid = QGridLayout()
        checkbox_grid.setHorizontalSpacing(10)
        checkbox_grid.setVerticalSpacing(8)
        checkbox_grid.setColumnStretch(0, 1)
        checkbox_grid.setColumnStretch(1, 1)
        
        # Third column if we have many properties
        if len(common_props) > 5:
            checkbox_grid.setColumnStretch(2, 1)
        
        self.display_checkboxes = {}
        
        # Add display checkboxes for common properties in a grid with improved visual clarity
        row, col = 0, 0
        max_cols = 3 if len(common_props) > 5 else 2
        
        # Sort properties alphabetically for better organization
        sorted_props = sorted(common_props, key=lambda p: p.lower())
        
        for prop_name in sorted_props:
            # Skip color property for display options
            if prop_name.lower() == 'color':
                continue
                
            # Determine if this property is displayed in all, some, or no devices
            display_count = 0
            for device in devices:
                if (hasattr(device, 'display_properties') and 
                    prop_name in device.display_properties and 
                    device.display_properties[prop_name]):
                    display_count += 1
            
            # Create checkbox with appropriate state and better formatting
            readable_name = prop_name.replace('_', ' ').title()
            checkbox = QCheckBox(readable_name)
            
            # Set an appropriate style based on state
            if display_count == len(devices):
                # Displayed in all devices - checked
                checkbox.setChecked(True)
                checkbox.setTristate(False)
            elif display_count > 0:
                # Displayed in some devices - partial
                checkbox.setTristate(True)
                checkbox.setCheckState(Qt.PartiallyChecked)
                checkbox.setStyleSheet("QCheckBox::indicator:indeterminate { background-color: #3498db; }")
            else:
                # Not displayed - unchecked
                checkbox.setChecked(False)
                checkbox.setTristate(False)
                
            # Connect to handler that will toggle display for all selected devices
            checkbox.stateChanged.connect(lambda state, name=prop_name: 
                                         self._emit_display_toggle(name, state))
            self.display_checkboxes[prop_name] = checkbox
            
            # Add to grid layout
            checkbox_grid.addWidget(checkbox, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        display_layout.addLayout(checkbox_grid)
        main_layout.addWidget(display_group)
        
        # Add spacer at the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)
        
        # Add the main container to the content layout
        self.content_layout.addWidget(main_container)
    
    def _get_common_properties(self, devices):
        """Get common property names across all selected devices."""
        if not devices:
            return []
            
        # Start with the first device's properties
        if not hasattr(devices[0], 'properties'):
            return []
            
        common_props = set(devices[0].properties.keys())
        
        # Find intersection with properties from all other devices
        for device in devices[1:]:
            if not hasattr(device, 'properties'):
                return []
            
            common_props.intersection_update(device.properties.keys())
        
        # Sort properties for consistent display
        return sorted(common_props)
    
    def clear(self):
        """Clear all content from the properties panel."""
        # Hide all sections
        self.general_group.hide()
        self.device_group.hide()
        self.connection_group.hide()
        self.boundary_group.hide()
        
        # Reset current item reference
        self.current_item = None
        self.boundary_devices = []
        
        # Clear any content in the main layout
        # First, save the scroll area which is the main content
        scroll_area = None
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QScrollArea):
                scroll_area = item.widget()
                break
        
        # Clear all widgets directly added to the layout (not in the scroll area)
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Add the scroll area back
        if scroll_area:
            self.layout().addWidget(scroll_area)
            
        # Show a "No selection" message with improved styling
        no_selection_label = QLabel("No item selected")
        no_selection_label.setAlignment(Qt.AlignCenter)
        no_selection_label.setStyleSheet("color: #95a5a6; font-style: italic; padding: 20px;")
        self.content_layout.addWidget(no_selection_label)
    
    def _emit_property_change(self, prop_name, value):
        """Emit property change signal for multiple device editing."""
        self.device_property_changed.emit(prop_name, value)

    def _emit_display_toggle(self, prop_name, state):
        """Emit property display toggle signal for multiple device editing."""
        # Convert from Qt.CheckState to boolean
        # Treat PartiallyChecked as checked (true)
        display_enabled = state != Qt.Unchecked
        self.property_display_toggled.emit(prop_name, display_enabled)
