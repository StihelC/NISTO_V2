"""
Toolbar with device alignment controls.
"""
import logging
from PyQt5.QtWidgets import QToolBar, QAction, QActionGroup, QMenu, QToolButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
import os

class AlignmentToolbar(QToolBar):
    """Toolbar with buttons for aligning selected devices."""
    
    def __init__(self, parent=None, controller=None):
        super().__init__("Alignment", parent)
        self.logger = logging.getLogger(__name__)
        self.alignment_controller = controller
        self._setup_actions()
    
    def set_controller(self, controller):
        """Set the alignment controller."""
        self.alignment_controller = controller
    
    def _setup_actions(self):
        """Create alignment actions."""
        # Create alignment dropdown menu and toolbar button
        self.align_menu = QMenu("Align")
        
        # Basic alignment actions
        self.align_left_action = QAction(QIcon("resources/icons/align_left.png"), "Align Left", self)
        self.align_right_action = QAction(QIcon("resources/icons/align_right.png"), "Align Right", self)
        self.align_top_action = QAction(QIcon("resources/icons/align_top.png"), "Align Top", self)
        self.align_bottom_action = QAction(QIcon("resources/icons/align_bottom.png"), "Align Bottom", self)
        self.align_center_h_action = QAction(QIcon("resources/icons/align_center_h.png"), "Align Center Horizontal", self)
        self.align_center_v_action = QAction(QIcon("resources/icons/align_center_v.png"), "Align Center Vertical", self)
        
        # Distribution actions
        self.distribute_h_action = QAction(QIcon("resources/icons/distribute_h.png"), "Distribute Horizontally", self)
        self.distribute_v_action = QAction(QIcon("resources/icons/distribute_v.png"), "Distribute Vertically", self)
        
        # Advanced arrangement actions
        self.arrange_grid_action = QAction(QIcon("resources/icons/arrange_grid.png"), "Arrange in Grid", self)
        self.arrange_circle_action = QAction(QIcon("resources/icons/arrange_circle.png"), "Arrange in Circle", self)
        self.arrange_by_type_action = QAction(QIcon("resources/icons/arrange_type.png"), "Group by Device Type", self)
        self.arrange_hierarchical_action = QAction(QIcon("resources/icons/arrange_tree.png"), "Hierarchical Tree Layout", self)
        
        # Create new connection-focused layout actions
        self.ortho_layers_action = QAction(QIcon("resources/icons/ortho_layers.png"), "Orthogonal Layer Layout", self)
        self.optimize_ortho_action = QAction(QIcon("resources/icons/optimize_ortho.png"), "Optimize Orthogonal Connections", self)
        self.bus_topology_action = QAction(QIcon("resources/icons/bus_topology.png"), "Bus Topology", self)
        self.star_topology_action = QAction(QIcon("resources/icons/star_topology.png"), "Star Topology", self)
        
        # Create basic alignment submenu
        basic_align_menu = QMenu("Basic Alignment", self)
        basic_align_menu.addAction(self.align_left_action)
        basic_align_menu.addAction(self.align_right_action)
        basic_align_menu.addAction(self.align_top_action)
        basic_align_menu.addAction(self.align_bottom_action)
        basic_align_menu.addSeparator()
        basic_align_menu.addAction(self.align_center_h_action)
        basic_align_menu.addAction(self.align_center_v_action)
        
        # Create distribution submenu
        distribute_menu = QMenu("Distribute", self)
        distribute_menu.addAction(self.distribute_h_action)
        distribute_menu.addAction(self.distribute_v_action)
        
        # Create arrange submenu
        arrange_menu = QMenu("Arrange", self)
        arrange_menu.addAction(self.arrange_grid_action)
        arrange_menu.addAction(self.arrange_circle_action)
        arrange_menu.addAction(self.arrange_by_type_action)
        arrange_menu.addAction(self.arrange_hierarchical_action)
        
        # Create network topology submenu
        topology_menu = QMenu("Network Topologies", self)
        topology_menu.addAction(self.ortho_layers_action)
        topology_menu.addAction(self.optimize_ortho_action)
        topology_menu.addAction(self.bus_topology_action)
        topology_menu.addAction(self.star_topology_action)
        
        # Add submenus to main menu
        self.align_menu.addMenu(basic_align_menu)
        self.align_menu.addMenu(distribute_menu)
        self.align_menu.addMenu(arrange_menu)
        self.align_menu.addMenu(topology_menu)  # Add the new topology menu
        
        # Create dropdown button
        self.align_button = QToolButton(self)
        self.align_button.setPopupMode(QToolButton.InstantPopup)
        self.align_button.setMenu(self.align_menu)
        self.align_button.setIcon(QIcon("resources/icons/align.png"))
        self.align_button.setText("Arrange")
        self.align_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addWidget(self.align_button)
        
        # Connect basic alignment actions
        self.align_left_action.triggered.connect(self._on_align_left)
        self.align_right_action.triggered.connect(self._on_align_right)
        self.align_top_action.triggered.connect(self._on_align_top)
        self.align_bottom_action.triggered.connect(self._on_align_bottom)
        self.align_center_h_action.triggered.connect(self._on_align_center_h)
        self.align_center_v_action.triggered.connect(self._on_align_center_v)
        
        # Connect distribution actions
        self.distribute_h_action.triggered.connect(self._on_distribute_h)
        self.distribute_v_action.triggered.connect(self._on_distribute_v)
        
        # Connect advanced arrangement actions
        self.arrange_grid_action.triggered.connect(self._on_arrange_grid)
        self.arrange_circle_action.triggered.connect(self._on_arrange_circle)
        self.arrange_by_type_action.triggered.connect(self._on_arrange_by_type)
        self.arrange_hierarchical_action.triggered.connect(self._on_arrange_hierarchical)
        
        # Connect new connection-focused actions
        self.ortho_layers_action.triggered.connect(self._on_ortho_layers)
        self.optimize_ortho_action.triggered.connect(self._on_optimize_ortho)
        self.bus_topology_action.triggered.connect(self._on_bus_topology)
        self.star_topology_action.triggered.connect(self._on_star_topology)
        
        # Initially disable all actions until selection changes
        self.update_actions_state()
    
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
        
        # Enable grid and circle arrangements for 4+ devices
        grid_circle_enabled = device_count >= 4
        self.arrange_grid_action.setEnabled(grid_circle_enabled)
        self.arrange_circle_action.setEnabled(device_count >= 3)
        
        # Enable advanced arrangements for 2+ devices
        advanced_enabled = device_count >= 2
        self.arrange_by_type_action.setEnabled(advanced_enabled)
        self.arrange_hierarchical_action.setEnabled(advanced_enabled)
        
        # Enable network topology actions for appropriate device counts
        self.ortho_layers_action.setEnabled(device_count >= 4)
        self.optimize_ortho_action.setEnabled(device_count >= 3)
        self.bus_topology_action.setEnabled(device_count >= 3)
        self.star_topology_action.setEnabled(device_count >= 3)
    
    # Connect existing alignment functions
    def _on_align_left(self):
        if self.alignment_controller:
            self.alignment_controller.align_left()
    
    def _on_align_right(self):
        if self.alignment_controller:
            self.alignment_controller.align_right()
    
    def _on_align_top(self):
        if self.alignment_controller:
            self.alignment_controller.align_top()
    
    def _on_align_bottom(self):
        if self.alignment_controller:
            self.alignment_controller.align_bottom()
    
    def _on_align_center_h(self):
        if self.alignment_controller:
            self.alignment_controller.align_center_horizontal()
    
    def _on_align_center_v(self):
        if self.alignment_controller:
            self.alignment_controller.align_center_vertical()
    
    def _on_distribute_h(self):
        if self.alignment_controller:
            self.alignment_controller.distribute_horizontally()
    
    def _on_distribute_v(self):
        if self.alignment_controller:
            self.alignment_controller.distribute_vertically()
    
    # Connect new arrangement functions
    def _on_arrange_grid(self):
        if self.alignment_controller:
            self.alignment_controller.arrange_in_grid()
    
    def _on_arrange_circle(self):
        if self.alignment_controller:
            self.alignment_controller.arrange_in_circle()
    
    def _on_arrange_by_type(self):
        if self.alignment_controller:
            self.alignment_controller.arrange_by_type()
    
    def _on_arrange_hierarchical(self):
        if self.alignment_controller:
            self.alignment_controller.arrange_hierarchical()
    
    # Connection-focused layout handlers
    def _on_ortho_layers(self):
        if self.alignment_controller:
            self.alignment_controller.align_orthogonal_layers()
    
    def _on_optimize_ortho(self):
        if self.alignment_controller:
            self.alignment_controller.optimize_orthogonal_layout()
    
    def _on_bus_topology(self):
        if self.alignment_controller:
            self.alignment_controller.arrange_bus_topology()
    
    def _on_star_topology(self):
        if self.alignment_controller:
            self.alignment_controller.arrange_star_topology()
