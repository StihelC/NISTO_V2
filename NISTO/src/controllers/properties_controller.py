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
        
        # Connect panel signals
        self.panel.name_changed.connect(self._on_name_changed)
        self.panel.z_value_changed.connect(self._on_z_value_changed)
        self.panel.device_property_changed.connect(self._on_device_property_changed)
        self.panel.connection_property_changed.connect(self._on_connection_property_changed)
        self.panel.boundary_property_changed.connect(self._on_boundary_property_changed)
        self.panel.change_icon_requested.connect(self._on_change_icon_requested)  # Connect new signal
        
        # Listen to canvas selection changes
        if hasattr(canvas, 'selection_changed'):
            canvas.selection_changed.connect(self.on_selection_changed)
    
    def on_selection_changed(self, selected_items):
        """Handle canvas selection changes."""
        # For simplicity, focus on the first selected item
        self.selected_item = None
        
        if selected_items:
            self.selected_item = selected_items[0]
            self.panel.display_item_properties(self.selected_item)
            
            # Log selection details for debugging
            self.logger.info(f"Selected item: {type(self.selected_item).__name__}")
            
            # If a boundary is selected, find contained devices
            if isinstance(self.selected_item, Boundary):
                contained_devices = self._get_devices_in_boundary(self.selected_item)
                self.panel.set_boundary_contained_devices(contained_devices)
        else:
            self.panel.display_item_properties(None)
    
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
