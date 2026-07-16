# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for the AirMouse macOS application."""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
)


# MediaPipe includes native libraries and package data that its Tasks API loads
# at runtime. Collect those files without pulling its unrelated tests, benchmark
# tools, and optional GenAI conversion modules into AirMouse.
mediapipe_datas = collect_data_files("mediapipe")
mediapipe_binaries = collect_dynamic_libs("mediapipe")

hidden_imports = [
    # MediaPipe Tasks
    "mediapipe",
    "mediapipe.tasks",
    "mediapipe.tasks.python",
    "mediapipe.tasks.python.vision",
    "mediapipe.tasks.python.vision.hand_landmarker",
    # OpenCV
    "cv2",
    # PyAutoGUI and its platform-specific modules
    "pyautogui",
    "pyautogui._pyautogui_osx",
    # Quartz/PyObjC used by native macOS double-click events
    "Quartz",
    "CoreFoundation",
    "Foundation",
    "objc",
    # Tkinter launcher
    "_tkinter",
    "tkinter",
    "tkinter.ttk",
]

# Remove duplicates while preserving the readable order above.
hidden_imports = list(dict.fromkeys(hidden_imports))

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=mediapipe_binaries,
    datas=[
        ("models/hand_landmarker.task", "models"),
        ("config/settings.json", "config"),
        *mediapipe_datas,
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AirMouse",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AirMouse",
)

app = BUNDLE(
    coll,
    name="AirMouse.app",
    icon=None,
    bundle_identifier="com.airmouse.app",
    info_plist={
        "CFBundleDisplayName": "AirMouse",
        "NSCameraUsageDescription": (
            "AirMouse uses the camera to detect hand gestures for mouse control."
        ),
    },
)
