import os

import PyInstaller.__main__


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

args = [
    "config_editor.py",
    "--name=TaikoNautsConfigEditor",
    "--onefile",
    "--windowed",
    "--clean",
    "--noconfirm",
]

icon_path = os.path.join(PROJECT_DIR, "icon.ico")
if os.path.exists(icon_path):
    args.append(f"--icon={icon_path}")

PyInstaller.__main__.run(args)

print("Build completed:")
print(os.path.join(PROJECT_DIR, "dist", "TaikoNautsConfigEditor.exe"))
