# Device Canvas Application

## Overview
The Device Canvas Application is a PyQt-based application that allows users to create, configure, and manage device objects on a canvas. Users can add, select, move, and remove devices, each represented by its own class. The application is designed for future expansion, including support for custom icons.

## Features
- **Interactive Canvas**: A central area where devices can be displayed and interacted with.
- **Device Management**: Users can add new devices, configure their properties, and manipulate them on the canvas.
- **Custom Configuration Dialogs**: Each device has an associated dialog for configuration, enhancing user experience.
- **Future Expansion**: The architecture supports the addition of custom icons and other features.

## Project Structure
```
device-canvas-app
├── src
│   ├── main.py                # Entry point of the application
│   ├── views                  # Contains UI components
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main window UI
│   │   └── canvas.py           # Canvas for device interaction
│   ├── models                 # Contains data models
│   │   ├── __init__.py
│   │   └── device.py           # Device class definition
│   ├── dialogs                # Contains dialog definitions
│   │   ├── __init__.py
│   │   └── device_config_dialog.py # Device configuration dialog
│   └── utils                  # Utility functions
│       ├── __init__.py
│       └── helpers.py          # Helper functions
├── requirements.txt           # Project dependencies
├── .gitignore                 # Files to ignore in version control
├── setup.py                   # Packaging information
└── README.md                  # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd device-canvas-app
   ```
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```
5. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the application, execute the following command:
```
python src/main.py
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.