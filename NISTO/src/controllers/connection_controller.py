from PyQt5.QtWidgets import QMessageBox
import logging
import traceback

from models.connection import Connection
from constants import ConnectionTypes

class ConnectionController:
    """Controller for managing connection-related operations."""
    
    def __init__(self, canvas, event_bus):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Initialize connection settings
        self.current_connection_style = Connection.STYLE_STRAIGHT
        self.last_connection = None
    
    def on_add_connection_requested(self, source_device, target_device, connection_data=None):
        """Handle request to add a connection between two devices."""
        if connection_data is None:
            # Use defaults if no connection data provided (backward compatibility)
            connection_data = {
                'type': ConnectionTypes.ETHERNET,
                'label': "Link",
                'bandwidth': "",
                'latency': ""
            }
            
        # Create the connection with the given data
        self.create_connection(
            source_device, 
            target_device, 
            connection_data['type'], 
            connection_data['label'],
            connection_data.get('bandwidth', ''),
            connection_data.get('latency', '')
        )
    
    def on_delete_connection_requested(self, connection):
        """Handle request to delete a connection."""
        if connection:
            self.logger.info(f"Deleting connection between {connection.source_device.name} and {connection.target_device.name}")
            
            # Use the connection's delete method to clean up references
            connection.delete()
            
            # Remove from connections list
            if hasattr(self.canvas, "connections") and connection in self.canvas.connections:
                self.canvas.connections.remove(connection)
            
            # Notify through event bus
            self.event_bus.emit("connection_deleted", connection)
    
    def create_connection(self, source_device, target_device, connection_type=None, label=None, bandwidth=None, latency=None):
        """Create a connection between two devices."""
        try:
            # Check if connection already exists
            existing = self._find_existing_connection(source_device, target_device)
            if existing:
                self.logger.info(f"Connection already exists between {source_device.name} and {target_device.name}")
                return existing
            
            # Create the connection
            connection = Connection(source_device, target_device, connection_type, label)
            
            # Set additional properties if provided
            if bandwidth:
                connection.bandwidth = bandwidth
            if latency:
                connection.latency = latency
            
            # Apply the current connection style
            connection.set_routing_style(self.current_connection_style)
            
            # Add to scene
            self.canvas.scene().addItem(connection)
            
            # Store connection if needed
            if not hasattr(self.canvas, "connections"):
                self.canvas.connections = []
            self.canvas.connections.append(connection)
            
            # Store as last connection for quick style changes
            self.last_connection = connection
            
            # Notify through event bus
            self.event_bus.emit("connection_created", connection)
            
            self.logger.info(f"Connection created between {source_device.name} and {target_device.name}")
            return connection
        
        except Exception as e:
            self.logger.error(f"Error creating connection: {str(e)}")
            traceback.print_exc()
            self._show_error(f"Failed to create connection: {str(e)}")
        
        return None
    
    def _find_existing_connection(self, device1, device2):
        """Check if a connection already exists between two devices."""
        if hasattr(self.canvas, "connections"):
            for conn in self.canvas.connections:
                if ((conn.source_device == device1 and conn.target_device == device2) or
                    (conn.source_device == device2 and conn.target_device == device1)):
                    return conn
        return None
    
    def set_connection_style(self, style):
        """Set the routing style for new and selected connections."""
        # Store current style for new connections
        self.current_connection_style = style
        
        # Update all selected connections
        for item in self.canvas.scene().selectedItems():
            if isinstance(item, Connection):
                item.set_routing_style(style)
        
        # Also update the last created connection if available
        if self.last_connection:
            self.last_connection.set_routing_style(style)
        
        style_names = {
            Connection.STYLE_STRAIGHT: "Straight",
            Connection.STYLE_ORTHOGONAL: "Orthogonal",
            Connection.STYLE_CURVED: "Curved"
        }
        self.logger.info(f"Connection style set to: {style_names.get(style, 'Unknown')}")
        
        # Notify through event bus
        self.event_bus.emit("connection_style_changed", style)
    
    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)
