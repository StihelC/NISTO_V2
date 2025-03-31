# Import the Canvas class which will aggregate all components
from .canvas import Canvas

# Import canvas components for direct access if needed
from .graphics_manager import TemporaryGraphicsManager
from .selection_box import SelectionBox
from .mode_manager import CanvasModeManager

# Import modes
from .modes import (
    CanvasMode, DeviceInteractionMode,
    SelectMode, AddDeviceMode, 
    DeleteMode, DeleteSelectedMode,
    AddBoundaryMode, AddConnectionMode
)

# Define what gets imported with "from canvas import *"
__all__ = [
    'Canvas',
    'TemporaryGraphicsManager',
    'SelectionBox',
    'CanvasModeManager',
    'CanvasMode',
    'DeviceInteractionMode',
    'SelectMode',
    'AddDeviceMode',
    'DeleteMode',
    'DeleteSelectedMode',
    'AddBoundaryMode',
    'AddConnectionMode'
]
