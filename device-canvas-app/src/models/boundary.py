from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, QGraphicsItemGroup
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
        self._original_flags = self.flags()
        
        # Style
        self.setDefaultTextColor(QColor(20, 20, 20, 200))
        self.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Add a slight background for better visibility
        self._add_background()
    
    def _add_background(self):
        """Add semi-transparent background rect behind text."""
        # This is done when the text changes or initially set
        rect = self.boundingRect()
        rect = QRectF(rect.x() - 2, rect.y() - 2, rect.width() + 4, rect.height() + 4)
        
        # Store the rect for later adjustment
        self._bg_rect = rect
    
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
            # Adjustment to ensure text stays properly sized
            self._add_background()
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
        
        # Apply visual style
        self._apply_style()
        
        # Create label at the bottom left outside
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
        # Create editable text item
        self.label = EditableTextItem(self.name)
        
        # Make label part of the scene but not a child of this item
        # so it doesn't move with the boundary
        if self.scene():
            self.scene().addItem(self.label)
            
        # Position at bottom left outside
        self._update_label_position()
    
    def _update_label_position(self):
        """Update the label position relative to the boundary."""
        # Position at bottom left outside
        rect = self.rect()
        scene_rect = self.mapRectToScene(rect)
        # Place text just below the bottom-left corner
        self.label.setPos(scene_rect.left(), scene_rect.bottom() + 5)
    
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
        self.name = name
        self.label.setPlainText(name)
    
    def set_color(self, color):
        """Change the boundary color."""
        self.color = color
        self._apply_style()
    
    def shape(self):
        """Define the shape for hit detection and selection."""
        # Use default shape but with a bit of padding for easier selection
        path = super().shape()
        return path
    
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