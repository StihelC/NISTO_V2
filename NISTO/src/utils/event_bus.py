from PyQt5.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    """
    A simple event bus for communication between components.
    
    Usage:
    - Register callbacks with event_bus.on(event_name, callback)
    - Emit events with event_bus.emit(event_name, *args, **kwargs)
    """
    
    def __init__(self):
        super().__init__()
        self.callbacks = {}
        self.controllers = {}  # Store controller references
    
    def on(self, event_name, callback):
        """Register a callback for an event."""
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)
        
    def off(self, event_name, callback=None):
        """Remove a callback for an event."""
        if event_name not in self.callbacks:
            return
        
        if callback is None:
            # Remove all callbacks for this event
            self.callbacks[event_name] = []
        else:
            # Remove specific callback
            self.callbacks[event_name] = [cb for cb in self.callbacks[event_name] if cb != callback]
    
    def emit(self, event_name, *args, **kwargs):
        """Emit an event with arguments."""
        if event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                callback(*args, **kwargs)
    
    def register_controller(self, name, controller):
        """Register a controller with the event bus."""
        self.controllers[name] = controller
        
    def get_controller(self, name):
        """Get a registered controller."""
        return self.controllers.get(name)
