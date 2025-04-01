import logging

class CanvasModeManager:
    """Manages available interaction modes for the canvas."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.modes = {}  # Changed from _modes to modes for consistency
        self.current_mode_instance = None
        self.current_mode = None  # Store current mode ID
        self.logger = logging.getLogger(__name__)
        
    def register_mode(self, mode_enum, mode_instance):
        """Register a mode with an enum identifier."""
        self.modes[mode_enum] = mode_instance
        
    def get_mode(self, mode_enum):
        """Get a mode instance by enum identifier."""
        return self.modes.get(mode_enum)
    
    def get_mode_instance(self, mode_enum=None):
        """Get the mode instance and update the current mode tracking."""
        if mode_enum is None:
            return self.current_mode_instance
        return self.get_mode(mode_enum)
        
    def set_mode(self, mode_id):
        """Switch to the specified mode.
        
        Args:
            mode_id: The mode identifier
            
        Returns:
            bool: True if mode was successfully set, False otherwise
        """
        if mode_id not in self.modes:  # Fixed: Changed _modes to modes
            self.logger.error(f"Invalid mode: {mode_id}")
            return False
            
        if mode_id == self.current_mode:
            # Already in this mode
            return True
            
        # Deactivate current mode
        if self.current_mode_instance:
            self.current_mode_instance.deactivate()
            
        # Get new mode instance
        mode_instance = self.modes[mode_id]  # Fixed: Changed _modes to modes
        
        # Set as current
        self.current_mode = mode_id
        self.current_mode_instance = mode_instance
        
        # Activate new mode
        mode_instance.activate()
        
        # Get mode name safely
        mode_name = getattr(mode_instance, 'name', mode_instance.__class__.__name__)
        self.canvas.logger.info(f"Canvas: Switching to mode {mode_name}")
        
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
                self.logger.error(f"Error in {event_name}: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return False
        return False
