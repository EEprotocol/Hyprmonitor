from setuptools import setup 
setup(
    name="hyprmonitor",
    version="0.1.0",
    package=["hyprmonitor"],
    install_requires=[],
    entry_point={
      "console_scripts":[
        "hyprmonitor = hyprmonitor.hyprmonitor:main",
      ],
    },
)
