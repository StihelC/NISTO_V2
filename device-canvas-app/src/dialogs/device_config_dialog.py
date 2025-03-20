from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

class DeviceConfigDialog(QDialog):
    def __init__(self, parent=None):
        super(DeviceConfigDialog, self).__init__(parent)
        self.setWindowTitle("Device Configuration")
        
        self.layout = QVBoxLayout()
        
        self.name_label = QLabel("Device Name:")
        self.layout.addWidget(self.name_label)
        
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_input)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_device)
        self.layout.addWidget(self.save_button)
        
        self.setLayout(self.layout)

    def save_device(self):
        device_name = self.name_input.text()
        # Logic to save the device configuration can be added here
        self.accept()