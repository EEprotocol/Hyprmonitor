import sys

from PyQt6.QtWidgets import QApplication

from .window import MonitorConfigurator


def main() -> int:
    app = QApplication(sys.argv)
    window = MonitorConfigurator()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
