"""
FinanceKit Desktop App v5.2 — Double-click to launch.

Opens FinanceKit in a native desktop window (no browser needed).
Features: auto-install deps, splash screen, system tray, auto-update check.
Falls back to browser if pywebview is unavailable.
"""

import sys
import os
import subprocess
import time
import socket
import threading
import atexit
import signal

_base_dir = os.path.dirname(os.path.abspath(__file__))
_server_proc = None
_port = None


def _read_version():
    """Read the current version from version.txt."""
    vpath = os.path.join(_base_dir, "version.txt")
    try:
        with open(vpath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "5.2"


def _port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _find_port():
    for p in range(8501, 8520):
        if not _port_in_use(p):
            return p
    raise RuntimeError("No available ports (8501-8519)")


def _start_streamlit(port):
    global _server_proc
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        os.path.join(_base_dir, "app.py"),
        "--server.headless", "true",
        "--server.port", str(port),
        "--browser.gatherUsageStats", "false",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
    ]
    kwargs = {
        "cwd": _base_dir,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    _server_proc = subprocess.Popen(cmd, **kwargs)
    return _server_proc


def _wait_for_server(port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_in_use(port):
            time.sleep(1)
            return True
        time.sleep(0.5)
    return False


def _stop_server():
    global _server_proc
    if _server_proc:
        try:
            _server_proc.terminate()
            _server_proc.wait(timeout=5)
        except Exception:
            try:
                _server_proc.kill()
            except Exception:
                pass
        _server_proc = None


def _install_deps_if_needed():
    """Check and install core + desktop deps on first run."""
    marker = os.path.join(_base_dir, ".deps_installed")
    if os.path.exists(marker):
        return
    req = os.path.join(_base_dir, "requirements.txt")
    if not os.path.exists(req):
        return
    print("Setting up FinanceKit (first time only)...")
    print("Installing core dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req],
        cwd=_base_dir,
    )
    # Install desktop-only extras
    print("Installing desktop extras...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "pywebview>=5.0", "pystray==0.19.5"],
        cwd=_base_dir,
    )
    if result.returncode == 0:
        from pathlib import Path
        Path(marker).touch()


def _check_internet():
    """Check if internet connection is available."""
    try:
        import requests
        requests.get("https://httpbin.org/get", timeout=3)
        return True
    except Exception:
        return False


def _check_for_updates(version):
    """Check GitHub for newer version. Returns (new_version, None) or (None, None)."""
    try:
        import requests
        resp = requests.get(
            "https://api.github.com/repos/brandocalricia/financekit/releases/latest",
            timeout=5,
        )
        if resp.status_code == 200:
            latest = resp.json().get("tag_name", "").lstrip("v")
            if latest and latest != version:
                return latest
    except Exception:
        pass
    return None


def _show_splash():
    """Show a splash screen while Streamlit starts (pywebview)."""
    try:
        import webview
        splash_html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        body {
            margin: 0; display: flex; align-items: center; justify-content: center;
            height: 100vh; background: #0f1117; color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            flex-direction: column;
        }
        .logo { font-size: 3rem; margin-bottom: 0.5rem; }
        .title {
            font-size: 1.5rem; font-weight: 700;
            background: linear-gradient(90deg, #6366f1, #a78bfa);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .sub { color: #94a3b8; font-size: 0.9rem; margin-top: 0.5rem; }
        .spinner {
            margin-top: 1.5rem; width: 24px; height: 24px;
            border: 3px solid #2a2a40; border-top: 3px solid #6366f1;
            border-radius: 50%; animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        </style></head>
        <body>
        <div class="logo">💰</div>
        <div class="title">FinanceKit</div>
        <div class="sub">Loading your financial toolkit...</div>
        <div class="spinner"></div>
        </body></html>
        """
        splash = webview.create_window(
            "FinanceKit",
            html=splash_html,
            width=400, height=280,
            frameless=True,
            on_top=True,
        )
        return splash
    except Exception:
        return None


def _run_tray(window_ref, version):
    """Run system tray icon in background (Windows/macOS)."""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        return

    # Load or create tray icon
    icon_path = os.path.join(_base_dir, "static", "icons", "icon-192.png")
    try:
        icon_image = Image.open(icon_path)
    except Exception:
        # Create a simple colored icon
        icon_image = Image.new("RGB", (64, 64), "#6366f1")

    def on_open(icon, item):
        if window_ref and hasattr(window_ref, "show"):
            window_ref.show()

    def on_restart(icon, item):
        icon.stop()
        _stop_server()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def on_quit(icon, item):
        icon.stop()
        _stop_server()
        if window_ref and hasattr(window_ref, "destroy"):
            try:
                window_ref.destroy()
            except Exception:
                pass
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem(f"FinanceKit v{version}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open", on_open, default=True),
        pystray.MenuItem("Restart", on_restart),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon("FinanceKit", icon_image, f"FinanceKit v{version}", menu)
    icon.run()


def main():
    global _port

    version = _read_version()
    _install_deps_if_needed()

    _port = _find_port()

    # Start Streamlit server
    _start_streamlit(_port)
    atexit.register(_stop_server)

    # Wait for server with progress indication
    print(f"Starting FinanceKit v{version} on port {_port}...")
    if not _wait_for_server(_port):
        print("ERROR: Server failed to start. Try: streamlit run app.py")
        _stop_server()
        sys.exit(1)

    url = f"http://localhost:{_port}"

    # Check for updates in background
    if _check_internet():
        def _update_check():
            new_ver = _check_for_updates(version)
            if new_ver:
                print(f"\n  Update available: FinanceKit v{new_ver}")
                print(f"  Run: git pull   to update.\n")
        threading.Thread(target=_update_check, daemon=True).start()

    # Try native window via pywebview
    try:
        import webview

        def _on_closed():
            _stop_server()

        window = webview.create_window(
            f"FinanceKit v{version}",
            url,
            width=1280,
            height=800,
            min_size=(900, 600),
            confirm_close=False,
        )
        window.events.closed += _on_closed

        # Start system tray in background
        tray_thread = threading.Thread(
            target=_run_tray, args=(window, version), daemon=True
        )
        tray_thread.start()

        webview.start(debug=False)

    except ImportError:
        # pywebview not available — fall back to browser
        import webbrowser
        webbrowser.open(url)
        print(f"FinanceKit v{version} is running at {url}")
        print("Press Ctrl+C to stop.")

        def _sig_handler(sig, frame):
            _stop_server()
            sys.exit(0)

        signal.signal(signal.SIGINT, _sig_handler)

        try:
            while _server_proc and _server_proc.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    _stop_server()


if __name__ == "__main__":
    main()
