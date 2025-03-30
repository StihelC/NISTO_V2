from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QFontMetrics
import logging
import traceback
import math

from models.device import Device
from models.connection import Connection
from views.device_dialog import DeviceDialog
from constants import DeviceTypes, ConnectionTypes
from controllers.commands import AddDeviceCommand, DeleteDeviceCommand

class DeviceController:
    """Controller for managing device-related operations."""
    
    def __init__(self, canvas, event_bus, undo_redo_manager=None):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Initialize device counter for generating unique names
        self.device_counter = 0
        self.undo_redo_manager = undo_redo_manager
    
    def on_add_device_requested(self, pos=None):
        """Show dialog to add a new device."""
        try:
            dialog = DeviceDialog(self.canvas.parent())
            if dialog.exec_() == QDialog.Accepted:
                device_data = dialog.get_device_data()
                multiplier = dialog.get_multiplier()
                
                # Get connection options
                should_connect = dialog.should_connect_devices()
                connection_data = dialog.get_connection_data() if should_connect else None
                
                # Store connection data temporarily for spacing calculations
                if should_connect:
                    self.canvas.connection_data = connection_data
                else:
                    self.canvas.connection_data = None
                
                if multiplier <= 1:
                    # Create a single device with undo support
                    if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
                        # Create device using command for undo support
                        command = AddDeviceCommand(
                            self, 
                            device_data['type'], 
                            pos, 
                            device_data['name'],
                            device_data['properties'],
                            device_data.get('custom_icon_path')
                        )
                        self.undo_redo_manager.push_command(command)
                        return True
                    else:
                        # Create without undo support
                        self.create_device(device_data, pos)
                else:
                    # Create multiple devices in a grid with undo/redo support
                    if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
                        # Create a composite command for multiple device creation and connections
                        from controllers.commands import CompositeCommand
                        
                        # Create composite command
                        composite_cmd = CompositeCommand(description=f"Add {multiplier} {device_data['type']} Devices")
                        
                        # Create devices through the command pattern
                        device_info = self._create_multiple_devices_with_commands(
                            device_data, pos, multiplier, composite_cmd, should_connect, connection_data)
                        
                        # Push the composite command to the undo stack
                        self.undo_redo_manager.push_command(composite_cmd)
                    else:
                        # Create without undo support (old implementation)
                        device_info = self._create_multiple_devices(device_data, pos, multiplier)
                        
                        # Connect devices if specified
                        if should_connect and device_info['devices'] and len(device_info['devices']) > 1:
                            self._connect_devices(device_info, connection_data)
                    
                self.logger.info(f"Added {multiplier} device(s) of type {device_data['type']}")
                return True
        except Exception as e:
            self.logger.error(f"Error adding device: {str(e)}")
            self.logger.debug(traceback.format_exc())
            self._show_error(f"Failed to add device: {str(e)}")
        return False
    
    def _create_multiple_devices(self, device_data, pos, count):
        """Create multiple devices arranged in a grid."""
        if pos is None:
            # Default position at center if none provided
            scene_rect = self.canvas.scene().sceneRect()
            pos = QPointF(scene_rect.width() / 2, scene_rect.height() / 2)
        
        # Determine grid dimensions - aim for a roughly square grid
        grid_size = math.ceil(math.sqrt(count))
        
        # Standard device size
        device_width = 60  # standard device width
        device_height = 60  # standard device height
        
        # Estimate text width for the device name to improve spacing
        base_name = device_data['name']
        font_metrics = QFontMetrics(self.canvas.font())
        longest_name = base_name + str(count)
        text_width = font_metrics.horizontalAdvance(longest_name)
        
        # Calculate connection label width - use the connection label if connecting
        connection_label_width = 0
        if hasattr(self.canvas, 'connection_data') and self.canvas.connection_data:
            connection_label = self.canvas.connection_data.get('label', '')
            if connection_label:
                connection_label_width = font_metrics.horizontalAdvance(connection_label)
        
        # Calculate spacing based on device size, text width, and connection labels
        # Make sure we have enough space for the device, its label, and connection labels
        horizontal_spacing = max(80, text_width - device_width + 20, connection_label_width + 30)
        vertical_spacing = max(80, device_height + 40)  # Ensure enough vertical space for connections between rows
        
        # Calculate grid starting position
        # Center the entire grid around the original position
        grid_width = grid_size * device_width + (grid_size - 1) * horizontal_spacing
        grid_height = grid_size * device_height + (grid_size - 1) * vertical_spacing
        start_x = pos.x() - (grid_width / 2) + (device_width / 2)
        start_y = pos.y() - (grid_height / 2) + (device_height / 2)
        
        devices_created = 0
        created_devices = []
        
        # Store device positions for connection logic
        device_positions = []
        
        # Create devices in a grid pattern
        for row in range(grid_size):
            for col in range(grid_size):
                if devices_created >= count:
                    break
                
                # Calculate position for this device
                device_pos = QPointF(
                    start_x + col * (device_width + horizontal_spacing),
                    start_y + row * (device_height + vertical_spacing)
                )
                
                # Make a copy of device data and update name for uniqueness
                current_data = device_data.copy()
                if count > 1:
                    current_data['name'] = f"{base_name}{devices_created+1}"
                
                # Create device at calculated position
                device = self.create_device(current_data, device_pos)
                if device:
                    created_devices.append(device)
                    # Store position information for connection logic
                    device_positions.append((row, col, device))
                devices_created += 1
        
        # Store grid info with the devices for connection logic
        return {
            'devices': created_devices,
            'positions': device_positions,
            'grid_size': grid_size,
            'count': count
        }
    
    def _create_multiple_devices_with_commands(self, device_data, pos, count, composite_cmd, should_connect=False, connection_data=None):
        """Create multiple devices arranged in a grid with undo/redo support."""
        if pos is None:
            # Default position at center if none provided
            scene_rect = self.canvas.scene().sceneRect()
            pos = QPointF(scene_rect.width() / 2, scene_rect.height() / 2)
        
        # Determine grid dimensions - aim for a roughly square grid
        grid_size = math.ceil(math.sqrt(count))
        
        # Standard device size
        device_width = 60  # standard device width
        device_height = 60  # standard device height
        
        # Estimate text width for the device name to improve spacing
        base_name = device_data['name']
        font_metrics = QFontMetrics(self.canvas.font())
        longest_name = base_name + str(count)
        text_width = font_metrics.horizontalAdvance(longest_name)
        
        # Calculate connection label width - use the connection label if connecting
        connection_label_width = 0
        if hasattr(self.canvas, 'connection_data') and self.canvas.connection_data:
            connection_label = self.canvas.connection_data.get('label', '')
            if connection_label:
                connection_label_width = font_metrics.horizontalAdvance(connection_label)
        
        # Calculate spacing based on device size, text width, and connection labels
        horizontal_spacing = max(80, text_width - device_width + 20, connection_label_width + 30)
        vertical_spacing = max(80, device_height + 40)  # Ensure enough vertical space for connections
        
        # Calculate grid starting position
        # Center the entire grid around the original position
        grid_width = grid_size * device_width + (grid_size - 1) * horizontal_spacing
        grid_height = grid_size * device_height + (grid_size - 1) * vertical_spacing
        start_x = pos.x() - (grid_width / 2) + (device_width / 2)
        start_y = pos.y() - (grid_height / 2) + (device_height / 2)
        
        devices_created = 0
        created_devices = []
        device_positions = []
        
        # First create all devices
        for row in range(grid_size):
            for col in range(grid_size):
                if devices_created >= count:
                    break
                
                # Calculate position for this device
                device_pos = QPointF(
                    start_x + col * (device_width + horizontal_spacing),
                    start_y + row * (device_height + vertical_spacing)
                )
                
                # Make a copy of device data and update name for uniqueness
                current_data = device_data.copy()
                if count > 1:
                    current_data['name'] = f"{base_name}{devices_created+1}"
                
                # Create AddDeviceCommand and add to composite command
                add_cmd = AddDeviceCommand(
                    self, 
                    current_data['type'],
                    device_pos,
                    current_data['name'],
                    current_data['properties'],
                    current_data.get('custom_icon_path')
                )
                
                # Add the command to the composite command
                composite_cmd.add_command(add_cmd)
                
                # Execute the command to create the device now
                # Pass undo_redo_manager to be used in execute() for proper tracking
                if not hasattr(add_cmd, 'undo_redo_manager') and hasattr(self, 'undo_redo_manager'):
                    add_cmd.undo_redo_manager = self.undo_redo_manager
                device = add_cmd.execute()
                
                if device:
                    created_devices.append(device)
                    # Store position information for connection logic
                    device_positions.append((row, col, device))
                
                devices_created += 1
        
        # Now create connections if needed
        if should_connect and len(created_devices) > 1:
            device_info = {
                'devices': created_devices,
                'positions': device_positions,
                'grid_size': grid_size,
                'count': count
            }
            
            # Create connections using commands
            self._connect_devices_with_commands(device_info, connection_data, composite_cmd)
        
        # Return info about the created devices
        return {
            'devices': created_devices,
            'positions': device_positions,
            'grid_size': grid_size,
            'count': count
        }
    
    def _connect_devices(self, device_info, connection_data):
        """Connect multiple devices based on their grid positions in a snake pattern."""
        try:
            devices = device_info['devices']
            positions = device_info['positions']
            grid_size = device_info['grid_size']
            count = device_info['count']
            
            self.logger.info(f"Creating connections between {len(devices)} devices in a snake pattern")
            
            # Create a 2D grid representation for easier lookup
            grid = {}
            for row, col, device in positions:
                grid[(row, col)] = device
                
            # Process each row to create a snake pattern
            for row in range(grid_size):
                if row % 2 == 0:  # Even rows (0, 2, 4...) go left to right
                    for col in range(grid_size - 1):
                        if (row, col) in grid and (row, col + 1) in grid:
                            source = grid[(row, col)]
                            target = grid[(row, col + 1)]
                            self._create_connection(source, target, connection_data)
                    
                    # Connect to the next row if not the last row
                    if row < grid_size - 1 and (row, grid_size - 1) in grid and (row + 1, grid_size - 1) in grid:
                        source = grid[(row, grid_size - 1)]
                        target = grid[(row + 1, grid_size - 1)]
                        self._create_connection(source, target, connection_data)
                else:  # Odd rows (1, 3, 5...) go right to left
                    for col in range(grid_size - 1, 0, -1):
                        if (row, col) in grid and (row, col - 1) in grid:
                            source = grid[(row, col)]
                            target = grid[(row, col - 1)]
                            self._create_connection(source, target, connection_data)
                    
                    # Connect to the next row if not the last row
                    if row < grid_size - 1 and (row, 0) in grid and (row + 1, 0) in grid:
                        source = grid[(row, 0)]
                        target = grid[(row + 1, 0)]
                        self._create_connection(source, target, connection_data)
                        
        except Exception as e:
            self.logger.error(f"Error creating connections: {str(e)}")
            traceback.print_exc()
            self._show_error(f"Failed to create connections: {str(e)}")
    
    def _connect_devices_with_commands(self, device_info, connection_data, composite_cmd):
        """Connect multiple devices based on their grid positions with undo/redo support."""
        try:
            devices = device_info['devices']
            positions = device_info['positions']
            grid_size = device_info['grid_size']
            
            # Create a 2D grid representation for easier lookup
            grid = {}
            for row, col, device in positions:
                grid[(row, col)] = device
            
            # Import the necessary command class
            from controllers.commands import AddConnectionCommand
            
            # Get the connection controller
            connection_controller = self._get_connection_controller()
            if not connection_controller:
                self.logger.error("Cannot connect devices: Connection controller not found")
                return
                
            # Process each row to create a snake pattern
            for row in range(grid_size):
                if row % 2 == 0:  # Even rows go left to right
                    for col in range(grid_size - 1):
                        if (row, col) in grid and (row, col + 1) in grid:
                            source = grid[(row, col)]
                            target = grid[(row, col + 1)]
                            
                            # Create connection command
                            conn_cmd = AddConnectionCommand(
                                connection_controller,
                                source,
                                target,
                                None,  # source_port (will be calculated)
                                None,  # target_port (will be calculated)
                                connection_data
                            )
                            
                            # Share the same undo_redo_manager
                            if hasattr(composite_cmd, 'undo_redo_manager') and composite_cmd.undo_redo_manager:
                                conn_cmd.undo_redo_manager = composite_cmd.undo_redo_manager
                            
                            # Add to composite command
                            composite_cmd.add_command(conn_cmd)
                    
                    # Connect to the next row if not the last row
                    if row < grid_size - 1 and (row, grid_size - 1) in grid and (row + 1, grid_size - 1) in grid:
                        source = grid[(row, grid_size - 1)]
                        target = grid[(row + 1, grid_size - 1)]
                        
                        # Create connection command
                        conn_cmd = AddConnectionCommand(
                            connection_controller,
                            source,
                            target,
                            None,
                            None,
                            connection_data
                        )
                        
                        # Add to composite command
                        composite_cmd.add_command(conn_cmd)
                else:  # Odd rows go right to left
                    for col in range(grid_size - 1, 0, -1):
                        if (row, col) in grid and (row, col - 1) in grid:
                            source = grid[(row, col)]
                            target = grid[(row, col - 1)]
                            
                            # Create connection command
                            conn_cmd = AddConnectionCommand(
                                connection_controller,
                                source,
                                target,
                                None,
                                None,
                                connection_data
                            )
                            
                            # Add to composite command
                            composite_cmd.add_command(conn_cmd)
                    
                    # Connect to the next row if not the last row
                    if row < grid_size - 1 and (row, 0) in grid and (row + 1, 0) in grid:
                        source = grid[(row, 0)]
                        target = grid[(row + 1, 0)]
                        
                        # Create connection command
                        conn_cmd = AddConnectionCommand(
                            connection_controller,
                            source,
                            target,
                            None,
                            None,
                            connection_data
                        )
                        
                        # Add to composite command
                        composite_cmd.add_command(conn_cmd)
        except Exception as e:
            self.logger.error(f"Error creating connections with commands: {str(e)}")
            traceback.print_exc()
    
    def _create_connection(self, source, target, connection_data):
        """Helper method to create a single connection between two devices."""
        try:
            # Create connection
            connection = Connection(source, target)
            
            # Set connection type
            connection.connection_type = connection_data['type']
            
            # Get the display name directly from ConnectionTypes
            if 'label' in connection_data and connection_data['label']:
                # Use explicit label if provided
                connection.label_text = connection_data['label']
            else:
                # Otherwise use the display name from the connection type
                display_name = ConnectionTypes.DISPLAY_NAMES.get(connection_data['type'], "Link")
                connection.label_text = display_name
            
            # Set other connection properties
            if 'bandwidth' in connection_data:
                connection.bandwidth = connection_data['bandwidth']
            if 'latency' in connection_data:
                connection.latency = connection_data['latency']
            
            # Add to scene
            self.canvas.scene().addItem(connection)
            
            # Add to connections list
            self.canvas.connections.append(connection)
            
            # Notify through event bus
            self.event_bus.emit("connection_created", connection)
            
            self.logger.info(f"Created connection from {source.name} to {target.name}")
            return connection
        except Exception as e:
            self.logger.error(f"Error creating connection: {str(e)}")
            return None
    
    def create_device(self, device_data, pos=None):
        """Create a device with the specified properties."""
        try:
            self.logger.info(f"Creating device '{device_data['name']}' of type '{device_data['type']}'")
            
            # Create device object
            device = Device(device_data['name'], device_data['type'], device_data['properties'], device_data.get('custom_icon_path'))
            device.setPos(pos)
            
            # Add to scene
            scene = self.canvas.scene()
            if scene:
                scene.addItem(device)
                
                # Add to devices list
                self.canvas.devices.append(device)
                
                # Notify through event bus
                self.event_bus.emit("device_created", device)
                
                self.logger.info(f"Device '{device_data['name']}' added at position ({pos.x()}, {pos.y()})")
                return device
            else:
                self.logger.error("No scene available to add device")
                self._show_error("Canvas scene not initialized")
        
        except Exception as e:
            self.logger.error(f"Error creating device: {str(e)}")
            traceback.print_exc()
            self._show_error(f"Failed to create device: {str(e)}")
        
        return None
    
    # Add this method for compatibility with commands
    def _create_device(self, name, device_type, position, properties=None, custom_icon_path=None):
        """Create a device directly (used by commands)."""
        # Create a data dictionary for the device
        device_data = {
            'name': name if name else f"Device {len(self.canvas.devices) + 1}",
            'type': device_type,
            'properties': properties or {},
            'custom_icon_path': custom_icon_path
        }
        
        # Use the existing create_device method
        return self.create_device(device_data, position)
    
    def on_delete_device_requested(self, device):
        """Handle request to delete a specific device."""
        # Use command pattern if undo_redo_manager is available and not already in command
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            command = DeleteDeviceCommand(self, device)
            self.undo_redo_manager.push_command(command)
        else:
            # Original implementation
            self._delete_device(device)

    def _delete_device(self, device):
        """Actual implementation of device deletion."""
        if device is None:
            self.logger.warning("Attempted to delete a null device")
            return

        try:
            self.logger.info(f"Deleting device '{device.name}'")
            
            # First remove all connections to this device
            if hasattr(device, 'connections'):
                connections_to_remove = list(device.connections)  # Create a copy to avoid modification during iteration
                for conn in connections_to_remove:
                    # If using connection controller, route through it for proper cleanup
                    connection_controller = self._get_connection_controller()
                    if connection_controller:
                        # Use _delete_connection directly to avoid creating another command
                        connection_controller._delete_connection(conn)
                    else:
                        # Manual removal as fallback
                        self._remove_connection_manually(conn)
            
            # Remove from scene
            if device.scene():
                self.canvas.scene().removeItem(device)
            else:
                self.logger.warning(f"Device '{device.name}' not in scene")
            
            # Remove from devices list
            if device in self.canvas.devices:
                self.canvas.devices.remove(device)
            else:
                self.logger.warning(f"Device '{device.name}' not in canvas devices list")
            
            # Notify through event bus
            self.event_bus.emit("device_deleted", device)
            
            # Force a complete viewport update
            self.canvas.viewport().update()
        except Exception as e:
            self.logger.error(f"Error in _delete_device: {str(e)}")
            import traceback
            traceback.print_exc()

    def _remove_connection_manually(self, conn):
        """Manual connection cleanup when connection controller isn't available."""
        if conn in self.canvas.connections:
            self.canvas.connections.remove(conn)
        
        if conn.scene():
            self.canvas.scene().removeItem(conn)
        
        # Remove from devices' connection lists
        if hasattr(conn.source_device, 'connections'):
            if conn in conn.source_device.connections:
                conn.source_device.connections.remove(conn)
        
        if hasattr(conn.target_device, 'connections'):
            if conn in conn.target_device.connections:
                conn.target_device.connections.remove(conn)

    def _get_connection_controller(self):
        """Helper to get the connection controller for proper deletion routing."""
        if hasattr(self.event_bus, 'get_controller'):
            return self.event_bus.get_controller('connection_controller')
        return None
    
    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)
