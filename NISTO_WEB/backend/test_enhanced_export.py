#!/usr/bin/env python3
"""Test enhanced export functionality directly."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import io
import pandas as pd
from sqlalchemy.orm import sessionmaker
from app.db import engine
from app import models, crud
from app.api import _calculate_risk_score

def test_enhanced_export():
    """Test enhanced export functionality locally."""
    print("🔍 Testing Enhanced Export Functionality")
    print("=" * 50)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        devices = crud.get_devices(db)
        connections = crud.get_connections(db)
        
        print(f"📊 Found {len(devices)} devices and {len(connections)} connections")
        
        # Build connectivity mappings
        device_connections = {}
        for connection in connections:
            # Track outgoing connections  
            if connection.source_device_id not in device_connections:
                device_connections[connection.source_device_id] = {'incoming': [], 'outgoing': []}
            device_connections[connection.source_device_id]['outgoing'].append({
                'target_name': connection.target_device.name if connection.target_device else f'Device_{connection.target_device_id}',
                'link_type': connection.link_type
            })
            
            # Track incoming connections
            if connection.target_device_id not in device_connections:
                device_connections[connection.target_device_id] = {'incoming': [], 'outgoing': []}
            device_connections[connection.target_device_id]['incoming'].append({
                'source_name': connection.source_device.name if connection.source_device else f'Device_{connection.source_device_id}',
                'link_type': connection.link_type
            })
        
        # Build enhanced device data
        devices_data = []
        for device in devices:
            conn_info = device_connections.get(device.id, {'incoming': [], 'outgoing': []})
            
            connected_to = '; '.join([c['target_name'] for c in conn_info['outgoing']]) if conn_info['outgoing'] else ''
            connected_from = '; '.join([c['source_name'] for c in conn_info['incoming']]) if conn_info['incoming'] else ''
            total_connections = len(conn_info['incoming']) + len(conn_info['outgoing'])
            
            # Get RMF data from config
            risk_level = device.config.get('riskLevel', 'Unknown') if device.config else 'Unknown'
            vulnerability_count = int(device.config.get('vulnerabilities', '0') if device.config else '0')
            compliance_status = device.config.get('complianceStatus', 'Unknown') if device.config else 'Unknown'
            department = device.config.get('department', 'Unknown') if device.config else 'Unknown'
            monitoring = device.config.get('monitoringEnabled', 'Unknown') if device.config else 'Unknown'
            
            risk_score = _calculate_risk_score(risk_level, vulnerability_count, total_connections)
            
            device_row = {
                'ID': device.id,
                'Device Name': device.name,
                'Device Type': device.type,
                'X Coordinate': device.x if device.x is not None else '',
                'Y Coordinate': device.y if device.y is not None else '',
                'Total Connections': total_connections,
                'Connected To': connected_to,
                'Connected From': connected_from,
                'Risk Level': risk_level,
                'Vulnerability Count': vulnerability_count,
                'Compliance Status': compliance_status,
                'Department': department,
                'Monitoring Enabled': monitoring,
                'Overall Risk Score': risk_score,
                'Network Risk Level': 'High' if total_connections > 3 else 'Medium' if total_connections > 1 else 'Low'
            }
            
            # Add config properties with user-friendly names (no "Config:" prefix)
            all_device_config_keys = set()
            for dev in devices:
                if dev.config:
                    all_device_config_keys.update(dev.config.keys())
            
            for key in sorted(all_device_config_keys):
                # Convert camelCase to Title Case for user-friendly column names
                friendly_key = ''.join([' ' + c if c.isupper() else c for c in key]).strip().title()
                device_row[friendly_key] = device.config.get(key, '') if device.config else ''
            devices_data.append(device_row)
        
        # Create CSV
        devices_df = pd.DataFrame(devices_data)
        
        print(f"\n📋 Enhanced Device Export Columns ({len(devices_df.columns)}):")
        for col in devices_df.columns:
            print(f"   - {col}")
        
        # Show sample data for first device
        if not devices_df.empty:
            print(f"\n📊 Sample Data for Device {devices_df.iloc[0]['Device Name']}:")
            for col in devices_df.columns:
                value = devices_df.iloc[0][col]
                print(f"   {col}: {value}")
        
        # Save to CSV file for testing
        output_file = "enhanced_export_test_local.csv"
        devices_df.to_csv(output_file, index=False)
        print(f"\n✅ Enhanced export saved to: {output_file}")
        print(f"📏 CSV has {len(devices_df.columns)} columns and {len(devices_df)} rows")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_enhanced_export()
