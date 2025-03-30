from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                           QPushButton, QFormLayout, QLineEdit, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt
from constants import ConnectionTypes

class ConnectionTypeDialog(QDialog):
    """Dialog for selecting a connection type between devices."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Connection Type")
        self.setMinimumWidth(400)
        
        # Connection properties
        self.selected_connection_type = ConnectionTypes.ETHERNET
        self.bandwidth = ""
        self.latency = ""
        self.label_text = "Link"
        
        self._create_ui()
        
    def _create_ui(self):
        """Create the dialog UI."""
        main_layout = QVBoxLayout()
        
        # Connection Type Selection Section
        connection_group = QGroupBox("Connection Type")
        connection_layout = QFormLayout()
        
        # Connection type dropdown
        self.type_combo = QComboBox()
        
        # Add all connection types from constants
        for conn_type, display_name in ConnectionTypes.DISPLAY_NAMES.items():
            self.type_combo.addItem(display_name, conn_type)
            
        # Connect signals to update bandwidth and label when type changes
        self.type_combo.currentIndexChanged.connect(self._update_bandwidth_for_type)
        self.type_combo.currentIndexChanged.connect(self._update_label_for_type)
        
        connection_layout.addRow("Type:", self.type_combo)
        
        # Label field
        self.label_edit = QLineEdit()
        # Set initial label text based on selected connection type
        self._update_label_for_type()
        
        connection_layout.addRow("Label:", self.label_edit)
        
        # Optional advanced properties
        self.advanced_check = QCheckBox("Set Advanced Properties")
        self.advanced_check.stateChanged.connect(self._toggle_advanced_properties)
        connection_layout.addRow("", self.advanced_check)
        
        # Advanced properties section
        self.advanced_group = QGroupBox("Advanced Properties")
        self.advanced_group.setVisible(False)
        advanced_layout = QFormLayout()
        
        # Bandwidth field
        self.bandwidth_edit = QLineEdit()
        advanced_layout.addRow("Bandwidth:", self.bandwidth_edit)
        
        # Latency field
        self.latency_edit = QLineEdit()
        advanced_layout.addRow("Latency:", self.latency_edit)
        
        self.advanced_group.setLayout(advanced_layout)
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        main_layout.addWidget(self.advanced_group)
        
        # Set initial bandwidth based on default type
        self._update_bandwidth_for_type()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.create_button = QPushButton("Create Connection")
        self.create_button.clicked.connect(self.accept)
        self.create_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.create_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def _update_bandwidth_for_type(self):
        """Update the bandwidth field with the default for the selected connection type."""
        conn_type = self.type_combo.currentData()
        default_bandwidth = ConnectionTypes.DEFAULT_BANDWIDTHS.get(conn_type, "")
        self.bandwidth_edit.setText(default_bandwidth)
    
    def _update_label_for_type(self):
        """Update the label field with the display name of the selected connection type."""
        conn_type = self.type_combo.currentData()
        display_name = ConnectionTypes.DISPLAY_NAMES.get(conn_type, "Link")
        self.label_edit.setText(display_name)
    
    def _toggle_advanced_properties(self, state):
        """Show or hide advanced properties based on checkbox state."""
        self.advanced_group.setVisible(state == Qt.Checked)
        self.adjustSize()  # Resize dialog to fit content
    
    def get_connection_data(self):
        """Get the connection configuration data."""
        return {
            'type': self.type_combo.currentData(),
            'label': self.label_edit.text(),
            'bandwidth': self.bandwidth_edit.text() if self.advanced_check.isChecked() else ConnectionTypes.DEFAULT_BANDWIDTHS.get(self.type_combo.currentData(), ""),
            'latency': self.latency_edit.text() if self.advanced_check.isChecked() else ""
        }
