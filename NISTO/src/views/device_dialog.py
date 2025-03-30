from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                           QComboBox, QPushButton, QHBoxLayout, QLabel, QFileDialog)
from PyQt5.QtCore import Qt
from constants import DeviceTypes
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