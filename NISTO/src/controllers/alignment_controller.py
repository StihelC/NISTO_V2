"""
Controller for managing device alignment operations.
"""
import logging
from PyQt5.QtCore import QObject, QPointF
from collections import defaultdict

class AlignmentController(QObject):
    """Controller for aligning selected devices on the canvas."""
    
    def __init__(self, canvas, event_bus=None, undo_redo_manager=None):
        super().__init__()
        self.canvas = canvas
        self.event_bus = event_bus
        self.undo_redo_manager = undo_redo_manager
        self.logger = logging.getLogger(__name__)
        
        # Configuration parameters for alignment
        self.CONFIG = {
            'min_spacing': 60,           # Minimum spacing between devices (pixels)
            'connection_padding': 30,     # Additional padding for connections and labels
            'grid_spacing_x': 150,        # Default grid spacing for X (pixels)
            'grid_spacing_y': 120,        # Default grid spacing for Y (pixels)
            'snap_threshold': 10,         # Snap to grid threshold (pixels)
            'orthogonal_spacing': 120,    # Spacing for orthogonal layouts
            'layer_spacing_y': 180,       # Vertical spacing between layers
            'bus_spacing': 150,           # Spacing for bus topology
        }
    
    def get_selected_devices(self):
        """Get all selected devices from the canvas."""
        return [item for item in self.canvas.scene().selectedItems() 
                if item in self.canvas.devices]
    
    def align_left(self):
        """Align selected devices to the leftmost device with a minimum separation."""
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
        
        # Calculate total available width
        left_pos = sorted_devices[0].scenePos().x()
        right_pos = sorted_devices[-1].scenePos().x() + sorted_devices[-1].width
        total_width = right_pos - left_pos
        
        # Calculate space needed for all devices
        total_device_width = sum(device.width for device in sorted_devices)
        
        # Calculate space available for distribution
        available_space = max(0, total_width - total_device_width)
        
        # Calculate equal spacing between devices (with minimum spacing)
        spacing = max(self.CONFIG['min_spacing'], available_space / (len(sorted_devices) - 1))
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Position devices with the calculated spacing
        current_x = left_pos
        for i, device in enumerate(sorted_devices):
            if i == 0:
                # Don't move the leftmost device
                current_x = left_pos + device.width + spacing
                continue
            elif i == len(sorted_devices) - 1:
                # Don't move the rightmost device
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
        
        # Calculate total available height
        top_pos = sorted_devices[0].scenePos().y()
        bottom_pos = sorted_devices[-1].scenePos().y() + sorted_devices[-1].height
        total_height = bottom_pos - top_pos
        
        # Calculate space needed for all devices
        total_device_height = sum(device.height for device in sorted_devices)
        
        # Calculate space available for distribution
        available_space = max(0, total_height - total_device_height)
        
        # Calculate equal spacing between devices (with minimum spacing)
        spacing = max(self.CONFIG['min_spacing'], available_space / (len(sorted_devices) - 1))
        
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Position devices with the calculated spacing
        current_y = top_pos
        for i, device in enumerate(sorted_devices):
            if i == 0:
                # Don't move the topmost device
                current_y = top_pos + device.height + spacing
                continue
            elif i == len(sorted_devices) - 1:
                # Don't move the bottommost device
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
    
    def arrange_in_grid(self):
        """Arrange selected devices in a grid pattern."""
        devices = self.get_selected_devices()
        if len(devices) < 4:  # Minimum number for a grid to make sense
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Calculate average device dimensions
        avg_width = sum(device.width for device in devices) / len(devices)
        avg_height = sum(device.height for device in devices) / len(devices)
        
        # Calculate grid dimensions with spacing
        grid_spacing_x = max(avg_width * 1.5, self.CONFIG['grid_spacing_x'])
        grid_spacing_y = max(avg_height * 1.5, self.CONFIG['grid_spacing_y'])
        
        # Calculate number of columns based on the square root of the number of devices
        import math
        cols = max(2, round(math.sqrt(len(devices))))
        rows = math.ceil(len(devices) / cols)
        
        # Find the top-left position (using the leftmost, topmost device)
        top = min(device.scenePos().y() for device in devices)
        left = min(device.scenePos().x() for device in devices)
        start_pos = QPointF(left, top)
        
        # Place devices in a grid
        for i, device in enumerate(devices):
            row = i // cols
            col = i % cols
            
            new_pos = QPointF(
                start_pos.x() + col * grid_spacing_x,
                start_pos.y() + row * grid_spacing_y
            )
            
            device.setPos(new_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='grid'
            )
        
        self.canvas.viewport().update()
        return True
    
    def arrange_in_circle(self):
        """Arrange selected devices in a circle pattern."""
        devices = self.get_selected_devices()
        if len(devices) < 3:  # Need at least 3 devices for a circle
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Find center point of all devices
        center_x = sum(device.scenePos().x() + device.width/2 for device in devices) / len(devices)
        center_y = sum(device.scenePos().y() + device.height/2 for device in devices) / len(devices)
        center = QPointF(center_x, center_y)
        
        # Calculate radius based on number of devices and average device size
        avg_device_size = sum(max(device.width, device.height) for device in devices) / len(devices)
        radius = max(len(devices) * avg_device_size / (2 * 3.14159), 200)  # Minimum radius
        
        # Place devices in a circle
        import math
        for i, device in enumerate(devices):
            angle = 2 * math.pi * i / len(devices)
            
            # Calculate position on the circle
            x = center.x() + radius * math.cos(angle) - device.width/2
            y = center.y() + radius * math.sin(angle) - device.height/2
            
            new_pos = QPointF(x, y)
            device.setPos(new_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='circle'
            )
        
        self.canvas.viewport().update()
        return True
        
    def arrange_by_type(self):
        """Group and arrange devices by their type."""
        devices = self.get_selected_devices()
        if len(devices) < 2:
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Group devices by type
        groups = defaultdict(list)
        for device in devices:
            device_type = getattr(device, 'device_type', 'unknown')
            groups[device_type].append(device)
        
        # Calculate grid dimensions
        grid_spacing_x = self.CONFIG['grid_spacing_x']
        grid_spacing_y = self.CONFIG['grid_spacing_y']
        
        # Find top-left starting position
        top = min(device.scenePos().y() for device in devices)
        left = min(device.scenePos().x() for device in devices)
        
        # Arrange each group in a row
        current_y = top
        for device_type, group_devices in groups.items():
            # Sort devices in each group by name for consistent ordering
            sorted_group = sorted(group_devices, key=lambda d: getattr(d, 'name', ''))
            
            # Arrange devices in this group horizontally
            current_x = left
            for device in sorted_group:
                device.setPos(QPointF(current_x, current_y))
                device.update_connections()
                current_x += device.width + grid_spacing_x
            
            # Move to the next row for the next group
            tallest_in_group = max(device.height for device in group_devices)
            current_y += tallest_in_group + grid_spacing_y
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='by_type'
            )
        
        self.canvas.viewport().update()
        return True
        
    def arrange_hierarchical(self):
        """Arrange devices in a hierarchical tree structure based on connections."""
        devices = self.get_selected_devices()
        if len(devices) < 2:
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Build connection graph
        connection_map = defaultdict(list)
        devices_set = set(devices)
        
        # Get all connections between the selected devices
        for device in devices:
            for connection in device.connections:
                source = connection.source_device
                target = connection.target_device
                
                if source in devices_set and target in devices_set:
                    # Add both directions to easily find neighbors
                    connection_map[source].append(target)
                    connection_map[target].append(source)
        
        # Calculate a heuristic score to find potential root devices
        # Devices with more connections are more likely to be central
        device_scores = {device: len(connection_map.get(device, [])) for device in devices}
        
        # Choose the device with the highest score as root
        root_device = max(device_scores.items(), key=lambda x: x[1])[0]
        
        # Function to place a device and its neighbors recursively
        def place_subtree(device, x, y, level, visited):
            if device in visited:
                return
                
            visited.add(device)
            
            # Place this device
            new_pos = QPointF(x, y)
            device.setPos(new_pos)
            device.update_connections()
            
            # Get connected neighbors not yet visited
            neighbors = [d for d in connection_map.get(device, []) if d not in visited]
            
            if not neighbors:
                return
                
            # Calculate spacing for this level
            level_spacing = 150 + (level * 30)  # Increase spacing with depth
            
            # Place neighbors
            total_width = len(neighbors) * level_spacing
            start_x = x - (total_width / 2) + (level_spacing / 2)
            
            for i, neighbor in enumerate(neighbors):
                neighbor_x = start_x + i * level_spacing
                neighbor_y = y + 150  # Vertical spacing between levels
                place_subtree(neighbor, neighbor_x, neighbor_y, level + 1, visited)
        
        # Start placing from the root
        center_x = sum(device.scenePos().x() for device in devices) / len(devices)
        top_y = min(device.scenePos().y() for device in devices)
        place_subtree(root_device, center_x, top_y, 0, set())
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='hierarchical'
            )
        
        self.canvas.viewport().update()
        return True

    def align_orthogonal_layers(self):
        """Arrange devices in horizontal layers with optimized orthogonal connections."""
        devices = self.get_selected_devices()
        if len(devices) < 4:  # Need enough devices for meaningful layers
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Find all connections between selected devices
        connections = []
        device_set = set(devices)
        
        for device in devices:
            for connection in getattr(device, 'connections', []):
                source = connection.source_device
                target = connection.target_device
                if source in device_set and target in device_set and source != target:
                    connections.append((source, target, connection))
        
        # Analyze connection topology to determine device layers
        # This uses a simple algorithm to group devices by connectivity
        layers = self._determine_device_layers(devices, connections)
        
        # Calculate layout dimensions
        spacing_x = self.CONFIG['orthogonal_spacing']
        spacing_y = self.CONFIG['layer_spacing_y']
        
        # Get top-left starting position
        top = min(device.scenePos().y() for device in devices)
        left = min(device.scenePos().x() for device in devices)
        
        # Position devices by layer
        for layer_idx, layer_devices in enumerate(layers):
            # Sort devices in each layer by connectivity density
            # This helps place more connected devices in the center
            layer_devices.sort(key=lambda d: sum(1 for c in connections if d in (c[0], c[1])))
            
            # Calculate total width needed for this layer
            layer_width = sum(d.width for d in layer_devices) + spacing_x * (len(layer_devices) - 1)
            
            # Position devices in this layer
            current_x = left + (layer_width / 2) - (sum(d.width for d in layer_devices) / 2)
            layer_y = top + layer_idx * spacing_y
            
            for device in layer_devices:
                device.setPos(QPointF(current_x, layer_y))
                current_x += device.width + spacing_x
                device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='orthogonal_layers'
            )
        
        self.canvas.viewport().update()
        return True
    
    def _determine_device_layers(self, devices, connections):
        """Group devices into logical layers based on connection patterns."""
        # Create connection graph
        graph = defaultdict(set)
        for src, tgt, _ in connections:
            graph[src].add(tgt)
            graph[tgt].add(src)  # Bidirectional
            
        # Find potential root nodes (devices with most connections)
        connection_counts = {d: len(graph.get(d, set())) for d in devices}
        sorted_devices = sorted(devices, key=lambda d: connection_counts.get(d, 0), reverse=True)
        
        # Create layers starting from top devices
        layers = []
        assigned_devices = set()
        
        # First layer: devices with most connections
        first_layer = [sorted_devices[0]]  # Start with the most connected device
        # Add devices with similar connection count to the first layer
        threshold = connection_counts[sorted_devices[0]] * 0.8  # 80% threshold
        for device in sorted_devices[1:5]:  # Consider up to 5 top devices
            if connection_counts.get(device, 0) >= threshold:
                first_layer.append(device)
                
        layers.append(first_layer)
        assigned_devices.update(first_layer)
        
        # Build subsequent layers based on connections to previous layer
        max_layers = 5  # Limit to prevent too many layers
        for i in range(max_layers):
            if len(assigned_devices) == len(devices):
                break
                
            current_layer = []
            for prev_device in layers[-1]:
                for connected in graph.get(prev_device, set()):
                    if connected not in assigned_devices:
                        current_layer.append(connected)
                        assigned_devices.add(connected)
            
            if current_layer:
                layers.append(current_layer)
            else:
                # Add any remaining unassigned devices to a final layer
                remaining = [d for d in devices if d not in assigned_devices]
                if remaining:
                    layers.append(remaining)
                    assigned_devices.update(remaining)
        
        return layers
    
    def optimize_orthogonal_layout(self):
        """Optimize device positions for cleaner orthogonal connections."""
        devices = self.get_selected_devices()
        if len(devices) < 3:
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Group devices by approximate vertical position (rows)
        row_tolerance = 60  # Devices within this vertical distance are considered in the same row
        rows = defaultdict(list)
        
        # Get y positions and sort devices into rows
        all_y_pos = sorted([device.scenePos().y() for device in devices])
        row_y_positions = [all_y_pos[0]]  # Start with first device
        
        # Group y-positions into distinct rows
        for y in all_y_pos:
            if not any(abs(y - row_y) <= row_tolerance for row_y in row_y_positions):
                row_y_positions.append(y)
                
        # Assign devices to rows
        for device in devices:
            y = device.scenePos().y()
            for row_y in row_y_positions:
                if abs(y - row_y) <= row_tolerance:
                    rows[row_y].append(device)
                    break
        
        # For each row, align devices horizontally with equal spacing
        for row_y, row_devices in rows.items():
            if len(row_devices) < 2:
                continue
                
            # Sort by x position
            row_devices.sort(key=lambda d: d.scenePos().x())
            
            # Distribute devices horizontally with optimal spacing
            left_x = row_devices[0].scenePos().x()
            right_x = row_devices[-1].scenePos().x() + row_devices[-1].width
            total_width = right_x - left_x
            
            device_widths = sum(device.width for device in row_devices)
            # Use a consistent spacing between devices in the same row
            spacing = (total_width - device_widths) / (len(row_devices) - 1)
            spacing = max(self.CONFIG['min_spacing'], spacing)
            
            # Align all devices in this row at the same y-coordinate
            target_y = sum(d.scenePos().y() for d in row_devices) / len(row_devices)
            
            # Position devices in this row
            current_x = left_x
            for device in row_devices:
                device.setPos(QPointF(current_x, target_y))
                current_x += device.width + spacing
                device.update_connections()
        
        # Similarly, handle columns (vertical alignment)
        col_tolerance = 60
        cols = defaultdict(list)
        
        # Group devices into columns
        all_x_pos = sorted([device.scenePos().x() for device in devices])
        col_x_positions = [all_x_pos[0]]
        
        for x in all_x_pos:
            if not any(abs(x - col_x) <= col_tolerance for col_x in col_x_positions):
                col_x_positions.append(x)
                
        # Assign devices to columns
        for device in devices:
            x = device.scenePos().x()
            for col_x in col_x_positions:
                if abs(x - col_x) <= col_tolerance:
                    cols[col_x].append(device)
                    break
        
        # For each column, align devices vertically
        for col_x, col_devices in cols.items():
            if len(col_devices) < 2:
                continue
                
            # Sort by y position
            col_devices.sort(key=lambda d: d.scenePos().y())
            
            # Calculate average x-position for this column
            target_x = sum(d.scenePos().x() for d in col_devices) / len(col_devices)
            
            # Keep the existing y positions but align x
            for device in col_devices:
                current_y = device.scenePos().y()
                device.setPos(QPointF(target_x, current_y))
                device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='optimize_orthogonal'
            )
        
        self.canvas.viewport().update()
        return True
        
    def arrange_bus_topology(self):
        """Arrange devices in a bus network topology with a central backbone."""
        devices = self.get_selected_devices()
        if len(devices) < 3:
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Get starting position from current device positions
        center_x = sum(device.scenePos().x() + device.width/2 for device in devices) / len(devices)
        top_y = min(device.scenePos().y() for device in devices)
        
        # Setup spacing
        spacing_y = self.CONFIG['bus_spacing']
        
        # Place backbone in the center, and devices on both sides
        devices_sorted = sorted(devices, key=lambda d: d.scenePos().x())
        mid_point = len(devices) // 2
        
        # Place devices in two columns on either side of an imaginary backbone
        left_side = devices_sorted[:mid_point]
        right_side = devices_sorted[mid_point:]
        
        # Position devices
        current_y = top_y
        for i, (left, right) in enumerate(zip(left_side, right_side + [None] * (len(left_side) - len(right_side)))):
            # Place left device
            if left:
                left.setPos(QPointF(center_x - self.CONFIG['bus_spacing'] - left.width, current_y))
                left.update_connections()
                
            # Place right device at the same height
            if i < len(right_side):
                right = right_side[i]
                right.setPos(QPointF(center_x + self.CONFIG['bus_spacing'], current_y))
                right.update_connections()
                
            current_y += spacing_y
            
        # Handle extra devices if left_side is shorter than right_side
        if len(right_side) > len(left_side):
            for i in range(len(left_side), len(right_side)):
                right = right_side[i]
                right.setPos(QPointF(center_x + self.CONFIG['bus_spacing'], current_y))
                right.update_connections()
                current_y += spacing_y
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='bus_topology'
            )
        
        self.canvas.viewport().update()
        return True
        
    def arrange_star_topology(self):
        """Arrange devices in a star network topology with one central device."""
        devices = self.get_selected_devices()
        if len(devices) < 3:
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Find the most connected device to use as the center
        # If connection information isn't available, use the one closest to the center
        center_device = None
        
        # First try to find the device with most connections
        max_connections = -1
        for device in devices:
            num_connections = len(getattr(device, 'connections', []))
            if num_connections > max_connections:
                max_connections = num_connections
                center_device = device
            
        # If connection info not available, use device closest to center
        if center_device is None or max_connections == 0:
            devices_x = [d.scenePos().x() + d.width/2 for d in devices]
            devices_y = [d.scenePos().y() + d.height/2 for d in devices]
            center_x = sum(devices_x) / len(devices)
            center_y = sum(devices_y) / len(devices)
            
            min_dist = float('inf')
            for device in devices:
                dev_x = device.scenePos().x() + device.width/2
                dev_y = device.scenePos().y() + device.height/2
                dist = ((dev_x - center_x)**2 + (dev_y - center_y)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    center_device = device
        
        # Remove center device from the list
        other_devices = [device for device in devices if device != center_device]
        
        # Calculate positions for center device
        center_x = sum(device.scenePos().x() + device.width/2 for device in devices) / len(devices)
        center_y = sum(device.scenePos().y() + device.height/2 for device in devices) / len(devices)
        
        # Position center device at the calculated center
        center_device.setPos(QPointF(
            center_x - center_device.width/2,
            center_y - center_device.height/2
        ))
        center_device.update_connections()
        
        # Position other devices in a circle around the center device
        import math
        radius = max(150, len(other_devices) * 20)  # Scale radius based on number of devices
        
        for i, device in enumerate(other_devices):
            angle = 2 * math.pi * i / len(other_devices)
            x = center_x + radius * math.cos(angle) - device.width/2
            y = center_y + radius * math.sin(angle) - device.height/2
            
            device.setPos(QPointF(x, y))
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='star_topology'
            )
        
        self.canvas.viewport().update()
        return True

    def optimize_connection_distances(self):
        """Arrange devices to minimize total connection length using force-directed layout."""
        devices = self.get_selected_devices()
        if len(devices) < 3:
            return False
            
        # Store original positions for undo
        original_positions = {device: device.scenePos() for device in devices}
        
        # Find all connections between selected devices
        connections = []
        device_set = set(devices)
        
        for device in devices:
            for connection in getattr(device, 'connections', []):
                source = connection.source_device
                target = connection.target_device
                if source in device_set and target in device_set and source != target:
                    connections.append((source, target, connection))
        
        # If no connections found, fall back to grid arrangement
        if not connections:
            self.arrange_in_grid()
            return True
        
        # Use force-directed algorithm to find optimal positions
        # This is a simplified implementation of the Fruchterman-Reingold algorithm
        
        # Configuration
        iterations = 50          # Number of iterations for layout algorithm
        cooling_factor = 0.95    # Temperature reduction per iteration
        repulsive_force = 20000  # Strength of repulsive force between devices
        attractive_force = 0.2   # Strength of attractive force for connections
        
        # Initial temperature (maximum movement per iteration)
        temperature = max(
            max(d.scenePos().x() for d in devices) - min(d.scenePos().x() for d in devices),
            max(d.scenePos().y() for d in devices) - min(d.scenePos().y() for d in devices)
        ) / 10
        
        # Current positions (will be modified during optimization)
        positions = {device: QPointF(device.scenePos()) for device in devices}
        
        # Run the force-directed layout algorithm
        for iteration in range(iterations):
            # Calculate repulsive forces between all devices
            forces = {device: QPointF(0, 0) for device in devices}
            
            # Apply repulsive forces between all pairs of devices
            for i, device1 in enumerate(devices):
                for device2 in devices[i+1:]:
                    # Get displacement vector between devices
                    dx = positions[device1].x() - positions[device2].x()
                    dy = positions[device1].y() - positions[device2].y()
                    
                    # Avoid division by zero
                    distance = max(0.1, (dx*dx + dy*dy)**0.5)
                    
                    # Calculate repulsive force (inversely proportional to distance)
                    force = repulsive_force / (distance * distance)
                    
                    # Normalize direction
                    force_x = (dx / distance) * force
                    force_y = (dy / distance) * force
                    
                    # Apply force to both devices in opposite directions
                    forces[device1] += QPointF(force_x, force_y)
                    forces[device2] += QPointF(-force_x, -force_y)
            
            # Apply attractive forces for connected devices
            for source, target, _ in connections:
                # Get displacement vector between connected devices
                dx = positions[source].x() - positions[target].x()
                dy = positions[source].y() - positions[target].y()
                
                # Distance between devices
                distance = max(0.1, (dx*dx + dy*dy)**0.5)
                
                # Calculate attractive force (proportional to distance)
                force = attractive_force * distance
                
                # Normalize direction
                force_x = (dx / distance) * force
                force_y = (dy / distance) * force
                
                # Apply force to both devices (pull them together)
                forces[source] -= QPointF(force_x, force_y)
                forces[target] += QPointF(force_x, force_y)
            
            # Apply forces with temperature limiting
            for device in devices:
                # Calculate force magnitude
                force = forces[device]
                force_mag = (force.x()**2 + force.y()**2)**0.5
                
                if force_mag > 0:
                    # Limit force to current temperature
                    movement = min(force_mag, temperature) / force_mag
                    
                    # Update position based on force
                    positions[device] += QPointF(force.x() * movement, force.y() * movement)
            
            # Cool down the system
            temperature *= cooling_factor
        
        # Normalize positions to keep the center of mass unchanged
        original_center_x = sum(device.scenePos().x() + device.width/2 for device in devices) / len(devices)
        original_center_y = sum(device.scenePos().y() + device.height/2 for device in devices) / len(devices)
        
        new_center_x = sum(pos.x() + device.width/2 for device, pos in positions.items()) / len(devices)
        new_center_y = sum(pos.y() + device.height/2 for device, pos in positions.items()) / len(devices)
        
        dx = original_center_x - new_center_x
        dy = original_center_y - new_center_y
        
        # Apply final positions to devices
        for device, pos in positions.items():
            final_pos = QPointF(pos.x() + dx, pos.y() + dy)
            device.setPos(final_pos)
            device.update_connections()
        
        # Notify about the move for undo tracking
        if self.event_bus:
            self.event_bus.emit('devices.aligned', 
                devices=devices,
                original_positions=original_positions,
                alignment_type='optimize_connections'
            )
        
        self.canvas.viewport().update()
        return True
