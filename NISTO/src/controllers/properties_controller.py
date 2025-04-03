import logging
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor, QBrush
from models.device import Device
from models.connection import Connection
from models.boundary import Boundary
from controllers.commands import Command

class SetItemNameCommand(Command):
    """Command to change an item's name."""
    
    def __init__(self, item, old_name, new_name):
        super().__init__(f"Change {type(item).__name__} Name")
        self.item = item
        self.old_name = old_name
        self.new_name = new_name
    
    def execute(self):
        self.item.name = self.new_name
        if hasattr(self.item, 'update_name'):
            self.item.update_name()
        elif hasattr(self.item, 'text_item'):
            self.item.text_item.setPlainText(self.new_name)
    
    def undo(self):
        self.item.name = self.old_name
        if hasattr(self.item, 'update_name'):
            self.item.update_name()
        elif hasattr(self.item, 'text_item'):
            self.item.text_item.setPlainText(self.old_name)

class SetItemZValueCommand(Command):
    """Command to change an item's Z value (layer)."""
    
    def __init__(self, item, old_value, new_value):
        super().__init__(f"Change {type(item).__name__} Layer")
        self.item = item
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        self.item.setZValue(self.new_value)
    
    def undo(self):
        self.item.setZValue(self.old_value)

class PropertiesController:
    """Controller for managing properties panel interactions."""
    
    def __init__(self, canvas, properties_panel, event_bus, undo_redo_manager=None):
        """Initialize the properties controller."""
        self.canvas = canvas
        self.panel = properties_panel
        self.event_bus = event_bus
        self.undo_redo_manager = undo_redo_manager
        self.logger = logging.getLogger(__name__)
        self.selected_item = None
        self.selected_items = []  # Add this line to store multiple selected items
        
        # Connect panel signals
        self.panel.name_changed.connect(self._on_name_changed)
        self.panel.z_value_changed.connect(self._on_z_value_changed)
        self.panel.device_property_changed.connect(self._on_device_property_changed)
        self.panel.connection_property_changed.connect(self._on_connection_property_changed)
        self.panel.boundary_property_changed.connect(self._on_boundary_property_changed)
        self.panel.change_icon_requested.connect(self._on_change_icon_requested)  # Connect new signal
        self.panel.property_display_toggled.connect(self._on_property_display_toggled)  # Connect the new signal
        
        # Listen to canvas selection changes
        if hasattr(canvas, 'selection_changed'):
            canvas.selection_changed.connect(self.on_selection_changed)
    
    def on_selection_changed(self, selected_items):
        """Handle canvas selection changes."""
        self.update_properties_panel(selected_items)
    
    def update_properties_panel(self, selected_items=None):
        """Update properties panel based on selection."""
        if selected_items is None:
            # If no items provided, get the current selection from the canvas
            selected_items = self.canvas.scene().selectedItems()
        
        # Clear current selection reference
        self.selected_item = None
        self.selected_items = []
        
        # Handle the case when multiple items are selected
        if len(selected_items) > 1:
            # Filter to handle only devices for multi-selection
            devices = [item for item in selected_items if item in self.canvas.devices]
            if devices:
                self.selected_items = devices
                self.panel.show_multiple_devices(devices)
                return
        
        # If we reach here, either nothing is selected or only one item is selected
        if not selected_items:
            # Nothing selected, show empty panel
            self.panel.clear()
            return
        
        # Get the first selected item
        item = selected_items[0]
        
        # For simplicity, focus on the first selected item
        self.selected_item = item
        self.panel.display_item_properties(self.selected_item)
        
        # Log selection details for debugging
        self.logger.info(f"Selected item: {type(self.selected_item).__name__}")
        
        # If a boundary is selected, find contained devices
        if isinstance(self.selected_item, Boundary):
            contained_devices = self._get_devices_in_boundary(self.selected_item)
            self.panel.set_boundary_contained_devices(contained_devices)
    
    def _get_devices_in_boundary(self, boundary):
        """Get all devices contained within the boundary."""
        devices = []
        boundary_rect = boundary.sceneBoundingRect()
        
        for item in self.canvas.scene().items():
            if isinstance(item, Device):
                # Check if device is fully contained within boundary
                device_rect = item.sceneBoundingRect()
                if boundary_rect.contains(device_rect):
                    devices.append(item)
        
        return devices
    
    def _on_name_changed(self, new_name):
        """Handle name change in properties panel."""
        if not self.selected_item or not hasattr(self.selected_item, 'name'):
            return
            
        old_name = self.selected_item.name
        if old_name != new_name:
            self.logger.info(f"Changing name from '{old_name}' to '{new_name}'")
            
            if self.undo_redo_manager:
                cmd = SetItemNameCommand(self.selected_item, old_name, new_name)
                self.undo_redo_manager.push_command(cmd)
            else:
                self.selected_item.name = new_name
                if hasattr(self.selected_item, 'update_name'):
                    self.selected_item.update_name()
                elif hasattr(self.selected_item, 'text_item'):
                    self.selected_item.text_item.setPlainText(new_name)
            
            # Notify via event bus based on item type
            if isinstance(self.selected_item, Device):
                self.event_bus.emit("device_name_changed", self.selected_item)
            elif isinstance(self.selected_item, Connection):
                self.event_bus.emit("connection_name_changed", self.selected_item)
            elif isinstance(self.selected_item, Boundary):
                self.event_bus.emit("boundary_name_changed", self.selected_item)
    
    def _on_z_value_changed(self, new_z_value):
        """Handle Z-value (layer) change in properties panel."""
        if not self.selected_item:
            return
            
        old_z_value = self.selected_item.zValue()
        if old_z_value != new_z_value:
            self.logger.info(f"Changing Z-value from {old_z_value} to {new_z_value}")
            
            if self.undo_redo_manager:
                cmd = SetItemZValueCommand(self.selected_item, old_z_value, new_z_value)
                self.undo_redo_manager.push_command(cmd)
            else:
                self.selected_item.setZValue(new_z_value)
            
            # Force canvas update
            self.canvas.viewport().update()
            
            # Notify via event bus
            item_type = type(self.selected_item).__name__.lower()
            self.event_bus.emit(f"{item_type}_layer_changed", self.selected_item)
    
    def _on_device_property_changed(self, key, value):
        """Handle device property change in properties panel."""
        if not self.selected_item or not isinstance(self.selected_item, Device):
            return
            
        if hasattr(self.selected_item, 'properties') and key in self.selected_item.properties:
            old_value = self.selected_item.properties[key]
            
            # Try to convert value to appropriate type
            if isinstance(old_value, int):
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif isinstance(old_value, float):
                try:
                    value = float(value)
                except ValueError:
                    pass
            elif isinstance(old_value, bool):
                value = value.lower() in ('true', 'yes', '1')
            
            if old_value != value:
                self.logger.info(f"Changing device property '{key}' from '{old_value}' to '{value}'")
                self.selected_item.properties[key] = value
                
                # Notify via event bus
                self.event_bus.emit("device_property_changed", self.selected_item, key)
    
    def _on_connection_property_changed(self, key, value):
        """Handle connection property change in properties panel."""
        if not self.selected_item or not isinstance(self.selected_item, Connection):
            return
            
        if key == "line_style":
            # Map UI text back to internal style names
            style_map = {
                "Straight": Connection.STYLE_STRAIGHT, 
                "Orthogonal": Connection.STYLE_ORTHOGONAL, 
                "Curved": Connection.STYLE_CURVED
            }
            internal_style = style_map.get(value, Connection.STYLE_STRAIGHT)
            
            if self.selected_item.routing_style != internal_style:
                self.logger.info(f"Changing connection routing style from {self.selected_item.routing_style} to {internal_style}")
                
                # Capture the old routing style for undo
                old_style = self.selected_item.routing_style
                
                # Create a command for the routing style change if using undo/redo
                if self.undo_redo_manager:
                    class ChangeConnectionStyleCommand(Command):
                        def __init__(self, connection, old_style, new_style):
                            super().__init__("Change Connection Style")
                            self.connection = connection
                            self.old_style = old_style
                            self.new_style = new_style
                        
                        def execute(self):
                            self.connection.set_routing_style(self.new_style)
                        
                        def undo(self):
                            self.connection.set_routing_style(self.old_style)
                    
                    cmd = ChangeConnectionStyleCommand(self.selected_item, old_style, internal_style)
                    self.undo_redo_manager.push_command(cmd)
                else:
                    # Direct change without undo/redo
                    self.selected_item.set_routing_style(internal_style)
                    
                # Notify via event bus
                self.event_bus.emit("connection_style_changed", self.selected_item)
        
        # Handle standard properties that should be in the properties dictionary
        elif key in ["Bandwidth", "Latency", "Label"]:
            # Ensure properties dictionary exists
            if not hasattr(self.selected_item, 'properties'):
                self.selected_item.properties = {}
                
            # Update the value in the properties dictionary
            old_value = self.selected_item.properties.get(key)
            if old_value != value:
                self.selected_item.properties[key] = value
                
                # Also update the corresponding attribute
                if key == "Bandwidth":
                    self.selected_item.bandwidth = value
                elif key == "Latency":
                    self.selected_item.latency = value
                elif key == "Label":
                    self.selected_item.label_text = value
                    
                self.event_bus.emit("connection_property_changed", self.selected_item, key)
    
    def _on_boundary_property_changed(self, key, value):
        """Handle boundary property change in properties panel."""
        if not self.selected_item or not isinstance(self.selected_item, Boundary):
            return
    
    def _on_change_icon_requested(self, item):
        """Handle request to change a device's icon."""
        if isinstance(item, Device):
            self.logger.info(f"Changing icon for device: {item.name}")
            item.upload_custom_icon()
    
    def _on_property_display_toggled(self, prop_name, display_enabled):
        """Handle toggling of property display under device icons."""
        # Handle single or multiple device selection
        if self.selected_items:
            # Apply to all selected devices
            for device in self.selected_items:
                self._toggle_property_display_for_device(device, prop_name, display_enabled)
        elif self.selected_item and isinstance(self.selected_item, Device):
            # Apply to single selected device
            self._toggle_property_display_for_device(self.selected_item, prop_name, display_enabled)
    
    def _toggle_property_display_for_device(self, device, prop_name, display_enabled):
        """Toggle property display for a single device with undo/redo support."""
        if not isinstance(device, Device):
            return
            
        # Ensure the display_properties dict exists
        if not hasattr(device, 'display_properties'):
            device.display_properties = {}
            
        # Set the display preference for this property
        old_value = device.display_properties.get(prop_name, False)
        if old_value != display_enabled:
            self.logger.info(f"Toggling display of property '{prop_name}' to {display_enabled} for device {device.name}")
            
            if self.undo_redo_manager:
                cmd = TogglePropertyDisplayCommand(device, prop_name, old_value, display_enabled)
                self.undo_redo_manager.push_command(cmd)
            else:
                device.display_properties[prop_name] = display_enabled
                device.update_property_labels()
                
            # Notify via event bus
            if self.event_bus:
                self.event_bus.emit("device_display_properties_changed", device)

    def on_property_changed(self, property_name, value):
        """Handle property changes from the panel."""
        if self.selected_items:
            # Handle multiple selected items
            self._handle_multiple_property_change(property_name, value)
        elif self.selected_item:
            # Handle single selected item
            self._handle_single_property_change(property_name, value)
    
    def _handle_multiple_property_change(self, property_name, value):
        """Handle property change for multiple selected devices."""
        # Store original values for undo/redo
        original_values = {}
        
        for device in self.selected_items:
            if hasattr(device, 'properties') and property_name in device.properties:
                original_values[device] = device.properties.get(property_name)
        
        # If using command pattern
        if self.undo_redo_manager:
            from controllers.commands import BulkChangePropertyCommand
            
            cmd = BulkChangePropertyCommand(
                self.selected_items,
                property_name,
                value,
                original_values,
                self.event_bus  # Pass event bus to the command
            )
            
            self.undo_redo_manager.push_command(cmd)
        else:
            # Apply changes directly
            for device in self.selected_items:
                if hasattr(device, 'properties'):
                    device.properties[property_name] = value
                    # Notify about property change
                    if self.event_bus:
                        self.event_bus.emit('device_property_changed', device, property_name)
        
        # Notify that multiple devices' properties were changed
        if self.event_bus:
            self.event_bus.emit('bulk_properties_changed', self.selected_items)
    
    def _handle_single_property_change(self, property_name, value):
        """Handle property change for a single selected device."""
        if not self.selected_item or not isinstance(self.selected_item, Device):
            return
            
        if hasattr(self.selected_item, 'properties') and property_name in self.selected_item.properties:
            old_value = self.selected_item.properties[property_name]
            
            # Try to convert value to appropriate type
            if isinstance(old_value, int):
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif isinstance(old_value, float):
                try:
                    value = float(value)
                except ValueError:
                    pass
            elif isinstance(old_value, bool):
                value = value.lower() in ('true', 'yes', '1')
            
            if old_value != value:
                self.logger.info(f"Changing device property '{property_name}' from '{old_value}' to '{value}'")
                self.selected_item.properties[property_name] = value
                
                # Notify via event bus
                if self.event_bus:
                    self.event_bus.emit("device_property_changed", self.selected_item, property_name)
    
class TogglePropertyDisplayCommand(Command):
    """Command for toggling device property display."""
    
    def __init__(self, device, property_name, old_state, new_state):
        """Initialize the command."""
        super().__init__(f"Toggle Display of '{property_name}'")
        self.device = device
        self.property_name = property_name
        self.old_state = old_state
        self.new_state = new_state
        
    def execute(self):
        """Execute the command."""
        if not hasattr(self.device, 'display_properties'):
            self.device.display_properties = {}
        self.device.display_properties[self.property_name] = self.new_state
        self.device.update_property_labels()
        
    def undo(self):
        """Undo the command."""
        self.device.display_properties[self.property_name] = self.old_state
        self.device.update_property_labels()
