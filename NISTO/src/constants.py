"""
Central module for application constants.
This helps avoid duplication and ensures consistency across the codebase.
"""

class Modes:
    """Constants for canvas interaction modes."""
    SELECT = "select"
    ADD_DEVICE = "add_device"
    DELETE = "delete"
    DELETE_SELECTED = "delete_selected"
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
    # Basic connection types
    ETHERNET = "ethernet"
    SERIAL = "serial"
    FIBER = "fiber"
    WIRELESS = "wireless"
    
    # Enterprise connection types
    GIGABIT_ETHERNET = "gigabit_ethernet"
    TEN_GIGABIT_ETHERNET = "10gig_ethernet"
    FORTY_GIGABIT_ETHERNET = "40gig_ethernet"
    HUNDRED_GIGABIT_ETHERNET = "100gig_ethernet"
    FIBER_CHANNEL = "fiber_channel"
    MPLS = "mpls"
    POINT_TO_POINT = "p2p"
    VPN = "vpn"
    SDWAN = "sdwan"
    SATELLITE = "satellite"
    MICROWAVE = "microwave"
    BLUETOOTH = "bluetooth"
    CUSTOM = "custom"

    # Dictionary mapping connection types to display names
    DISPLAY_NAMES = {
        ETHERNET: "Ethernet",
        SERIAL: "Serial",
        FIBER: "Fiber",
        WIRELESS: "Wireless",
        GIGABIT_ETHERNET: "Gigabit Ethernet (1GbE)",
        TEN_GIGABIT_ETHERNET: "10 Gigabit Ethernet (10GbE)",
        FORTY_GIGABIT_ETHERNET: "40 Gigabit Ethernet (40GbE)",
        HUNDRED_GIGABIT_ETHERNET: "100 Gigabit Ethernet (100GbE)",
        FIBER_CHANNEL: "Fiber Channel",
        MPLS: "MPLS",
        POINT_TO_POINT: "Point-to-Point",
        VPN: "VPN Tunnel",
        SDWAN: "SD-WAN",
        SATELLITE: "Satellite",
        MICROWAVE: "Microwave",
        BLUETOOTH: "Bluetooth",
        CUSTOM: "Custom Connection"
    }

    # Dictionary mapping connection types to default bandwidth values
    DEFAULT_BANDWIDTHS = {
        ETHERNET: "100 Mbps",
        SERIAL: "2 Mbps",
        FIBER: "1 Gbps",
        WIRELESS: "54 Mbps",
        GIGABIT_ETHERNET: "1 Gbps",
        TEN_GIGABIT_ETHERNET: "10 Gbps",
        FORTY_GIGABIT_ETHERNET: "40 Gbps",
        HUNDRED_GIGABIT_ETHERNET: "100 Gbps",
        FIBER_CHANNEL: "16 Gbps",
        MPLS: "Variable",
        POINT_TO_POINT: "100 Mbps",
        VPN: "50 Mbps",
        SDWAN: "Variable",
        SATELLITE: "15 Mbps",
        MICROWAVE: "1 Gbps",
        BLUETOOTH: "3 Mbps",
        CUSTOM: ""
    }

    @classmethod
    def get_all_types(cls):
        """Return a list of all connection types."""
        return [
            cls.ETHERNET,
            cls.SERIAL,
            cls.FIBER, 
            cls.WIRELESS,
            cls.GIGABIT_ETHERNET,
            cls.TEN_GIGABIT_ETHERNET,
            cls.FORTY_GIGABIT_ETHERNET,
            cls.HUNDRED_GIGABIT_ETHERNET,
            cls.FIBER_CHANNEL,
            cls.MPLS,
            cls.POINT_TO_POINT,
            cls.VPN,
            cls.SDWAN,
            cls.SATELLITE,
            cls.MICROWAVE,
            cls.BLUETOOTH,
            cls.CUSTOM
        ]