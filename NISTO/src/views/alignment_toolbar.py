"""
Toolbar with device alignment controls.
"""
from PyQt5.QtWidgets import QToolBar, QAction, QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
import os

class AlignmentToolbar(QToolBar):
    """Toolbar with buttons for aligning selected devices."""
    
    def __init__(self, parent=None, alignment_controller=None):
        super().__init__("Alignment Tools", parent)
        self.alignment_controller = alignment_controller
        
        # Set toolbar properties
        self.setObjectName("alignmentToolbar")
        self.setMovable(True)
        self.setIconSize(QSize(16, 16))  # Use QSize directly, not as a property of Qt
        
        # Create actions
        self.setup_actions()
    
    def setup_actions(self):
        """Set up the alignment actions."""
        # Create actions with icons
        self.align_left_action = QAction("Align Left", self)
        self.align_left_action.setToolTip("Align selected devices to the left edge")
        self.align_left_action.triggered.connect(self._on_align_left)
        
        self.align_right_action = QAction("Align Right", self)
        self.align_right_action.setToolTip("Align selected devices to the right edge")
        self.align_right_action.triggered.connect(self._on_align_right)
        
        self.align_top_action = QAction("Align Top", self)
        self.align_top_action.setToolTip("Align selected devices to the top edge")
        self.align_top_action.triggered.connect(self._on_align_top)
        
        self.align_bottom_action = QAction("Align Bottom", self)
        self.align_bottom_action.setToolTip("Align selected devices to the bottom edge")
        self.align_bottom_action.triggered.connect(self._on_align_bottom)
        
        self.align_center_h_action = QAction("Center Horizontally", self)
        self.align_center_h_action.setToolTip("Align selected devices to a horizontal center")
        self.align_center_h_action.triggered.connect(self._on_align_center_h)
        
        self.align_center_v_action = QAction("Center Vertically", self)
        self.align_center_v_action.setToolTip("Align selected devices to a vertical center")
        self.align_center_v_action.triggered.connect(self._on_align_center_v)
        
        self.distribute_h_action = QAction("Distribute Horizontally", self)
        self.distribute_h_action.setToolTip("Distribute selected devices horizontally with even spacing")
        self.distribute_h_action.triggered.connect(self._on_distribute_h)
        
        self.distribute_v_action = QAction("Distribute Vertically", self)
        self.distribute_v_action.setToolTip("Distribute selected devices vertically with even spacing")
        self.distribute_v_action.triggered.connect(self._on_distribute_v)
        
        # Add actions to toolbar
        self.addAction(self.align_left_action)
        self.addAction(self.align_right_action)
        self.addAction(self.align_top_action)
        self.addAction(self.align_bottom_action)
        self.addSeparator()
        self.addAction(self.align_center_h_action)
        self.addAction(self.align_center_v_action)
        self.addSeparator()
        self.addAction(self.distribute_h_action)
        self.addAction(self.distribute_v_action)
    
    def set_controller(self, alignment_controller):
        """Set the alignment controller."""
        self.alignment_controller = alignment_controller
        
    def update_actions_state(self, selected_items=None):
        """Update actions enabled/disabled state based on selection."""
        if selected_items is None:
            # Default to no selection
            selected_items = []
            
        # Count selected devices
        if hasattr(self.alignment_controller, 'canvas'):
            devices = [item for item in selected_items if item in self.alignment_controller.canvas.devices]
            device_count = len(devices)
        else:
            device_count = 0
        
        # Enable align actions when 2+ devices are selected
        align_enabled = device_count >= 2
        self.align_left_action.setEnabled(align_enabled)
        self.align_right_action.setEnabled(align_enabled)
        self.align_top_action.setEnabled(align_enabled)
        self.align_bottom_action.setEnabled(align_enabled)
        self.align_center_h_action.setEnabled(align_enabled)
        self.align_center_v_action.setEnabled(align_enabled)
        
        # Enable distribute actions when 3+ devices are selected
        distribute_enabled = device_count >= 3
        self.distribute_h_action.setEnabled(distribute_enabled)
        self.distribute_v_action.setEnabled(distribute_enabled)
    
    def _on_align_left(self):
        """Handle align left action."""
        if self.alignment_controller:
            self.alignment_controller.align_left()
    
    def _on_align_right(self):
        """Handle align right action."""
        if self.alignment_controller:
            self.alignment_controller.align_right()
    
    def _on_align_top(self):
        """Handle align top action."""
        if self.alignment_controller:
            self.alignment_controller.align_top()
    
    def _on_align_bottom(self):
        """Handle align bottom action."""
        if self.alignment_controller:
            self.alignment_controller.align_bottom()
    
    def _on_align_center_h(self):
        """Handle align center horizontally action."""
        if self.alignment_controller:
            self.alignment_controller.align_center_horizontal()
    
    def _on_align_center_v(self):
        """Handle align center vertically action."""
        if self.alignment_controller:
            self.alignment_controller.align_center_vertical()
    
    def _on_distribute_h(self):
        """Handle distribute horizontally action."""
        if self.alignment_controller:
            self.alignment_controller.distribute_horizontally()
    
    def _on_distribute_v(self):
        """Handle distribute vertically action."""
        if self.alignment_controller:
            self.alignment_controller.distribute_vertically()
