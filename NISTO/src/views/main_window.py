from PyQt5.QtWidgets import QMainWindow, QDialog, QMessageBox, QAction, QDockWidget, QMenu
from PyQt5.QtCore import QPointF, QTimer, Qt
from PyQt5.QtGui import QColor, QIcon
import logging
import os

from views.canvas.canvas import Canvas
from constants import Modes
from controllers.menu_manager import MenuManager
from controllers.device_controller import DeviceController
from controllers.connection_controller import ConnectionController
from controllers.boundary_controller import BoundaryController
from controllers.clipboard_manager import ClipboardManager
from controllers.bulk_device_controller import BulkDeviceController
from controllers.bulk_property_controller import BulkPropertyController
from utils.event_bus import EventBus
from models.device import Device
from models.connection import Connection
from models.boundary import Boundary
from views.properties_panel import PropertiesPanel
from controllers.properties_controller import PropertiesController
from views.alignment_toolbar import AlignmentToolbar
from controllers.commands import AlignDevicesCommand
from controllers.device_alignment_controller import DeviceAlignmentController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NISTO")
        # Set a reasonable default size instead of maximizing
        self.setGeometry(100, 100, 1280, 800)

        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Create canvas
        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Connect status message signal
        self.canvas.statusMessage.connect(self.statusBar().showMessage)
        
        # Create event bus for communication between components
        self.event_bus = EventBus()
        
        # Initialize command_manager with a None value to avoid attribute errors
        self.command_manager = None
        
        # Initialize undo_redo_manager to None to avoid attribute errors
        self.undo_redo_manager = None
        
        # Initialize controllers
        self._init_controllers()
        
        # Create menu manager and toolbar
        self.menu_manager = MenuManager(self, self.canvas, self.event_bus)
        self.menu_manager.create_toolbar()
        
        # Create UI components
        self._create_ui_components()
        
        # Connect signals
        self.connect_signals()
        
        # Set initial mode
        self.set_mode(Modes.SELECT)
        
        # Register event handlers
        self._register_event_handlers()
        
        # Remove the line that maximizes the window on startup
        # self.showMaximized()

    def _init_controllers(self):
        """Initialize controllers for device, connection, and boundary management."""
        self.device_controller = DeviceController(self.canvas, self.event_bus)
        self.connection_controller = ConnectionController(self.canvas, self.event_bus)
        self.boundary_controller = BoundaryController(self.canvas, self.event_bus)
        
        # Initialize clipboard manager
        self.clipboard_manager = ClipboardManager(
            self.canvas, 
            self.device_controller,
            self.connection_controller,
            self.event_bus
        )
        
        # Initialize bulk controllers - these will be fully set up after command_manager is initialized
        self.bulk_device_controller = None
        self.bulk_property_controller = None

    def _create_ui_components(self):
        """Create UI components like menus, panels, and toolbars."""
        # Create menus
        self._create_file_menu()
        self._create_view_menu()
        self._create_device_menu()  # New menu for device operations
        
        # Set up keyboard shortcuts
        self._setup_shortcuts()
        
        # Create properties panel
        self.properties_panel = PropertiesPanel(self)
        self.right_panel = QDockWidget("Properties", self)
        self.right_panel.setWidget(self.properties_panel)
        self.right_panel.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_panel)

        # Initialize properties controller - defer its creation until command_manager is properly set in main.py
        self.properties_controller = None

        # Setup alignment tools
        self.setup_alignment_tools()

    def _create_device_menu(self):
        """Create a dedicated device menu for device operations."""
        device_menu = self.menuBar().addMenu("&Devices")
        
        # Add device action
        add_device_action = QAction("&Add Device...", self)
        add_device_action.setStatusTip("Add a new device to the canvas")
        add_device_action.triggered.connect(lambda: self._on_add_device_requested())
        device_menu.addAction(add_device_action)
        
        # Bulk add action
        bulk_add_action = QAction("Add &Multiple Devices...", self)
        bulk_add_action.setStatusTip("Add multiple different devices in bulk")
        bulk_add_action.triggered.connect(self._on_bulk_add_device_requested)
        device_menu.addAction(bulk_add_action)
        
        device_menu.addSeparator()
        
        # Bulk edit action
        bulk_edit_action = QAction("&Edit Selected Devices...", self)
        bulk_edit_action.setStatusTip("Edit properties of multiple selected devices")
        bulk_edit_action.triggered.connect(self._on_edit_selected_devices)
        device_menu.addAction(bulk_edit_action)
        
        # Device import/export submenu
        export_menu = QMenu("&Export", self)
        export_menu.addAction("Export Selected Devices as CSV...")
        export_menu.addAction("Export All Devices as CSV...")
        device_menu.addMenu(export_menu)
        
        import_action = QAction("&Import Devices from CSV...", self)
        device_menu.addAction(import_action)

    def _register_event_handlers(self):
        """Register event handlers with the event bus."""
        if self.event_bus:
            # Device property events
            self.event_bus.on('device_property_changed', self._on_device_property_changed)
            self.event_bus.on('device_display_properties_changed', self._on_device_display_properties_changed)
            
            # Device modification events
            self.event_bus.on('device_added', self._on_device_added)
            self.event_bus.on('device_removed', self._on_device_removed)
            
            # Connection events
            self.event_bus.on('connection_added', self._on_connection_added)
            self.event_bus.on('connection_removed', self._on_connection_removed)
            
            # Bulk operation events
            self.event_bus.on('bulk_devices_added', self._on_bulk_devices_added)
            self.event_bus.on('bulk_properties_changed', self._on_bulk_properties_changed)

    def setup_properties_controller(self):
        """Set up the properties controller after command_manager is initialized."""
        if self.properties_controller is None:
            self.properties_controller = PropertiesController(
                self.canvas,
                self.properties_panel,
                self.event_bus,
                self.command_manager.undo_redo_manager if self.command_manager else None
            )
        
        # Set up bulk controllers now that command_manager is available
        if self.bulk_device_controller is None:
            self.bulk_device_controller = BulkDeviceController(
                self.canvas,
                self.device_controller,
                self.event_bus,
                self.command_manager.undo_redo_manager if self.command_manager else None
            )
        
        if self.bulk_property_controller is None:
            self.bulk_property_controller = BulkPropertyController(
                self.canvas,
                self.device_controller,
                self.event_bus,
                self.command_manager.undo_redo_manager if self.command_manager else None
            )
        
        # Initialize device alignment controller after undo_redo_manager is available
        if not hasattr(self, 'device_alignment_controller') or self.device_alignment_controller is None:
            self.undo_redo_manager = self.command_manager.undo_redo_manager if self.command_manager else None
            self.device_alignment_controller = DeviceAlignmentController(
                event_bus=self.event_bus,
                undo_redo_manager=self.undo_redo_manager
            )
            
            # Connect canvas alignment signal to controller
            self.canvas.align_devices_requested.connect(self._on_align_devices_requested)

    def setup_alignment_tools(self):
        """Set up the alignment toolbar and controller."""
        # Create alignment controller - use DeviceAlignmentController instead of undefined AlignmentController
        self.alignment_controller = DeviceAlignmentController(
            self.event_bus, 
            self.command_manager.undo_redo_manager if (hasattr(self, 'command_manager') and self.command_manager) else None
        )
        
        # Store a reference to the canvas in the alignment controller
        self.alignment_controller.canvas = self.canvas
        
        # Create alignment dropdown button instead of toolbar
        self._create_alignment_button()
        
        # Connect selection changed signal to update button state
        self.canvas.selection_changed.connect(self._update_alignment_button_state)
        
        # Connect alignment signals
        if self.event_bus:
            self.event_bus.on('devices.aligned', self.on_devices_aligned)

    def _create_alignment_button(self):
        """Create a dropdown button for alignment options."""
        from PyQt5.QtWidgets import QToolBar, QToolButton
        from PyQt5.QtGui import QIcon
        
        # Create a small toolbar for the alignment button
        alignment_toolbar = QToolBar("Alignment", self)
        alignment_toolbar.setMovable(True)
        alignment_toolbar.setFloatable(True)
        
        # Create the dropdown button
        self.alignment_button = QToolButton()
        self.alignment_button.setText("Align")
        self.alignment_button.setIcon(QIcon.fromTheme("format-justify-fill"))
        self.alignment_button.setPopupMode(QToolButton.InstantPopup)
        self.alignment_button.setToolTip("Alignment Options")
        
        # Create the menu for the button
        alignment_menu = QMenu(self)
        
        # Basic alignment submenu
        basic_align = alignment_menu.addMenu("Basic Alignment")
        
        basic_actions = {
            "Align Left": "left",
            "Align Right": "right",
            "Align Top": "top",
            "Align Bottom": "bottom",
            "Align Center Horizontally": "center_h",
            "Align Center Vertically": "center_v",
            "Distribute Horizontally": "distribute_h",
            "Distribute Vertically": "distribute_v"
        }
        
        for action_text, alignment_type in basic_actions.items():
            action = basic_align.addAction(action_text)
            action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                   self.canvas.align_selected_devices(a_type))
        
        # Network layouts submenu
        network_layouts = alignment_menu.addMenu("Network Layouts")
        
        layout_actions = {
            "Grid Arrangement": "grid",
            "Circle Arrangement": "circle",
            "Star Arrangement": "star",
            "Bus Arrangement": "bus"
        }
        
        for action_text, alignment_type in layout_actions.items():
            action = network_layouts.addAction(action_text)
            action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                   self.canvas.align_selected_devices(a_type))
        
        # NIST RMF related layouts
        security_layouts = alignment_menu.addMenu("Security Architectures")
        
        security_actions = {
            "DMZ Architecture": "dmz",
            "Defense-in-Depth Layers": "defense_in_depth",
            "Segmented Network": "segments",
            "Zero Trust Architecture": "zero_trust",
            "SCADA/ICS Zones": "ics_zones"
        }
        
        for action_text, alignment_type in security_actions.items():
            action = security_layouts.addAction(action_text)
            action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                   self.canvas.align_selected_devices(a_type))
        
        # Set the menu to the button
        self.alignment_button.setMenu(alignment_menu)
        
        # Add the button to the toolbar
        alignment_toolbar.addWidget(self.alignment_button)
        
        # Add the toolbar to the main window
        self.addToolBar(Qt.TopToolBarArea, alignment_toolbar)
        
        # Set initial state
        self._update_alignment_button_state()
    
    def _update_alignment_button_state(self, selected_items=None):
        """Update alignment button state based on selection."""
        # Get selected devices if not provided
        if selected_items is None:
            selected_items = self.canvas.scene().selectedItems()
        
        # Count selected devices
        selected_devices = [item for item in selected_items if item in self.canvas.devices]
        
        # Enable/disable the button based on selection count
        self.alignment_button.setEnabled(len(selected_devices) >= 2)
        
        # Update tooltip to show how many devices are selected
        if len(selected_devices) >= 2:
            self.alignment_button.setToolTip(f"Align {len(selected_devices)} selected devices")
        else:
            self.alignment_button.setToolTip("Alignment (select at least 2 devices)")

    # Event handler methods
    def _on_device_property_changed(self, device, property_name):
        """Handle device property change events."""
        # If the property is being displayed, update the label
        if hasattr(device, 'display_properties') and property_name in device.display_properties:
            if device.display_properties[property_name]:
                device.update_property_labels()

    def _on_device_display_properties_changed(self, device):
        """Handle changes to which properties are displayed under devices."""
        device.update_property_labels()
        
    def _on_device_added(self, device):
        """Handle device added event."""
        self.statusBar().showMessage(f"Added device: {device.name}", 3000)
        
    def _on_device_removed(self, device):
        """Handle device removed event."""
        self.statusBar().showMessage(f"Removed device: {device.name}", 3000)
        
    def _on_connection_added(self, connection):
        """Handle connection added event."""
        source = connection.source_device.name if hasattr(connection, 'source_device') else "unknown"
        target = connection.target_device.name if hasattr(connection, 'target_device') else "unknown"
        self.statusBar().showMessage(f"Added connection: {source} to {target}", 3000)
        
    def _on_connection_removed(self, connection):
        """Handle connection removed event."""
        self.statusBar().showMessage("Connection removed", 3000)

    def on_devices_aligned(self, devices, original_positions, alignment_type):
        """Handle device alignment for undo/redo support."""
        if hasattr(self, 'command_manager') and self.command_manager and hasattr(self.command_manager, 'undo_redo_manager'):
            # Create command for undo/redo
            command = AlignDevicesCommand(
                self.alignment_controller,
                devices,
                original_positions,
                alignment_type
            )
            
            # Push command to undo stack
            self.command_manager.undo_redo_manager.push_command(command)
            
            self.logger.debug(f"Added alignment command to undo stack: {alignment_type}")
            self.statusBar().showMessage(f"Aligned {len(devices)} devices: {alignment_type}", 3000)

    def _on_bulk_devices_added(self, count):
        """Handle bulk device addition event."""
        self.statusBar().showMessage(f"Added {count} devices in bulk", 3000)
    
    def _on_bulk_properties_changed(self, devices):
        """Handle bulk property change event."""
        self.statusBar().showMessage(f"Updated properties for {len(devices)} devices", 3000)
        
    def _on_add_device_requested(self):
        """Show dialog to add a device at center of view."""
        view_center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
        self.device_controller.on_add_device_requested(view_center)
    
    def _on_bulk_add_device_requested(self):
        """Show dialog to add multiple devices in bulk."""
        if self.bulk_device_controller:
            # Get the center of the current view as default position
            view_center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
            self.bulk_device_controller.show_bulk_add_dialog(view_center)
        else:
            self.logger.error("Bulk device controller not initialized")
    
    def _on_edit_selected_devices(self):
        """Show dialog to edit properties of selected devices."""
        if self.bulk_property_controller:
            self.bulk_property_controller.edit_selected_devices()
        else:
            self.logger.error("Bulk property controller not initialized")

    def _create_file_menu(self):
        """Create the File menu with save/load actions."""
        file_menu = self.menuBar().addMenu("File")
        
        # Save canvas action
        save_action = QAction("Save Canvas", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_canvas)
        file_menu.addAction(save_action)
        
        # Load canvas action
        load_action = QAction("Load Canvas", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_canvas)
        file_menu.addAction(load_action)
        
        # Exit action
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _create_edit_menu(self):
        """Create the Edit menu with clipboard and undo/redo actions."""
        edit_menu = self.menuBar().addMenu("Edit")
        
        # Only add undo/redo actions if command_manager is initialized
        if self.command_manager:
            # Undo action
            undo_action = QAction("Undo", self)
            undo_action.setShortcut("Ctrl+Z")
            undo_action.triggered.connect(self.command_manager.undo)
            undo_action.setEnabled(self.command_manager.can_undo())
            self.undo_action = undo_action
            edit_menu.addAction(undo_action)
            
            # Redo action
            redo_action = QAction("Redo", self)
            redo_action.setShortcut("Ctrl+Y")
            redo_action.triggered.connect(self.command_manager.redo)
            redo_action.setEnabled(self.command_manager.can_redo())
            self.redo_action = redo_action
            edit_menu.addAction(redo_action)
            
            # Add separator after undo/redo
            edit_menu.addSeparator()
            
            # Connect to undo/redo manager signals for updates
            self.command_manager.undo_redo_manager.stack_changed.connect(self._update_undo_redo_actions)
        
        # Cut action
        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.clipboard_manager.cut_selected)
        edit_menu.addAction(cut_action)
        
        # Copy action
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.clipboard_manager.copy_selected)
        edit_menu.addAction(copy_action)
        
        # Paste action
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.clipboard_manager.paste)
        edit_menu.addAction(paste_action)
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.on_delete_selected_requested)
        edit_menu.addAction(delete_action)

    def _update_undo_redo_actions(self):
        """Update the undo/redo actions based on state."""
        if self.command_manager and hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(self.command_manager.can_undo())
            self.undo_action.setText(self.command_manager.get_undo_text())
            
        if self.command_manager and hasattr(self, 'redo_action'):
            self.redo_action.setEnabled(self.command_manager.can_redo())
            self.redo_action.setText(self.command_manager.get_redo_text())

    def _create_view_menu(self):
        """Create the View menu."""
        view_menu = self.menuBar().addMenu("&View")
        
        # Zoom In action - Fix shortcut
        zoom_in_action = QAction("Zoom In", self)
        # Using equals sign for plus to avoid issues with Qt shortcut parsing
        zoom_in_action.setShortcut("Ctrl+=")  # This works for both Ctrl++ and Ctrl+=
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        # Zoom Out action
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        # Reset Zoom action
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        # Reset View action (zoom + center)
        reset_view_action = QAction("Reset View to Home", self)
        reset_view_action.setShortcut("Ctrl+Home")
        reset_view_action.triggered.connect(self.canvas.reset_view)
        view_menu.addAction(reset_view_action)
        
        # Set Home Position action
        set_home_action = QAction("Set Current View as Home", self)
        set_home_action.triggered.connect(self._set_current_as_home)
        view_menu.addAction(set_home_action)
        
        view_menu.addSeparator()
        
        return view_menu

    def _set_current_as_home(self):
        """Set the current view center as the home position."""
        # Get the current center of the viewport in scene coordinates
        viewport_center = self.canvas.mapToScene(
            self.canvas.viewport().rect().center()
        )
        self.canvas.set_home_position(viewport_center)
        self.statusBar().showMessage(f"Home position set to ({viewport_center.x():.1f}, {viewport_center.y():.1f})")

    def _setup_shortcuts(self):
        """Set up additional keyboard shortcuts."""
        # These shortcuts work globally in the main window
        
        # Delete key for deleting selected items
        # This function is already handled by the canvas and mode system
        pass

    def connect_signals(self):
        """Connect canvas signals to appropriate controller handlers."""
        self.canvas.add_device_requested.connect(self.device_controller.on_add_device_requested)
        self.canvas.delete_device_requested.connect(self.device_controller.on_delete_device_requested)
        self.canvas.add_boundary_requested.connect(self.boundary_controller.on_add_boundary_requested)
        self.canvas.add_connection_requested.connect(self.connection_controller.on_add_connection_requested)
        self.canvas.delete_connection_requested.connect(self.connection_controller.on_delete_connection_requested)
        self.canvas.delete_boundary_requested.connect(self.boundary_controller.on_delete_boundary_requested)
        self.canvas.delete_item_requested.connect(self.on_delete_item_requested)
        self.canvas.delete_selected_requested.connect(self.on_delete_selected_requested)
        self.canvas.connect_multiple_devices_requested.connect(self.connection_controller.on_connect_multiple_devices_requested)
    
    def set_mode(self, mode):
        """Set the current interaction mode."""
        self.canvas.set_mode(mode)
        self.logger.info(f"Mode changed to: {mode}")
        # Update menu/toolbar to reflect current mode
        self.menu_manager.update_mode_actions(mode)
        
    def on_delete_item_requested(self, item):
        """Handle request to delete a non-specific item."""
        if item:
            self.logger.info(f"Deleting item of type {type(item).__name__}")
            
            # Find the top-level parent item if it's part of a composite
            top_item = item
            while top_item.parentItem():
                top_item = top_item.parentItem()
                
            # Dispatch to appropriate controller based on type
            from models.device import Device
            from models.connection import Connection
            from models.boundary import Boundary
            
            if isinstance(top_item, Device):
                self.device_controller.on_delete_device_requested(top_item)
            elif isinstance(top_item, Connection):
                self.connection_controller.on_delete_connection_requested(top_item)
            elif isinstance(top_item, Boundary):
                self.boundary_controller.on_delete_boundary_requested(top_item)
            else:
                # Generic item with no specific controller
                self.canvas.scene().removeItem(top_item)
        
    def on_delete_selected_requested(self):
        """Handle request to delete all selected items."""
        selected_items = self.canvas.scene().selectedItems()
        
        if not selected_items:
            return
        
        try:
            self.logger.info(f"Attempting to delete {len(selected_items)} selected items")
            
            # Group items by type to handle deletion in the correct order
            connections = [item for item in selected_items if isinstance(item, Connection)]
            devices = [item for item in selected_items if isinstance(item, Device)]
            boundaries = [item for item in selected_items if isinstance(item, Boundary)]
            
            # Use composite command to handle undo/redo for multiple items
            if hasattr(self, 'command_manager') and self.command_manager:
                from controllers.commands import CompositeCommand
                composite_cmd = CompositeCommand(description=f"Delete {len(selected_items)} Selected Items")
                composite_cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                using_commands = True
            else:
                composite_cmd = None
                using_commands = False
            
            # Delete connections first to avoid references to deleted devices
            self.logger.info(f"Deleting {len(connections)} connections")
            for connection in connections:
                if using_commands:
                    from controllers.commands import DeleteConnectionCommand
                    cmd = DeleteConnectionCommand(self.connection_controller, connection)
                    cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                    composite_cmd.add_command(cmd)
                else:
                    self.connection_controller._delete_connection(connection)
            
            # Delete devices
            self.logger.info(f"Deleting {len(devices)} devices")
            for device in devices:
                if using_commands:
                    from controllers.commands import DeleteDeviceCommand
                    cmd = DeleteDeviceCommand(self.device_controller, device)
                    cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                    composite_cmd.add_command(cmd)
                else:
                    self.device_controller._delete_device(device)
            
            # Delete boundaries
            self.logger.info(f"Deleting {len(boundaries)} boundaries")
            for boundary in boundaries:
                if using_commands:
                    from controllers.commands import DeleteBoundaryCommand
                    cmd = DeleteBoundaryCommand(self.boundary_controller, boundary)
                    composite_cmd.add_command(cmd)
                else:
                    self.boundary_controller.on_delete_boundary_requested(boundary)
            
            # Push the composite command if we're using undo/redo
            if composite_cmd and composite_cmd.commands:
                self.logger.info(f"Pushing composite delete command with {len(composite_cmd.commands)} actions")
                self.command_manager.undo_redo_manager.push_command(composite_cmd)
                
            # Force a complete update of the canvas
            self.canvas.viewport().update()
            
            self.logger.info(f"Deleted {len(connections)} connections, {len(devices)} devices, and {len(boundaries)} boundaries")
        except Exception as e:
            self.logger.error(f"Error in delete_selected: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def keyPressEvent(self, event):
        """Handle key press events."""
        # Let the canvas and its modes handle the key first
        if self.canvas.scene().focusItem():
            # If an item has focus, let Qt's standard event handling work
            super().keyPressEvent(event)
            return
            
        # Handle keyboard shortcuts using key combinations directly
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.copy_selected()
            event.accept()
        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.paste()
            event.accept()
        elif event.key() == Qt.Key_X and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.cut_selected()
            event.accept()
        else:
            # Pass to parent for default handling
            super().keyPressEvent(event)
    
    def save_canvas(self):
        """Save the current canvas to a file."""
        from views.file_dialog import SaveCanvasDialog
        
        success, message = SaveCanvasDialog.save_canvas(self, self.canvas)
        if success:
            self.logger.info("Canvas saved successfully")
        else:
            self.logger.warning(f"Canvas save failed: {message}")

    def load_canvas(self):
        """Load a canvas from a file."""
        from views.file_dialog import LoadCanvasDialog
        
        success, message = LoadCanvasDialog.load_canvas(self, self.canvas)
        if success:
            self.logger.info("Canvas loaded successfully")
        else:
            self.logger.warning(f"Canvas load failed: {message}")

    def _on_align_devices_requested(self, alignment_type, devices):
        """Handle request to align devices."""
        # Make sure the controller exists
        if not hasattr(self, 'device_alignment_controller') or self.device_alignment_controller is None:
            self.undo_redo_manager = self.command_manager.undo_redo_manager if self.command_manager else None
            self.device_alignment_controller = DeviceAlignmentController(
                event_bus=self.event_bus,
                undo_redo_manager=self.undo_redo_manager
            )
            
        self.device_alignment_controller.align_devices(alignment_type, devices)