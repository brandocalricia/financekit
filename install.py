"""
FinanceKit Installer — Creates a desktop shortcut for one-click launching.

Usage:  python install.py
Safe to run multiple times (idempotent).
"""

import sys
import os
import subprocess
import stat

_base_dir = os.path.dirname(os.path.abspath(__file__))


def _check_python():
    """Verify Python is available."""
    print("  Checking Python installation...")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        print(f"  [WARNING] Python {v.major}.{v.minor} detected. Python 3.9+ is recommended.")
    else:
        print(f"  Python {v.major}.{v.minor}.{v.micro} found. OK")


def _install_dependencies():
    """Install dependencies from requirements.txt."""
    req = os.path.join(_base_dir, "requirements.txt")
    marker = os.path.join(_base_dir, ".deps_installed")

    if os.path.exists(marker):
        print("  Dependencies already installed. Skipping.")
        return True

    if not os.path.exists(req):
        print("  [WARNING] requirements.txt not found. Skipping dependency install.")
        return True

    print("  Installing dependencies from requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req],
        cwd=_base_dir,
    )
    if result.returncode == 0:
        with open(marker, "w") as f:
            f.write("")
        print("  Dependencies installed successfully!")
        return True
    else:
        print("  [ERROR] Failed to install some dependencies.")
        print("  Try running manually: pip install -r requirements.txt")
        return False


def _get_desktop_path():
    """Return the path to the user's Desktop folder."""
    if sys.platform == "win32":
        # Use Windows API to get Desktop path
        try:
            import ctypes.wintypes
            CSIDL_DESKTOPDIRECTORY = 0x0010
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, 0, buf)
            return buf.value
        except Exception:
            return os.path.join(os.path.expanduser("~"), "Desktop")
    elif sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    else:
        return os.path.join(os.path.expanduser("~"), "Desktop")


def _create_windows_shortcut():
    """Create a .bat launcher + .vbs wrapper for silent launch on Windows Desktop."""
    desktop = _get_desktop_path()
    if not os.path.isdir(desktop):
        print(f"  [WARNING] Desktop folder not found at {desktop}")
        desktop = os.path.expanduser("~")

    launcher_py = os.path.join(_base_dir, "launcher.py")
    python_exe = sys.executable

    # Create a .bat that runs launcher.py
    bat_path = os.path.join(_base_dir, "_launch_silent.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(f'@echo off\r\n')
        f.write(f'cd /d "{_base_dir}"\r\n')
        f.write(f'"{python_exe}" "{launcher_py}"\r\n')

    # Create a .vbs wrapper to run the .bat without a visible console window
    vbs_path = os.path.join(_base_dir, "_launch_hidden.vbs")
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(f'Set WshShell = CreateObject("WScript.Shell")\r\n')
        f.write(f'WshShell.Run chr(34) & "{bat_path}" & chr(34), 0, False\r\n')

    # Create the desktop shortcut as a .bat (simple, no COM dependencies)
    # Actually, let's try to create a proper .lnk shortcut using PowerShell
    shortcut_path = os.path.join(desktop, "FinanceKit.lnk")
    ico_path = os.path.join(_base_dir, "assets", "financekit.ico")

    # Use PowerShell to create the .lnk shortcut pointing to the vbs
    ps_script = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{shortcut_path}"); '
        f'$s.TargetPath = "wscript.exe"; '
        f'$s.Arguments = """{vbs_path}"""; '
        f'$s.WorkingDirectory = "{_base_dir}"; '
        f'$s.Description = "FinanceKit - Personal Finance Toolkit"; '
    )

    if os.path.exists(ico_path):
        ps_script += f'$s.IconLocation = "{ico_path}"; '

    ps_script += f'$s.Save()'

    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        print(f"  Desktop shortcut created: {shortcut_path}")
        return True
    else:
        # Fallback: just put a .bat on the desktop
        fallback_bat = os.path.join(desktop, "FinanceKit.bat")
        with open(fallback_bat, "w", encoding="utf-8") as f:
            f.write(f'@echo off\r\n')
            f.write(f'cd /d "{_base_dir}"\r\n')
            f.write(f'start "" wscript.exe "{vbs_path}"\r\n')
        print(f"  Desktop shortcut created: {fallback_bat}")
        return True


def _create_mac_shortcut():
    """Create a .command file on Mac Desktop."""
    desktop = _get_desktop_path()
    launcher_py = os.path.join(_base_dir, "launcher.py")
    shortcut = os.path.join(desktop, "FinanceKit.command")

    with open(shortcut, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f'cd "{_base_dir}"\n')
        f.write(f'python3 "{launcher_py}"\n')

    os.chmod(shortcut, os.stat(shortcut).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"  Desktop shortcut created: {shortcut}")
    return True


def _create_linux_shortcut():
    """Create a .desktop file for Linux."""
    apps_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "applications")
    os.makedirs(apps_dir, exist_ok=True)

    launcher_py = os.path.join(_base_dir, "launcher.py")
    ico_path = os.path.join(_base_dir, "assets", "financekit.ico")
    desktop_file = os.path.join(apps_dir, "financekit.desktop")

    icon_line = f"Icon={ico_path}" if os.path.exists(ico_path) else "Icon=gnome-money"

    with open(desktop_file, "w") as f:
        f.write("[Desktop Entry]\n")
        f.write("Type=Application\n")
        f.write("Name=FinanceKit\n")
        f.write("Comment=Personal Finance Toolkit\n")
        f.write(f"Exec=python3 {launcher_py}\n")
        f.write(f"Path={_base_dir}\n")
        f.write(f"{icon_line}\n")
        f.write("Terminal=false\n")
        f.write("Categories=Office;Finance;\n")

    os.chmod(desktop_file, os.stat(desktop_file).st_mode | stat.S_IEXEC)
    print(f"  Application entry created: {desktop_file}")

    # Also create on Desktop if it exists
    desktop = _get_desktop_path()
    if os.path.isdir(desktop):
        desktop_link = os.path.join(desktop, "FinanceKit.desktop")
        with open(desktop_link, "w") as f:
            f.write("[Desktop Entry]\n")
            f.write("Type=Application\n")
            f.write("Name=FinanceKit\n")
            f.write("Comment=Personal Finance Toolkit\n")
            f.write(f"Exec=python3 {launcher_py}\n")
            f.write(f"Path={_base_dir}\n")
            f.write(f"{icon_line}\n")
            f.write("Terminal=false\n")
            f.write("Categories=Office;Finance;\n")
        os.chmod(desktop_link, os.stat(desktop_link).st_mode | stat.S_IEXEC)
        print(f"  Desktop shortcut created: {desktop_link}")

    return True


def main():
    print()
    print("  ================================================")
    print("     FinanceKit Installer")
    print("  ================================================")
    print()

    # Step 1: Check Python
    _check_python()
    print()

    # Step 2: Install dependencies
    if not _install_dependencies():
        print()
        print("  Installation completed with warnings.")
        print("  You may need to install dependencies manually.")
    print()

    # Step 3: Create desktop shortcut
    print("  Creating desktop shortcut...")
    if sys.platform == "win32":
        success = _create_windows_shortcut()
    elif sys.platform == "darwin":
        success = _create_mac_shortcut()
    else:
        success = _create_linux_shortcut()

    print()
    if success:
        print("  ================================================")
        print("     FinanceKit installed successfully!")
        print("  ================================================")
        print()
        print("  Double-click the FinanceKit icon on your desktop")
        print("  to launch the app.")
        print()
    else:
        print("  [ERROR] Could not create desktop shortcut.")
        print("  You can still run FinanceKit manually:")
        print(f"    cd \"{_base_dir}\"")
        print(f"    python launcher.py")
        print()


if __name__ == "__main__":
    main()
