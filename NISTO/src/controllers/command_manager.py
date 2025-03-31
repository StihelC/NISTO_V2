import logging
from PyQt5.QtCore import QObject

from controllers.undo_redo_manager import UndoRedoManager
from controllers.commands import (
    AddDeviceCommand, DeleteDeviceCommand,
    AddBoundaryCommand, DeleteBoundaryCommand,
    AddConnectionCommand, DeleteConnectionCommand,
    MoveItemCommand, CompositeCommand
)

class CommandManager(QObject):
    """Central manager for command creation and execution."""
    
    def __init__(self, undo_redo_manager, event_bus=None):
        """Initialize the command manager with an undo/redo manager."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Create the undo-redo manager
        self.undo_redo_manager = undo_redo_manager
        
        # Reference to event bus
        self.event_bus = event_bus
        
        # Only set up event listeners if we have an event bus
        if self.event_bus:
            self._setup_event_listeners()
    
    def set_event_bus(self, event_bus):
        """Set the event bus after initialization."""
        self.event_bus = event_bus
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Set up listeners for events that should create commands."""
        if not self.event_bus:
            self.logger.warning("Cannot set up event listeners: no event_bus available")
            return
            
        # Listen for item movement events
        self.event_bus.on("item_moved", self.on_item_moved)
    
    def on_item_moved(self, item, start_pos, end_pos):
        """Handle item moved event."""
        self.logger.info(f"Item moved: {item} from {start_pos} to {end_pos}")
        
        # Create and execute the move command
        cmd = MoveItemCommand(item, start_pos, end_pos)
        self.undo_redo_manager.push_command(cmd)
    
    def undo(self):
        """Undo the last command."""
        if self.can_undo():
            self.undo_redo_manager.undo()
            self.logger.info("Undid last action")
            return True
        self.logger.info("Nothing to undo")
        return False
    
    def redo(self):
        """Redo the last undone command."""
        if self.can_redo():
            self.undo_redo_manager.redo()
            self.logger.info("Redid last undone action")
            return True
        self.logger.info("Nothing to redo")
        return False
    
    def can_undo(self):
        """Check if there is a command to undo."""
        return self.undo_redo_manager.can_undo()
    
    def can_redo(self):
        """Check if there is a command to redo."""
        return self.undo_redo_manager.can_redo()
    
    def get_undo_text(self):
        """Get descriptive text for the next undo action."""
        if self.can_undo():
            try:
                # Try to get the next command to undo
                if hasattr(self.undo_redo_manager, 'get_next_undo'):
                    command = self.undo_redo_manager.get_next_undo()
                    if command:
                        return f"Undo {command.description}"
            except Exception as e:
                self.logger.error(f"Error getting undo text: {str(e)}")
        return "Undo"
    
    def get_redo_text(self):
        """Get descriptive text for the next redo action."""
        if self.can_redo():
            try:
                # Try to get the next command to redo
                if hasattr(self.undo_redo_manager, 'get_next_redo'):
                    command = self.undo_redo_manager.get_next_redo()
                    if command:
                        return f"Redo {command.description}"
            except Exception as e:
                self.logger.error(f"Error getting redo text: {str(e)}")
        return "Redo"
    
    def clear_history(self):
        """Clear the command history."""
        self.undo_redo_manager.clear()
