#!/usr/bin/env python3
"""
Simple WSGI server runner for plagiarism detection system.
Uses Flask's built-in server with minimal configuration.
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    from app import app
    
    print("Starting Plagiarism Detection Server")
    print("URL: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop\n")
    
    # Run Flask app with minimal settings
    # These settings avoid Werkzeug auto-reload issues on Windows
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False,
        use_debugger=False
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
