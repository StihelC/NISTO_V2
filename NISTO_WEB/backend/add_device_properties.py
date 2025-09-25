#!/usr/bin/env python3
"""Add sample properties to existing devices for testing export functionality."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import sessionmaker
from app.db import engine
from app import models, crud, schemas

def add_device_properties():
    """Add sample config properties to existing devices."""
    print("🔧 Adding Device Properties for Export Testing")
    print("=" * 50)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        devices = crud.get_devices(db)
        print(f"📊 Found {len(devices)} devices")
        
        # Sample properties to add
        sample_configs = [
            {"riskLevel": "High", "vulnerabilities": "3", "complianceStatus": "Non-Compliant", "monitoringEnabled": "true", "department": "IT"},
            {"riskLevel": "Low", "vulnerabilities": "0", "complianceStatus": "Compliant", "monitoringEnabled": "true", "department": "Finance"},
            {"riskLevel": "Moderate", "vulnerabilities": "1", "complianceStatus": "Partially Compliant", "monitoringEnabled": "false", "department": "HR"},
            {"riskLevel": "High", "vulnerabilities": "5", "complianceStatus": "Non-Compliant", "monitoringEnabled": "true", "department": "Operations"},
            {"riskLevel": "Very Low", "vulnerabilities": "0", "complianceStatus": "Compliant", "monitoringEnabled": "true", "department": "Sales"},
            {"riskLevel": "Moderate", "vulnerabilities": "2", "complianceStatus": "Compliant", "monitoringEnabled": "false", "department": "Marketing"},
            {"riskLevel": "High", "vulnerabilities": "4", "complianceStatus": "Non-Compliant", "monitoringEnabled": "true", "department": "Support"}
        ]
        
        for i, device in enumerate(devices):
            if not device.config or len(device.config) == 0:
                # Add properties to devices that don't have any
                config_to_add = sample_configs[i % len(sample_configs)]
                
                update_data = schemas.DeviceUpdate(config=config_to_add)
                updated_device = crud.update_device(db, device, update_data)
                
                print(f"   ✅ Updated device {device.id} ({device.name}) with config: {config_to_add}")
            else:
                print(f"   ⏭️  Device {device.id} ({device.name}) already has config: {device.config}")
        
        print(f"\n🔍 Verifying updates...")
        devices = crud.get_devices(db)
        
        all_config_keys = set()
        for device in devices:
            if device.config:
                all_config_keys.update(device.config.keys())
                print(f"   Device {device.id}: {list(device.config.keys())}")
        
        print(f"\n📊 All config properties found: {sorted(all_config_keys)}")
        print(f"✅ Device properties added successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    add_device_properties()
