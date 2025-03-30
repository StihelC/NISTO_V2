from PyQt5.QtWidgets import QMessageBox
import logging
import traceback

from models.connection import Connection
from controllers.commands import AddConnectionCommand, DeleteConnectionCommand

class ConnectionController:
    """Controller for managing connection-related operations."""
    
    def __init__(self, canvas, event_bus, undo_redo_manager=None):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.undo_redo_manager = undo_redo_manager
    
    def on_add_connection_requested(self, source_device, target_device, connection_data=None):
        """Handle request to add a connection with data from the connection dialog."""
        # Extract properties from connection_data if available
        properties = None
        source_port = None
        target_port = None
        
        if connection_data:
            properties = {}
            if 'type' in connection_data:
                properties['connection_type'] = connection_data['type']
            if 'bandwidth' in connection_data:
                properties['bandwidth'] = connection_data['bandwidth']
            if 'latency' in connection_data:
                properties['latency'] = connection_data['latency']
            if 'label' in connection_data:
                properties['label_text'] = connection_data['label']
        
        # Pass to the regular connection request method
        return self.on_connection_requested(source_device, target_device, source_port, target_port, properties)
    
    def on_connection_requested(self, source_device, target_device, source_port=None, target_port=None, properties=None):
        """Handle request to create a connection between two devices."""
        # Use command pattern if undo_redo_manager is available
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            command = AddConnectionCommand(self, source_device, target_device, source_port, target_port, properties)
            self.undo_redo_manager.push_command(command)
            return command.created_connection
        else:
            # Original implementation
            return self.create_connection(source_device, target_device, source_port, target_port, properties)
    
    def on_delete_connection_requested(self, connection):
        """Handle request to delete a specific connection."""
        # Use command pattern if undo_redo_manager is available and not already in command
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            command = DeleteConnectionCommand(self, connection)
            self.undo_redo_manager.push_command(command)
        else:
            # Original implementation
            self._delete_connection(connection)

    def _delete_connection(self, connection):
        """Actual implementation of connection deletion."""
        if connection is None:
            self.logger.warning("Attempted to delete a null connection")
            return
            
        try:
            if hasattr(connection, 'source_device') and hasattr(connection, 'target_device'):
                self.logger.info(f"Deleting connection between {connection.source_device.name} and {connection.target_device.name}")
            else:
                self.logger.info(f"Deleting connection (unknown endpoints)")
            
            # Remove from devices' connection lists
            if hasattr(connection, 'source_device') and connection.source_device:
                if hasattr(connection.source_device, 'connections'):
                    if connection in connection.source_device.connections:
                        connection.source_device.connections.remove(connection)
            
            if hasattr(connection, 'target_device') and connection.target_device:
                if hasattr(connection.target_device, 'connections'):
                    if connection in connection.target_device.connections:
                        connection.target_device.connections.remove(connection)
            
            # Remove from scene
            if connection.scene():
                self.canvas.scene().removeItem(connection)
            else:
                self.logger.warning("Connection not in scene")
            
            # Remove from canvas connections list
            if connection in self.canvas.connections:
                self.canvas.connections.remove(connection)
            else:
                self.logger.warning("Connection not in canvas connections list")
            
            # Notify through event bus
            self.event_bus.emit("connection_deleted", connection)
            
            # Force update the canvas view
            self.canvas.viewport().update()
        except Exception as e:
            self.logger.error(f"Error in _delete_connection: {str(e)}")
            import traceback
            traceback.print_exc()

    def create_connection(self, source_device, target_device, source_port=None, target_port=None, properties=None):
        """Create a new connection between devices."""
        if not source_device or not target_device:
            self.logger.error("Cannot create connection: Missing source or target device")
            return None

        try:
            self.logger.info(f"Creating connection from '{source_device.name}' to '{target_device.name}'")
            
            # If ports are not specified, determine the closest connection points
            if not source_port:
                source_port = source_device.get_nearest_port(target_device.get_center_position())
            if not target_port:
                target_port = target_device.get_nearest_port(source_device.get_center_position())
                
            # Debug the connection port information
            self.logger.debug(f"Source port: ({source_port.x()}, {source_port.y()})")
            self.logger.debug(f"Target port: ({target_port.x()}, {target_port.y()})")
            
            # Create connection object
            connection = Connection(source_device, target_device, source_port, target_port)
            
            # Set properties if provided
            if properties:
                for key, value in properties.items():
                    # Skip None values
                    if value is not None:
                        self.logger.debug(f"Setting property {key}={value}")
                        setattr(connection, key, value)
                        
                # Ensure label text is set correctly
                if 'label_text' in properties and properties['label_text']:
                    connection.label_text = properties['label_text']  # Use preferred name from properties
                    self.logger.debug(f"Setting label_text to '{properties['label_text']}'")
                elif 'connection_type' in properties:
                    # Use ConnectionTypes display name
                    from constants import ConnectionTypes
                    display_name = ConnectionTypes.DISPLAY_NAMES.get(properties['connection_type'], "Link")
                    connection.label_text = display_name
                    self.logger.debug(f"Setting label_text from connection_type to '{display_name}'")
                
                # If the connection_type is set, update the style
                if 'connection_type' in properties and hasattr(connection, 'set_style_for_type'):
                    connection.set_style_for_type(properties['connection_type'])
            
            # Add to scene
            scene = self.canvas.scene()
            scene.addItem(connection)
            
            # Add to connections list
            self.canvas.connections.append(connection)
            
            # Notify through event bus
            self.event_bus.emit("connection_created", connection)
            
            return connection
        
        except Exception as e:
            self.logger.error(f"Error creating connection: {str(e)}")
            import traceback
            traceback.print_exc()
            self._show_error(f"Failed to create connection: {str(e)}")
            return None
    
    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)
