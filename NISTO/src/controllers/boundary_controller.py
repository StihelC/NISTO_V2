from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor
import logging
import traceback

from models.boundary import Boundary

class BoundaryController:
    """Controller for managing boundary-related operations."""
    
    def __init__(self, canvas, event_bus):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Initialize boundary counter for naming
        self.boundary_counter = 0
    
    def on_add_boundary_requested(self, rect):
        """Handle request to add a boundary region."""
        self.logger.info(f"Adding boundary at {rect}")
        self.create_boundary(rect)
    
    def on_delete_boundary_requested(self, boundary):
        """Handle request to delete a specific boundary."""
        if boundary:
            self.logger.info(f"Deleting boundary '{boundary.name}'")
            
            # Use the boundary's delete method to ensure label is removed too
            boundary.delete()
            
            # Remove from scene
            self.canvas.scene().removeItem(boundary)
            
            # Remove from boundaries list
            if boundary in self.canvas.boundaries:
                self.canvas.boundaries.remove(boundary)
            
            # Notify through event bus
            self.event_bus.emit("boundary_deleted", boundary)
    
    def create_boundary(self, rect, name=None, color=None):
        """Create a boundary with the given parameters."""
        try:
            # Generate a name if not provided
            if not name:
                self.boundary_counter += 1
                name = f"Zone {self.boundary_counter}"
            
            # Default color if none provided
            if not color:
                color = QColor(40, 120, 200, 80)
            
            # Create boundary object
            boundary = Boundary(rect, name, color)
            
            # Add to scene
            scene = self.canvas.scene()
            if scene:
                scene.addItem(boundary)
                
                # Store boundary if needed
                if not hasattr(self.canvas, "boundaries"):
                    self.canvas.boundaries = []
                self.canvas.boundaries.append(boundary)
                
                # Notify through event bus
                self.event_bus.emit("boundary_created", boundary)
                
                self.logger.info(f"Boundary '{name}' added at {rect}")
                return boundary
            else:
                self.logger.error("No scene available to add boundary")
                self._show_error("Canvas scene not initialized")
        
        except Exception as e:
            self.logger.error(f"Error creating boundary: {str(e)}")
            traceback.print_exc()
            self._show_error(f"Failed to create boundary: {str(e)}")
        
        return None
    
    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)
