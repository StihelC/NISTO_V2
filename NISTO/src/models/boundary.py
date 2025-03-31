from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PyQt5.QtGui import QColor, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject

class BoundarySignals(QObject):
    """Signals for the Boundary class."""
    name_changed = pyqtSignal(object, str)  # boundary, new_name

class EditableTextItem(QGraphicsTextItem):
    """An editable text item that supports interactive editing."""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFlag(QGraphicsTextItem.ItemIsSelectable, True)
        self._editable = False
        self._original_text = text
        
        # Style
        self.setDefaultTextColor(QColor(20, 20, 20, 200))
        self.setFont(QFont("Arial", 10, QFont.Bold))
    
    def start_editing(self):
        """Make the text editable."""
        if not self._editable:
            self._editable = True
            self._original_text = self.toPlainText()
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.setFocus()
    
    def finish_editing(self):
        """Finish editing and return to normal state."""
        if self._editable:
            self._editable = False
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            self.clearFocus()
            return self.toPlainText()
        return None
    
    def cancel_editing(self):
        """Cancel editing and revert changes."""
        if self._editable:
            self.setPlainText(self._original_text)
            self.finish_editing()
    
    def mouseDoubleClickEvent(self, event):
        """Enter edit mode on double click."""
        self.start_editing()
        super().mouseDoubleClickEvent(event)
    
    def focusOutEvent(self, event):
        """Complete editing when focus is lost."""
        if self._editable:
            new_text = self.finish_editing()
            # Notify parent of text change
            if self.parentItem() and hasattr(self.parentItem(), 'text_edited'):
                self.parentItem().text_edited(new_text)
        super().focusOutEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events during editing."""
        if self._editable:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # Apply changes on Enter
                new_text = self.finish_editing()
                # Notify parent of text change
                if self.parentItem() and hasattr(self.parentItem(), 'text_edited'):
                    self.parentItem().text_edited(new_text)
                return
            elif event.key() == Qt.Key_Escape:
                # Cancel editing on Escape
                self.cancel_editing()
                return
        super().keyPressEvent(event)

class Boundary(QGraphicsRectItem):
    """A visual boundary region on the network topology with editable label."""
    
    def __init__(self, rect, name="Boundary", color=QColor(40, 120, 200, 80)):
        super().__init__(rect)
        
        # Create signals object
        self.signals = BoundarySignals()
        
        # Set basic properties
        self.name = name
        self.color = color
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)
        
        # Apply visual style
        self._apply_style()
        
        # Create label
        self._create_label()
        
    def _apply_style(self):
        """Apply visual styling to the boundary."""
        # Set border with semi-transparency
        self.setPen(QPen(QColor(self.color.red(), self.color.green(), 
                               self.color.blue(), 160), 2, Qt.SolidLine))
        
        # Set fill with transparency
        self.setBrush(QBrush(self.color))
        
        # Set Z-value to be below devices but above background
        self.setZValue(-10)
    
    def _create_label(self):
        """Create and position the editable label text."""
        # Create editable text item as a child of this boundary
        self.label = EditableTextItem(self.name, self)
        
        # Position at bottom left outside the boundary
        self._update_label_position()
    
    def _update_label_position(self):
        """Update the label position relative to the boundary."""
        if hasattr(self, 'label') and self.label:
            # Position at bottom left outside the boundary rectangle
            rect = self.rect()
            # Use local coordinates since the label is a child item
            self.label.setPos(rect.left(), rect.bottom() + 5)
    
    def text_edited(self, new_text):
        """Handle when the label text has been edited."""
        if new_text != self.name:
            old_name = self.name
            self.name = new_text
            # Emit signal for name change
            self.signals.name_changed.emit(self, new_text)
            print(f"Boundary name changed from '{old_name}' to '{new_text}'")
    
    def set_name(self, name):
        """Change the boundary name."""
        if name != self.name:
            self.name = name
            if hasattr(self, 'label') and self.label:
                self.label.setPlainText(name)
    
    def set_color(self, color):
        """Change the boundary color."""
        self.color = color
        self._apply_style()
    
    def itemChange(self, change, value):
        """Handle changes in item state."""
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            # No need to update label position when boundary moves
            # since the label is a child item and moves automatically
            pass
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event with visual feedback."""
        # Highlight boundary when hovering
        self.setPen(QPen(QColor(self.color.red(), self.color.green(), 
                               self.color.blue(), 220), 3, Qt.SolidLine))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        # Restore original appearance
        self._apply_style()
        super().hoverLeaveEvent(event)
    
    def update_geometry(self, rect):
        """Update the boundary's rect."""
        self.setRect(rect)
        self._update_label_position()
    
    def delete(self):
        """Clean up resources before deletion."""
        # Store scene and rect before removal for updating
        scene = self.scene()
        update_rect = self.sceneBoundingRect().adjusted(-10, -10, 10, 10)
        
        # Remove the label first if it exists
        if hasattr(self, 'label') and self.label:
            if self.label.scene():
                # Include label area in update region
                if hasattr(self.label, 'boundingRect'):
                    label_rect = self.label.sceneBoundingRect()
                    update_rect = update_rect.united(label_rect)
                self.scene().removeItem(self.label)
            self.label = None
            
        # Emit signals or perform additional cleanup if needed
        if hasattr(self, 'signals'):
            # You might want to add a deleted signal in BoundarySignals class
            if hasattr(self.signals, 'deleted'):
                self.signals.deleted.emit(self)
        
        # Force update the scene area after deletion
        if scene:
            scene.update(update_rect)
            # Force update on all views
            for view in scene.views():
                view.viewport().update()

    def update_color(self):
        """Update boundary visual appearance after color change."""
        if hasattr(self, 'color'):
            # Apply the color to the boundary's brush and pen
            brush = self.brush()
            brush.setColor(self.color)
            self.setBrush(brush)
            
            # Update the pen too for consistent appearance
            pen = QPen(QColor(self.color.red(), self.color.green(), 
                             self.color.blue(), 160), 2, Qt.SolidLine)
            self.setPen(pen)
            
            # Force redraw
            self.update()

    def update_name(self):
        """Update boundary label text after name change."""
        if hasattr(self, 'label') and self.label:
            self.label.setPlainText(self.name)

