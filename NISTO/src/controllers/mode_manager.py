import logging
from PyQt5.QtWidgets import QGraphicsItem, QApplication
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
        self.current_mode_id = None
        self.logger = logging.getLogger(__name__)
        
        # Track previous mode for potential toggling back
        self.previous_mode = None
    
    def register_mode(self, mode_id, mode_instance):
        """Register a mode with the manager."""
        self.modes[mode_id] = mode_instance
        self.logger.debug(f"Registered mode {mode_id}: {mode_instance.__class__.__name__}")
    
    def set_mode(self, mode_id):
        """Change to a different interaction mode."""
        if mode_id not in self.modes:
            self.logger.error(f"Unknown mode ID: {mode_id}")
            return False
        
        old_mode_id = self.current_mode_id
        
        # Deactivate current mode if one is active
        if self.current_mode:
            self.current_mode.deactivate()
            
        # Store previous mode
        self.previous_mode = self.current_mode_id
            
        # Activate new mode
        self.current_mode = self.modes[mode_id]
        self.current_mode_id = mode_id
        self._activate_mode(mode_id)
        
        # Emit signal for mode change
        if old_mode_id:
            self.mode_changed.emit(str(old_mode_id), str(mode_id))
        
        # Update cursor
        QApplication.restoreOverrideCursor()
        QApplication.setOverrideCursor(self.current_mode.cursor())
        
        self.logger.debug(f"Mode changed to: {mode_id}")
        return True
    
    def toggle_select_mode(self):
        """Toggle between select mode and previous mode."""
        if self.current_mode_id == Modes.SELECT and self.previous_mode:
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
    
    def _set_devices_draggable(self, draggable):
        """Helper to set draggability for all devices."""
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, draggable)
    
    def handle_event(self, event_type, event):
        """Centralized event handling for the current mode."""
        if not self.current_mode:
            return False
        
        handler = getattr(self.current_mode, event_type, None)
        
        if handler:
            try:
                result = handler(event)
                # Add more detailed debug logging for mouse events
                if event_type == "mouse_move_event" and event.pos().x() % 500 == 0 and event.pos().y() % 500 == 0:
                    self.logger.debug(f"Mode {self.current_mode.name} handling {event_type}")
                return result
            except Exception as e:
                self.logger.error(f"Error handling {event_type} in mode {self.current_mode_id}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        return False
    
    def get_current_mode(self):
        """Get the current active mode."""
        return self.current_mode_id
    
    def get_mode_instance(self, mode_id=None):
        """Get a specific mode instance or the current one."""
        if mode_id is None:
            mode_id = self.current_mode_id
        return self.modes.get(mode_id)