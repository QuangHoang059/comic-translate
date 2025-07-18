#!/usr/bin/env python3
"""
Main entry point for Comic Translate Application
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
# project_root = Path(__file__).parent
# sys.path.insert(0, str(project_root))

from container.app_container import AppContainer
from api.app import create_app


def main():
    """Main entry point"""

    # Initialize container and load config
    container = AppContainer()
    container.load_config()

    # Create FastAPI app
    app = create_app()

    # Include container in app state
    app.state.container = container

    return app


if __name__ == "__main__":
    import uvicorn

    app = main()

    # Run the application
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
