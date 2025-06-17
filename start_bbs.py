#!/usr/bin/env python3
"""
BBS Server Startup Script
Provides options for running the secure BBS
"""

import os
import sys
import argparse
from secure_bbs import SecureBBSServer

def main():
    parser = argparse.ArgumentParser(description='Start the Secure BBS Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=2323, help='Port to bind to (default: 2323)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("           SECURE TEXT BBS SERVER")
    print("="*60)
    print(f"Starting BBS on {args.host}:{args.port}")
    print("")
    print("Security Features:")
    print("  ✓ Input validation and sanitization")
    print("  ✓ Rate limiting and abuse prevention")
    print("  ✓ Secure password hashing (PBKDF2)")
    print("  ✓ SQL injection protection")
    print("  ✓ Session timeouts")
    print("  ✓ Comprehensive logging")
    print("")
    print(f"Connect using: telnet {args.host} {args.port}")
    print("")
    print("Press Ctrl+C to stop the server")
    print("="*60)
    print("")
    
    try:
        server = SecureBBSServer(host=args.host, port=args.port)
        server.start()
    except KeyboardInterrupt:
        print("\n\nShutting down BBS server...")
        print("Goodbye!")
    except Exception as e:
        print(f"\nError starting BBS server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

