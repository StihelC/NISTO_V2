from PyQt5.QtCore import QObject, QPointF
import logging
import copy

from models.device import Device
from models.connection import Connection

class ClipboardManager(QObject):
    """Manager for handling copy and paste operations on canvas elements."""
    
    def __init__(self, canvas, device_controller, connection_controller, event_bus):
        super().__init__()
        self.canvas = canvas
        self.device_controller = device_controller
        self.connection_controller = connection_controller
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Storage for copied items
        self.copied_devices = []
        self.copied_connections = []
        
        # Offset for pasting multiple times
        self.paste_offset = QPointF(20, 20)
        self.paste_count = 0
    
    def copy_selected(self):
        """Copy all selected items on the canvas to the clipboard."""
        # Clear previous copies
        self.copied_devices = []
        self.copied_connections = []
        
        # Reset paste counter
        self.paste_count = 0
        
        # Get all selected items
        selected_items = self.canvas.scene().selectedItems()
        
        # First, collect all selected devices
        devices_to_copy = []
        for item in selected_items:
            if isinstance(item, Device):
                devices_to_copy.append(item)
        
        # Then collect connections between selected devices
        connections_to_copy = []
        for item in selected_items:
            if isinstance(item, Connection):
                # Only copy connections where both devices are selected or 
                # at least the connection itself is selected
                source_selected = item.source_device in devices_to_copy
                target_selected = item.target_device in devices_to_copy
                
                if source_selected and target_selected:
                    connections_to_copy.append(item)
        
        # Store references to the copied items
        self.copied_devices = devices_to_copy
        self.copied_connections = connections_to_copy
        
        self.logger.info(f"Copied {len(self.copied_devices)} devices and {len(self.copied_connections)} connections")
        return len(self.copied_devices) > 0 or len(self.copied_connections) > 0
    
    def paste(self):
        """Paste previously copied items onto the canvas."""
        if not self.copied_devices and not self.copied_connections:
            self.logger.info("Nothing to paste")
            return False
        
        # Increment paste counter for offset calculation
        self.paste_count += 1
        
        # Calculate offset for this paste operation
        offset = QPointF(self.paste_offset.x() * self.paste_count, 
                         self.paste_offset.y() * self.paste_count)
        
        # Track new devices and their mapping to original devices
        new_devices = {}  # Maps original device ID to new device
        
        # First, create copies of all devices
        for device in self.copied_devices:
            # Get device data
            pos = device.scenePos() + offset
            name = f"{device.name} (Copy)"
            custom_icon_path = device.custom_icon_path if hasattr(device, 'custom_icon_path') else None
            
            # Create a copy of the device's properties
            properties = copy.deepcopy(device.properties) if hasattr(device, 'properties') else None
            
            # Create the new device
            new_device = self.device_controller._create_device(
                name, 
                device.device_type, 
                pos,
                properties,
                custom_icon_path
            )
            
            if new_device:
                # Store mapping for connection creation
                new_devices[device.id] = new_device
        
        # Then, recreate connections between copied devices
        for connection in self.copied_connections:
            # Check if both source and target devices were copied
            if (connection.source_device.id in new_devices and 
                connection.target_device.id in new_devices):
                
                source = new_devices[connection.source_device.id]
                target = new_devices[connection.target_device.id]
                
                # Create the connection with original properties
                self.connection_controller.create_connection(
                    source,
                    target,
                    connection.connection_type,
                    connection.label_text
                )
        
        # Select the newly pasted devices
        self.canvas.scene().clearSelection()
        for device in new_devices.values():
            device.setSelected(True)
        
        self.logger.info(f"Pasted {len(new_devices)} devices")
        return True
    
    def cut_selected(self):
        """Cut (copy and delete) selected items."""
        if self.copy_selected():
            # Delete all selected items
            selected_devices = [item for item in self.canvas.scene().selectedItems() 
                              if isinstance(item, Device)]
            
            selected_connections = [item for item in self.canvas.scene().selectedItems() 
                                  if isinstance(item, Connection)]
            
            # Delete connections first to avoid issues with device references
            for connection in selected_connections:
                self.connection_controller.on_delete_connection_requested(connection)
            
            # Then delete devices
            for device in selected_devices:
                self.device_controller.on_delete_device_requested(device)
            
            self.logger.info(f"Cut {len(selected_devices)} devices and {len(selected_connections)} connections")
            return True
        return False
