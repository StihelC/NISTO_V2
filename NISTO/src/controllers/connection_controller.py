from PyQt5.QtWidgets import QMessageBox
import logging
import traceback

from models.connection import Connection
from controllers.commands import AddConnectionCommand, DeleteConnectionCommand
from constants import ConnectionTypes

class ConnectionController:
    """Controller for managing connection-related operations."""
    
    def __init__(self, canvas, event_bus, undo_redo_manager=None):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.undo_redo_manager = undo_redo_manager
    
    def on_add_connection_requested(self, source_device, target_device, properties=None):
        """Handle request to add a new connection."""
        try:
            self.logger.info(f"Adding connection between devices")
            
            # Make sure both devices are actual Device objects
            if not hasattr(source_device, 'get_nearest_port') or not hasattr(target_device, 'get_nearest_port'):
                self.logger.error("Invalid device objects provided for connection")
                return False
            
            # Calculate optimal connection ports
            target_center = target_device.get_center_position()
            source_center = source_device.get_center_position()
            
            source_port = source_device.get_nearest_port(target_center)
            target_port = target_device.get_nearest_port(source_center)
            
            # Delegate to shared method
            return self.on_connection_requested(source_device, target_device, source_port, target_port, properties)
        except Exception as e:
            self.logger.error(f"Error handling add connection request: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def on_connection_requested(self, source_device, target_device, source_port=None, target_port=None, properties=None):
        """Common method for creating a connection with undo/redo support."""
        try:
            # Use command pattern if available
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                from controllers.commands import AddConnectionCommand
                command = AddConnectionCommand(self, source_device, target_device, source_port, target_port, properties)
                self.undo_redo_manager.push_command(command)
                return command.connection  # Return the created connection
            else:
                # No undo/redo support, create directly
                return self._create_connection(source_device, target_device, source_port, target_port, properties)
        except Exception as e:
            self.logger.error(f"Error creating connection: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
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
        """Create a connection between two devices."""
        try:
            # Create the connection object
            connection = Connection(source_device, target_device)
            
            # Determine connection type - check if it's in the expected format
            if properties and 'type' in properties:
                connection_type = properties['type']
            elif properties and 'connection_type' in properties:
                connection_type = properties['connection_type']
            else:
                connection_type = ConnectionTypes.ETHERNET
                
            connection.connection_type = connection_type
            
            # Set connection label using proper display name
            if properties and 'label' in properties and properties['label']:
                connection.label_text = properties['label']
            elif properties and 'label_text' in properties and properties['label_text']:
                connection.label_text = properties['label_text']
            else:
                # Use display name directly from ConnectionTypes
                connection.label_text = ConnectionTypes.DISPLAY_NAMES.get(connection_type)
            
            # Set additional properties
            if properties:
                if 'bandwidth' in properties:
                    connection.bandwidth = properties['bandwidth']
                if 'latency' in properties:
                    connection.latency = properties['latency']
            
            # Add to scene
            self.canvas.scene().addItem(connection)
            
            # Track in connections list
            self.canvas.connections.append(connection)
            
            # Notify through event bus
            self.event_bus.emit("connection_created", connection)
            
            self.logger.info(f"Creating connection from '{source_device.name}' to '{target_device.name}'")
            
            return connection
        
        except Exception as e:
            self.logger.error(f"Error creating connection: {str(e)}")
            traceback.print_exc()
            return None

    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)

    def set_connection_style(self, style):
        """Set the routing style for selected connections."""
        selected_connections = [
            item for item in self.canvas.scene().selectedItems() 
            if isinstance(item, Connection)
        ]
        
        if not selected_connections:
            self.logger.info("No connections selected to change style")
            return
            
        self.logger.info(f"Setting connection style to {style} for {len(selected_connections)} connections")
        
        # Update style for each selected connection
        for connection in selected_connections:
            if hasattr(connection, 'set_routing_style'):
                connection.set_routing_style(style)
        
        # Force a complete update of the canvas
        self.canvas.viewport().update()

    def set_connection_type(self, connection_type):
        """Set the connection type and visual appearance for selected connections."""
        selected_connections = [
            item for item in self.canvas.scene().selectedItems() 
            if isinstance(item, Connection)
        ]
        
        if not selected_connections:
            self.logger.info("No connections selected to change type")
            return
            
        # Get display name for connection type
        from constants import ConnectionTypes
        display_name = ConnectionTypes.DISPLAY_NAMES.get(connection_type, "Link")
            
        self.logger.info(f"Setting connection type to {display_name} for {len(selected_connections)} connections")
        
        # Update type and visual style for each selected connection
        for connection in selected_connections:
            connection.connection_type = connection_type
            
            # Update the label to show the connection type
            connection.label_text = display_name
            
            # Apply visual style based on type
            if hasattr(connection, 'set_style_for_type'):
                connection.set_style_for_type(connection_type)
                
        # Force update the view
        self.canvas.viewport().update()
