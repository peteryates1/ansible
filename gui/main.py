#!/usr/bin/env python3
import sys
import os

# Add project root to path so 'gui' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_dependencies():
    missing = []
    try:
        import PySide6.QtCore  # noqa: F401
        import PySide6.QtGui  # noqa: F401
        import PySide6.QtWidgets  # noqa: F401
    except ImportError:
        missing.append(
            "python3-pyside6.qtcore python3-pyside6.qtgui "
            "python3-pyside6.qtwidgets"
        )
    try:
        import libvirt  # noqa: F401
    except ImportError:
        missing.append("python3-libvirt")

    if missing:
        print("Missing dependencies. Install with:", file=sys.stderr)
        print(f"  sudo apt install {' '.join(missing)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    check_dependencies()
    from gui.app import run
    run()
