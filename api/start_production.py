#!/usr/bin/env python3
"""
Production startup script for FinCompliance API
Optimized for Render deployment with minimal memory usage
"""
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Start the FastAPI application with production settings"""
    
    # Production configuration
    host = os.getenv("HOST", "0.0.0.0")  # Bind to all interfaces for Render
    port = int(os.getenv("PORT", 10000))  # Use Render's provided PORT
    
    # Memory optimization settings
    config = {
        "app": "app:app",
        "host": host,
        "port": port,
        "reload": False,  # Disable reload to save memory
        "workers": 1,     # Single worker for free tier
        "access_log": False,  # Disable access logs to save memory
        "log_level": "warning",  # Reduce log verbosity
    }
    
    print(f"🚀 Starting FinCompliance API in production mode")
    print(f"📡 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"💾 Memory optimizations: enabled")
    print(f"🔄 Auto-reload: disabled")
    
    # Start the server
    uvicorn.run(**config)

if __name__ == "__main__":
    main()
