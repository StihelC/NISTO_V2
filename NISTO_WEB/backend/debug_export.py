#!/usr/bin/env python3
"""Debug script to test export functionality locally."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import sessionmaker
from app.db import engine
from app import models, crud

def debug_export():
    """Debug the enhanced export functionality."""
    print("🔍 Debugging Enhanced Export Functionality")
    print("=" * 50)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        devices = crud.get_devices(db)
        connections = crud.get_connections(db)
        
        print(f"📊 Found {len(devices)} devices and {len(connections)} connections")
        
        # Test the connectivity mapping logic
        device_connections = {}  # device_id -> {'incoming': [], 'outgoing': []}
        for connection in connections:
            # Outgoing connections (device is source)
            if connection.source_device_id not in device_connections:
                device_connections[connection.source_device_id] = {'incoming': [], 'outgoing': []}
            device_connections[connection.source_device_id]['outgoing'].append({
                'target_id': connection.target_device_id,
                'target_name': connection.target_device.name if connection.target_device else f'Device_{connection.target_device_id}',
                'link_type': connection.link_type,
                'properties': connection.properties or {}
            })
            
            # Incoming connections (device is target)
            if connection.target_device_id not in device_connections:
                device_connections[connection.target_device_id] = {'incoming': [], 'outgoing': []}
            device_connections[connection.target_device_id]['incoming'].append({
                'source_id': connection.source_device_id,
                'source_name': connection.source_device.name if connection.source_device else f'Device_{connection.source_device_id}',
                'link_type': connection.link_type,
                'properties': connection.properties or {}
            })
        
        print(f"\n🔗 Device Connections Map:")
        for device_id, conn_info in device_connections.items():
            print(f"   Device {device_id}: {len(conn_info['outgoing'])} outgoing, {len(conn_info['incoming'])} incoming")
        
        # Test building enhanced device row for first device
        if devices:
            device = devices[0]
            conn_info = device_connections.get(device.id, {'incoming': [], 'outgoing': []})
            
            # Build connectivity strings
            connected_to_names = [conn['target_name'] for conn in conn_info['outgoing']]
            connected_to_types = [conn['link_type'] for conn in conn_info['outgoing']]
            connected_from_names = [conn['source_name'] for conn in conn_info['incoming']]
            connected_from_types = [conn['link_type'] for conn in conn_info['incoming']]
            
            # Calculate risk metrics
            total_connections = len(conn_info['incoming']) + len(conn_info['outgoing'])
            vulnerability_count = int(device.config.get('vulnerabilities', '0') if device.config else '0')
            risk_level = device.config.get('riskLevel', 'Unknown') if device.config else 'Unknown'
            compliance_status = device.config.get('complianceStatus', 'Unknown') if device.config else 'Unknown'
            
            print(f"\n🧪 Testing Enhanced Row for Device {device.id} ({device.name}):")
            print(f"   Total Connections: {total_connections}")
            print(f"   Connected To: {'; '.join(connected_to_names) if connected_to_names else 'None'}")
            print(f"   Connected From: {'; '.join(connected_from_names) if connected_from_names else 'None'}")
            print(f"   Risk Level: {risk_level}")
            print(f"   Vulnerabilities: {vulnerability_count}")
            print(f"   Compliance: {compliance_status}")
            
            # Show what the enhanced device_row would look like
            enhanced_columns = [
                'total_connections', 'outgoing_connections_count', 'incoming_connections_count',
                'connected_to_devices', 'connected_from_devices', 'rmf_risk_level', 
                'rmf_vulnerability_count', 'rmf_compliance_status', 'combined_risk_score'
            ]
            
            print(f"\n📋 Enhanced Columns Should Include:")
            for col in enhanced_columns:
                print(f"   - {col}")
        
        print(f"\n✅ Debug complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_export()
