import uvicorn
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    port = int(os.getenv("ARCHON_SERVER_PORT", "8181"))
    host = os.getenv("ARCHON_HOST", "0.0.0.0")
    
    print(f"Starting Archon Server on {host}:{port}")
    
    uvicorn.run(
        "src.server.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
