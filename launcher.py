"""
FinanceKit Launcher — Background server with system tray icon (Windows).

Starts Streamlit as a subprocess, waits for it to be ready, opens the browser,
and (on Windows) shows a system tray icon with Open / Restart / Quit actions.
On Mac/Linux it simply waits for Ctrl+C.
"""

import sys
import os
import subprocess
import time
import signal
import socket
import webbrowser
import threading
import atexit

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
_server_proc = None
_selected_port = None
_base_dir = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Port helpers
# ---------------------------------------------------------------------------

def _port_in_use(port: int) -> bool:
    """Check if a TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_available_port(start: int = 8501, end: int = 8510) -> int:
    """Return the first available port in [start, end]."""
    for port in range(start, end + 1):
        if not _port_in_use(port):
            return port
    raise RuntimeError(f"All ports {start}-{end} are in use. Close another app and try again.")

# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------

def _start_server(port: int) -> subprocess.Popen:
    """Launch `streamlit run app.py` as a subprocess."""
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        os.path.join(_base_dir, "app.py"),
        "--server.headless", "true",
        "--server.port", str(port),
        "--browser.gatherUsageStats", "false",
    ]

    kwargs = {
        "cwd": _base_dir,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }

    # On Windows, hide the console window
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    return subprocess.Popen(cmd, **kwargs)


def _wait_for_server(port: int, timeout: int = 30) -> bool:
    """Poll localhost:{port} until it responds or timeout (seconds)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_in_use(port):
            return True
        time.sleep(0.5)
    return False


def _stop_server():
    """Terminate the Streamlit subprocess if it is running."""
    global _server_proc
    if _server_proc is not None:
        try:
            _server_proc.terminate()
            _server_proc.wait(timeout=5)
        except Exception:
            try:
                _server_proc.kill()
            except Exception:
                pass
        _server_proc = None


def _open_browser():
    """Open the app in the default browser."""
    webbrowser.open(f"http://localhost:{_selected_port}")

# ---------------------------------------------------------------------------
# System tray (Windows only)
# ---------------------------------------------------------------------------

def _run_tray():
    """Show a system tray icon with Open / Restart / Quit menu."""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        # pystray or Pillow not installed — fall back to simple wait
        return False

    def _make_icon_image():
        """Create a simple 64x64 icon image (indigo coin)."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        # Draw a filled circle
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=(99, 102, 241, 255))
        # Draw a dollar sign in white
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial", 32)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), "$", font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((64 - tw) / 2 - bbox[0], (64 - th) / 2 - bbox[1]), "$", fill="white", font=font)
        return img

    def on_open(icon, item):
        _open_browser()

    def on_restart(icon, item):
        global _server_proc, _selected_port
        _stop_server()
        time.sleep(1)
        _selected_port = find_available_port()
        _server_proc = _start_server(_selected_port)
        if _wait_for_server(_selected_port):
            _open_browser()

    def on_quit(icon, item):
        _stop_server()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Open FinanceKit", on_open, default=True),
        pystray.MenuItem("Restart Server", on_restart),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon(
        "FinanceKit",
        _make_icon_image(),
        "FinanceKit",
        menu,
    )

    icon.run()  # blocks until icon.stop()
    return True

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

def _ensure_dependencies():
    """Install requirements.txt if not already done."""
    marker = os.path.join(_base_dir, ".deps_installed")
    if os.path.exists(marker):
        return
    req = os.path.join(_base_dir, "requirements.txt")
    if not os.path.exists(req):
        return
    print("  Installing dependencies (first time only)...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req],
        cwd=_base_dir,
    )
    if result.returncode == 0:
        with open(marker, "w") as f:
            f.write("")
        print("  Dependencies installed successfully!\n")
    else:
        print("  [WARNING] Some dependencies may have failed to install.")
        print("  Try running: pip install -r requirements.txt\n")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global _server_proc, _selected_port

    print()
    print("  ================================================")
    print("     FinanceKit - Personal Finance Toolkit")
    print("  ================================================")
    print()

    # Auto-install deps if needed
    _ensure_dependencies()

    print("  Starting FinanceKit... (this may take a few seconds on first launch)")
    print()

    # Find a free port
    try:
        _selected_port = find_available_port()
    except RuntimeError as e:
        print(f"  [ERROR] {e}")
        sys.exit(1)

    if _selected_port != 8501:
        print(f"  Port 8501 is in use. Using port {_selected_port} instead.")

    # Start Streamlit
    _server_proc = _start_server(_selected_port)
    atexit.register(_stop_server)

    # Handle Ctrl+C gracefully
    def _sig_handler(sig, frame):
        print("\n  Shutting down FinanceKit...")
        _stop_server()
        sys.exit(0)

    signal.signal(signal.SIGINT, _sig_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _sig_handler)

    # Wait for server
    if not _wait_for_server(_selected_port):
        print("  [ERROR] Server failed to start within 30 seconds.")
        print("  Try running manually: streamlit run app.py")
        _stop_server()
        sys.exit(1)

    print(f"  FinanceKit is running at http://localhost:{_selected_port}")
    print()

    # Open browser
    _open_browser()

    # Windows: show system tray icon (blocks until quit)
    # Mac/Linux: wait for Ctrl+C
    if sys.platform == "win32":
        tray_started = _run_tray()
        if not tray_started:
            # pystray not available — just wait
            print("  Press Ctrl+C to stop.")
            try:
                while _server_proc and _server_proc.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    else:
        print("  Press Ctrl+C to stop.")
        try:
            while _server_proc and _server_proc.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    _stop_server()
    print("  FinanceKit stopped.")


if __name__ == "__main__":
    main()
