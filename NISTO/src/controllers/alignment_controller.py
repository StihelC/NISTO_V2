"""
Controller for managing device alignment operations.
"""
import logging
from PyQt5.QtCore import QObject, QPointF

class AlignmentController(QObject):
    """Controller for aligning selected devices on the canvas."""
    
    def __init__(self, canvas, event_bus=None, undo_redo_manager=None):
        super().__init__()
        self.canvas = canvas
        self.event_bus = event_bus
        self.undo_redo_manager = undo_redo_manager
        self.logger = logging.getLogger(__name__)
    
    def get_selected_devices(self):
        """Get all selected devices from the canvas."""
        return [item for item in self.canvas.scene().selectedItems() 
                if item in self.canvas.devices]
    
    def align_left(self):
        """Align selected devices to the leftmost device."""
        devices = self.get_selected_devices()
        if len(devices) < 2:
            return False
        
        # Find leftmost position
        left_pos = min(device.scenePos().x() for device in devices)
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Move all devices to align with leftmost
        for device in devices:
            new_pos = QPointF(left_pos, device.scenePos().y())
            device.setPos(new_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='left'
            )
        
        self.canvas.viewport().update()
        return True
    
    def align_right(self):
        """Align selected devices to the rightmost device."""
        devices = self.get_selected_devices()
        if len(devices) < 2:
            return False
        
        # Find rightmost position (considering device width)
        right_positions = [(device.scenePos().x() + device.width) for device in devices]
        right_pos = max(right_positions)
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Move all devices to align with rightmost
        for device in devices:
            new_x = right_pos - device.width
            new_pos = QPointF(new_x, device.scenePos().y())
            device.setPos(new_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='right'
            )
        
        self.canvas.viewport().update()
        return True
    
    def align_top(self):
        """Align selected devices to the topmost device."""
        devices = self.get_selected_devices()
        if len(devices) < 2:
            return False
        
        # Find topmost position
        top_pos = min(device.scenePos().y() for device in devices)
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Move all devices to align with topmost
        for device in devices:
            new_pos = QPointF(device.scenePos().x(), top_pos)
            device.setPos(new_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='top'
            )
        
        self.canvas.viewport().update()
        return True
    
    def align_bottom(self):
        """Align selected devices to the bottommost device."""
        devices = self.get_selected_devices()
        if len(devices) < 2:
            return False
        
        # Find bottommost position (considering device height)
        bottom_positions = [(device.scenePos().y() + device.height) for device in devices]
        bottom_pos = max(bottom_positions)
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Move all devices to align with bottommost
        for device in devices:
            new_y = bottom_pos - device.height
            new_pos = QPointF(device.scenePos().x(), new_y)
            device.setPos(new_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='bottom'
            )
        
        self.canvas.viewport().update()
        return True
    
    def align_center_horizontal(self):
        """Align selected devices to their horizontal center."""
        devices = self.get_selected_devices()
        if len(devices) < 2:
            return False
        
        # Calculate average x position (center)
        all_center_x = sum(device.scenePos().x() + device.width / 2 for device in devices) / len(devices)
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Move all devices to align with center
        for device in devices:
            new_x = all_center_x - device.width / 2
            new_pos = QPointF(new_x, device.scenePos().y())
            device.setPos(new_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='center_horizontal'
            )
        
        self.canvas.viewport().update()
        return True
    
    def align_center_vertical(self):
        """Align selected devices to their vertical center."""
        devices = self.get_selected_devices()
        if len(devices) < 2:
            return False
        
        # Calculate average y position (center)
        all_center_y = sum(device.scenePos().y() + device.height / 2 for device in devices) / len(devices)
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Move all devices to align with center
        for device in devices:
            new_y = all_center_y - device.height / 2
            new_pos = QPointF(device.scenePos().x(), new_y)
            device.setPos(new_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='center_vertical'
            )
        
        self.canvas.viewport().update()
        return True
    
    def distribute_horizontally(self):
        """Distribute selected devices horizontally with even spacing."""
        devices = self.get_selected_devices()
        if len(devices) < 3:
            return False
        
        # Sort devices by x position
        sorted_devices = sorted(devices, key=lambda d: d.scenePos().x())
        
        # Calculate total width to be distributed
        left_pos = sorted_devices[0].scenePos().x()
        right_pos = sorted_devices[-1].scenePos().x() + sorted_devices[-1].width
        total_width = right_pos - left_pos
        
        # Calculate equal spacing between devices
        total_device_width = sum(device.width for device in sorted_devices)
        spacing = (total_width - total_device_width) / (len(sorted_devices) - 1)
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Don't move the leftmost and rightmost devices
        current_x = left_pos
        for i, device in enumerate(sorted_devices):
            if i == 0:
                current_x += device.width + spacing
                continue
            elif i == len(sorted_devices) - 1:
                continue
            else:
                new_pos = QPointF(current_x, device.scenePos().y())
                device.setPos(new_pos)
                device.update_connections()
                current_x += device.width + spacing
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='distribute_horizontally'
            )
        
        self.canvas.viewport().update()
        return True
    
    def distribute_vertically(self):
        """Distribute selected devices vertically with even spacing."""
        devices = self.get_selected_devices()
        if len(devices) < 3:
            return False
        
        # Sort devices by y position
        sorted_devices = sorted(devices, key=lambda d: d.scenePos().y())
        
        # Calculate total height to be distributed
        top_pos = sorted_devices[0].scenePos().y()
        bottom_pos = sorted_devices[-1].scenePos().y() + sorted_devices[-1].height
        total_height = bottom_pos - top_pos
        
        # Calculate equal spacing between devices
        total_device_height = sum(device.height for device in sorted_devices)
        spacing = (total_height - total_device_height) / (len(sorted_devices) - 1)
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Don't move the topmost and bottommost devices
        current_y = top_pos
        for i, device in enumerate(sorted_devices):
            if i == 0:
                current_y += device.height + spacing
                continue
            elif i == len(sorted_devices) - 1:
                continue
            else:
                new_pos = QPointF(device.scenePos().x(), current_y)
                device.setPos(new_pos)
                device.update_connections()
                current_y += device.height + spacing
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='distribute_vertically'
            )
        
        self.canvas.viewport().update()
        return True
