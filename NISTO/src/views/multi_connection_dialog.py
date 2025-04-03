from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox,
                            QDialogButtonBox, QLabel, QLineEdit, QCheckBox)
from PyQt5.QtCore import Qt
from constants import ConnectionTypes

class MultiConnectionDialog(QDialog):
    """Dialog for configuring properties when connecting multiple devices."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect Multiple Devices")
        self.setMinimumWidth(300)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header label
        header_label = QLabel("Configure connections between selected devices")
        layout.addWidget(header_label)
        
        # Form for connection properties
        form = QFormLayout()
        
        # Connection type selection
        self.connection_type_combo = QComboBox()
        for conn_type in ConnectionTypes:
            display_name = ConnectionTypes.DISPLAY_NAMES.get(conn_type, conn_type)
            self.connection_type_combo.addItem(display_name, conn_type)
        form.addRow("Connection Type:", self.connection_type_combo)
        
        # Connection label field
        self.connection_label = QLineEdit()
        self.connection_label.setText(
            ConnectionTypes.DISPLAY_NAMES.get(ConnectionTypes.ETHERNET, "Link"))
        self.connection_type_combo.currentIndexChanged.connect(self._update_connection_label)
        form.addRow("Label:", self.connection_label)
        
        # Bandwidth field
        self.bandwidth_edit = QLineEdit()
        self.bandwidth_edit.setText(
            ConnectionTypes.DEFAULT_BANDWIDTHS.get(ConnectionTypes.ETHERNET, "1G"))
        self.connection_type_combo.currentIndexChanged.connect(self._update_bandwidth)
        form.addRow("Bandwidth:", self.bandwidth_edit)
        
        # Latency field
        self.latency_edit = QLineEdit()
        self.latency_edit.setText("0ms")
        form.addRow("Latency:", self.latency_edit)
        
        # Mesh connectivity option
        self.mesh_checkbox = QCheckBox("Create mesh network (connect all-to-all)")
        self.mesh_checkbox.setChecked(True)
        self.mesh_checkbox.setToolTip("If unchecked, devices will be connected in a chain")
        form.addRow("", self.mesh_checkbox)
        
        layout.addLayout(form)
        
        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
    
    def _update_connection_label(self):
        """Update the label field based on the selected connection type."""
        conn_type = self.connection_type_combo.currentData()
        self.connection_label.setText(
            ConnectionTypes.DISPLAY_NAMES.get(conn_type, "Link"))
    
    def _update_bandwidth(self):
        """Update the bandwidth field based on the selected connection type."""
        conn_type = self.connection_type_combo.currentData()
        self.bandwidth_edit.setText(
            ConnectionTypes.DEFAULT_BANDWIDTHS.get(conn_type, "1G"))
    
    def get_connection_data(self):
        """Get the connection configuration data."""
        return {
            'type': self.connection_type_combo.currentData(),
            'label': self.connection_label.text(),
            'bandwidth': self.bandwidth_edit.text(),
            'latency': self.latency_edit.text(),
            'mesh': self.mesh_checkbox.isChecked()
        }
