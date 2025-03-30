from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import QPointF
import logging
import traceback

from models.device import Device
from views.device_dialog import DeviceDialog
from constants import DeviceTypes

class DeviceController:
    """Controller for managing device-related operations."""
    
    def __init__(self, canvas, event_bus):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Initialize device counter for generating unique names
        self.device_counter = 0
    
    def on_add_device_requested(self, pos):
        """Handle request to add a new device at the specified position."""
        try:
            # Show dialog to get device details
            dialog = DeviceDialog(self.canvas.parent())
            if (dialog.exec_() != QDialog.Accepted):
                return
            
            # Get the data from dialog
            device_data = dialog.get_device_data()
            
            # Generate name if empty
            if not device_data['name']:
                self.device_counter += 1
                device_data['name'] = f"Device{self.device_counter}"
            
            # Create the device
            self._create_device(
                device_data['name'], 
                device_data['type'], 
                pos, 
                device_data['properties'],
                device_data.get('custom_icon_path')
            )
            
        except Exception as e:
            self.logger.error(f"Error adding device: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self.canvas.parent(), "Error", f"Failed to add device: {str(e)}")
    
    def on_delete_device_requested(self, device):
        """Handle request to delete a specific device."""
        if device:
            self.logger.info(f"Deleting device '{device.name}' (ID: {device.id})")
            
            # Use the device's delete method if available
            if hasattr(device, 'delete'):
                device.delete()
            
            # Remove from scene
            self.canvas.scene().removeItem(device)
            
            # Remove from devices list
            if device in self.canvas.devices:
                self.canvas.devices.remove(device)
                
            # Notify through event bus
            self.event_bus.emit("device_deleted", device)
            
            # Force a complete viewport update
            self.canvas.viewport().update()
    
    def _create_device(self, name, device_type, position, properties=None, custom_icon_path=None):
        """Create a device and add it to the canvas."""
        try:
            self.logger.info(f"Creating device '{name}' of type '{device_type}'")
            
            # Create device object
            device = Device(name, device_type, properties, custom_icon_path)
            device.setPos(position)
            
            # Add to scene
            scene = self.canvas.scene()
            if scene:
                scene.addItem(device)
                
                # Add to devices list
                self.canvas.devices.append(device)
                
                # Notify through event bus
                self.event_bus.emit("device_created", device)
                
                self.logger.info(f"Device '{name}' added at position ({position.x()}, {position.y()})")
                return device
            else:
                self.logger.error("No scene available to add device")
                self._show_error("Canvas scene not initialized")
        
        except Exception as e:
            self.logger.error(f"Error creating device: {str(e)}")
            traceback.print_exc()
            self._show_error(f"Failed to create device: {str(e)}")
        
        return None
    
    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)
