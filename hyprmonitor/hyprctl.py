"""Thin wrapper around `hyprctl`: monitor state, parsing and command building."""
import json
import subprocess
from dataclasses import dataclass, field


class HyprctlError(RuntimeError):
    pass


@dataclass
class Monitor:
    name: str
    x: int
    y: int
    width: int
    height: int
    modes: list[str]
    resolution: str
    disabled: bool = False
    mirror: bool = False
    mirror_of: str = ""
    transform: int = 0
    extra: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_json(cls, data: dict) -> "Monitor":
        modes = data.get("availableModes", [])
        current = f"{data['width']}x{data['height']}@{data.get('refreshRate', 0):.2f}Hz"
        mirror_of = data.get("mirrorOf", "none")
        mirrored = mirror_of not in ("none", "", None)
        return cls(
            name=data["name"],
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            modes=modes,
            resolution=current if current in modes else (modes[0] if modes else current),
            disabled=bool(data.get("disabled", False)),
            mirror=mirrored,
            mirror_of=mirror_of if mirrored else "",
            transform=data.get("transform", 0),
        )

    def keyword(self, x: int, y: int) -> str:
        """Argument of `hyprctl keyword monitor` for this monitor at (x, y)."""
        if self.disabled:
            return f"{self.name},disable"
        if self.mirror:
            return f"{self.name},preferred,auto,1,mirror,{self.mirror_of}"
        return f"{self.name},{self.resolution},{x}x{y},1"


def _run(*args: str) -> str:
    try:
        result = subprocess.run(["hyprctl", *args], capture_output=True, text=True, check=True)
    except FileNotFoundError as e:
        raise HyprctlError("hyprctl not found (is Hyprland installed?)") from e
    except subprocess.CalledProcessError as e:
        raise HyprctlError(e.stderr.strip() or str(e)) from e
    return result.stdout


def list_monitors() -> list[Monitor]:
    try:
        return [Monitor.from_json(m) for m in json.loads(_run("monitors", "all", "-j"))]
    except (json.JSONDecodeError, KeyError) as e:
        raise HyprctlError(f"unexpected hyprctl output: {e}") from e


def apply_monitor(monitor: Monitor, x: int, y: int) -> None:
    _run("keyword", "monitor", monitor.keyword(x, y))
