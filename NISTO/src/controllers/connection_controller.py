from PyQt5.QtWidgets import QMessageBox, QGraphicsItem, QDialog
from PyQt5.QtCore import Qt
import logging
import traceback

from models.connection import Connection
from controllers.commands import AddConnectionCommand, DeleteConnectionCommand
from constants import ConnectionTypes
from views.multi_connection_dialog import MultiConnectionDialog

class ConnectionController:
    """Controller for managing connection-related operations."""
    
    def __init__(self, canvas, event_bus, undo_redo_manager=None):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.undo_redo_manager = undo_redo_manager
        
        # Debug flag for more verbose logging
        self.debug_mode = True
        
        # Connect to canvas signals
        self.canvas.add_connection_requested.connect(self.on_add_connection_requested)
        self.canvas.connect_multiple_devices_requested.connect(self.on_connect_multiple_devices_requested)
    
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
                return self.create_connection(source_device, target_device, source_port, target_port, properties)
        except Exception as e:
            self.logger.error(f"Error creating connection: {e}")
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
            traceback.print_exc()

    def create_connection(self, source_device, target_device, source_port=None, target_port=None, properties=None):
        """Create a connection between two devices."""
        try:
            # Create the connection object with debug logging
            if self.debug_mode:
                self.logger.info(f"Creating connection between {source_device.name} and {target_device.name}")
                
            # Initialize connection - label attribute will be created inside the Connection constructor
            connection = Connection(source_device, target_device, source_port, target_port)
            
            # Determine connection type
            connection_type = ConnectionTypes.ETHERNET  # Default
            if properties:
                if 'type' in properties:
                    connection_type = properties['type']
                elif 'connection_type' in properties:
                    connection_type = properties['connection_type']
                
            # Ensure the connection is selectable with additional debugging
            connection.setFlag(QGraphicsItem.ItemIsSelectable, True)
            connection.setFlag(QGraphicsItem.ItemIsFocusable, True)
            connection.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
            
            if self.debug_mode:
                self.logger.debug(f"Connection flags: ItemIsSelectable={bool(connection.flags() & QGraphicsItem.ItemIsSelectable)}")
                self.logger.debug(f"Connection mouse buttons: {connection.acceptedMouseButtons()}")
            
            # Set connection type before setting label text
            connection.connection_type = connection_type
            
            # Set connection label text
            if properties and 'label' in properties and properties['label']:
                connection.label_text = properties['label']
            elif properties and 'label_text' in properties and properties['label_text']:
                connection.label_text = properties['label_text']
            else:
                # Use display name from ConnectionTypes
                display_name = ConnectionTypes.DISPLAY_NAMES.get(connection_type, "Link")
                connection.label_text = display_name
            
            # Set additional properties
            if properties:
                if 'bandwidth' in properties:
                    connection.bandwidth = properties['bandwidth']
                if 'latency' in properties:
                    connection.latency = properties['latency']
            
            # Apply visual style based on type
            if hasattr(connection, 'set_style_for_type'):
                connection.set_style_for_type(connection_type)
            
            # Add to scene
            self.canvas.scene().addItem(connection)
            
            # Track in connections list
            self.canvas.connections.append(connection)
            
            # Notify through event bus
            self.event_bus.emit("connection_created", connection)
            
            return connection
            
        except Exception as e:
            self.logger.error(f"Error creating connection: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def on_connect_multiple_devices_requested(self, devices):
        """Handle request to connect multiple devices together.
        
        This creates connections between all pairs of devices in the selection.
        
        Args:
            devices: List of selected devices to connect
        """
        self.logger.info(f"Connecting {len(devices)} devices together")
        
        if len(devices) < 2:
            self.logger.warning("Need at least 2 devices to create connections")
            return
        
        # Show dialog to configure connection properties
        dialog = MultiConnectionDialog(self.canvas.parent())
        if dialog.exec_() != QDialog.Accepted:
            self.logger.info("User cancelled multi-device connection")
            return False
        
        # Get connection properties from dialog
        connection_data = dialog.get_connection_data()
        properties = {
            'type': connection_data['type'],
            'label': connection_data['label'],
            'bandwidth': connection_data['bandwidth'],
            'latency': connection_data['latency']
        }
        
        # Determine connection mode
        mesh_mode = connection_data['mesh']
        
        # Use a composite command if undo/redo is available
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            from controllers.commands import CompositeCommand, AddConnectionCommand
            
            composite_cmd = CompositeCommand(description=f"Connect {len(devices)} Devices")
            
            # Create connections based on selected mode
            connection_count = 0
            
            if mesh_mode:
                # Mesh mode: connect all devices to each other
                for i in range(len(devices)):
                    source_device = devices[i]
                    for j in range(i+1, len(devices)):
                        target_device = devices[j]
                        
                        # Skip if connection already exists
                        if self._connection_exists(source_device, target_device):
                            continue
                        
                        # Create the connection command
                        conn_cmd = AddConnectionCommand(
                            self,
                            source_device, 
                            target_device,
                            None,
                            None,
                            properties
                        )
                        
                        composite_cmd.add_command(conn_cmd)
                        connection_count += 1
            else:
                # Chain mode: connect devices in sequence
                for i in range(len(devices)-1):
                    source_device = devices[i]
                    target_device = devices[i+1]
                    
                    # Skip if connection already exists
                    if self._connection_exists(source_device, target_device):
                        continue
                    
                    # Create the connection command
                    conn_cmd = AddConnectionCommand(
                        self,
                        source_device, 
                        target_device,
                        None,
                        None,
                        properties
                    )
                    
                    composite_cmd.add_command(conn_cmd)
                    connection_count += 1
            
            # Only push if we actually created connections
            if connection_count > 0:
                self.undo_redo_manager.push_command(composite_cmd)
                self.logger.info(f"Created {connection_count} connections with undo support")
                return True
        else:
            # Direct creation without undo support
            connection_count = 0
            
            if mesh_mode:
                # Mesh mode: connect all devices to each other
                for i in range(len(devices)):
                    source_device = devices[i]
                    for j in range(i+1, len(devices)):
                        target_device = devices[j]
                        
                        # Skip if connection already exists
                        if self._connection_exists(source_device, target_device):
                            continue
                        
                        # Create the connection
                        connection = self.create_connection(source_device, target_device, None, None, properties)
                        if connection:
                            connection_count += 1
            else:
                # Chain mode: connect devices in sequence
                for i in range(len(devices)-1):
                    source_device = devices[i]
                    target_device = devices[i+1]
                    
                    # Skip if connection already exists
                    if self._connection_exists(source_device, target_device):
                        continue
                    
                    # Create the connection
                    connection = self.create_connection(source_device, target_device, None, None, properties)
                    if connection:
                        connection_count += 1
            
            self.logger.info(f"Created {connection_count} connections")
            return connection_count > 0
        
        return False

    def _connection_exists(self, device1, device2):
        """Check if a connection already exists between two devices."""
        for conn in self.canvas.connections:
            if ((conn.source_device == device1 and conn.target_device == device2) or
                (conn.source_device == device2 and conn.target_device == device1)):
                return True
        return False

    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)

    def set_connection_style(self, style):
        """Set the routing style for selected connections."""
        selected_connections = [
            item for item in self.canvas.scene().selectedItems() 
            if isinstance(item, Connection)
        ]
        
        if self.debug_mode:
            self.logger.debug(f"Found {len(selected_connections)} selected connections")
            
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
        
        if self.debug_mode:
            self.logger.debug(f"Found {len(selected_connections)} selected connections")
            
        if not selected_connections:
            self.logger.info("No connections selected to change type")
            return
            
        # Get display name for connection type
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
        
    def get_all_connections(self):
        """Get all connections in the canvas."""
        return self.canvas.connections
        
    def debug_connections(self):
        """Print debug information about all connections."""
        if not self.debug_mode:
            return
            
        connections = self.get_all_connections()
        self.logger.debug(f"Total connections: {len(connections)}")
        
        for i, conn in enumerate(connections):
            flags = conn.flags()
            self.logger.debug(f"Connection {i}: ID={conn.id} | Selectable={bool(flags & QGraphicsItem.ItemIsSelectable)} | "
                             f"Visible={conn.isVisible()} | Selected={conn.isSelected()}")
