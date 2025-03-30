from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from constants import Modes

class ModeManager(QObject):
    """
    Central manager for canvas interaction modes.
    
    Responsibilities:
    - Track current active mode
    - Manage mode transitions
    - Handle common mode behaviors
    - Provide consistent interface for mode-specific actions
    """
    
    # Signals
    mode_changed = pyqtSignal(str, str)  # old_mode, new_mode
    
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.current_mode = None
        self.modes = {}
        
        # Track previous mode for potential toggling back
        self.previous_mode = None
    
    def register_mode(self, mode_id, mode_instance):
        """Register a mode with the manager."""
        self.modes[mode_id] = mode_instance
    
    def set_mode(self, mode_id):
        """Change to a different interaction mode."""
        if mode_id not in self.modes:
            print(f"Warning: Unknown mode '{mode_id}', defaulting to select mode")
            mode_id = Modes.SELECT
        
        old_mode = self.current_mode
        
        # Deactivate current mode if one is active
        if self.current_mode:
            self._deactivate_mode(self.current_mode)
            
        # Store previous mode
        self.previous_mode = self.current_mode
            
        # Activate new mode
        self.current_mode = mode_id
        self._activate_mode(mode_id)
        
        # Emit signal for mode change
        self.mode_changed.emit(old_mode, mode_id)
        
        # Return the mode instance for chaining
        return self.modes[mode_id]
    
    def toggle_select_mode(self):
        """Toggle between select mode and previous mode."""
        if self.current_mode == Modes.SELECT and self.previous_mode:
            self.set_mode(self.previous_mode)
        else:
            self.set_mode(Modes.SELECT)
    
    def _activate_mode(self, mode_id):
        """Activate a specific mode with common behaviors."""
        mode = self.modes[mode_id]
        
        # Common activation behaviors
        self._set_devices_draggable(mode_id == Modes.SELECT)
        self.canvas.setCursor(mode.cursor())
        
        # Mode-specific activation
        mode.activate()
    
    def _deactivate_mode(self, mode_id):
        """Deactivate a specific mode."""
        mode = self.modes[mode_id]
        mode.deactivate()
    
    def _set_devices_draggable(self, draggable):
        """Helper to set draggability for all devices."""
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, draggable)
    
    def handle_event(self, event_type, event):
        """Centralized event handling for the current mode."""
        if not self.current_mode:
            return False
        
        mode = self.modes[self.current_mode]
        handler = getattr(mode, event_type, None)
        
        if handler:
            try:
                result = handler(event)
                # Add debug logging
                if event_type == "mouse_press_event":
                    print(f"ModeManager: {event_type} in {self.current_mode} mode, result: {result}")
                return result
            except Exception as e:
                import traceback
                print(f"Error in {event_type} for {self.current_mode} mode: {e}")
                traceback.print_exc()
        
        return False
    
    def get_current_mode(self):
        """Get the current active mode."""
        return self.current_mode
    
    def get_mode_instance(self, mode_id=None):
        """Get a specific mode instance or the current one."""
        if mode_id is None:
            mode_id = self.current_mode
        return self.modes.get(mode_id)