from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPen
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem

ENABLED_COLOR = QColor("skyblue")
DISABLED_COLOR = QColor("#888888")


class MonitorRect(QGraphicsRectItem):
    """Draggable rectangle representing one monitor in the layout view."""

    def __init__(self, name: str, width: float, height: float):
        super().__init__(0, 0, width, height)
        self.name = name
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setBrush(QBrush(ENABLED_COLOR))
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
        )

        self.label = QGraphicsSimpleTextItem(name, self)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self._center_label()

    def _center_label(self) -> None:
        rect, label = self.rect(), self.label.boundingRect()
        self.label.setPos((rect.width() - label.width()) / 2, (rect.height() - label.height()) / 2)

    def resize(self, width: float, height: float) -> None:
        self.setRect(0, 0, width, height)
        self._center_label()

    def set_disabled_look(self, disabled: bool) -> None:
        self.setBrush(QBrush(DISABLED_COLOR if disabled else ENABLED_COLOR))
