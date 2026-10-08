# Hyprmonitor
**A tiny multi monitor QT-app for Hyprland**

## Requirement
Python >=3.12, PyQt6, `hyprctl` (Hyprland)

## Usage
```
uv run hyprmonitor          # from source
pip install . && hyprmonitor
```

## Standalone binary
```
./build.sh                  # -> dist/hyprmonitor (PyInstaller, one file)
```

## Layout
- `hyprmonitor/hyprctl.py` – `hyprctl` wrapper and monitor model
- `hyprmonitor/widgets.py` – draggable monitor rectangle
- `hyprmonitor/window.py` – main window
- `packaging/entry.py` – PyInstaller entry point

## Future work
- Specify the workspace to send
- monitor rotation

I welcome those whom improve this tool with me!  
Please contact to keik4656{at}gmail.com.  
I'm very new to Python, so I'm seeking help!  
