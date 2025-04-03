import copy
from PyQt5.QtCore import QPointF, QRectF
from controllers.undo_redo_manager import Command
from models.device import Device
from models.connection import Connection
from models.boundary import Boundary
import logging

class AddDeviceCommand(Command):
    """Command to add a device to the canvas."""
    
    def __init__(self, device_controller, device_type, position, name=None, properties=None, custom_icon_path=None):
        super().__init__(f"Add {device_type} Device")
        self.device_controller = device_controller
        self.device_type = device_type
        self.position = position
        self.name = name
        self.properties = properties or {}
        self.custom_icon_path = custom_icon_path
        self.created_device = None
        self.logger = logging.getLogger(__name__)
    
    def execute(self):
        """Create and add the device."""
        # Check if we're in a bulk creation process
        in_bulk = hasattr(self.device_controller, '_in_bulk_creation') and self.device_controller._in_bulk_creation
        self.logger.debug(f"CMD: AddDeviceCommand execute for {self.name}, in_bulk_creation={in_bulk}")
        
        if in_bulk:
            # In bulk creation, the device was already created directly
            self.logger.debug(f"CMD: Skipping device creation for {self.name} (already created in bulk)")
            return None
        
        self.created_device = self.device_controller._create_device(
            self.name, 
            self.device_type, 
            self.position,
            self.properties,
            self.custom_icon_path
        )
        self.logger.debug(f"CMD: Created device {self.name} through command execution")
        return self.created_device
    
    def undo(self):
        """Remove the device."""
        if self.created_device:
            # Set flag to prevent recursive command creation
            if hasattr(self.device_controller, 'undo_redo_manager') and self.device_controller.undo_redo_manager:
                self.device_controller.undo_redo_manager.is_executing_command = True
            
            # Delete the device
            self.device_controller.on_delete_device_requested(self.created_device)
            
            # Reset flag
            if hasattr(self.device_controller, 'undo_redo_manager') and self.device_controller.undo_redo_manager:
                self.device_controller.undo_redo_manager.is_executing_command = False
                
            # Force canvas update
            if hasattr(self.device_controller, 'canvas') and self.device_controller.canvas:
                self.device_controller.canvas.viewport().update()


class DeleteDeviceCommand(Command):
    """Command to delete a device from the canvas."""
    
    def __init__(self, device_controller, device):
        super().__init__(f"Delete Device {device.name}")
        self.device_controller = device_controller
        self.device = device
        self.position = device.scenePos()
        self.device_type = device.device_type
        self.name = device.name
        self.properties = copy.deepcopy(device.properties) if hasattr(device, 'properties') else None
        self.custom_icon_path = device.custom_icon_path if hasattr(device, 'custom_icon_path') else None
        
        # Save connections
        self.connections = []
        if hasattr(device, 'connections'):
            for conn in device.connections:
                # Save connection info
                source_id = conn.source_device.id
                target_id = conn.target_device.id
                source_port = conn.source_port
                target_port = conn.target_port
                properties = copy.deepcopy(conn.properties) if hasattr(conn, 'properties') else None
                
                # Create connection info dictionary
                self.connections.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'source_port': source_port,
                    'target_port': target_port,
                    'properties': properties
                })
    
    def execute(self):
        """Delete the device."""
        self.device_controller._delete_device(self.device)
    
    def undo(self):
        """Recreate the device and its connections."""
        # Recreate the device
        new_device = self.device_controller._create_device(
            self.name,
            self.device_type,
            self.position,
            self.properties,
            self.custom_icon_path
        )
        
        # Force canvas update
        if hasattr(self.device_controller, 'canvas') and self.device_controller.canvas:
            self.device_controller.canvas.viewport().update()
        
        # TODO: Reconnect the device's connections
        # This would require access to the connection controller and a way to find devices by ID
        # For now, connections will need to be restored manually


class AddBoundaryCommand(Command):
    """Command to add a boundary to the canvas."""
    
    def __init__(self, boundary_controller, rect, name=None, color=None):
        super().__init__("Add Boundary")
        self.boundary_controller = boundary_controller
        self.rect = rect
        self.name = name
        self.color = color
        self.created_boundary = None
    
    def execute(self):
        """Create and add the boundary."""
        self.created_boundary = self.boundary_controller.create_boundary(
            self.rect,
            self.name,
            self.color
        )
        return self.created_boundary
    
    def undo(self):
        """Remove the boundary."""
        if self.created_boundary:
            self.boundary_controller.on_delete_boundary_requested(self.created_boundary)


class DeleteBoundaryCommand(Command):
    """Command to delete a boundary from the canvas."""
    
    def __init__(self, boundary_controller, boundary):
        super().__init__(f"Delete Boundary {boundary.name}")
        self.boundary_controller = boundary_controller
        self.boundary = boundary
        self.rect = boundary.rect()
        self.name = boundary.name
        self.color = boundary.color if hasattr(boundary, 'color') else None
    
    def execute(self):
        """Delete the boundary."""
        self.boundary_controller.on_delete_boundary_requested(self.boundary)
    
    def undo(self):
        """Recreate the boundary."""
        new_boundary = self.boundary_controller.create_boundary(
            self.rect,
            self.name,
            self.color
        )
        return new_boundary


class AddConnectionCommand(Command):
    """Command to add a connection between two devices."""
    
    def __init__(self, connection_controller, source_device, target_device, source_port=None, target_port=None, properties=None):
        # Make sure we have name attributes for the description, with fallbacks
        source_name = getattr(source_device, 'name', 'Source')
        target_name = getattr(target_device, 'name', 'Target')
        
        super().__init__(f"Add Connection {source_name} to {target_name}")
        
        self.connection_controller = connection_controller
        self.source_device = source_device
        self.target_device = target_device
        self.source_port = source_port
        self.target_port = target_port
        self.properties = properties or {}
        self.connection = None
    
    def execute(self):
        """Create and add the connection."""
        if self.connection_controller.undo_redo_manager:
            self.connection_controller.undo_redo_manager.is_executing_command = True
        
        self.created_connection = self.connection_controller.create_connection(
            self.source_device,
            self.target_device,
            self.source_port,
            self.target_port,
            self.properties
        )
        
        if self.connection_controller.undo_redo_manager:
            self.connection_controller.undo_redo_manager.is_executing_command = False
            
        return self.created_connection
    
    def undo(self):
        """Remove the connection."""
        if self.created_connection:
            if self.connection_controller.undo_redo_manager:
                self.connection_controller.undo_redo_manager.is_executing_command = True
                
            self.connection_controller._delete_connection(self.created_connection)
            
            if self.connection_controller.undo_redo_manager:
                self.connection_controller.undo_redo_manager.is_executing_command = False


class DeleteConnectionCommand(Command):
    """Command to delete a connection."""
    
    def __init__(self, connection_controller, connection):
        super().__init__(f"Delete Connection {connection.source_device.name} to {connection.target_device.name}")
        self.connection_controller = connection_controller
        self.connection = connection
        self.source_device = connection.source_device
        self.target_device = connection.target_device
        self.source_port = connection.source_port
        self.target_port = connection.target_port
        self.properties = copy.deepcopy(connection.properties) if hasattr(connection, 'properties') else None
    
    def execute(self):
        """Delete the connection."""
        self.connection_controller.on_delete_connection_requested(self.connection)
    
    def undo(self):
        """Recreate the connection."""
        new_connection = self.connection_controller.create_connection(
            self.source_device,
            self.target_device,
            self.source_port,
            self.target_port,
            self.properties
        )
        return new_connection


class MoveItemCommand(Command):
    """Command to move an item (device or boundary) on the canvas."""
    
    def __init__(self, item, old_pos, new_pos):
        if isinstance(item, Device):
            name = f"Move Device {item.name}"
        elif isinstance(item, Boundary):
            name = f"Move Boundary {item.name}"
        else:
            name = "Move Item"
        
        super().__init__(name)
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def execute(self):
        """Move the item to the new position."""
        self.item.setPos(self.new_pos)
    
    def undo(self):
        """Move the item back to the old position."""
        self.item.setPos(self.old_pos)


class CompositeCommand(Command):
    """A command that groups multiple commands together."""
    
    def __init__(self, commands=None, description="Composite Command"):
        super().__init__(description)
        self.commands = commands or []
        self.logger = logging.getLogger(__name__)
        
    def add_command(self, command):
        """Add a command to the composite."""
        self.commands.append(command)
        
    def execute(self):
        """Execute all commands in the composite."""
        self.logger.debug(f"Executing composite command with {len(self.commands)} sub-commands")
        results = []
        
        for command in self.commands:
            result = command.execute()
            results.append(result)
            
        return results
        
    def undo(self):
        """Undo all commands in reverse order."""
        self.logger.debug(f"Undoing composite command with {len(self.commands)} sub-commands")
        # Undo in reverse order
        for command in reversed(self.commands):
            command.undo()


class AlignDevicesCommand(Command):
    """Command to align multiple devices."""
    
    def __init__(self, alignment_controller, devices, original_positions, alignment_type):
        super().__init__(f"Align Devices {alignment_type}")
        self.alignment_controller = alignment_controller
        self.devices = devices
        self.original_positions = original_positions
        self.alignment_type = alignment_type
        self.new_positions = {device: device.scenePos() for device in devices}
        self.logger = logging.getLogger(__name__)
    
    def execute(self):
        """Execute the alignment (already done, just for interface conformity)."""
        # The alignment has already been performed, this is just for conformity
        pass
    
    def undo(self):
        """Restore the original positions of the devices."""
        self.logger.debug(f"Undoing alignment of {len(self.devices)} devices")
        
        for device, orig_pos in self.original_positions.items():
            if device.scene():  # Check if device still exists in scene
                device.setPos(orig_pos)
                if hasattr(device, 'update_connections'):
                    device.update_connections()
        
        # Force canvas update
        if hasattr(self.alignment_controller, 'canvas') and self.alignment_controller.canvas:
            self.alignment_controller.canvas.viewport().update()
    
    def redo(self):
        """Re-apply the alignment."""
        self.logger.debug(f"Redoing alignment of {len(self.devices)} devices")
        
        for device, new_pos in self.new_positions.items():
            if device.scene():  # Check if device still exists in scene
                device.setPos(new_pos)
                if hasattr(device, 'update_connections'):
                    device.update_connections()
        
        # Force canvas update
        if hasattr(self.alignment_controller, 'canvas') and self.alignment_controller.canvas:
            self.alignment_controller.canvas.viewport().update()


class BulkChangePropertyCommand(Command):
    """Command for changing a property on multiple devices at once."""
    
    def __init__(self, devices, property_name, new_value, original_values, event_bus=None):
        """Initialize the command.
        
        Args:
            devices: List of devices to modify
            property_name: Name of the property to change
            new_value: New value for the property
            original_values: Dictionary mapping devices to their original values
            event_bus: Optional event bus for notifications
        """
        super().__init__(f"Change {property_name} on multiple devices")
        self.devices = devices
        self.property_name = property_name
        self.new_value = new_value
        self.original_values = original_values
        self.event_bus = event_bus
        
    def execute(self):
        """Execute the command by applying the new property value to all devices."""
        for device in self.devices:
            if hasattr(device, 'properties'):
                device.properties[self.property_name] = self.new_value
                # Notify event bus if available
                if self.event_bus:
                    self.event_bus.emit('device_property_changed', device, self.property_name)
                    
                # Update labels if this property is displayed under the device
                if hasattr(device, 'display_properties') and device.display_properties.get(self.property_name, False):
                    device.update_property_labels()
        
        # Emit bulk change notification
        if self.event_bus:
            self.event_bus.emit('bulk_properties_changed', self.devices)
            
        return True
        
    def undo(self):
        """Undo the command by restoring original property values."""
        for device, orig_value in self.original_values.items():
            if hasattr(device, 'properties'):
                device.properties[self.property_name] = orig_value
                # Notify event bus if available
                if self.event_bus:
                    self.event_bus.emit('device_property_changed', device, self.property_name)
                    
                # Update labels if this property is displayed under the device
                if hasattr(device, 'display_properties') and device.display_properties.get(self.property_name, False):
                    device.update_property_labels()
        
        # Emit bulk change notification
        if self.event_bus:
            self.event_bus.emit('bulk_properties_changed', list(self.original_values.keys()))
            
        return True

class BulkTogglePropertyDisplayCommand(Command):
    """Command for toggling display properties on multiple devices at once."""
    
    def __init__(self, devices, property_name, display_enabled, original_states, event_bus=None):
        """Initialize the command."""
        super().__init__(f"Toggle display of {property_name} on multiple devices")
        self.devices = devices
        self.property_name = property_name
        self.display_enabled = display_enabled
        self.original_states = original_states  # Dictionary mapping devices to original display states
        self.event_bus = event_bus
        
    def execute(self):
        """Execute the command by updating display settings on all devices."""
        for device in self.devices:
            if not hasattr(device, 'display_properties'):
                device.display_properties = {}
                
            device.display_properties[self.property_name] = self.display_enabled
            device.update_property_labels()
            
            # Notify via event bus
            if self.event_bus:
                self.event_bus.emit('device_display_properties_changed', device)
        
        return True
        
    def undo(self):
        """Undo the command by restoring original display settings."""
        for device, orig_state in self.original_states.items():
            if orig_state is not None:  # Only restore if there was an original state
                device.display_properties[self.property_name] = orig_state
                device.update_property_labels()
                
                # Notify via event bus
                if self.event_bus:
                    self.event_bus.emit('device_display_properties_changed', device)
        
        return True
