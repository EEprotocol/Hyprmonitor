import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QGraphicsScene, QGraphicsView, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from . import hyprctl
from .hyprctl import HyprctlError, Monitor
from .widgets import MonitorRect

SCALE = 12  # one scene unit == SCALE screen pixels


class MonitorConfigurator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wayland Monitor Configurator")
        self.setMinimumSize(800, 500)

        self.state: dict[str, Monitor] = {}
        self.rects: dict[str, MonitorRect] = {}
        self.current: Monitor | None = None
        self._updating = False  # True while widgets are being filled programmatically

        self._build_ui()
        self.reload_monitors()
        self.scene.selectionChanged.connect(self.update_panel)

    # ---- UI construction -------------------------------------------------
    def _build_ui(self) -> None:
        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        main_layout.addWidget(self.view, stretch=3)

        panel = QGroupBox("Monitor Settings")
        layout = QVBoxLayout()

        self.name_label = QLabel("Monitor: (None selected)")
        layout.addWidget(self.name_label)

        self.resolution_combo = QComboBox()
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        layout.addWidget(QLabel("Resolution"))
        layout.addWidget(self.resolution_combo)

        self.disabled_checkbox = QCheckBox("Disabled")
        self.disabled_checkbox.toggled.connect(self.on_disabled_changed)
        layout.addWidget(self.disabled_checkbox)

        self.mirror_checkbox = QCheckBox("Mirror")
        self.mirror_checkbox.toggled.connect(self.on_mirror_changed)
        layout.addWidget(self.mirror_checkbox)

        self.mirror_source_combo = QComboBox()
        self.mirror_source_combo.currentTextChanged.connect(self.on_mirror_source_changed)
        layout.addWidget(QLabel("Mirror Source"))
        layout.addWidget(self.mirror_source_combo)

        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self.reload_monitors)
        layout.addWidget(reload_button)

        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(apply_button)

        layout.addStretch()
        panel.setLayout(layout)
        main_layout.addWidget(panel, stretch=1)
        self._sync_enabled_states()

    # ---- loading ---------------------------------------------------------
    def reload_monitors(self) -> None:
        try:
            monitors = hyprctl.list_monitors()
        except HyprctlError as e:
            QMessageBox.critical(self, "Error", f"Failed to load monitor info:\n{e}")
            return

        self.scene.blockSignals(True)
        for rect in self.rects.values():
            self.scene.removeItem(rect)
        self.scene.blockSignals(False)
        self.rects.clear()
        self.state = {m.name: m for m in monitors}
        self.current = None

        for m in monitors:
            rect = MonitorRect(m.name, m.width / SCALE, m.height / SCALE)
            rect.setPos(m.x / SCALE, m.y / SCALE)
            rect.set_disabled_look(m.disabled)
            self.scene.addItem(rect)
            self.rects[m.name] = rect

        self.update_panel()

    # ---- panel -----------------------------------------------------------
    def update_panel(self) -> None:
        selected = self.scene.selectedItems()
        self.current = self.state.get(selected[0].name) if selected else None
        m = self.current

        self._updating = True
        self.resolution_combo.clear()
        self.mirror_source_combo.clear()
        if m is None:
            self.name_label.setText("Monitor: (None selected)")
            self.disabled_checkbox.setChecked(False)
            self.mirror_checkbox.setChecked(False)
        else:
            self.name_label.setText(f"Monitor: {m.name}")
            self.disabled_checkbox.setChecked(m.disabled)
            self.mirror_checkbox.setChecked(m.mirror)
            self.resolution_combo.addItems(m.modes)
            self.resolution_combo.setCurrentText(m.resolution)
            self.mirror_source_combo.addItems(n for n in self.state if n != m.name)
            if m.mirror_of:
                self.mirror_source_combo.setCurrentText(m.mirror_of)
        self._updating = False
        self._sync_enabled_states()

    def _sync_enabled_states(self) -> None:
        m = self.current
        others_enabled = sum(not s.disabled for s in self.state.values() if s is not m)
        has_choice = m is not None and len(self.state) > 1
        # the last remaining enabled monitor must not be disabled
        self.disabled_checkbox.setEnabled(has_choice and (m.disabled or others_enabled > 0))
        self.mirror_checkbox.setEnabled(has_choice and not m.disabled)
        self.mirror_source_combo.setEnabled(has_choice and not m.disabled and m.mirror)
        self.resolution_combo.setEnabled(m is not None)

    # ---- widget handlers -------------------------------------------------
    def on_disabled_changed(self, checked: bool) -> None:
        if self._updating or self.current is None:
            return
        self.current.disabled = checked
        self.rects[self.current.name].set_disabled_look(checked)
        self._sync_enabled_states()

    def on_mirror_changed(self, checked: bool) -> None:
        if self._updating or self.current is None:
            return
        self.current.mirror = checked
        self.current.mirror_of = self.mirror_source_combo.currentText() if checked else ""
        self._sync_enabled_states()

    def on_mirror_source_changed(self, source: str) -> None:
        if self._updating or self.current is None or not self.current.mirror:
            return
        self.current.mirror_of = source

    def on_resolution_changed(self, mode: str) -> None:
        if self._updating or self.current is None:
            return
        match = re.match(r"(\d+)x(\d+)", mode)
        if not match:
            return
        self.current.resolution = mode
        width, height = map(int, match.groups())
        self.rects[self.current.name].resize(width / SCALE, height / SCALE)

    # ---- apply -----------------------------------------------------------
    def apply_settings(self) -> None:
        try:
            for name, m in self.state.items():
                pos = self.rects[name].pos()
                hyprctl.apply_monitor(m, round(pos.x() * SCALE), round(pos.y() * SCALE))
        except HyprctlError as e:
            QMessageBox.critical(self, "Error", f"Failed to apply settings:\n{e}")
            return
        QMessageBox.information(self, "Settings Applied", "Monitor configurations have been applied.")
        self.reload_monitors()
