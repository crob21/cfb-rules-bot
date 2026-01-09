#!/usr/bin/env python3
"""
Run the Harry Dashboard
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", 8080))
    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    
    print(f"🏈 Starting Harry Dashboard on {host}:{port}")
    print(f"📍 Open http://localhost:{port} in your browser")
    
    uvicorn.run(
        "src.dashboard.app:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes
    )

