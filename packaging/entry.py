"""PyInstaller entry point (absolute import so the package is bundled intact)."""
import sys

from hyprmonitor.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
