import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QDialogButtonBox, QHeaderView,
    QCheckBox, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt

from models.device import Device
from controllers.commands import Command, CompositeCommand


class BulkPropertyChangeCommand(Command):
    """Command for changing properties of multiple devices at once."""
    
    def __init__(self, devices, property_changes):
        """Initialize the command.
        
        Args:
            devices: List of affected devices
            property_changes: Dictionary mapping device IDs to {property: (old_value, new_value)} dicts
        """
        super().__init__(f"Change Properties of {len(devices)} Devices")
        self.devices = devices
        self.property_changes = property_changes
        
    def execute(self):
        """Execute the command by applying all property changes."""
        for device in self.devices:
            if device.id in self.property_changes:
                changes = self.property_changes[device.id]
                for prop, (old_val, new_val) in changes.items():
                    device.properties[prop] = new_val
                    
                # Update property labels if necessary
                if hasattr(device, 'display_properties'):
                    device.update_property_labels()
        
        return True
        
    def undo(self):
        """Undo the command by restoring previous property values."""
        for device in self.devices:
            if device.id in self.property_changes:
                changes = self.property_changes[device.id]
                for prop, (old_val, new_val) in changes.items():
                    device.properties[prop] = old_val
                    
                # Update property labels
                if hasattr(device, 'display_properties'):
                    device.update_property_labels()
        
        return True


class BulkPropertyController:
    """Controller for handling bulk property operations."""
    
    def __init__(self, canvas, device_controller, event_bus, undo_redo_manager=None):
        """Initialize the bulk property controller.
        
        Args:
            canvas: The canvas to operate on
            device_controller: The device controller for accessing devices
            event_bus: Event bus for broadcasting events
            undo_redo_manager: Undo/redo manager for command pattern support
        """
        self.canvas = canvas
        self.device_controller = device_controller
        self.event_bus = event_bus
        self.undo_redo_manager = undo_redo_manager
        self.logger = logging.getLogger(__name__)
    
    def edit_selected_devices(self):
        """Open a dialog to edit properties of selected devices."""
        # Get all selected devices
        selected_items = self.canvas.scene().selectedItems()
        selected_devices = [item for item in selected_items if isinstance(item, Device)]
        
        if not selected_devices:
            self.logger.warning("No devices selected for bulk editing")
            return
        
        # Open property editing dialog
        dialog = BulkPropertyEditDialog(selected_devices)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get property changes from the dialog
            property_changes = dialog.get_property_changes()
            if property_changes:
                self._apply_bulk_property_changes(selected_devices, property_changes)
    
    def _apply_bulk_property_changes(self, devices, property_changes):
        """Apply bulk property changes to multiple devices.
        
        Args:
            devices: List of devices to modify
            property_changes: Dictionary of property changes by device ID
        """
        self.logger.info(f"Applying bulk property changes to {len(devices)} devices")
        
        # Use command pattern if undo/redo manager is available
        if self.undo_redo_manager:
            cmd = BulkPropertyChangeCommand(devices, property_changes)
            self.undo_redo_manager.push_command(cmd)
        else:
            # Apply changes directly without undo support
            for device in devices:
                if device.id in property_changes:
                    changes = property_changes[device.id]
                    for prop, (old_val, new_val) in changes.items():
                        device.properties[prop] = new_val
                        
                    # Update property labels if necessary
                    if hasattr(device, 'display_properties'):
                        device.update_property_labels()
        
        # Notify that devices were modified
        if self.event_bus:
            self.event_bus.emit("bulk_properties_changed", devices)


class BulkPropertyEditDialog(QDialog):
    """Dialog for editing properties of multiple devices."""
    
    def __init__(self, devices, parent=None):
        """Initialize the dialog.
        
        Args:
            devices: List of devices to edit
            parent: Parent widget
        """
        super().__init__(parent)
        self.devices = devices
        self.setWindowTitle(f"Edit Properties of {len(devices)} Devices")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.original_values = {}
        self.changed_values = {}
        
        self._init_ui()
        self._populate_common_properties()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header
        layout.addWidget(QLabel("<b>Edit Common Properties</b>"))
        layout.addWidget(QLabel(f"Selected devices: {len(self.devices)}"))
        
        # Table for common properties
        self.property_table = QTableWidget(0, 3)
        self.property_table.setHorizontalHeaderLabels(["Property", "Value", "Apply to All"])
        self.property_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.property_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.property_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.property_table)
        
        # Display properties section
        layout.addWidget(QLabel("<b>Display Options</b>"))
        layout.addWidget(QLabel("Select properties to display under devices:"))
        
        # Grid for display checkboxes
        self.display_layout = QGridLayout()
        layout.addLayout(self.display_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _populate_common_properties(self):
        """Find common properties across selected devices and populate the table."""
        # Get all properties from all devices
        all_properties = {}
        
        for device in self.devices:
            for prop, value in device.properties.items():
                # Skip 'color' and 'icon' properties as they're handled specially
                if prop in ['color', 'icon']:
                    continue
                
                # Track each property and how many devices have it
                if prop not in all_properties:
                    all_properties[prop] = {
                        'count': 1,
                        'values': {str(value): 1},
                        'type': type(value)
                    }
                else:
                    all_properties[prop]['count'] += 1
                    val_str = str(value)
                    if val_str in all_properties[prop]['values']:
                        all_properties[prop]['values'][val_str] += 1
                    else:
                        all_properties[prop]['values'][val_str] = 1
        
        # Add rows for each property
        row = 0
        for prop, data in all_properties.items():
            # Only include properties that exist in all devices
            if data['count'] == len(self.devices):
                self.property_table.insertRow(row)
                
                # Property name (not editable)
                name_item = QTableWidgetItem(prop)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.property_table.setItem(row, 0, name_item)
                
                # Value editor - type depends on property type
                prop_type = data['type']
                
                # Get most common value for this property
                most_common_value = max(data['values'].items(), key=lambda x: x[1])[0]
                
                # For boolean properties, use a checkbox
                if prop_type == bool:
                    cell_widget = QCheckBox()
                    cell_widget.setChecked(most_common_value.lower() in ('true', 'yes', '1'))
                    self.property_table.setCellWidget(row, 1, cell_widget)
                
                # For enum types that have specific values, use combo box
                elif prop in ['routing_protocol', 'inspection_type', 'os', 'provider']:
                    cell_widget = QComboBox()
                    # Add all unique values found across devices
                    for val in data['values'].keys():
                        cell_widget.addItem(val)
                    # Select most common value
                    cell_widget.setCurrentText(most_common_value)
                    self.property_table.setCellWidget(row, 1, cell_widget)
                
                # For other types, use text edit
                else:
                    value_item = QTableWidgetItem(most_common_value)
                    self.property_table.setItem(row, 1, value_item)
                
                # Apply checkbox
                apply_checkbox = QCheckBox()
                apply_checkbox.setChecked(True)  # Default to applying changes
                self.property_table.setCellWidget(row, 2, apply_checkbox)
                
                row += 1
        
        # Add display property checkboxes
        common_display_props = {}
        
        # Find all properties that are being displayed in at least one device
        for device in self.devices:
            if hasattr(device, 'display_properties'):
                for prop, is_displayed in device.display_properties.items():
                    if is_displayed and prop in device.properties:
                        if prop not in common_display_props:
                            common_display_props[prop] = 1
                        else:
                            common_display_props[prop] += 1
        
        # Add checkboxes for display properties
        row, col = 0, 0
        self.display_checkboxes = {}
        
        for prop in all_properties.keys():
            if prop in ['color', 'icon']:
                continue
                
            checkbox = QCheckBox(prop)
            # Check the box if this property is displayed in the majority of devices
            checkbox.setChecked(common_display_props.get(prop, 0) > len(self.devices) / 2)
            self.display_layout.addWidget(checkbox, row, col)
            self.display_checkboxes[prop] = checkbox
            
            col += 1
            if col >= 3:  # 3 checkboxes per row
                col = 0
                row += 1
    
    def get_property_changes(self):
        """Get the property changes from the dialog.
        
        Returns:
            Dictionary mapping device IDs to {property: (old_value, new_value)} dicts
        """
        property_changes = {}
        
        # First, gather all property changes from the table
        property_updates = {}
        
        for row in range(self.property_table.rowCount()):
            # Get property name
            prop_name = self.property_table.item(row, 0).text()
            
            # Check if we should apply this property
            apply_checkbox = self.property_table.cellWidget(row, 2)
            if not apply_checkbox.isChecked():
                continue
            
            # Get the new value
            cell_widget = self.property_table.cellWidget(row, 1)
            
            if isinstance(cell_widget, QCheckBox):
                # Boolean property
                new_value = cell_widget.isChecked()
            elif isinstance(cell_widget, QComboBox):
                # Enum property
                new_value = cell_widget.currentText()
            else:
                # Text property
                new_value = self.property_table.item(row, 1).text()
                
                # Try to convert to the appropriate type
                for device in self.devices:
                    if prop_name in device.properties:
                        old_val = device.properties[prop_name]
                        if isinstance(old_val, int):
                            try:
                                new_value = int(new_value)
                            except ValueError:
                                pass
                        elif isinstance(old_val, float):
                            try:
                                new_value = float(new_value)
                            except ValueError:
                                pass
                        break
            
            # Store the update
            property_updates[prop_name] = new_value
        
        # Now apply these updates to each device
        for device in self.devices:
            device_changes = {}
            
            for prop_name, new_value in property_updates.items():
                if prop_name in device.properties:
                    old_value = device.properties[prop_name]
                    if old_value != new_value:
                        device_changes[prop_name] = (old_value, new_value)
            
            # Handle display properties
            for prop_name, checkbox in self.display_checkboxes.items():
                if prop_name in device.properties:
                    # Initialize display_properties if needed
                    if not hasattr(device, 'display_properties'):
                        device.display_properties = {}
                        
                    # Check if display setting changed
                    old_display = device.display_properties.get(prop_name, False)
                    new_display = checkbox.isChecked()
                    
                    if old_display != new_display:
                        # Store the change in a special property name
                        display_prop = f"_display_{prop_name}"
                        device_changes[display_prop] = (old_display, new_display)
            
            # Only add to changes if there are actually changes for this device
            if device_changes:
                property_changes[device.id] = device_changes
        
        return property_changes
