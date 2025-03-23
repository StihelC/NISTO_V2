from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                           QComboBox, QPushButton, QHBoxLayout, QLabel)
from PyQt5.QtCore import Qt
from constants import DeviceTypes

class DeviceDialog(QDialog):
    """Dialog for creating or editing a device."""
    
    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self.setWindowTitle("Device Properties")
        
        # Store the device if editing
        self.device = device
        
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
        
        # Add form to main layout
        main_layout.addLayout(form_layout)
        
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
        return {
            'name': self.get_name(),
            'type': self.get_type(),
            'properties': self.get_properties()
        }