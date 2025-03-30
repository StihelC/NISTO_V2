from PyQt5.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    """
    A simple event bus to facilitate communication between components.
    
    This provides a centralized mechanism for components to communicate
    without having to know about each other directly.
    """
    
    # Define signals
    device_event = pyqtSignal(str, object)
    connection_event = pyqtSignal(str, object)
    boundary_event = pyqtSignal(str, object)
    mode_event = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self.listeners = {}
    
    def emit(self, event_name, data=None):
        """Emit an event with optional data."""
        # Emit on the appropriate signal based on event prefix
        if event_name.startswith("device_"):
            self.device_event.emit(event_name, data)
        elif event_name.startswith("connection_"):
            self.connection_event.emit(event_name, data)
        elif event_name.startswith("boundary_"):
            self.boundary_event.emit(event_name, data)
        elif event_name.startswith("mode_"):
            self.mode_event.emit(event_name, data)
            
        # Also call any registered callback listeners
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    import traceback
                    print(f"Error in event listener for {event_name}: {e}")
                    traceback.print_exc()
    
    def on(self, event_name, callback):
        """Register a callback for an event."""
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
        
        # Return a function that can be called to remove this listener
        return lambda: self.remove_listener(event_name, callback)
    
    def remove_listener(self, event_name, callback):
        """Remove a registered callback."""
        if event_name in self.listeners and callback in self.listeners[event_name]:
            self.listeners[event_name].remove(callback)
