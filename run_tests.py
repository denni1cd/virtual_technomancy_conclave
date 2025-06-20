#!/usr/bin/env python3
"""
Simple test runner for the virtual_technomancy_conclave project.
Run with: python run_tests.py
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run pytest with appropriate settings."""
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    if not (project_root / "conclave").exists():
        print("Error: conclave directory not found. Are you in the project root?")
        sys.exit(1)
    
    # Run pytest with quiet mode
    cmd = [sys.executable, "-m", "pytest", "-q", "tests/"]
    
    print("Running tests with pytest -q...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 