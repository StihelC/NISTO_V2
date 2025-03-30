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
    
    def __init__(self, event_bus, device_controller=None, boundary_controller=None, connection_controller=None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Create the undo-redo manager
        self.undo_redo_manager = UndoRedoManager(event_bus)
        
        # Store controllers for command creation
        self.device_controller = device_controller
        self.boundary_controller = boundary_controller
        self.connection_controller = connection_controller
        
        # Reference to event bus
        self.event_bus = event_bus
        
        # Initialize event listeners
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Set up event listeners for item movements."""
        # Listen for item movement events to create MoveItemCommands
        self.event_bus.on("item_moved", self.on_item_moved)
        
    def on_item_moved(self, item, old_pos, new_pos):
        """Create and execute a command for item movement."""
        command = MoveItemCommand(item, old_pos, new_pos)
        self.undo_redo_manager.push_command(command)
    
    def set_controllers(self, device_controller=None, boundary_controller=None, connection_controller=None):
        """Set controller references after initialization."""
        if device_controller:
            self.device_controller = device_controller
            device_controller.undo_redo_manager = self.undo_redo_manager
        
        if boundary_controller:
            self.boundary_controller = boundary_controller
            boundary_controller.undo_redo_manager = self.undo_redo_manager
        
        if connection_controller:
            self.connection_controller = connection_controller
            connection_controller.undo_redo_manager = self.undo_redo_manager
    
    def undo(self):
        """Undo the last command."""
        return self.undo_redo_manager.undo()
    
    def redo(self):
        """Redo the last undone command."""
        return self.undo_redo_manager.redo()
    
    def can_undo(self):
        """Check if there are commands that can be undone."""
        return self.undo_redo_manager.can_undo()
    
    def can_redo(self):
        """Check if there are commands that can be redone."""
        return self.undo_redo_manager.can_redo()
    
    def get_undo_text(self):
        """Get the description of the next command to undo."""
        return self.undo_redo_manager.get_undo_text()
    
    def get_redo_text(self):
        """Get the description of the next command to redo."""
        return self.undo_redo_manager.get_redo_text()
    
    def clear_history(self):
        """Clear the command history."""
        self.undo_redo_manager.clear()
