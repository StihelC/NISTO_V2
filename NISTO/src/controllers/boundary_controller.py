from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor
import logging
import traceback

from models.boundary import Boundary
from controllers.commands import AddBoundaryCommand, DeleteBoundaryCommand

class BoundaryController:
    """Controller for managing boundary-related operations."""
    
    def __init__(self, canvas, event_bus, undo_redo_manager=None):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.undo_redo_manager = undo_redo_manager
        
        # Initialize boundary counter for naming
        self.boundary_counter = 0
    
    def on_add_boundary_requested(self, rect, name=None, color=None):
        """Handle request to add a boundary with the given rect."""
        # Use command pattern if undo_redo_manager is available
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            command = AddBoundaryCommand(self, rect, name, color)
            self.undo_redo_manager.push_command(command)
            return command.created_boundary
        else:
            # Original implementation
            return self.create_boundary(rect, name, color)
    
    def on_delete_boundary_requested(self, boundary):
        """Handle request to delete a specific boundary."""
        # Use command pattern if undo_redo_manager is available and not already in command
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            command = DeleteBoundaryCommand(self, boundary)
            self.undo_redo_manager.push_command(command)
        else:
            # Original implementation
            if boundary:
                self.logger.info(f"Deleting boundary '{boundary.name}'")
                
                # Use the boundary's delete method to ensure label is properly removed
                if hasattr(boundary, 'delete'):
                    boundary.delete()
                else:
                    # Fallback if delete method not available
                    if hasattr(boundary, 'label') and boundary.label:
                        self.canvas.scene().removeItem(boundary.label)
                
                # Remove from scene
                self.canvas.scene().removeItem(boundary)
                
                # Remove from boundaries list
                if boundary in self.canvas.boundaries:
                    self.canvas.boundaries.remove(boundary)
                
                # Notify through event bus
                self.event_bus.emit("boundary_deleted", boundary)
    
    def create_boundary(self, rect, name=None, color=None):
        """Create a new boundary with the given parameters."""
        # Implementation for creating a boundary directly
        # Will be used by both normal calls and from commands
        from models.boundary import Boundary
        from PyQt5.QtGui import QColor
        
        # Use default name if none provided
        if not name:
            name = f"Boundary {len(self.canvas.boundaries) + 1}"
        
        # Use default color if none provided
        if not color:
            color = QColor(40, 120, 200, 80)
        
        # Create the boundary
        boundary = Boundary(rect, name, color)
        
        # Add to scene
        self.canvas.scene().addItem(boundary)
        
        # Add to boundaries list
        self.canvas.boundaries.append(boundary)
        
        self.logger.info(f"Created boundary '{name}'")
        
        # Notify through event bus
        self.event_bus.emit("boundary_created", boundary)
        
        return boundary
    
    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)
