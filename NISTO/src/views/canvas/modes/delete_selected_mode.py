import logging
from PyQt5.QtCore import Qt
from views.canvas.modes.base_mode import CanvasMode

class DeleteSelectedMode(CanvasMode):
    """Mode for deleting selected items."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
    
    def activate(self):
        """When activated, delete all selected items."""
        super().activate()
        selected_items = self.canvas.scene().selectedItems()
        if selected_items:
            self.logger.debug(f"DeleteSelectedMode: Deleting {len(selected_items)} selected items")
            self.canvas.delete_selected_requested.emit()
        else:
            self.logger.debug("DeleteSelectedMode: No items selected")
