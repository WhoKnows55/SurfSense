"""
Main entry point for running the SurfSense application.

Run with: python -m app
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main application entry point."""
    print("=" * 60)
    print("🏄 SurfSense - AI Surf Trip Planning Assistant")
    print("=" * 60)
    print("\nVersion: 0.1.0")
    print("Status: Development Setup Complete")
    print("\nNext steps:")
    print("  1. Configure your API keys in .env file")
    print("  2. Install dependencies: pip install -r requirements.txt")
    print("  3. Run the application (coming soon)")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
