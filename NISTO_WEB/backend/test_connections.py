#!/usr/bin/env python3
"""Test script to verify connection persistence in the database."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import sessionmaker
from app.db import engine
from app import models, crud, schemas

def test_connection_persistence():
    """Test if connections are properly saved and retrieved from database."""
    print("🧪 Testing Connection Persistence")
    print("=" * 50)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get current devices and connections
        devices = crud.get_devices(db)
        connections = crud.get_connections(db)
        
        print(f"📊 Current Database State:")
        print(f"   Devices: {len(devices)}")
        print(f"   Connections: {len(connections)}")
        
        # Show device details
        print(f"\n📋 Device Details:")
        for device in devices:
            print(f"   ID {device.id}: {device.name} ({device.type})")
            print(f"     Position: ({device.x}, {device.y})")
            print(f"     Config: {device.config}")
        
        # Show connection details
        print(f"\n🔗 Connection Details:")
        for connection in connections:
            print(f"   ID {connection.id}: {connection.source_device_id} → {connection.target_device_id}")
            print(f"     Type: {connection.link_type}")
            print(f"     Properties: {connection.properties}")
            if connection.source_device and connection.target_device:
                print(f"     Devices: {connection.source_device.name} → {connection.target_device.name}")
        
        # Test creating a connection if we have 2+ devices and no connections
        if len(devices) >= 2 and len(connections) == 0:
            print(f"\n➕ Creating test connection between devices...")
            connection_data = schemas.ConnectionCreate(
                source_device_id=devices[0].id,
                target_device_id=devices[1].id,
                link_type="ethernet",
                properties={"bandwidth": "1Gbps", "test": "auto-created"}
            )
            
            new_connection = crud.create_connection(db, connection_data)
            print(f"   ✅ Created connection ID {new_connection.id}")
            
            # Verify it was saved
            connections = crud.get_connections(db)
            print(f"   📊 Connections after creation: {len(connections)}")
        
        # Test property export data structure
        print(f"\n🔍 Export Data Analysis:")
        
        # Collect all device config keys
        all_device_config_keys = set()
        for device in devices:
            if device.config:
                all_device_config_keys.update(device.config.keys())
        
        # Collect all connection property keys
        all_connection_property_keys = set()
        for connection in connections:
            if connection.properties:
                all_connection_property_keys.update(connection.properties.keys())
        
        print(f"   Device config properties found: {sorted(all_device_config_keys) if all_device_config_keys else 'None'}")
        print(f"   Connection properties found: {sorted(all_connection_property_keys) if all_connection_property_keys else 'None'}")
        
        # Prepare export-style data
        devices_data = []
        for device in devices:
            device_row = {
                'ID': device.id,
                'Name': device.name,
                'Type': device.type,
                'X Position': device.x if device.x is not None else '',
                'Y Position': device.y if device.y is not None else '',
            }
            
            # Add all possible config properties as individual columns
            for key in sorted(all_device_config_keys):
                device_row[f'Config: {key}'] = device.config.get(key, '') if device.config else ''
                
            devices_data.append(device_row)
        
        print(f"\n📄 Sample Export Data:")
        print(f"   Device columns: {list(devices_data[0].keys()) if devices_data else 'No devices'}")
        
        print(f"\n✅ Connection persistence test complete!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_connection_persistence()
