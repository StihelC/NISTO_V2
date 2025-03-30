from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFileDialog,
                           QLabel, QCheckBox, QPushButton, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, QDateTime
import json
import os
import gzip
from utils.serializer import CanvasSerializer

class FileHandler:
    """Handles file operations for saving and loading canvas data."""
    
    @staticmethod
    def save_canvas(canvas, filepath, options=None):
        """Save the canvas to the given filepath with specified options."""
        try:
            # Get serialized data
            data = CanvasSerializer.serialize_canvas(canvas)
            
            # Add metadata if requested
            if options and options.get('include_metadata', True):
                data['metadata'] = {
                    'created': QDateTime.currentDateTime().toString(Qt.ISODate),
                    'version': '1.0'
                }
            
            # Determine file format
            file_format = options.get('format', 'canvas') if options else 'canvas'
            
            # Save the file
            if options and options.get('compress', False):
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            return True, "Canvas saved successfully."
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error saving canvas: {str(e)}"
    
    @staticmethod
    def load_canvas(canvas, filepath):
        """Load the canvas from the given filepath."""
        try:
            print(f"Loading canvas from: {filepath}")
            # Detect if file is compressed
            is_compressed = False
            with open(filepath, 'rb') as f:
                signature = f.read(2)
                is_compressed = signature == b'\x1f\x8b'  # gzip signature
            
            # Load data based on whether it's compressed or not
            if is_compressed:
                print("Detected compressed file format")
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                print("Detected standard JSON format")
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Log basic stats for debugging
            device_count = len(data.get('devices', []))
            connection_count = len(data.get('connections', []))
            boundary_count = len(data.get('boundaries', []))
            print(f"Loaded {device_count} devices, {connection_count} connections, and {boundary_count} boundaries")
            
            # Deserialize into canvas
            CanvasSerializer.deserialize_canvas(data, canvas)
            
            return True, f"Canvas loaded successfully: {device_count} devices, {connection_count} connections, {boundary_count} boundaries."
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error loading canvas: {str(e)}"

class SaveOptionsDialog(QDialog):
    """Dialog for showing additional save options."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Options")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # File format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("File Format:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItem("Canvas Format (.canvas)", "canvas")
        self.format_combo.addItem("JSON (.json)", "json")
        format_layout.addWidget(self.format_combo)
        
        layout.addLayout(format_layout)
        
        # Compression option
        self.compress_check = QCheckBox("Compress file data")
        layout.addWidget(self.compress_check)
        
        # Include metadata option
        self.metadata_check = QCheckBox("Include metadata (creation date, author)")
        self.metadata_check.setChecked(True)
        layout.addWidget(self.metadata_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_options(self):
        """Get the selected save options."""
        return {
            'format': self.format_combo.currentData(),
            'compress': self.compress_check.isChecked(),
            'include_metadata': self.metadata_check.isChecked()
        }

class SaveCanvasDialog:
    """Handles the save dialog and canvas saving process."""
    
    @staticmethod
    def save_canvas(parent, canvas):
        """Show save dialog and save the canvas if confirmed."""
        # First show options dialog
        options_dialog = SaveOptionsDialog(parent)
        if options_dialog.exec_() != QDialog.Accepted:
            return False, "Save canceled"
        
        # Get options
        options = options_dialog.get_options()
        
        # Determine file extension
        file_format = options['format']
        extension = '.canvas' if file_format == 'canvas' else '.json'
        
        # Show file dialog
        filepath, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Canvas",
            "",
            f"Canvas Files (*{extension});;All Files (*)",
        )
        
        if not filepath:
            return False, "Save canceled"
        
        # Ensure file has correct extension
        if not filepath.endswith(extension):
            filepath += extension
        
        # Save the file
        success, message = FileHandler.save_canvas(canvas, filepath, options)
        
        # Show result message
        if success:
            QMessageBox.information(parent, "Save Successful", message)
        else:
            QMessageBox.critical(parent, "Save Failed", message)
        
        return success, message

class LoadCanvasDialog:
    """Handles the load dialog and canvas loading process."""
    
    @staticmethod
    def load_canvas(parent, canvas):
        """Show load dialog and load the canvas if file selected."""
        # Show file dialog
        filepath, _ = QFileDialog.getOpenFileName(
            parent,
            "Open Canvas",
            "",
            "Canvas Files (*.canvas);;JSON Files (*.json);;All Files (*)",
        )
        
        if not filepath:
            return False, "Load canceled"
        
        # Confirm loading (will overwrite current canvas)
        confirm = QMessageBox.question(
            parent,
            "Confirm Load",
            "Loading will replace the current canvas. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return False, "Load canceled"
        
        # Load the file
        success, message = FileHandler.load_canvas(canvas, filepath)
        
        # Show result message
        if success:
            QMessageBox.information(parent, "Load Successful", message)
        else:
            QMessageBox.critical(parent, "Load Failed", message)
        
        return success, message
