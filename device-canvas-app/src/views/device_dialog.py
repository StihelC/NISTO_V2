from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLineEdit, QComboBox, QPushButton, QLabel, QGroupBox)
from PyQt5.QtCore import Qt
from models.device import Device

class DeviceDialog(QDialog):
    """Dialog for creating or editing a device."""
    
    def __init__(self, parent=None, existing_device=None):
        super().__init__(parent)
        
        self.existing_device = existing_device
        self.device_data = {}
        
        # Set window properties
        self.setWindowTitle("Device Properties" if existing_device else "Add Device")
        self.setMinimumWidth(400)
        
        # Create layout
        self._create_ui()
        
        # Initialize with existing device data if editing
        if existing_device:
            self._populate_from_device(existing_device)
    
    def _create_ui(self):
        """Create the dialog UI elements."""
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Device name
        self.name_edit = QLineEdit()
        form_layout.addRow("Device Name:", self.name_edit)
        
        # Device type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            Device.ROUTER,
            Device.SWITCH, 
            Device.SERVER,
            Device.FIREWALL,
            Device.CLOUD,
            Device.WORKSTATION,
            Device.GENERIC
        ])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        form_layout.addRow("Device Type:", self.type_combo)
        
        # Properties groupbox
        self.properties_group = QGroupBox("Device Properties")
        self.properties_layout = QFormLayout(self.properties_group)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.properties_group)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Create or cancel buttons
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # Initialize property fields based on current device type
        self._on_type_changed(self.type_combo.currentText())
    
    def _on_type_changed(self, device_type):
        """Update property fields when device type changes."""
        # Clear existing fields
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get properties for selected device type
        device_type = device_type.lower()
        if device_type in Device.DEVICE_PROPERTIES:
            properties = Device.DEVICE_PROPERTIES[device_type]
            
            # Add fields for each property
            self.property_fields = {}
            for key, default_value in properties.items():
                # Skip the icon property
                if key == 'icon':
                    continue
                    
                field = QLineEdit()
                field.setText(str(default_value))
                self.property_fields[key] = field
                self.properties_layout.addRow(f"{key.replace('_', ' ').title()}:", field)
    
    def _populate_from_device(self, device):
        """Populate dialog fields from existing device."""
        self.name_edit.setText(device.name)
        
        # Find and set the device type in combo box
        index = self.type_combo.findText(device.device_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        # Set property values
        for key, value in device.properties.items():
            if key in self.property_fields and key != 'icon':
                self.property_fields[key].setText(str(value))
    
    def get_device_data(self):
        """Get the entered device data."""
        if not self.result():  # Dialog was rejected
            return None
            
        # Collect basic data
        data = {
            'name': self.name_edit.text(),
            'device_type': self.type_combo.currentText().lower(),
            'properties': {}
        }
        
        # Collect property values
        for key, field in self.property_fields.items():
            value = field.text()
            
            # Try to convert to appropriate type
            if isinstance(Device.DEVICE_PROPERTIES[data['device_type']].get(key), bool):
                value = value.lower() in ('true', 'yes', '1')
            elif isinstance(Device.DEVICE_PROPERTIES[data['device_type']].get(key), int):
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif isinstance(Device.DEVICE_PROPERTIES[data['device_type']].get(key), float):
                try:
                    value = float(value)
                except ValueError:
                    pass
                
            data['properties'][key] = value
            
        return data