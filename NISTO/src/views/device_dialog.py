from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                           QComboBox, QPushButton, QHBoxLayout, QLabel, QFileDialog,
                           QSpinBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt
from constants import DeviceTypes, ConnectionTypes
import os

class DeviceDialog(QDialog):
    """Dialog for creating or editing a device."""
    
    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self.setWindowTitle("Device Properties")
        
        # Store the device if editing
        self.device = device
        
        # Initialize custom_icon_path for new device creation
        self.custom_icon_path = None
        
        # Create the UI
        self._create_ui()
        
        # If editing, populate fields
        if device:
            self._populate_from_device()
    
    def _create_ui(self):
        """Create the dialog UI."""
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Device type dropdown
        self.type_combo = QComboBox()
        
        # Add device types from constants
        self.type_combo.addItem("Router", DeviceTypes.ROUTER)
        self.type_combo.addItem("Switch", DeviceTypes.SWITCH)
        self.type_combo.addItem("Firewall", DeviceTypes.FIREWALL)
        self.type_combo.addItem("Server", DeviceTypes.SERVER)
        self.type_combo.addItem("Workstation", DeviceTypes.WORKSTATION)
        self.type_combo.addItem("Cloud", DeviceTypes.CLOUD)
        self.type_combo.addItem("Generic", DeviceTypes.GENERIC)
        
        form_layout.addRow("Type:", self.type_combo)
        
        # IP Address field
        self.ip_edit = QLineEdit()
        form_layout.addRow("IP Address:", self.ip_edit)
        
        # Description field
        self.desc_edit = QLineEdit()
        form_layout.addRow("Description:", self.desc_edit)
        
        # Custom icon upload button
        self.icon_label = QLabel("No icon selected")
        self.upload_icon_button = QPushButton("Upload Custom Icon")
        self.upload_icon_button.clicked.connect(self.upload_custom_icon)
        
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.icon_label)
        icon_layout.addWidget(self.upload_icon_button)
        
        form_layout.addRow("Custom Icon:", icon_layout)
        
        # Add form_layout to main layout
        main_layout.addLayout(form_layout)
        
        # Create collapsible section for multiple device options
        self.multiple_check = QCheckBox("Create Multiple Devices")
        self.multiple_check.toggled.connect(self._toggle_multiple_options)
        main_layout.addWidget(self.multiple_check)
        
        # Multiple devices section (hidden by default)
        self.multiple_group = QGroupBox("Multiple Device Settings")
        self.multiple_group.setVisible(False)
        multiple_layout = QVBoxLayout()
        
        # Multiplier spinner with label
        multiplier_form = QFormLayout()
        self.multiplier_spin = QSpinBox()
        self.multiplier_spin.setRange(1, 100)
        self.multiplier_spin.setValue(1)
        self.multiplier_spin.setToolTip("Number of devices to create")
        multiplier_form.addRow("Number of devices:", self.multiplier_spin)
        multiple_layout.addLayout(multiplier_form)
        
        # Grid spacing options
        spacing_group = QGroupBox("Grid Layout")
        spacing_layout = QFormLayout()
        
        # Horizontal spacing
        self.h_spacing_spin = QSpinBox()
        self.h_spacing_spin.setRange(20, 500)
        self.h_spacing_spin.setValue(100)
        self.h_spacing_spin.setSingleStep(10)
        self.h_spacing_spin.setSuffix(" px")
        self.h_spacing_spin.setToolTip("Horizontal distance between devices")
        spacing_layout.addRow("Horizontal spacing:", self.h_spacing_spin)
        
        # Vertical spacing
        self.v_spacing_spin = QSpinBox()
        self.v_spacing_spin.setRange(20, 500)
        self.v_spacing_spin.setValue(100)
        self.v_spacing_spin.setSingleStep(10)
        self.v_spacing_spin.setSuffix(" px")
        self.v_spacing_spin.setToolTip("Vertical distance between devices")
        spacing_layout.addRow("Vertical spacing:", self.v_spacing_spin)
        
        # Columns
        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 20)
        self.columns_spin.setValue(5)
        self.columns_spin.setToolTip("Number of columns in the grid")
        spacing_layout.addRow("Max columns:", self.columns_spin)
        
        # Grid preview
        self.preview_label = QLabel("Grid layout: 1 row × 1 column")
        spacing_layout.addRow("Preview:", self.preview_label)
        spacing_group.setLayout(spacing_layout)
        multiple_layout.addWidget(spacing_group)
        
        # Add update preview connections
        self.multiplier_spin.valueChanged.connect(self._update_grid_preview)
        self.columns_spin.valueChanged.connect(self._update_grid_preview)
        
        # Connection options
        connection_group = QGroupBox("Connection Options")
        connection_layout = QVBoxLayout()
        
        # Connect checkbox
        self.connect_checkbox = QCheckBox("Connect devices in grid pattern")
        self.connect_checkbox.setToolTip("Create connections between devices")
        connection_layout.addWidget(self.connect_checkbox)
        
        # Connection type selection
        conn_form = QFormLayout()
        self.connection_type_combo = QComboBox()
        
        # Populate with connection types
        for conn_type, display_name in ConnectionTypes.DISPLAY_NAMES.items():
            self.connection_type_combo.addItem(display_name, conn_type)
        
        conn_form.addRow("Connection Type:", self.connection_type_combo)
        connection_layout.addLayout(conn_form)
        connection_group.setLayout(connection_layout)
        multiple_layout.addWidget(connection_group)
        
        self.multiple_group.setLayout(multiple_layout)
        main_layout.addWidget(self.multiple_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Initial grid update
        self._update_grid_preview()

    def _toggle_multiple_options(self, checked):
        """Show or hide multiple device options based on checkbox state."""
        self.multiple_group.setVisible(checked)
        
        # Adjust dialog size when toggling
        if checked:
            self.adjustSize()
        
        # Only enable multiplier for new devices, not when editing
        if self.device is not None:
            self.multiple_check.setEnabled(False)
            self.multiple_group.setEnabled(False)

    def _toggle_connection_options(self, enabled):
        """Enable or disable the connection type options."""
        for i in range(self.connection_group.layout().count()):
            item = self.connection_group.layout().itemAt(i)
            if isinstance(item, QFormLayout):
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if widget and widget != self.connect_devices_check:
                        widget.setEnabled(enabled)
    
    def _update_connection_group_state(self, value):
        """Enable connection options only when creating multiple devices."""
        self.connection_group.setEnabled(value > 1 and self.device is None)
    
    def _update_connection_label(self):
        """Update the label field with the display name of the selected connection type."""
        conn_type = self.connection_type_combo.currentData()
        display_name = ConnectionTypes.DISPLAY_NAMES.get(conn_type, "Link")
        self.connection_label_edit.setText(display_name)
    
    def _populate_from_device(self):
        """Populate dialog fields from an existing device."""
        if not self.device:
            return
            
        # Set name
        self.name_edit.setText(self.device.name)
        
        # Set device type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.device.device_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        # Set properties
        if self.device.properties:
            if 'ip_address' in self.device.properties:
                self.ip_edit.setText(self.device.properties['ip_address'])
            if 'description' in self.device.properties:
                self.desc_edit.setText(self.device.properties['description'])
        
        # Update custom icon label if there's a custom icon
        if hasattr(self.device, 'custom_icon_path') and self.device.custom_icon_path:
            self.custom_icon_path = self.device.custom_icon_path
            self.icon_label.setText(os.path.basename(self.custom_icon_path))
    
    def upload_custom_icon(self):
        """Open a file dialog to upload a custom icon."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Custom Icon", "", "Images (*.png *.xpm *.jpg)", options=options)
        if file_path:
            self.custom_icon_path = file_path
            self.icon_label.setText(os.path.basename(file_path))
            
            # If we're editing an existing device, update it directly
            if self.device:
                self.device.custom_icon_path = file_path
                self.device._try_load_icon()
                self.device.update()  # Force redraw
    
    def get_name(self):
        """Get the device name from the dialog."""
        return self.name_edit.text().strip()
    
    def get_type(self):
        """Get the selected device type."""
        return self.type_combo.currentData()
    
    def get_properties(self):
        """Get the entered properties."""
        return {
            'ip_address': self.ip_edit.text().strip(),
            'description': self.desc_edit.text().strip()
        }
    
    def get_device_data(self):
        """Get all device data as a dictionary."""
        data = {
            'name': self.get_name(),
            'type': self.get_type(),
            'properties': self.get_properties()
        }
        
        # Add custom icon path if one was selected
        if self.custom_icon_path:
            data['custom_icon_path'] = self.custom_icon_path
            
        return data
        
    def get_multiplier(self):
        """Get the number of devices to create."""
        if self.multiple_check.isChecked():
            return self.multiplier_spin.value()
        return 1
    
    def should_connect_devices(self):
        """Check if devices should be connected to each other."""
        return (self.multiple_check.isChecked() and 
                self.connect_checkbox.isChecked() and
                self.multiplier_spin.value() > 1)
    
    def get_connection_data(self):
        """Get the connection configuration data."""
        conn_type = self.connection_type_combo.currentData()
        display_name = ConnectionTypes.DISPLAY_NAMES.get(conn_type, "Link")
        
        print(f"DEBUG - DeviceDialog - Connection type: {conn_type}")
        print(f"DEBUG - DeviceDialog - Display name: {display_name}")
        
        return {
            'type': conn_type,
            'label': display_name,  # Always use the display name
            'bandwidth': ConnectionTypes.DEFAULT_BANDWIDTHS.get(conn_type, ""),
            'latency': ""
        }
    
    def _update_grid_preview(self):
        """Update the grid layout preview based on current settings."""
        devices = self.multiplier_spin.value()
        max_columns = self.columns_spin.value()
        
        # Calculate grid dimensions
        columns = min(devices, max_columns)
        rows = (devices + columns - 1) // columns  # Ceiling division
        
        self.preview_label.setText(f"Grid layout: {rows} row{'s' if rows > 1 else ''} × {columns} column{'s' if columns > 1 else ''}")
    
    def get_spacing_data(self):
        """Get the grid spacing configuration."""
        return {
            'horizontal_spacing': self.h_spacing_spin.value(),
            'vertical_spacing': self.v_spacing_spin.value(),
            'max_columns': self.columns_spin.value()
        }