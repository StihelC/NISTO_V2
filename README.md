# NISTO

## Overview
NISTO is a PyQt-based application that allows users to create, configure, and manage device objects on a canvas. Users can add, select, move, and remove devices, create boundaries, and establish connections between devices. The application supports custom icons, device properties, and advanced interaction modes.

## Features
- **Interactive Canvas**: A central area where devices, boundaries, and connections can be displayed and interacted with.
- **Device Management**: Users can add new devices, configure their properties, and manipulate them on the canvas.
- **Connection Management**: Create and manage connections between devices with customizable styles (straight, orthogonal, curved).
- **Boundary Management**: Define and manage boundaries to group devices visually.
- **Custom Configuration Dialogs**: Each device has an associated dialog for configuration, enhancing user experience.
- **Serialization**: Save and load canvas states, including devices, connections, and boundaries.
- **Custom Icons**: Support for uploading custom icons for devices.
- **Debugging Tools**: Visualize device bounds and toggle connection points for debugging.

## Project Structure
```
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

## Key Features
### Device Management
- Add devices with predefined types (Router, Switch, Firewall, Server, etc.).
- Configure device properties such as name, IP address, and description.
- Upload custom icons for devices.

### Connection Management
- Create connections between devices with customizable styles:
  - Straight lines
  - Orthogonal (right-angle) lines
  - Curved lines
- Edit connection labels and properties.

### Boundary Management
- Define boundaries to group devices visually.
- Customize boundary names and colors.

### Serialization
- Save the current canvas state to a `.canvas` or `.json` file.
- Load a saved canvas state to restore devices, connections, and boundaries.

### Debugging Tools
- Visualize device bounds for debugging.
- Toggle connection points visibility.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.