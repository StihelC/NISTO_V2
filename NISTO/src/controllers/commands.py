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
    
    def execute(self):
        """Create and add the device."""
        self.created_device = self.device_controller._create_device(
            self.name, 
            self.device_type, 
            self.position,
            self.properties,
            self.custom_icon_path
        )
        return self.created_device
    
    def undo(self):
        """Remove the device."""
        if self.created_device:
            # Set flag to prevent recursive command creation
            self.device_controller.undo_redo_manager.is_executing_command = True
            # Delete the device
            self.device_controller.on_delete_device_requested(self.created_device)
            # Reset flag
            self.device_controller.undo_redo_manager.is_executing_command = False


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
    """Command to add a connection between devices."""
    
    def __init__(self, connection_controller, source_device, target_device, source_port=None, target_port=None, properties=None):
        super().__init__(f"Add Connection {source_device.name} to {target_device.name}")
        self.connection_controller = connection_controller
        self.source_device = source_device
        self.target_device = target_device
        self.source_port = source_port
        self.target_port = target_port
        self.properties = properties
        self.created_connection = None
    
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
    """A command that consists of multiple sub-commands."""
    
    def __init__(self, commands=None, description="Multiple Actions"):
        super().__init__(description)
        self.commands = commands or []
        self.logger = logging.getLogger(__name__)
        self.completed_commands = []  # Track successfully executed commands
        self.undo_redo_manager = None  # Will be set from outside
    
    def add_command(self, command):
        """Add a command to the composite."""
        # Pass our undo_redo_manager to the command if we have one
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            if not hasattr(command, 'undo_redo_manager') or command.undo_redo_manager is None:
                command.undo_redo_manager = self.undo_redo_manager
        
        self.commands.append(command)
    
    def execute(self):
        """Execute all sub-commands."""
        # Mark that we're in a composite command execution
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            self.undo_redo_manager.is_executing_command = True
        
        # Clear completed commands list
        self.completed_commands.clear()
            
        for idx, cmd in enumerate(self.commands):
            try:
                # Store the result of the execution
                result = cmd.execute()
                self.completed_commands.append(cmd)  # Track successful executions
                self.logger.debug(f"Executed command {idx}: {cmd.__class__.__name__}")
                
                # If the command is an AddDeviceCommand, store the created device
                if isinstance(cmd, AddDeviceCommand) and result:
                    cmd.created_device = result
            except Exception as e:
                self.logger.error(f"Error executing command {idx}: {str(e)}")
                import traceback
                traceback.print_exc()
            
        # Reset the flag when done
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            self.undo_redo_manager.is_executing_command = False
        
        return True
    
    def undo(self):
        """Undo all sub-commands in reverse order."""
        # Mark that we're in a composite command undo
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            old_state = self.undo_redo_manager.is_executing_command
            self.undo_redo_manager.is_executing_command = True
            
        # Use the completed commands list if available, otherwise use the commands list
        commands_to_undo = list(reversed(self.completed_commands if self.completed_commands else self.commands))
            
        for idx, cmd in enumerate(commands_to_undo):
            try:
                cmd.undo()
                self.logger.debug(f"Undone command {len(commands_to_undo) - idx - 1}: {cmd.__class__.__name__}")
            except Exception as e:
                self.logger.error(f"Error undoing command {len(commands_to_undo) - idx - 1}: {str(e)}")
                import traceback
                traceback.print_exc()
            
        # Reset the flag when done
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            self.undo_redo_manager.is_executing_command = old_state
