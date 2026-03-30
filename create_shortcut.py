"""Create a desktop shortcut for FinanceKit on Windows, macOS, or Linux."""

import os
import sys
import platform

_base_dir = os.path.dirname(os.path.abspath(__file__))
_icon_path = os.path.join(_base_dir, "static", "icons", "icon-192.png")


def _create_windows_shortcut():
    """Create a .lnk shortcut on Windows Desktop."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )
        desktop = winreg.QueryValueEx(key, "Desktop")[0]
        winreg.CloseKey(key)
    except Exception:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")

    shortcut_path = os.path.join(desktop, "FinanceKit.lnk")
    bat_path = os.path.join(_base_dir, "start.bat")

    try:
        # Use PowerShell to create .lnk
        ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{shortcut_path}')
$s.TargetPath = '{bat_path}'
$s.WorkingDirectory = '{_base_dir}'
$s.Description = 'FinanceKit - Personal Finance Toolkit'
$s.WindowStyle = 7
$s.Save()
"""
        import subprocess
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, check=True,
        )
        print(f"Shortcut created: {shortcut_path}")
        return True
    except Exception as e:
        print(f"Could not create shortcut: {e}")
        print(f"You can manually create a shortcut to: {bat_path}")
        return False


def _create_macos_app():
    """Create a .app bundle in /Applications."""
    app_dir = os.path.expanduser("~/Applications/FinanceKit.app")
    contents = os.path.join(app_dir, "Contents")
    macos_dir = os.path.join(contents, "MacOS")
    resources_dir = os.path.join(contents, "Resources")

    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)

    # Info.plist
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>FinanceKit</string>
    <key>CFBundleDisplayName</key><string>FinanceKit</string>
    <key>CFBundleIdentifier</key><string>com.financekit.app</string>
    <key>CFBundleExecutable</key><string>launch</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleVersion</key><string>1.0</string>
</dict>
</plist>"""
    with open(os.path.join(contents, "Info.plist"), "w") as f:
        f.write(plist)

    # Launch script
    launch = f"""#!/bin/bash
cd "{_base_dir}"
python3 run_app.py
"""
    launch_path = os.path.join(macos_dir, "launch")
    with open(launch_path, "w") as f:
        f.write(launch)
    os.chmod(launch_path, 0o755)

    print(f"App created: {app_dir}")
    return True


def _create_linux_desktop():
    """Create a .desktop file for Linux."""
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(desktop_dir, exist_ok=True)

    desktop_file = os.path.join(desktop_dir, "financekit.desktop")
    content = f"""[Desktop Entry]
Name=FinanceKit
Comment=Personal Finance Toolkit
Exec=bash -c 'cd "{_base_dir}" && python3 run_app.py'
Icon={_icon_path}
Type=Application
Categories=Office;Finance;
Terminal=false
"""
    with open(desktop_file, "w") as f:
        f.write(content)
    os.chmod(desktop_file, 0o755)

    print(f"Desktop entry created: {desktop_file}")
    return True


def main():
    system = platform.system()
    print(f"Creating FinanceKit shortcut for {system}...")

    if system == "Windows":
        _create_windows_shortcut()
    elif system == "Darwin":
        _create_macos_app()
    elif system == "Linux":
        _create_linux_desktop()
    else:
        print(f"Unsupported platform: {system}")
        sys.exit(1)


if __name__ == "__main__":
    main()
