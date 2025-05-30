#!usr/bin/env python3
import sys
import json
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem, QVBoxLayout, QWidget, QGroupBox,
    QLabel, QComboBox, QCheckBox, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QBrush, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF
import re

class MonitorRect(QGraphicsRectItem):
    def __init__(self, name, width, height,parent_window):
        super().__init__(0, 0, width, height)
        self.setBrush(QBrush(QColor("skyblue")))
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.name = name
        self.parent_window=parent_window

        self.label = QGraphicsSimpleTextItem(name, self)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        label_rect = self.label.boundingRect()
        label_x = (width - label_rect.width()) / 2
        label_y = (height - label_rect.height()) / 2
        self.label.setPos(label_x, label_y)

    def resize(self, posx,posy,new_width, new_height):
        self.setRect(posx, posy, new_width, new_height)
        label_rect = self.label.boundingRect()
        label_x = posx+(new_width - label_rect.width()) / 2
        label_y = posy+(new_height - label_rect.height()) / 2
        self.label.setPos(label_x, label_y)

class MonitorConfigurator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wayland Monitor Configurator")
        self.setMinimumSize(800, 500)

        #current selected Monitor
        self.monitorname=""
        self.dataframe={}
        self.monitors = {}
        self.disable_monitors=set()

        # Top-level layout
        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Graphics view for monitor layout
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        main_layout.addWidget(self.view, stretch=3)

        # Settings panel
        self.panel = QGroupBox("Monitor Settings")
        panel_layout = QVBoxLayout()

        self.monitor_name_label = QLabel("Monitor: (None selected)")
        panel_layout.addWidget(self.monitor_name_label)

        self.resolution_label = QLabel("Resolution")
        self.resolution_combo = QComboBox()
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        panel_layout.addWidget(self.resolution_label)
        panel_layout.addWidget(self.resolution_combo)

        self.disabled_checkbox = QCheckBox("Disabled")
        self.disabled_checkbox.stateChanged.connect(self.on_disabled_changed)
        panel_layout.addWidget(self.disabled_checkbox)

        self.mirror_checkbox = QCheckBox("Mirror")
        self.mirror_checkbox.stateChanged.connect(self.on_mirror_changed)
        panel_layout.addWidget(self.mirror_checkbox)

        self.mirror_source_combo = QComboBox()
        self.mirror_source_combo.setEnabled(False)
        self.mirror_source_combo.currentTextChanged.connect(self.on_mirror_source_changed)
        panel_layout.addWidget(QLabel("Mirror Source"))
        panel_layout.addWidget(self.mirror_source_combo)

        self.mirror_checkbox.stateChanged.connect(
            lambda state: self.mirror_source_combo.setEnabled(state == Qt.CheckState.Checked.value)
        )

        #self.rotate_button = QPushButton("Rotate")
        #self.rotate_button.clicked.connect(self.on_rotation_changed)
        #panel_layout.addWidget(self.rotate_button)

        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload_monitors)
        panel_layout.addWidget(self.reload_button)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        panel_layout.addWidget(self.apply_button)

        panel_layout.addStretch()
        self.panel.setLayout(panel_layout)
        main_layout.addWidget(self.panel, stretch=1)

        self.reload_monitors()
        self.scene.selectionChanged.connect(self.update_panel)

    def create_monitor(self, name, x, y, width, height):
        rect = MonitorRect(name, width, height,self)
        rect.setPos(x, y)
        self.scene.addItem(rect)
        self.monitors[name]=rect
        if self.dataframe[name]["disabled"]:
            self.monitors[name].setBrush(QBrush(QColor('#888888')))
        else:
            self.monitors[name].setBrush(QBrush(QColor('skyblue')))

    def reload_monitors(self):
        for mon in self.monitors.values():
            self.scene.removeItem(mon)
        self.monitors = {}
        self.mirror_source_combo.clear()

        try:
            result = subprocess.run(["hyprctl", "monitors","all", "-j"], capture_output=True, text=True)
            print("I output the result")
            monitors = json.loads(result.stdout)
            print("here is the monitors")
            print(monitors)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load monitor info:\n{e}")
            return

        for mon in monitors:
            print(mon)
            name = mon.get("name", "unknown")
            available = mon.get("availableModes", "unknown")
            monitordata={"resolution":0,"disabled":0,"mirror":0,}
            monitordata["resolution"]=available[0]
            monitordata["disabled"]=mon.get("disabled","unknown")
            monitordata["mirrorOf"]=mon.get("mirrorOf","unknown")
            monitordata["transform"]=mon.get("transform","unknown")
            if(monitordata["mirrorOf"]=="none"):
                monitordata["mirror"]=False;
            else:
                monitordata["mirror"]=True;
            self.dataframe.setdefault(name,monitordata)

            width = mon["width"]//12
            height=mon['height']//12
            x = mon["x"]//12
            y = mon["y"]//12
            self.create_monitor(name, x, y, width, height)

            self.mirror_source_combo.addItem(name)

            print(available)
            #self.resolution_combo.clear()
            #self.resolution_combo.addItems(common_res)

            self.resolution_combo.blockSignals(True)
            self.resolution_combo.clear()
            self.resolution_combo.addItems(available)
            print("now(reloaded):",self.dataframe[name]["resolution"])
            self.resolution_combo.setCurrentText(self.dataframe[name]["resolution"])
            self.resolution_combo.blockSignals(False)

        #how many monitors?
        if(len(monitors)==1):
            print("soloplay")
            self.mirror_checkbox.setEnabled(False)
            self.disabled_checkbox.setEnabled(False)
            self.mirror_source_combo.setEnabled(False)
            onlyname=list(self.dataframe)[0]
            self.dataframe[onlyname]["disabled"]=False
            self.dataframe[onlyname]["mirror"]=False
            self.dataframe[onlyname]["mirrorOf"]="none"
        elif(len(monitors)>1):
            print("multiplay")
            self.mirror_checkbox.setEnabled(True)
            self.disabled_checkbox.setEnabled(True)
            if(self.monitorname!=''):
                if(self.mirror_checkbox.isChecked()==True):
                    self.mirror_source_combo.setEnabled(True)
                    self.dataframe[self.monitorname]["mirrorOf"]=self.mirror_source_combo.currentText()
                self.dataframe[self.monitorname]["disabled"]=self.disabled_checkbox.isChecked()
                self.dataframe[self.monitorname]["mirror"]=self.mirror_checkbox.isChecked()


    def on_rotation_changed(self):
        if self.monitorname not in self.dataframe:
            print(f"monitor:'{self.monitorname}' does not exit")
            return
        else:
            self.dataframe[self.monitorname]["transform"]+=1
            trans=self.dataframe[self.monitorname]["transform"]%4
            self.dataframe[self.monitorname]["transform"]=trans
            print("transform:",self.dataframe[self.monitorname]["transform"])
            self.monitors[self.monitorname].setRotation(-90*trans)



    def on_disabled_changed(self):
        if self.monitorname not in self.dataframe:
            print(f"monitor:'{self.monitorname}' does not exit")
            return
        else:
            if self.disabled_checkbox.isChecked():
                self.monitors[self.monitorname].setBrush(QBrush(QColor('#888888')))
                #self.monitors[self.monitorname].setRotation(90)
                print("disabledToggled", self.dataframe[self.monitorname]["disabled"],"->", self.disabled_checkbox.isChecked())
                self.mirror_source_combo.setEnabled(False)
                self.mirror_checkbox.setEnabled(False)
                self.disable_monitors.add(self.monitorname)
            else:
                self.monitors[self.monitorname].setBrush(QBrush(QColor('#87ceeb')))
                self.disable_monitors.discard(self.monitorname)
                self.mirror_checkbox.setEnabled(True)
                if(self.mirror_checkbox.isChecked()):
                    self.mirror_source_combo.setEnabled(True)
                else:
                    self.mirror_source_combo.setEnabled(False)
            self.dataframe[self.monitorname]["disabled"]=self.disabled_checkbox.isChecked()
            print(self.dataframe)

    def on_mirror_changed(self):
        if self.monitorname not in self.dataframe:
            print(f"monitor:'{self.monitorname}' does not exit")
            return
        else:
            if self.mirror_checkbox.isChecked():
                print("mirrorToggled", self.dataframe[self.monitorname]["mirror"],"->", self.mirror_checkbox.isChecked())
                self.dataframe[self.monitorname]["mirrorOf"]=self.mirror_source_combo.currentText()

            self.dataframe[self.monitorname]["mirror"]=self.mirror_checkbox.isChecked()
            print(self.dataframe)

    def on_resolution_changed(self):

        if self.monitorname not in self.dataframe:
            print(f"monitor:'{self.monitorname}' does not exit")
            return
        else:
            print(self.monitorname)
            print("resolutionchanged", self.dataframe[self.monitorname]["resolution"],"->", self.resolution_combo.currentText())
            s=self.dataframe[self.monitorname]["resolution"]=self.resolution_combo.currentText()
            match = re.search(r'(\d+)x(\d+)', s)
            width, height =tuple(map(int, match.groups()))
            monitor=self.monitors[self.monitorname]
            monitor.resize( monitor.pos().x(),monitor.pos().y(),width//12,height//12)
            print(self.dataframe)

    def on_mirror_source_changed(self):

        if self.monitorname not in self.dataframe:
            print(f"monitor:'{self.monitorname}' does not exit")
            return
        else:
            print("mirror_sourcechanged", self.dataframe[self.monitorname]["mirrorOf"],"->", self.mirror_source_combo.currentText())
            self.dataframe[self.monitorname]["mirrorOf"]=self.mirror_source_combo.currentText()
            print(self.dataframe)

    def get_available_modes(self, monitor_name: str):
        try:
            # hyprctl monitors all -j の出力を取得
            result = subprocess.run(["hyprctl", "monitors", "all", "-j"], capture_output=True, text=True, check=True)
            monitors = json.loads(result.stdout)

            # 指定したモニター名に一致するモニターを探す
            for monitor in monitors:
                if monitor.get("name") == monitor_name:
                    return monitor.get("availableModes", [])

            print(f"Monitor '{monitor_name}' not found.")
            return []

        except subprocess.CalledProcessError as e:
            print("Error running hyprctl:", e)
            return []
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
            return []

    def get_available_modes_old(self,monitor_name: str):
        try:
            # hyprctl monitors の出力を取得
            result = subprocess.run(["hyprctl", "monitors"], capture_output=True, text=True, check=True)
            output = result.stdout

            # モニターのセクションを抽出（例: Monitor DP-1 ... ~ availableModes: ...）
            monitor_pattern = rf"Monitor {re.escape(monitor_name)}.*?(?=Monitor |\Z)"  # 他のMonitorまたはEOFまで
            monitor_match = re.search(monitor_pattern, output, re.DOTALL)
            if not monitor_match:
                print(f"Monitor '{monitor_name}' not found.")
                return []

            monitor_block = monitor_match.group(0)

            # availableModes を探す
            modes_match = re.search(r"availableModes:\s*(.*)", monitor_block)
            if not modes_match:
                print(f"No availableModes found for monitor '{monitor_name}'.")
                return []

            # モードをすべて抽出
            modes_str = modes_match.group(1)
            modes = re.findall(r"\d+x\d+@\d+\.\d+Hz", modes_str)

            return modes

        except subprocess.CalledProcessError as e:
            print("Error running hyprctl:", e)
            return []


    def update_panel(self):
        selected = self.scene.selectedItems()
        print("monitors",self.monitors)
        print("scene",self.scene)
        if selected:
            monitor = selected[0]
            print("panel updated")
            self.monitor_name_label.setText(f"Monitor: {monitor.name}")
            print(f"Monitor: {monitor.name}")
            self.monitorname=f"{monitor.name}"
            print(self.monitorname)
            self.resolution_combo.blockSignals(True)
            self.disabled_checkbox.setChecked(self.dataframe[self.monitorname]["disabled"])
            self.mirror_checkbox.setChecked(self.dataframe[self.monitorname]["mirror"])
            self.resolution_combo.clear()
            print(self.monitorname,"available",self.get_available_modes(self.monitorname))
            self.resolution_combo.addItems(self.get_available_modes(self.monitorname))
            print("now:",self.dataframe[self.monitorname]["resolution"])
            self.resolution_combo.setCurrentText(self.dataframe[self.monitorname]["resolution"])
            self.resolution_combo.blockSignals(False)
            self.mirror_source_combo.blockSignals(True)
            self.mirror_source_combo.clear()
            for name in self.dataframe:
                if name != self.monitorname:
                    self.mirror_source_combo.addItem(name)
            if len(self.disable_monitors)==len(self.dataframe)-1:
                if self.dataframe[self.monitorname]["disabled"]:
                    self.disabled_checkbox.setEnabled(True)
                    self.mirror_source_combo.setEnabled(False)
                else:
                    self.disabled_checkbox.setEnabled(False)
            else:
                self.disabled_checkbox.setEnabled(True)
            self.mirror_source_combo.blockSignals(False)

            #=self.resolution_combo.currentText()
        else:
            self.monitor_name_label.setText("Monitor: (None selected)")
            self.monitorname=''

    def apply_settings(self):
        for monitor in self.monitors.values():
            name = monitor.name
            pos = monitor.pos()
            resolution = self.dataframe[name]["resolution"]
            disabled = self.dataframe[name]["disabled"]
            mirror =self.dataframe[name]["mirror"]
            mirror_source =self.dataframe[name]["mirrorOf"]
            transform= self.dataframe[name]["transform"]
            x=pos.x()*12
            y=pos.y()*12
            print("x:",pos.x(),"y:",pos.y())

            if disabled==False:
                if mirror:
                    cmd = ["hyprctl", "keyword", "monitor", f"{name},preffered,auto,1,mirror,{mirror_source}"]
                else:
                    cmd = ["hyprctl","keyword",  "monitor", f"{name},{resolution},{x}x{y},1"]

            else:
                cmd = ["hyprctl", "keyword", "monitor", f"{name},disable"]

            print(cmd)
            subprocess.run(cmd)

        QMessageBox.information(self, "Settings Applied", "Monitor configurations have been applied.")
        print(self.dataframe)
        self.reload_monitors()

def main():
    app = QApplication(sys.argv)
    window = MonitorConfigurator()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

#Todo
#workspace
#rotate
