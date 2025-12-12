"""
Simple script to run the OCR API server
"""

import uvicorn
import sys

if __name__ == "__main__":
    print("=" * 60)
    print("Starting OCR API Server")
    print("=" * 60)
    print()
    print("Server will be available at:")
    print("  - API: http://localhost:8080")
    print("  - Docs: http://localhost:8080/docs")
    print("  - ReDoc: http://localhost:8080/redoc")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8080,
            reload=True,  # Auto-reload on code changes
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting server: {e}")
        print("\nMake sure:")
        print("  1. Tesseract OCR is installed")
        print("  2. All dependencies are installed: pip install -r requirements.txt")
        print("  3. Port 8080 is available")
        sys.exit(1)

