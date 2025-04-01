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
                
                # Get grid spacing data
                spacing_data = dialog.get_spacing_data()
                
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
                    # Create multiple devices in a grid
                    self.logger.debug(f"BULK ADD: Starting creation of {multiplier} devices with spacing: {spacing_data}")
                    
                    if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
                        # Create a composite command for multiple device creation and connections
                        from controllers.commands import CompositeCommand
                        
                        # Create composite command
                        composite_cmd = CompositeCommand(description=f"Add {multiplier} {device_data['type']} Devices")
                        
                        # Set a flag to prevent execution during command creation
                        self.logger.debug(f"BULK ADD: Setting _in_bulk_creation flag to True")
                        self._in_bulk_creation = True
                        
                        try:
                            # Create devices through the command pattern
                            device_info = self._create_multiple_devices_with_commands(
                                device_data, pos, multiplier, composite_cmd, should_connect, connection_data, spacing_data
                            )
                            
                            self.logger.debug(f"BULK ADD: Created {len(device_info['devices'])} devices with commands")
                            
                            # Push the composite command to the undo stack
                            self.logger.debug(f"BULK ADD: Pushing composite command to undo stack")
                            self.undo_redo_manager.push_command(composite_cmd)
                        finally:
                            # Clear the flag
                            self.logger.debug(f"BULK ADD: Setting _in_bulk_creation flag to False")
                            self._in_bulk_creation = False
                    else:
                        # Create without undo support
                        device_info = self._create_multiple_devices(device_data, pos, multiplier, spacing_data)
                        
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
    
    def _create_multiple_devices(self, device_data, pos, count, spacing_data=None):
        """Create multiple devices arranged in a grid."""
        if pos is None:
            # Default position at center if none provided
            scene_rect = self.canvas.scene().sceneRect()
            pos = QPointF(scene_rect.width() / 2, scene_rect.height() / 2)
        
        # Get spacing configuration
        if not spacing_data:
            spacing_data = {
                'horizontal_spacing': 100,
                'vertical_spacing': 100,
                'max_columns': 5
            }
        
        horizontal_spacing = spacing_data.get('horizontal_spacing', 100)
        vertical_spacing = spacing_data.get('vertical_spacing', 100)
        max_columns = spacing_data.get('max_columns', 5)
        
        # Calculate grid size
        columns = min(count, max_columns)
        rows = (count + columns - 1) // columns  # Ceiling division
        grid_size = (rows, columns)
        
        # Device size for spacing calculation
        device_width = 60  # Default device width
        device_height = 60  # Default device height
        
        # Calculate total grid width and height
        grid_width = columns * device_width + (columns - 1) * horizontal_spacing
        grid_height = rows * device_height + (rows - 1) * vertical_spacing
        
        # Calculate starting position (top-left of the grid)
        start_x = pos.x() - grid_width / 2 + device_width / 2
        start_y = pos.y() - grid_height / 2 + device_height / 2
        
        # Store created devices and their positions
        created_devices = []
        device_positions = []
        
        # Create the base name
        base_name = device_data['name']
        if base_name.endswith(tuple("0123456789")):
            # If name already ends with a number, remove it for consistent numbering
            while base_name and base_name[-1].isdigit():
                base_name = base_name[:-1]
        
        # Create devices in a grid layout
        devices_created = 0
        for row in range(rows):
            for col in range(columns):
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
                
                # Create the device
                device = self.create_device(current_data, device_pos)
                if device:
                    created_devices.append(device)
                    device_positions.append((row, col, device))
                
                devices_created += 1
        
        # Return information about created devices
        return {
            'devices': created_devices,
            'positions': device_positions,
            'grid_size': grid_size,
            'count': count
        }
    
    def _create_multiple_devices_with_commands(self, device_data, pos, count, composite_cmd, should_connect=False, connection_data=None, spacing_data=None):
        """Create multiple devices arranged in a grid with undo/redo support."""
        if pos is None:
            # Default position at center if none provided
            scene_rect = self.canvas.scene().sceneRect()
            pos = QPointF(scene_rect.width() / 2, scene_rect.height() / 2)
        
        # Get spacing configuration
        if not spacing_data:
            spacing_data = {
                'horizontal_spacing': 100,
                'vertical_spacing': 100,
                'max_columns': 5
            }
        
        horizontal_spacing = spacing_data.get('horizontal_spacing', 100)
        vertical_spacing = spacing_data.get('vertical_spacing', 100)
        max_columns = spacing_data.get('max_columns', 5)
        
        # Calculate grid size
        columns = min(count, max_columns)
        rows = (count + columns - 1) // columns  # Ceiling division
        grid_size = (rows, columns)
        
        # Device size for spacing calculation
        device_width = 60  # Default device width
        device_height = 60  # Default device height
        
        # Calculate total grid width and height
        grid_width = columns * device_width + (columns - 1) * horizontal_spacing
        grid_height = rows * device_height + (rows - 1) * vertical_spacing
        
        # Calculate starting position (top-left of the grid)
        start_x = pos.x() - grid_width / 2 + device_width / 2
        start_y = pos.y() - grid_height / 2 + device_height / 2
        
        # Check if we're within a command execution already to prevent double execution
        is_executing = False
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            is_executing = self.undo_redo_manager.is_executing_command
            self.logger.debug(f"BULK ADD: Command execution state: {is_executing}")
            # Set flag to true to prevent recursive command execution
            self.undo_redo_manager.is_executing_command = True
            self.logger.debug(f"BULK ADD: Set executing_command flag to True")
        
        devices_created = 0
        created_devices = []
        device_positions = []
        
        try:
            # Create all devices first
            self.logger.debug(f"BULK ADD: Starting to create {count} devices in grid of {rows}x{columns}")
            
            # Store references to commands and devices they create for better tracking
            device_commands = []
            
            # Create the base name
            base_name = device_data['name']
            if base_name.endswith(tuple("0123456789")):
                # If name already ends with a number, remove it for consistent numbering
                while base_name and base_name[-1].isdigit():
                    base_name = base_name[:-1]
            
            for row in range(rows):
                for col in range(columns):
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
                    
                    # Create device command 
                    add_cmd = AddDeviceCommand(
                        self, 
                        current_data['type'],
                        device_pos,
                        current_data['name'],
                        current_data['properties'],
                        current_data.get('custom_icon_path')
                    )
                    
                    # Add command to composite command
                    composite_cmd.add_command(add_cmd)
                    self.logger.debug(f"BULK ADD: Added command for device {current_data['name']} at ({device_pos.x()}, {device_pos.y()})")
                    
                    # Only execute the command if we're not in the bulk creation process
                    # This prevents double device creation
                    device = None
                    if hasattr(self, '_in_bulk_creation') and self._in_bulk_creation:
                        # Create the device directly without executing the command
                        self.logger.debug(f"BULK ADD: Direct creation for {current_data['name']} (bulk mode)")
                        device = self._create_device(
                            current_data['name'],
                            current_data['type'],
                            device_pos,
                            current_data['properties'],
                            current_data.get('custom_icon_path')
                        )
                    else:
                        # Normal flow - execute the command
                        self.logger.debug(f"BULK ADD: Executing command for {current_data['name']} (not in bulk mode)")
                        device = add_cmd.execute()
                    
                    if device:
                        created_devices.append(device)
                        device_positions.append((row, col, device))
                        self.logger.debug(f"BULK ADD: Successfully created device {device.name}")
                        # Store the command with its target device for better tracking
                        add_cmd.created_device = device
                        device_commands.append((add_cmd, device))
                    else:
                        self.logger.warning(f"BULK ADD: Failed to create device {current_data['name']}")
                    
                    devices_created += 1
            
            # Store device commands in composite command for better undo tracking
            if hasattr(composite_cmd, '_device_commands'):
                composite_cmd._device_commands = device_commands
            else:
                setattr(composite_cmd, '_device_commands', device_commands)
                
            self.logger.debug(f"BULK ADD: Stored {len(device_commands)} device commands in composite command")
            
            # Create connections if needed
            if should_connect and len(created_devices) > 1:
                self.logger.debug(f"BULK ADD: Creating connections between {len(created_devices)} devices")
                device_info = {
                    'devices': created_devices,
                    'positions': device_positions,
                    'grid_size': grid_size,
                    'count': count
                }
                
                # Create connections using commands
                self._connect_devices_with_commands(device_info, connection_data, composite_cmd)
        
        finally:
            # Reset the execution flag
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                self.logger.debug(f"BULK ADD: Restoring executing_command flag to {is_executing}")
                self.undo_redo_manager.is_executing_command = is_executing
        
        # Ensure the canvas is updated
        self.canvas.viewport().update()
        
        self.logger.debug(f"BULK ADD: Completed with {len(created_devices)} devices")
        # Return info about created devices
        return {
            'devices': created_devices,
            'positions': device_positions,
            'grid_size': grid_size,
            'count': count
        }
    
    def _connect_devices(self, device_info, connection_data):
        """Connect devices in a grid pattern."""
        try:
            devices = device_info['devices']
            positions = device_info['positions']
            grid_size = device_info['grid_size']
            rows, cols = grid_size
            
            # Create a 2D grid representation for easier lookup
            grid = {}
            for row, col, device in positions:
                grid[(row, col)] = device
            
            self.logger.debug(f"Connecting devices in grid of {rows}x{cols}")
            for row in range(rows):
                for col in range(cols):
                    # Connect horizontally to the right
                    if col < cols-1 and (row, col) in grid and (row, col+1) in grid:
                        source = grid[(row, col)]
                        target = grid[(row, col+1)]
                        self.logger.debug(f"Creating horizontal connection: {source.name} -> {target.name}")
                        self._create_connection(source, target, connection_data)
                    
                    # Connect vertically downward
                    if row < rows-1 and (row, col) in grid and (row+1, col) in grid:
                        source = grid[(row, col)]
                        target = grid[(row+1, col)]
                        self.logger.debug(f"Creating vertical connection: {source.name} -> {target.name}")
                        self._create_connection(source, target, connection_data)
                    
        except Exception as e:
            self.logger.error(f"Error creating connections: {str(e)}")
            traceback.print_exc()
            self._show_error(f"Failed to create connections: {str(e)}")

    def _connect_devices_with_commands(self, device_info, connection_data, composite_cmd):
        """Connect devices in a grid pattern with undo/redo support."""
        try:
            devices = device_info['devices']
            positions = device_info['positions']
            grid_size = device_info['grid_size']
            rows, cols = grid_size
            
            # Create a 2D grid representation for easier lookup
            grid = {}
            for row, col, device in positions:
                grid[(row, col)] = device
            
            # Import the necessary command class
            from controllers.commands import AddConnectionCommand
            
            # Get the connection controller - improved method to find it
            connection_controller = self._get_connection_controller()
            
            # Log detailed connection controller retrieval attempts
            self.logger.debug(f"Connection controller lookup: {connection_controller}")
            
            if not connection_controller:
                self.logger.error("Connection controller not found, attempting alternative access methods")
                
                # Try alternative methods to get the connection controller
                if hasattr(self.event_bus, 'controllers') and 'connection_controller' in self.event_bus.controllers:
                    connection_controller = self.event_bus.controllers['connection_controller']
                    self.logger.info("Retrieved connection controller from event_bus.controllers dictionary")
                elif hasattr(self.canvas, 'parent') and hasattr(self.canvas.parent(), 'connection_controller'):
                    connection_controller = self.canvas.parent().connection_controller
                    self.logger.info("Retrieved connection controller from canvas parent")
                else:
                    # Create our own connections if we can't find the controller
                    self.logger.warning("Creating connections directly instead of using controller")
                    self._connect_devices(device_info, connection_data)
                    return
            
            self.logger.debug(f"Creating connections with commands for grid of {rows}x{cols}")
            for row in range(rows):
                for col in range(cols):
                    # Connect horizontally to the right
                    if col < cols-1 and (row, col) in grid and (row, col+1) in grid:
                        source = grid[(row, col)]
                        target = grid[(row, col+1)]
                        
                        self.logger.debug(f"Adding horizontal connection command: {source.name} -> {target.name}")
                        conn_cmd = AddConnectionCommand(
                            connection_controller,
                            source,
                            target,
                            None,  # source_port (will be calculated)
                            None,  # target_port (will be calculated)
                            connection_data
                        )
                        
                        composite_cmd.add_command(conn_cmd)
                    
                    # Connect vertically downward
                    if row < rows-1 and (row, col) in grid and (row+1, col) in grid:
                        source = grid[(row, col)]
                        target = grid[(row+1, col)]
                        
                        self.logger.debug(f"Adding vertical connection command: {source.name} -> {target.name}")
                        conn_cmd = AddConnectionCommand(
                            connection_controller,
                            source,
                            target,
                            None,
                            None,
                            connection_data
                        )
                        
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
            connection_type = connection_data['type']
            connection.connection_type = connection_type
            
            # Set the label text based on connection data
            if 'label' in connection_data and connection_data['label']:
                connection.label_text = connection_data['label']
            else:
                # Get display name from the connection type
                connection.label_text = ConnectionTypes.DISPLAY_NAMES.get(connection_type)
            
            # Set other connection properties
            if 'bandwidth' in connection_data:
                connection.bandwidth = connection_data['bandwidth']
            if 'latency' in connection_data:
                connection.latency = connection_data['latency']
            
            # Make connection selectable and focusable
            connection.setFlag(connection.ItemIsSelectable, True)
            connection.setFlag(connection.ItemIsFocusable, True)
            
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
        """Delete a device from the canvas.
        
        This method ensures all device components (image, label, box) are deleted together.
        """
        try:
            self.logger.info(f"Deleting device: {device}")
            
            # First, remove the device from device list
            if device in self.canvas.devices:
                self.canvas.devices.remove(device)
            
            # Remove any connected connections
            connected_connections = []
            for conn in self.canvas.connections[:]:  # Use a copy of the list to avoid modification during iteration
                if conn.source_device == device or conn.target_device == device:
                    connected_connections.append(conn)
            
            # Use connection controller to properly delete the connections
            for conn in connected_connections:
                self.event_bus.emit('connection.delete_requested', connection=conn)
            
            # Remove all child components first (if the device is a composite with children)
            if hasattr(device, 'childItems'):
                # Create a copy of the list to avoid modification during iteration
                children = list(device.childItems())
                for child in children:
                    self.canvas.scene().removeItem(child)
            
            # Now remove the device itself from the scene
            self.canvas.scene().removeItem(device)
            
            # Notify UI of the change
            self.canvas.viewport().update()
            
            # Notify the event bus - use emit instead of publish
            self.event_bus.emit('device.deleted', device=device)
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting device: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)

    def _get_connection_controller(self):
        """Helper to get the connection controller for proper deletion routing."""
        connection_controller = None
        
        # Method 1: Try to get from event_bus get_controller method
        if hasattr(self.event_bus, 'get_controller'):
            connection_controller = self.event_bus.get_controller('connection_controller')
            if connection_controller:
                self.logger.debug("Found connection_controller via event_bus.get_controller")
                return connection_controller
        
        # Method 2: Try direct access through main window
        if hasattr(self.canvas, 'parent'):
            parent = self.canvas.parent()
            if hasattr(parent, 'connection_controller'):
                connection_controller = parent.connection_controller
                self.logger.debug("Found connection_controller via canvas.parent()")
                return connection_controller
        
        # Method 3: Try to find in event_bus controllers dictionary
        if hasattr(self.event_bus, 'controllers'):
            if 'connection_controller' in self.event_bus.controllers:
                connection_controller = self.event_bus.controllers['connection_controller']
                self.logger.debug("Found connection_controller via event_bus.controllers")
                return connection_controller
                
        self.logger.error("Failed to find connection_controller")
        return None

def on_delete_device_requested(self, device):
    """Handle request to delete a device."""
    # Use command manager if available, otherwise delete directly
    if hasattr(self, 'command_manager') and self.command_manager:
        from controllers.commands import DeleteDeviceCommand
        cmd = DeleteDeviceCommand(self, device)
        self.command_manager.execute_command(cmd)
    else:
        self._delete_device(device)

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
