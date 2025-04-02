# NISTO

## Overview

NISTO is a PyQt-based network topology design and visualization application that allows users to create, configure, and manage network devices on an interactive canvas. Users can add, select, move, and delete devices, create boundaries, and establish connections between devices. The application supports custom icons, device properties, advanced alignment tools, and provides a complete solution for designing and documenting network topologies.

## Features

- **Interactive Canvas**: A central area where devices, boundaries, and connections can be displayed and interacted with.
- **Device Management**: Add, configure, move, and remove devices with custom properties.
- **Connection Management**: Create connections between devices with multiple routing styles (straight, orthogonal, curved).
- **Boundary Management**: Define visual boundaries to group related devices.
- **Property Display**: Show device properties directly under the device icons on the canvas.
- **Undo/Redo Support**: Complete history tracking for all operations.
- **Clipboard Operations**: Cut, copy, and paste devices and connections.
- **Alignment Tools**: Multiple alignment options including grid, circle, and custom topology arrangements.
- **Custom Configuration**: Each device type has associated properties that can be customized.
- **Serialization**: Save and load canvas states including devices, connections, boundaries, and their properties.
- **Custom Icons**: Support for uploading custom device icons.
- **Z-Order Management**: Control the visual layering of elements.
- **Bulk Operations**: Add or edit multiple devices at once.
- **Zoom and Pan**: Navigate large topologies with zoom in/out and canvas panning.

## Architecture

NISTO follows a Model-View-Controller (MVC) architecture:

- **Models**: Define the data structures for devices, connections, and boundaries
- **Views**: Handle the user interface elements including the canvas, toolbars, and property panels
- **Controllers**: Manage interaction between models and views, handle user input, and maintain application state

## Key Components

### Canvas

The central workspace where the network topology is displayed and manipulated. The canvas supports:

- Multiple interaction modes (select, add, delete)
- Zooming and panning
- Rubber-band selection
- Context menus

### Device Management

Devices are the core elements in network topologies. The application provides:

- Multiple device types (routers, switches, firewalls, etc.)
- Custom device icons
- Property editing
- Visual property display under device icons

### Connection Management

Connections represent links between devices:

- Multiple routing styles (straight lines, orthogonal routes, curves)
- Connection properties (bandwidth, latency, etc.)
- Visual connection points

### Boundary Management

Boundaries help organize devices into logical groups:

- Resizable boundary regions
- Custom names and colors
- Devices can be listed by boundary

### Properties Panel

A dynamic properties panel allows editing:

- General properties (name, z-index)
- Device-specific properties
- Connection properties
- Boundary properties
- Toggle which properties to display on the canvas

### Alignment Tools

Advanced alignment capabilities include:

- Basic alignment (left, right, top, bottom, center)
- Distribution (horizontal, vertical)
- Arrangement in patterns (grid, circle)
- Network topologies (bus, star, etc.)
- Orthogonal layout optimization

## Technical Details

- **Framework**: Built with PyQt5
- **Graphics**: Uses QGraphicsScene and QGraphicsView for rendering
- **Event System**: Custom event bus for component communication
- **Command Pattern**: For undo/redo functionality
- **Signal-Slot**: For UI updates and event handling

## Future Enhancements

- Network simulation capabilities
- IP addressing and subnet visualization
- Configuration generation for network devices
- Integration with external network tools
- Collaboration features

## Project Structure

```text
device-canvas-app
├── src
│   ├── main.py                # Entry point of the application
│   ├── constants.py           # Centralized constants for the application
│   ├── views                  # Contains UI components
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main window UI
│   │   ├── canvas.py           # Canvas for device interaction
│   │   ├── file_dialog.py      # File save/load dialogs
│   │   └── modes.py            # Base classes for canvas interaction modes
│   ├── models                 # Contains data models
│   │   ├── __init__.py
│   │   ├── device.py           # Device class definition
│   │   ├── connection.py       # Connection class definition
│   │   └── boundary.py         # Boundary class definition
│   ├── dialogs                # Contains dialog definitions
│   │   ├── __init__.py
│   │   ├── device_config_dialog.py # Device configuration dialog
│   │   └── device_dialog.py    # Dialog for creating/editing devices
│   ├── controllers            # Controllers for managing application logic
│   │   └── mode_manager.py     # Manages canvas interaction modes
│   ├── utils                  # Utility functions
│   │   ├── __init__.py
│   │   ├── helpers.py          # Helper functions
│   │   └── serializer.py       # Serialization and deserialization logic
├── requirements.txt           # Project dependencies
├── setup.py                   # Packaging information
├── README.md                  # Project documentation
└── 3321.canvas                # Example canvas file
```

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   ```

2. Navigate to the project directory:

   ```bash
   cd device-canvas-app
   ```

3. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:
   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

5. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:

```bash
python src/main.py
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
