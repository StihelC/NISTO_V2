from PyQt5.QtWidgets import QToolBar, QAction, QMenu, QActionGroup, QToolButton
from PyQt5.QtCore import Qt
import logging

from constants import Modes, DeviceTypes
from models.connection import Connection

class MenuManager:
    """Manager for creating and managing all menus and toolbars."""
    
    def __init__(self, main_window, canvas, event_bus):
        self.main_window = main_window
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Store mode actions for enabling/disabling
        self.mode_actions = {}
    
    def create_toolbar(self):
        """Create the main toolbar."""
        # Create main toolbar for canvas modes
        toolbar = QToolBar("Main Toolbar")
        self.main_window.addToolBar(toolbar)
        
        # Create mode actions
        self._create_mode_actions(toolbar)
        
        toolbar.addSeparator()
        
        # Add clipboard actions
        self._create_clipboard_actions(toolbar)
        
        toolbar.addSeparator()
        
        # Add connection style menu/button
        self._create_connection_style_menu(toolbar)
        
        # Note: File toolbar creation has been removed
    
    def _create_mode_actions(self, toolbar):
        """Create and add mode toggle actions to the toolbar."""
        # Define modes and their properties
        modes = [
            (Modes.SELECT, "Select"),
            (Modes.ADD_DEVICE, "Add Device"),
            (Modes.ADD_CONNECTION, "Add Connection"),
            (Modes.ADD_BOUNDARY, "Add Boundary"),
            (Modes.DELETE, "Delete Tool"),
            (Modes.DELETE_SELECTED, "Delete Selected")
        ]
        
        # Create action group for mutual exclusion
        mode_group = QActionGroup(self.main_window)
        mode_group.setExclusive(True)
        
        # Create actions for each mode
        for mode_id, mode_name in modes:
            action = QAction(mode_name, self.main_window)
            action.setCheckable(True)
            # Use a lambda that captures the specific mode_id for this iteration
            action.triggered.connect(lambda checked, m=mode_id: self.main_window.set_mode(m))
            
            # Add to group and toolbar
            mode_group.addAction(action)
            toolbar.addAction(action)
            
            # Store for later reference
            self.mode_actions[mode_id] = action
            
        # Set default mode
        self.mode_actions[Modes.SELECT].setChecked(True)
    
    def _create_clipboard_actions(self, toolbar):
        """Create clipboard actions for the toolbar."""
        # Copy action
        copy_action = QAction("Copy", self.main_window)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.main_window.clipboard_manager.copy_selected)
        toolbar.addAction(copy_action)
        
        # Cut action
        cut_action = QAction("Cut", self.main_window)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.main_window.clipboard_manager.cut_selected)
        toolbar.addAction(cut_action)
        
        # Paste action
        paste_action = QAction("Paste", self.main_window)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.main_window.clipboard_manager.paste)
        toolbar.addAction(paste_action)
    
    def _create_connection_style_menu(self, toolbar):
        """Create connection style menu and button."""
        # Create style menu
        connection_style_menu = QMenu("Connection Style", self.main_window)
        
        # Create actions with labels mapping to Connection styles
        styles = [
            (Connection.STYLE_STRAIGHT, "Straight Lines"),
            (Connection.STYLE_ORTHOGONAL, "Orthogonal (Right Angle)"),
            (Connection.STYLE_CURVED, "Curved Lines")
        ]
        
        # Create action group for mutual exclusion
        style_group = QActionGroup(self.main_window)
        style_group.setExclusive(True)
        
        # Create all style actions
        for style, label in styles:
            action = QAction(label, self.main_window)
            action.setCheckable(True)
            
            # Check the default style
            if style == Connection.STYLE_STRAIGHT:
                action.setChecked(True)
                
            # Connect to style setter with explicit lambda to fix scoping issues
            action.triggered.connect(
                lambda checked, style_val=style: self.main_window.connection_controller.set_connection_style(style_val)
            )
            
            # Add to group and menu
            style_group.addAction(action)
            connection_style_menu.addAction(action)
        
        # Create and add toolbar button with popup menu
        connection_style_btn = QToolButton()
        connection_style_btn.setText("Connection Style")
        connection_style_btn.setPopupMode(QToolButton.InstantPopup)
        connection_style_btn.setMenu(connection_style_menu)
        toolbar.addWidget(connection_style_btn)
    
    def _create_connection_menu(self):
        """Create connection style menu."""
        connection_menu = self.menuBar().addMenu("&Connection")
        
        # Add connection style submenu
        style_menu = connection_menu.addMenu("Routing Style")
        
        # Straight style
        from models.connection import Connection
        straight_action = style_menu.addAction("Straight")
        straight_action.triggered.connect(
            lambda checked, s=Connection.STYLE_STRAIGHT: self.main_window.connection_controller.set_connection_style(s))
        
        # Orthogonal style
        orthogonal_action = style_menu.addAction("Orthogonal")
        orthogonal_action.triggered.connect(
            lambda checked, s=Connection.STYLE_ORTHOGONAL: self.main_window.connection_controller.set_connection_style(s))
        
        # Curved style
        curved_action = style_menu.addAction("Curved")
        curved_action.triggered.connect(
            lambda checked, s=Connection.STYLE_CURVED: self.main_window.connection_controller.set_connection_style(s))
        
        # Connection appearance submenu
        appearance_menu = connection_menu.addMenu("Appearance")
        
        # Connection type actions that define the visual style
        from constants import ConnectionTypes
        for conn_type, display_name in ConnectionTypes.DISPLAY_NAMES.items():
            type_action = appearance_menu.addAction(display_name)
            type_action.triggered.connect(
                lambda checked, t=conn_type: self.main_window.connection_controller.set_connection_type(t))
    
    def update_mode_actions(self, current_mode):
        """Update checked state of mode actions."""
        for mode, action in self.mode_actions.items():
            action.setChecked(mode == current_mode)
