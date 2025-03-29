import json
from PyQt5.QtCore import QPointF, QRectF, QByteArray
from PyQt5.QtGui import QColor
import uuid
import os

class CanvasSerializer:
    """Handles serialization and deserialization of canvas elements."""
    
    @staticmethod
    def serialize_canvas(canvas):
        """Convert canvas state to serializable dictionary."""
        data = {
            'version': '1.0',
            'devices': [],
            'connections': [],
            'boundaries': []
        }
        
        # Serialize all devices
        for device in canvas.devices:
            device_data = CanvasSerializer.serialize_device(device)
            data['devices'].append(device_data)
        
        # Serialize all connections
        if hasattr(canvas, 'connections'):
            for connection in canvas.connections:
                connection_data = CanvasSerializer.serialize_connection(connection)
                data['connections'].append(connection_data)
        
        # Serialize all boundaries
        if hasattr(canvas, 'boundaries'):
            for boundary in canvas.boundaries:
                boundary_data = CanvasSerializer.serialize_boundary(boundary)
                data['boundaries'].append(boundary_data)
        
        return data
    
    @staticmethod
    def serialize_device(device):
        """Convert a device to a serializable dictionary."""
        pos = device.scenePos()
        
        # Create a deep copy of properties with QColor conversion
        serialized_properties = CanvasSerializer._process_properties(device.properties)
        
        device_data = {
            'id': device.id,
            'name': device.name,
            'device_type': device.device_type,
            'properties': serialized_properties,
            'position': {'x': pos.x(), 'y': pos.y()}
        }
        
        # Include custom icon path if it exists
        if hasattr(device, 'custom_icon_path') and device.custom_icon_path:
            device_data['custom_icon_path'] = device.custom_icon_path
        
        return device_data
    
    @staticmethod
    def _process_properties(props):
        """Process properties dictionary to make it JSON serializable."""
        if props is None:
            return {}
            
        result = {}
        for key, value in props.items():
            # Handle QColor objects
            if isinstance(value, QColor):
                result[key] = CanvasSerializer._serialize_color(value)
            # Handle lists/arrays
            elif isinstance(value, list):
                result[key] = [CanvasSerializer._process_value(item) for item in value]
            # Handle dictionaries (recursive)
            elif isinstance(value, dict):
                result[key] = CanvasSerializer._process_properties(value)
            else:
                # Try to serialize the value or convert to string if needed
                result[key] = CanvasSerializer._process_value(value)
                
        return result
    
    @staticmethod
    def _process_value(value):
        """Process a single value to make it JSON serializable."""
        if isinstance(value, QColor):
            return CanvasSerializer._serialize_color(value)
        elif hasattr(value, 'toDict') and callable(value.toDict):
            return value.toDict()
        elif hasattr(value, '__dict__'):
            # Custom object, convert to dict
            return {k: CanvasSerializer._process_value(v) for k, v in value.__dict__.items()}
        else:
            # Return as is, and let JSON serialization handle it
            return value
    
    @staticmethod
    def _serialize_color(color):
        """Convert QColor to serializable format."""
        if not color or not isinstance(color, QColor):
            return {'r': 0, 'g': 0, 'b': 0, 'a': 255}
            
        return {
            'r': color.red(),
            'g': color.green(),
            'b': color.blue(),
            'a': color.alpha()
        }
    
    @staticmethod
    def serialize_connection(connection):
        """Convert a connection to a serializable dictionary."""
        return {
            'id': connection.id,
            'source_device_id': connection.source_device.id,
            'target_device_id': connection.target_device.id,
            'connection_type': connection.connection_type,
            'label_text': connection.label_text,
            'bandwidth': connection.bandwidth,
            'latency': connection.latency,
            'routing_style': connection.routing_style,
            'line_width': connection.line_width,
            'line_color': CanvasSerializer._serialize_color(connection.line_color),
            'line_style': int(connection.line_style)  # Convert Qt.PenStyle to int
        }
    
    @staticmethod
    def serialize_boundary(boundary):
        """Convert a boundary to a serializable dictionary."""
        rect = boundary.rect()
        
        return {
            'name': boundary.name,
            'rect': {
                'x': rect.x(),
                'y': rect.y(),
                'width': rect.width(),
                'height': rect.height()
            },
            'color': CanvasSerializer._serialize_color(boundary.color)
        }
    
    @staticmethod
    def deserialize_canvas(data, canvas):
        """Restore canvas state from serialized data."""
        # Clear existing elements
        CanvasSerializer._clear_canvas(canvas)
        
        # Create device lookup for connection references
        device_lookup = {}
        
        # Restore devices first
        for device_data in data.get('devices', []):
            device = CanvasSerializer.deserialize_device(device_data, canvas)
            if device:
                device_lookup[device_data['id']] = device
        
        # Restore boundaries
        for boundary_data in data.get('boundaries', []):
            CanvasSerializer.deserialize_boundary(boundary_data, canvas)
        
        # Restore connections last (they need device references)
        for connection_data in data.get('connections', []):
            CanvasSerializer.deserialize_connection(connection_data, canvas, device_lookup)
        
        # Update the view to show all items
        canvas.viewport().update()
    
    @staticmethod
    def _clear_canvas(canvas):
        """Remove all items from the canvas."""
        # Remove all devices
        for device in list(canvas.devices):
            canvas.scene().removeItem(device)
        canvas.devices.clear()
        
        # Remove all connections
        if hasattr(canvas, 'connections'):
            for connection in list(canvas.connections):
                canvas.scene().removeItem(connection)
            canvas.connections.clear()
        
        # Remove all boundaries
        if hasattr(canvas, 'boundaries'):
            for boundary in list(canvas.boundaries):
                canvas.scene().removeItem(boundary)
            canvas.boundaries.clear()
    
    @staticmethod
    def deserialize_device(data, canvas):
        """Create a device from serialized data."""
        from models.device import Device
        
        try:
            # Convert serialized color properties back to QColor objects
            properties = data.get('properties', {})
            converted_properties = CanvasSerializer._convert_color_properties(properties)
            
            # Get the custom icon path if present
            custom_icon_path = data.get('custom_icon_path')
            
            # Verify the custom icon path exists
            if custom_icon_path and not os.path.exists(custom_icon_path):
                print(f"Warning: Custom icon not found at {custom_icon_path}")
                custom_icon_path = None
            
            # Create device with serialized properties
            device = Device(
                data['name'],
                data['device_type'],
                converted_properties,
                custom_icon_path
            )
            
            # Explicitly force icon loading if we have a custom path
            if custom_icon_path:
                device._try_load_icon()
            
            # Set ID if present
            if 'id' in data:
                device.id = data['id']
            
            # Position the device
            pos = data.get('position', {'x': 0, 'y': 0})
            device.setPos(QPointF(pos['x'], pos['y']))
            
            # Add to scene
            canvas.scene().addItem(device)
            canvas.devices.append(device)
            
            return device
            
        except Exception as e:
            import traceback
            print(f"Error deserializing device: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def _convert_color_properties(props):
        """Convert serialized color objects back to QColor."""
        if props is None:
            return {}
            
        result = {}
        for key, value in props.items():
            if isinstance(value, dict) and all(k in value for k in ['r', 'g', 'b']):
                # This looks like a serialized color
                result[key] = QColor(
                    value.get('r', 0),
                    value.get('g', 0),
                    value.get('b', 0),
                    value.get('a', 255)
                )
            elif isinstance(value, dict):
                # Recursive for nested dictionaries
                result[key] = CanvasSerializer._convert_color_properties(value)
            elif isinstance(value, list):
                # Process lists
                result[key] = [
                    CanvasSerializer._convert_color_value(item) for item in value
                ]
            else:
                result[key] = value
                
        return result
    
    @staticmethod
    def _convert_color_value(value):
        """Convert a single value from serialized format to proper object if needed."""
        if isinstance(value, dict):
            if all(k in value for k in ['r', 'g', 'b']):
                return QColor(
                    value.get('r', 0),
                    value.get('g', 0),
                    value.get('b', 0),
                    value.get('a', 255)
                )
            return CanvasSerializer._convert_color_properties(value)
        return value
    
    @staticmethod
    def deserialize_connection(data, canvas, device_lookup):
        """Create a connection from serialized data."""
        from models.connection import Connection
        from PyQt5.QtCore import Qt
        
        try:
            # Get source and target devices
            source_device_id = data.get('source_device_id')
            target_device_id = data.get('target_device_id')
            
            if not source_device_id or not target_device_id:
                print("Missing source or target device ID")
                return None
            
            source_device = device_lookup.get(source_device_id)
            target_device = device_lookup.get(target_device_id)
            
            if not source_device or not target_device:
                print("Could not find source or target device")
                return None
            
            # Create connection with label text
            connection_type = data.get('connection_type')
            label_text = data.get('label_text', '')
            
            print(f"Deserializing connection with label_text: '{label_text}'")
            
            connection = Connection(source_device, target_device, connection_type, label_text)
            
            # Set ID if present
            if 'id' in data:
                connection.id = data['id']
            
            # Set properties
            connection.bandwidth = data.get('bandwidth', '')
            connection.latency = data.get('latency', '')
            connection.label_text = label_text  # Explicitly set again to ensure it's set
            
            # Set style properties
            routing_style = data.get('routing_style')
            if routing_style is not None:
                connection.set_routing_style(routing_style)
                
            if 'line_width' in data:
                connection.line_width = data['line_width']
                
            if 'line_color' in data and isinstance(data['line_color'], dict):
                color_data = data['line_color']
                connection.line_color = QColor(
                    color_data.get('r', 0),
                    color_data.get('g', 0),
                    color_data.get('b', 0),
                    color_data.get('a', 255)
                )
                
            if 'line_style' in data:
                # Convert int back to Qt.PenStyle
                connection.line_style = data['line_style']
                
            # Add to scene
            canvas.scene().addItem(connection)
            if not hasattr(canvas, 'connections'):
                canvas.connections = []
            canvas.connections.append(connection)
            
            # IMPORTANT: Remove any existing label first to avoid conflicts
            if hasattr(connection, 'label') and connection.label is not None:
                connection.label.setParentItem(None)  # Detach from connection
                if connection.scene():
                    connection.scene().removeItem(connection.label)
                connection.label = None
            
            # Create label if needed - force it to be created and positioned
            if label_text:
                print(f"Creating label with text: '{label_text}'")
                connection.create_label()
                
                # Make sure the label text is set correctly
                if connection.label:
                    connection.label.setPlainText(label_text)
                    connection.label_text = label_text  # Ensure this is set correctly
                    
                # Force label to be positioned properly
                connection._update_label_position()
            
            # Apply style
            connection._apply_style()
            
            # Force update the path
            connection.update_path()
            
            print(f"Connection created with label_text: '{connection.label_text}'")
            
            return connection
            
        except Exception as e:
            import traceback
            print(f"Error deserializing connection: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def deserialize_boundary(data, canvas):
        """Create a boundary from serialized data."""
        from models.boundary import Boundary
        
        try:
            # Extract boundary data
            name = data.get('name', 'Boundary')
            
            # Create rectangle
            rect_data = data.get('rect', {'x': 0, 'y': 0, 'width': 100, 'height': 100})
            rect = QRectF(
                rect_data.get('x', 0),
                rect_data.get('y', 0),
                rect_data.get('width', 100),
                rect_data.get('height', 100)
            )
            
            # Create color
            color_data = data.get('color', {'r': 40, 'g': 120, 'b': 200, 'a': 80})
            color = QColor(
                color_data.get('r', 40),
                color_data.get('g', 120),
                color_data.get('b', 200),
                color_data.get('a', 80)
            )
            
            # Create boundary
            boundary = Boundary(rect, name, color)
            
            # Add to scene
            canvas.scene().addItem(boundary)
            if not hasattr(canvas, 'boundaries'):
                canvas.boundaries = []
            canvas.boundaries.append(boundary)
            
            return boundary
            
        except Exception as e:
            import traceback
            print(f"Error deserializing boundary: {e}")
            traceback.print_exc()
            return None
