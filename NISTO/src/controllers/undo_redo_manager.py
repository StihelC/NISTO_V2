import logging
from PyQt5.QtCore import QObject, pyqtSignal

class Command:
    """Base class for all commands that can be undone/redone."""
    
    def __init__(self, description="Unnamed Command"):
        self.description = description
    
    def execute(self):
        """Execute the command. Must be implemented by subclasses."""
        raise NotImplementedError("Commands must implement execute method")
    
    def undo(self):
        """Undo the command. Must be implemented by subclasses."""
        raise NotImplementedError("Commands must implement undo method")
    
    def redo(self):
        """Redo the command. Default implementation is to execute again."""
        self.execute()


class UndoRedoManager(QObject):
    """Manager for handling undo/redo operations."""
    
    # Signals for UI updates
    stack_changed = pyqtSignal()
    
    def __init__(self, event_bus):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus
        self.undo_stack = []  # Commands that can be undone
        self.redo_stack = []  # Commands that can be redone
        self.is_executing_command = False
        
        # Maximum stack size to prevent excessive memory usage
        self.max_stack_size = 100
    
    def push_command(self, command):
        """Push a command onto the undo stack and execute it."""
        self.logger.debug(f"UNDO_REDO: Pushing command {command.__class__.__name__}: {command.description}")
        # Clear redo stack when a new command is executed
        self.redo_stack.clear()
        
        # Execute the command
        old_state = self.is_executing_command
        self.is_executing_command = True
        self.logger.debug(f"UNDO_REDO: Set is_executing_command to True (was {old_state})")
        
        command.execute()
        
        self.is_executing_command = old_state
        self.logger.debug(f"UNDO_REDO: Restored is_executing_command to {old_state}")
        
        # Add to undo stack
        self.undo_stack.append(command)
        
        # Ensure stack doesn't grow too large
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)
        
        self.logger.debug(f"UNDO_REDO: Command executed and pushed to stack (stack size: {len(self.undo_stack)})")
        self.stack_changed.emit()
    
    def undo(self):
        """Undo the most recent command."""
        if not self.undo_stack:
            self.logger.info("Nothing to undo")
            return False
        
        try:
            # Set flag to indicate we're in a command execution to prevent recursive commands
            old_state = self.is_executing_command
            self.is_executing_command = True
            
            command = self.undo_stack.pop()
            self.logger.info(f"Undoing: {command.description}")
            
            command.undo()
            self.redo_stack.append(command)
            
            # Emit signal about changes - correcting the method call
            self.stack_changed.emit()
            
            return True
        except Exception as e:
            self.logger.error(f"Error in undo: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Reset the command execution flag when done
            self.is_executing_command = old_state
    
    def redo(self):
        """Redo the last undone command."""
        if not self.can_redo():
            self.logger.debug("Nothing to redo")
            return False
        
        command = self.redo_stack.pop()
        self.is_executing_command = True
        command.redo()
        self.is_executing_command = False
        
        self.undo_stack.append(command)
        self.logger.debug(f"Command redone: {command.description}")
        self.stack_changed.emit()
        return True
    
    def can_undo(self):
        """Check if there are commands that can be undone."""
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """Check if there are commands that can be redone."""
        return len(self.redo_stack) > 0
    
    def get_next_undo(self):
        """Get the next command to undo without removing it from stack."""
        if self.can_undo():
            return self.undo_stack[-1]
        return None
    
    def get_next_redo(self):
        """Get the next command to redo without removing it from stack."""
        if self.can_redo():
            return self.redo_stack[-1]
        return None
    
    def clear(self):
        """Clear both undo and redo stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.stack_changed.emit()
    
    def get_undo_text(self):
        """Get the description of the next command to undo."""
        if self.can_undo():
            return f"Undo {self.undo_stack[-1].description}"
        return "Undo"
    
    def get_redo_text(self):
        """Get the description of the next command to redo."""
        if self.can_redo():
            return f"Redo {self.redo_stack[-1].description}"
        return "Redo"
    
    def is_in_command_execution(self):
        """Check if we're currently executing a command."""
        result = self.is_executing_command
        self.logger.debug(f"UNDO_REDO: Checked is_in_command_execution, result={result}")
        return result
