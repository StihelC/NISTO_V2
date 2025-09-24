#!/bin/bash

echo "Testing NISTO Save/Load API..."
echo

# Test 1: Health check
echo "1. Testing backend health..."
curl -s http://localhost:8002/healthz
echo
echo

# Test 2: Get current devices (should be empty initially)
echo "2. Getting current devices..."
curl -s http://localhost:8002/api/devices | jq .
echo
echo

# Test 3: Create a test device
echo "3. Creating a test device..."
curl -s -X POST http://localhost:8002/api/devices \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Router", "type": "router", "config": {"ip": "192.168.1.1"}}' | jq .
echo
echo

# Test 4: Create another test device
echo "4. Creating another test device..."
curl -s -X POST http://localhost:8002/api/devices \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Switch", "type": "switch", "config": {"ip": "192.168.1.2"}}' | jq .
echo
echo

# Test 5: Get all devices
echo "5. Getting all devices..."
DEVICES=$(curl -s http://localhost:8002/api/devices)
echo $DEVICES | jq .
echo
echo

# Test 6: Create a connection between devices
echo "6. Creating a connection..."
DEVICE1_ID=$(echo $DEVICES | jq -r '.[0].id')
DEVICE2_ID=$(echo $DEVICES | jq -r '.[1].id')
curl -s -X POST http://localhost:8002/api/connections \
  -H "Content-Type: application/json" \
  -d "{\"source_device_id\": $DEVICE1_ID, \"target_device_id\": $DEVICE2_ID, \"link_type\": \"ethernet\"}" | jq .
echo
echo

# Test 7: Save current state as a project
echo "7. Saving current state as a project..."
curl -s -X POST http://localhost:8002/api/projects/save-current \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Network", "description": "Test network configuration"}' | jq .
echo
echo

# Test 8: Get all projects
echo "8. Getting all saved projects..."
curl -s http://localhost:8002/api/projects | jq .
echo
echo

# Test 9: Auto-save current state
echo "9. Testing auto-save..."
curl -s -X POST http://localhost:8002/api/projects/auto-save | jq .
echo
echo

# Test 10: Get projects again (should now include auto-save)
echo "10. Getting projects with auto-save..."
curl -s http://localhost:8002/api/projects | jq .
echo
echo

echo "✅ All API tests completed!"
echo
echo "Frontend is accessible at: http://localhost:5173"
echo "Backend API is accessible at: http://localhost:8002"
echo
echo "To test the frontend:"
echo "1. Open http://localhost:5173 in your browser"
echo "2. Click the 'Save' button to save a project"
echo "3. Click the 'Load' button to see saved projects"
echo "4. Create some devices and connections to test auto-save"
