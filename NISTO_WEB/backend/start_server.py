#!/usr/bin/env python3
"""Simple script to start the FastAPI server."""

import uvicorn
import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    try:
        print("Starting NISTO backend server...")
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8080,
            reload=True,
            reload_dirs=[backend_dir],
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Trying different port...")
        try:
            uvicorn.run(
                "app.main:app",
                host="127.0.0.1", 
                port=8081,
                reload=True,
                reload_dirs=[backend_dir],
                log_level="info"
            )
        except Exception as e2:
            print(f"Error on port 8081: {e2}")
            print("Trying port 3001...")
            uvicorn.run(
                "app.main:app",
                host="127.0.0.1",
                port=3001,
                reload=True,
                reload_dirs=[backend_dir],
                log_level="info"
            )
