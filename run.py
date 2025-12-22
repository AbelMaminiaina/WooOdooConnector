#!/usr/bin/env python
"""
Launcher script for WooCommerce-Odoo Connector

Usage:
    python run.py              # Start API server
    python run.py --help       # Show help
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    import uvicorn
    from connector.config import settings

    print("=" * 60)
    print("WooCommerce <-> Odoo Connector")
    print("=" * 60)
    print(f"Starting API server on {settings.api_host}:{settings.api_port}")
    print(f"WooCommerce URL: {settings.woo_url}")
    print(f"Odoo URL: {settings.odoo_url}")
    print("=" * 60)
    print(f"\nAPI Documentation: http://localhost:{settings.api_port}/docs")
    print(f"Health Check: http://localhost:{settings.api_port}/health\n")

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    uvicorn.run(
        "connector.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
