import logging

class CanvasModeManager:
    """Manages available interaction modes for the canvas."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.modes = {}
        self.current_mode_instance = None
        self.logger = logging.getLogger(__name__)
        
    def register_mode(self, mode_enum, mode_instance):
        """Register a mode with an enum identifier."""
        self.modes[mode_enum] = mode_instance
        
    def get_mode(self, mode_enum):
        """Get a mode instance by enum identifier."""
        return self.modes.get(mode_enum)
    
    @property    
    def current_mode(self):
        """Get the current mode enum."""
        # Find the mode enum for the current mode instance
        for mode_enum, mode in self.modes.items():
            if mode is self.current_mode_instance:
                return mode_enum
        return None
        
    def get_mode_instance(self, mode_enum=None):
        """Get the mode instance and update the current mode tracking."""
        if mode_enum is None:
            return self.current_mode_instance
        return self.get_mode(mode_enum)
        
    def set_mode(self, mode_enum):
        """Set the current mode by mode enum."""
        # Get the requested mode instance
        mode_instance = self.get_mode(mode_enum)
        
        # Check if the mode exists
        if not mode_instance:
            self.canvas.logger.error(f"Canvas: Mode {mode_enum} not registered")
            return False
            
        # Don't switch to the same mode
        if self.current_mode_instance is mode_instance:
            return False
            
        self.canvas.logger.info(f"Canvas: Switching to mode {mode_instance.name}")
        
        # Deactivate current mode
        if self.current_mode_instance:
            self.current_mode_instance.deactivate()
            
        # Set the current mode instance first (important for activate method)
        self.current_mode_instance = mode_instance
        
        # Activate new mode
        self.current_mode_instance.activate()
        
        # Update cursor
        self.canvas.setCursor(self.current_mode_instance.cursor())
        
        # Emit status message
        self.canvas.statusMessage.emit(f"Mode: {self.current_mode_instance.name}")
        
        return True
        
    def handle_event(self, event_name, *args, **kwargs):
        """Pass an event to the current mode for handling."""
        if not self.current_mode_instance:
            return False
            
        handler = getattr(self.current_mode_instance, event_name, None)
        if handler and callable(handler):
            try:
                return handler(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in {self.current_mode_instance.name}.{event_name}: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return False
        return False
