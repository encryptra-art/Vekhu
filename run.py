"""
PULSE Application Server Runner
Starts uvicorn development server on localhost:8000
"""

import uvicorn
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("  PULSE — Real-Time Public Sentiment & Perception Index")
    print("  Architecture: FastAPI + SQLite + Tailwind Design System")
    print("  Server launching on: http://127.0.0.1:8000")
    print("=" * 60)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=[current_dir])
