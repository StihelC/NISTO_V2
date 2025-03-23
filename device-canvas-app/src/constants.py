"""
Central module for application constants.
This helps avoid duplication and ensures consistency across the codebase.
"""

class Modes:
    """Constants for canvas interaction modes."""
    SELECT = "select"
    ADD_DEVICE = "add_device"
    DELETE = "delete"
    ADD_BOUNDARY = "add_boundary" 
    ADD_CONNECTION = "add_connection"

class DeviceTypes:
    """Constants for device types."""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    SERVER = "server"
    CLOUD = "cloud"
    WORKSTATION = "workstation"
    GENERIC = "generic"

class ConnectionTypes:
    """Constants for connection types."""
    ETHERNET = "ethernet"
    SERIAL = "serial"
    FIBER = "fiber"
    WIRELESS = "wireless"