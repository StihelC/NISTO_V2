import logging
import math
from PyQt5.QtCore import QPointF

from controllers.commands import Command

class AlignDevicesCommand(Command):
    """Command for aligning multiple devices."""
    
    def __init__(self, devices, old_positions, new_positions, description="Align Devices"):
        """Initialize the command.
        
        Args:
            devices: List of devices being aligned
            old_positions: Dictionary of original positions {device: QPointF}
            new_positions: Dictionary of new positions {device: QPointF}
            description: Command description
        """
        super().__init__(description)
        self.devices = devices
        self.old_positions = old_positions
        self.new_positions = new_positions
    
    def execute(self):
        """Execute the command by applying the new positions."""
        for device, pos in self.new_positions.items():
            device.setPos(pos)
        return True
        
    def undo(self):
        """Undo the command by restoring original positions."""
        for device, pos in self.old_positions.items():
            device.setPos(pos)
        return True


class DeviceAlignmentController:
    """Controller for aligning devices on the canvas."""
    
    def __init__(self, event_bus=None, undo_redo_manager=None):
        """Initialize the device alignment controller.
        
        Args:
            event_bus: Event bus for broadcasting events
            undo_redo_manager: Undo/redo manager for command pattern support
        """
        self.event_bus = event_bus
        self.undo_redo_manager = undo_redo_manager
        self.logger = logging.getLogger(__name__)
    
    def align_devices(self, alignment_type, devices):
        """Align the selected devices according to the specified type.
        
        Args:
            alignment_type: String specifying the type of alignment
            devices: List of device objects to align
        """
        if not devices or len(devices) < 2:
            self.logger.warning("At least two devices are required for alignment")
            return
            
        # Save original positions for undo/redo
        original_positions = {device: QPointF(device.scenePos()) for device in devices}
        
        # Dictionary of new positions to apply
        new_positions = {}
        
        # Description for undo/redo command
        command_description = f"Align Devices ({alignment_type})"
        
        # Determine alignment type and calculate new positions
        try:
            # Basic alignments
            if alignment_type == "left":
                self._align_left(devices, new_positions)
            elif alignment_type == "right":
                self._align_right(devices, new_positions)
            elif alignment_type == "top":
                self._align_top(devices, new_positions)
            elif alignment_type == "bottom":
                self._align_bottom(devices, new_positions)
            elif alignment_type == "center_h":
                self._align_center_horizontal(devices, new_positions)
            elif alignment_type == "center_v":
                self._align_center_vertical(devices, new_positions)
            elif alignment_type == "distribute_h":
                self._distribute_horizontal(devices, new_positions)
            elif alignment_type == "distribute_v":
                self._distribute_vertical(devices, new_positions)
            
            # Network layouts
            elif alignment_type == "grid":
                self._arrange_grid(devices, new_positions)
            elif alignment_type == "circle":
                self._arrange_circle(devices, new_positions)
            elif alignment_type == "star":
                self._arrange_star(devices, new_positions)
            elif alignment_type == "bus":
                self._arrange_bus(devices, new_positions)
            
            # NIST RMF related layouts
            elif alignment_type == "dmz":
                self._arrange_dmz(devices, new_positions)
            elif alignment_type == "defense_in_depth":
                self._arrange_defense_in_depth(devices, new_positions)
            elif alignment_type == "segments":
                self._arrange_segmented(devices, new_positions)
            elif alignment_type == "zero_trust":
                self._arrange_zero_trust(devices, new_positions)
            elif alignment_type == "ics_zones":
                self._arrange_ics_zones(devices, new_positions)
            else:
                self.logger.warning(f"Unknown alignment type: {alignment_type}")
                return
        except Exception as e:
            self.logger.error(f"Error during device alignment: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Apply the alignment using command pattern if available
        if self.undo_redo_manager:
            cmd = AlignDevicesCommand(devices, original_positions, new_positions, command_description)
            self.undo_redo_manager.push_command(cmd)
        else:
            # Apply directly without undo/redo support
            for device, pos in new_positions.items():
                device.setPos(pos)
        
        # Notify that devices were aligned
        if self.event_bus:
            self.event_bus.emit("devices_aligned", alignment_type, devices)
    
    # Basic alignment operations
    
    def _align_left(self, devices, new_positions):
        """Align devices to the leftmost device's position."""
        min_x = min(device.scenePos().x() for device in devices)
        
        for device in devices:
            if device.scenePos().x() != min_x:
                new_pos = QPointF(min_x, device.scenePos().y())
                new_positions[device] = new_pos
    
    def _align_right(self, devices, new_positions):
        """Align devices to the rightmost device's position."""
        # Find the rightmost edge considering device width
        max_x = max(device.scenePos().x() + device.boundingRect().width() for device in devices)
        
        for device in devices:
            if device.scenePos().x() + device.boundingRect().width() != max_x:
                new_x = max_x - device.boundingRect().width()
                new_pos = QPointF(new_x, device.scenePos().y())
                new_positions[device] = new_pos
    
    def _align_top(self, devices, new_positions):
        """Align devices to the topmost device's position."""
        min_y = min(device.scenePos().y() for device in devices)
        
        for device in devices:
            if device.scenePos().y() != min_y:
                new_pos = QPointF(device.scenePos().x(), min_y)
                new_positions[device] = new_pos
    
    def _align_bottom(self, devices, new_positions):
        """Align devices to the bottommost device's position."""
        # Find the bottommost edge considering device height
        max_y = max(device.scenePos().y() + device.boundingRect().height() for device in devices)
        
        for device in devices:
            if device.scenePos().y() + device.boundingRect().height() != max_y:
                new_y = max_y - device.boundingRect().height()
                new_pos = QPointF(device.scenePos().x(), new_y)
                new_positions[device] = new_pos
    
    def _align_center_horizontal(self, devices, new_positions):
        """Align devices to the horizontal center of the selection."""
        # Calculate the center y-coordinate
        total_y = 0
        for device in devices:
            total_y += device.scenePos().y() + (device.boundingRect().height() / 2)
        
        center_y = total_y / len(devices)
        
        for device in devices:
            current_center_y = device.scenePos().y() + (device.boundingRect().height() / 2)
            if current_center_y != center_y:
                new_y = center_y - (device.boundingRect().height() / 2)
                new_pos = QPointF(device.scenePos().x(), new_y)
                new_positions[device] = new_pos
    
    def _align_center_vertical(self, devices, new_positions):
        """Align devices to the vertical center of the selection."""
        # Calculate the center x-coordinate
        total_x = 0
        for device in devices:
            total_x += device.scenePos().x() + (device.boundingRect().width() / 2)
        
        center_x = total_x / len(devices)
        
        for device in devices:
            current_center_x = device.scenePos().x() + (device.boundingRect().width() / 2)
            if current_center_x != center_x:
                new_x = center_x - (device.boundingRect().width() / 2)
                new_pos = QPointF(new_x, device.scenePos().y())
                new_positions[device] = new_pos
    
    def _distribute_horizontal(self, devices, new_positions):
        """Distribute devices evenly in the horizontal space they occupy."""
        if len(devices) <= 2:
            return  # Need more than 2 devices to distribute
            
        # Sort devices by x position
        sorted_devices = sorted(devices, key=lambda d: d.scenePos().x())
        
        # Find total width
        leftmost = sorted_devices[0].scenePos().x()
        rightmost = sorted_devices[-1].scenePos().x() + sorted_devices[-1].boundingRect().width()
        
        # Calculate equal spacing
        total_space = rightmost - leftmost
        spacing = total_space / (len(devices) - 1)
        
        # Position each device (except first and last)
        for i in range(1, len(sorted_devices) - 1):
            device = sorted_devices[i]
            new_x = leftmost + i * spacing - (device.boundingRect().width() / 2)
            new_pos = QPointF(new_x, device.scenePos().y())
            new_positions[device] = new_pos
    
    def _distribute_vertical(self, devices, new_positions):
        """Distribute devices evenly in the vertical space they occupy."""
        if len(devices) <= 2:
            return  # Need more than 2 devices to distribute
            
        # Sort devices by y position
        sorted_devices = sorted(devices, key=lambda d: d.scenePos().y())
        
        # Find total height
        topmost = sorted_devices[0].scenePos().y()
        bottommost = sorted_devices[-1].scenePos().y() + sorted_devices[-1].boundingRect().height()
        
        # Calculate equal spacing
        total_space = bottommost - topmost
        spacing = total_space / (len(devices) - 1)
        
        # Position each device (except first and last)
        for i in range(1, len(sorted_devices) - 1):
            device = sorted_devices[i]
            new_y = topmost + i * spacing - (device.boundingRect().height() / 2)
            new_pos = QPointF(device.scenePos().x(), new_y)
            new_positions[device] = new_pos
    
    # Network layouts
    
    def _arrange_grid(self, devices, new_positions):
        """Arrange devices in a grid pattern."""
        # Calculate grid dimensions
        device_count = len(devices)
        cols = max(2, int(math.sqrt(device_count)))
        rows = (device_count + cols - 1) // cols  # Ceiling division
        
        # Find average device size for spacing
        avg_width = sum(device.boundingRect().width() for device in devices) / device_count
        avg_height = sum(device.boundingRect().height() for device in devices) / device_count
        
        # Calculate spacing
        h_spacing = avg_width * 1.5
        v_spacing = avg_height * 1.5
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        
        # Calculate top-left corner of grid
        start_x = center_x - (cols * h_spacing / 2)
        start_y = center_y - (rows * v_spacing / 2)
        
        # Position each device
        for i, device in enumerate(devices):
            row = i // cols
            col = i % cols
            
            new_x = start_x + (col * h_spacing)
            new_y = start_y + (row * v_spacing)
            
            new_positions[device] = QPointF(new_x, new_y)
    
    def _arrange_circle(self, devices, new_positions):
        """Arrange devices in a circular pattern."""
        device_count = len(devices)
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        center = QPointF(center_x, center_y)
        
        # Calculate appropriate radius based on device sizes
        avg_size = sum(max(device.boundingRect().width(), device.boundingRect().height()) 
                     for device in devices) / device_count
        radius = max(avg_size * 2, device_count * avg_size / (2 * math.pi))
        
        # Position devices around the circle
        for i, device in enumerate(devices):
            angle = (2 * math.pi * i) / device_count
            
            # Calculate position offset by device dimensions
            new_x = center.x() + radius * math.cos(angle) - (device.boundingRect().width() / 2)
            new_y = center.y() + radius * math.sin(angle) - (device.boundingRect().height() / 2)
            
            new_positions[device] = QPointF(new_x, new_y)
    
    def _arrange_star(self, devices, new_positions):
        """Arrange devices in a star pattern (one center, others around)."""
        if len(devices) < 3:
            return  # Need at least 3 devices for a meaningful star
            
        device_count = len(devices)
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        center = QPointF(center_x, center_y)
        
        # Calculate appropriate radius
        avg_size = sum(max(device.boundingRect().width(), device.boundingRect().height()) 
                     for device in devices) / device_count
        radius = max(avg_size * 2, (device_count - 1) * avg_size / (2 * math.pi))
        
        # First device goes to the center
        center_device = devices[0]
        new_positions[center_device] = QPointF(
            center.x() - (center_device.boundingRect().width() / 2),
            center.y() - (center_device.boundingRect().height() / 2)
        )
        
        # Remaining devices go around in a circle
        outer_devices = devices[1:]
        for i, device in enumerate(outer_devices):
            angle = (2 * math.pi * i) / len(outer_devices)
            
            new_x = center.x() + radius * math.cos(angle) - (device.boundingRect().width() / 2)
            new_y = center.y() + radius * math.sin(angle) - (device.boundingRect().height() / 2)
            
            new_positions[device] = QPointF(new_x, new_y)
    
    def _arrange_bus(self, devices, new_positions):
        """Arrange devices in a horizontal bus pattern."""
        device_count = len(devices)
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        
        # Calculate appropriate spacing
        avg_width = sum(device.boundingRect().width() for device in devices) / device_count
        spacing = avg_width * 1.5
        
        # Calculate total width of the bus
        total_width = spacing * (device_count - 1)
        start_x = center_x - (total_width / 2)
        
        # Position each device
        for i, device in enumerate(devices):
            new_x = start_x + (i * spacing) - (device.boundingRect().width() / 2)
            new_positions[device] = QPointF(new_x, center_y - (device.boundingRect().height() / 2))
    
    # NIST RMF related layouts
    
    def _arrange_dmz(self, devices, new_positions):
        """Arrange devices in a DMZ (perimeter defense) architecture."""
        if len(devices) < 3:
            return  # Need at least 3 devices for a meaningful DMZ
            
        device_count = len(devices)
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        
        # Calculate average device size for spacing
        avg_width = sum(device.boundingRect().width() for device in devices) / device_count
        avg_height = sum(device.boundingRect().height() for device in devices) / device_count
        
        # Spacing between zones
        zone_spacing = avg_width * 3
        
        # Divide devices into three zones (internal, DMZ, external)
        zone_devices = [[], [], []]  # Internal, DMZ, External
        
        # Distribute devices to zones
        for i, device in enumerate(devices):
            zone_idx = min(2, i * 3 // device_count)  # Ensure proper distribution across zones
            zone_devices[zone_idx].append(device)
        
        # Position devices in the internal zone (left side)
        internal_count = len(zone_devices[0])
        if internal_count > 0:
            internal_x = center_x - zone_spacing
            self._position_zone_devices(
                zone_devices[0], internal_x, center_y, 
                avg_width, avg_height, new_positions
            )
        
        # Position devices in the DMZ (middle)
        dmz_count = len(zone_devices[1])
        if dmz_count > 0:
            self._position_zone_devices(
                zone_devices[1], center_x, center_y, 
                avg_width, avg_height, new_positions
            )
        
        # Position devices in the external zone (right side)
        external_count = len(zone_devices[2])
        if external_count > 0:
            external_x = center_x + zone_spacing
            self._position_zone_devices(
                zone_devices[2], external_x, center_y, 
                avg_width, avg_height, new_positions
            )
    
    def _position_zone_devices(self, devices, center_x, center_y, avg_width, avg_height, new_positions):
        """Helper to position devices within a zone."""
        count = len(devices)
        
        if count == 1:
            # Single device centered
            device = devices[0]
            new_positions[device] = QPointF(
                center_x - device.boundingRect().width()/2,
                center_y - device.boundingRect().height()/2
            )
        else:
            # Multiple devices in a grid or vertical line
            cols = min(2, count)
            rows = (count + cols - 1) // cols
            
            # Calculate grid dimensions
            h_spacing = avg_width * 1.5
            v_spacing = avg_height * 1.5
            
            # Start position
            start_x = center_x - ((cols - 1) * h_spacing / 2)
            start_y = center_y - ((rows - 1) * v_spacing / 2)
            
            # Position each device
            for i, device in enumerate(devices):
                row = i // cols
                col = i % cols
                
                device_x = start_x + (col * h_spacing) - (device.boundingRect().width() / 2)
                device_y = start_y + (row * v_spacing) - (device.boundingRect().height() / 2)
                
                new_positions[device] = QPointF(device_x, device_y)
    
    def _arrange_defense_in_depth(self, devices, new_positions):
        """Arrange devices in concentric layers (defense-in-depth)."""
        device_count = len(devices)
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        center = QPointF(center_x, center_y)
        
        # Calculate average device size for spacing
        avg_size = sum(max(device.boundingRect().width(), device.boundingRect().height()) 
                       for device in devices) / device_count
        
        # Determine number of layers (3-4 based on device count)
        max_layers = min(4, max(3, device_count // 3))
        
        # Calculate devices per layer
        devices_per_layer = []
        remaining = device_count
        
        for layer in range(max_layers):
            # Outer layers get more devices
            layer_factor = layer + 1  # More devices in outer layers
            layer_count = min(remaining, max(1, int(device_count * layer_factor / (max_layers * (max_layers + 1) / 2))))
            devices_per_layer.append(layer_count)
            remaining -= layer_count
        
        # Ensure all devices are allocated
        devices_per_layer[-1] += remaining
        
        # Sort devices by property if available (more critical in inner layers)
        try:
            sorted_devices = sorted(
                devices, 
                key=lambda d: int(d.properties.get("priority", "5")),
                reverse=True  # Higher priority (lower number) in center
            )
        except (AttributeError, KeyError, ValueError):
            # If sorting fails, just use the original order
            sorted_devices = devices
        
        # Start positioning from the innermost layer outward
        device_index = 0
        
        for layer in range(max_layers):
            layer_devices = sorted_devices[device_index:device_index + devices_per_layer[layer]]
            device_index += devices_per_layer[layer]
            
            # Calculate radius based on layer
            radius = (layer + 1) * avg_size * 1.5
            
            # Position devices in this layer in a circle
            for i, device in enumerate(layer_devices):
                angle = (2 * math.pi * i) / len(layer_devices)
                
                new_x = center.x() + radius * math.cos(angle) - (device.boundingRect().width() / 2)
                new_y = center.y() + radius * math.sin(angle) - (device.boundingRect().height() / 2)
                
                new_positions[device] = QPointF(new_x, new_y)
    
    def _arrange_segmented(self, devices, new_positions):
        """Arrange devices in network segments."""
        device_count = len(devices)
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        
        # Calculate average device size for spacing
        avg_width = sum(device.boundingRect().width() for device in devices) / device_count
        avg_height = sum(device.boundingRect().height() for device in devices) / device_count
        
        # Calculate number of segments based on device count
        segment_count = min(4, max(2, device_count // 3))
        
        # Try to group devices by similar properties if available
        segments = [[] for _ in range(segment_count)]
        
        # Check if devices have a 'segment' property
        has_segment_prop = False
        for device in devices:
            if hasattr(device, 'properties') and 'segment' in device.properties:
                has_segment_prop = True
                break
        
        if has_segment_prop:
            # Group by segment property
            for device in devices:
                segment_id = int(device.properties.get('segment', 0)) % segment_count
                segments[segment_id].append(device)
        else:
            # Simple distribution
            for i, device in enumerate(devices):
                segment_id = i % segment_count
                segments[segment_id].append(device)
        
        # Position each segment
        segment_spacing = avg_width * 4
        
        # Start position
        start_x = center_x - ((segment_count - 1) * segment_spacing / 2)
        
        for seg_idx, segment_devices in enumerate(segments):
            if not segment_devices:
                continue
                
            # Position for this segment
            segment_x = start_x + (seg_idx * segment_spacing)
            
            # Arrange devices in this segment in a grid
            seg_count = len(segment_devices)
            seg_cols = min(2, seg_count)
            seg_rows = (seg_count + seg_cols - 1) // seg_cols
            
            # Calculate grid dimensions
            h_spacing = avg_width * 1.5
            v_spacing = avg_height * 1.5
            
            # Calculate starting position for this segment's grid
            seg_start_x = segment_x - ((seg_cols - 1) * h_spacing / 2)
            seg_start_y = center_y - ((seg_rows - 1) * v_spacing / 2)
            
            # Position each device within the segment
            for i, device in enumerate(segment_devices):
                row = i // seg_cols
                col = i % seg_cols
                
                device_x = seg_start_x + (col * h_spacing) - (device.boundingRect().width() / 2)
                device_y = seg_start_y + (row * v_spacing) - (device.boundingRect().height() / 2)
                
                new_positions[device] = QPointF(device_x, device_y)
    
    def _arrange_zero_trust(self, devices, new_positions):
        """Arrange devices in a zero trust architecture with microsegments."""
        device_count = len(devices)
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        
        # Calculate average device size for spacing
        avg_size = sum(max(device.boundingRect().width(), device.boundingRect().height()) 
                       for device in devices) / device_count
        
        # Calculate number of microsegments
        segment_count = min(6, max(3, device_count // 2))
        
        # Group devices into microsegments
        segments = [[] for _ in range(segment_count)]
        
        # Try to group by function/type if available
        for i, device in enumerate(devices):
            # Could use device type or a 'function' property if available
            if hasattr(device, 'device_type'):
                segment_id = hash(device.device_type) % segment_count
            else:
                segment_id = i % segment_count
            segments[segment_id].append(device)
        
        # Position the microsegments in a larger circle
        segment_radius = avg_size * 4
        
        for seg_idx, segment_devices in enumerate(segments):
            if not segment_devices:
                continue
                
            # Calculate position for this microsegment
            segment_angle = (2 * math.pi * seg_idx) / segment_count
            segment_x = center_x + segment_radius * math.cos(segment_angle)
            segment_y = center_y + segment_radius * math.sin(segment_angle)
            
            # Position devices in this microsegment in a small circle or grid
            seg_count = len(segment_devices)
            
            if seg_count <= 3:
                # Small circle for few devices
                inner_radius = avg_size * 1.2
                
                for i, device in enumerate(segment_devices):
                    inner_angle = (2 * math.pi * i) / seg_count
                    
                    device_x = segment_x + inner_radius * math.cos(inner_angle) - (device.boundingRect().width() / 2)
                    device_y = segment_y + inner_radius * math.sin(inner_angle) - (device.boundingRect().height() / 2)
                    
                    new_positions[device] = QPointF(device_x, device_y)
            else:
                # Grid for more devices
                seg_cols = min(2, seg_count)
                seg_rows = (seg_count + seg_cols - 1) // seg_cols
                
                # Calculate grid dimensions
                h_spacing = avg_size * 1.2
                v_spacing = avg_size * 1.2
                
                # Calculate starting position for this segment's grid
                seg_start_x = segment_x - ((seg_cols - 1) * h_spacing / 2)
                seg_start_y = segment_y - ((seg_rows - 1) * v_spacing / 2)
                
                # Position each device within the segment
                for i, device in enumerate(segment_devices):
                    row = i // seg_cols
                    col = i % seg_cols
                    
                    device_x = seg_start_x + (col * h_spacing) - (device.boundingRect().width() / 2)
                    device_y = seg_start_y + (row * v_spacing) - (device.boundingRect().height() / 2)
                    
                    new_positions[device] = QPointF(device_x, device_y)
    
    def _arrange_ics_zones(self, devices, new_positions):
        """Arrange devices in an industrial control system (ICS) architecture."""
        device_count = len(devices)
        
        # Find center of all devices
        center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in devices) / device_count
        center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in devices) / device_count
        
        # Calculate average device size for spacing
        avg_width = sum(device.boundingRect().width() for device in devices) / device_count
        avg_height = sum(device.boundingRect().height() for device in devices) / device_count
        
        # Define the ICS zones (Enterprise, DMZ, Control, Field)
        zones = ["Enterprise", "DMZ", "Control", "Field"]
        zone_count = len(zones)
        
        # Group devices into zones - try to use properties if available
        zone_devices = [[] for _ in range(zone_count)]
        
        # Check if devices have a 'zone' property
        has_zone_prop = False
        for device in devices:
            if hasattr(device, 'properties') and 'zone' in device.properties:
                has_zone_prop = True
                break
        
        if has_zone_prop:
            # Group by zone property
            for device in devices:
                zone_name = device.properties.get('zone', '').lower()
                zone_id = next((i for i, z in enumerate(zones) if z.lower() in zone_name), i % zone_count)
                zone_devices[zone_id].append(device)
        else:
            # Distribute evenly
            devices_per_zone = device_count // zone_count
            remainder = device_count % zone_count
            
            device_idx = 0
            for zone_idx in range(zone_count):
                count = devices_per_zone + (1 if zone_idx < remainder else 0)
                zone_devices[zone_idx] = devices[device_idx:device_idx + count]
                device_idx += count
        
        # Position zones vertically (Enterprise at top, Field at bottom)
        zone_spacing = avg_height * 3
        
        # Start position
        start_y = center_y - ((zone_count - 1) * zone_spacing / 2)
        
        for zone_idx, zone_devices_list in enumerate(zone_devices):
            if not zone_devices_list:
                continue
                
            # Position for this zone
            zone_y = start_y + (zone_idx * zone_spacing)
            
            # Arrange devices in this zone horizontally
            zone_count = len(zone_devices_list)
            
            # Calculate spacing
            h_spacing = avg_width * 1.5
            
            # Calculate starting position
            zone_start_x = center_x - ((zone_count - 1) * h_spacing / 2)
            
            # Position each device within the zone
            for i, device in enumerate(zone_devices_list):
                device_x = zone_start_x + (i * h_spacing) - (device.boundingRect().width() / 2)
                device_y = zone_y - (device.boundingRect().height() / 2)
                
                new_positions[device] = QPointF(device_x, device_y)
