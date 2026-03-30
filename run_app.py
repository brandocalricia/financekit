"""
FinanceKit Desktop App — Double-click to launch.

Opens FinanceKit in a native desktop window (no browser needed).
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
            # Give it another second to fully initialize
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
    marker = os.path.join(_base_dir, ".deps_installed")
    if os.path.exists(marker):
        return
    req = os.path.join(_base_dir, "requirements.txt")
    if not os.path.exists(req):
        return
    print("Installing dependencies (first time only)...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req],
        cwd=_base_dir,
    )
    if result.returncode == 0:
        with open(marker, "w") as f:
            f.write("")


def main():
    global _port

    _install_deps_if_needed()

    _port = _find_port()
    _start_streamlit(_port)
    atexit.register(_stop_server)

    if not _wait_for_server(_port):
        print("ERROR: Server failed to start. Try: streamlit run app.py")
        _stop_server()
        sys.exit(1)

    url = f"http://localhost:{_port}"

    # Try native window via pywebview
    try:
        import webview

        def _on_closed():
            _stop_server()

        window = webview.create_window(
            "FinanceKit",
            url,
            width=1280,
            height=800,
            min_size=(900, 600),
            confirm_close=False,
        )
        window.events.closed += _on_closed

        # Start tray icon in background (Windows)
        if sys.platform == "win32":
            def _start_tray():
                try:
                    from launcher import _run_tray
                except Exception:
                    pass
            # Don't start tray when using webview — the window IS the app

        webview.start(debug=False)

    except ImportError:
        # pywebview not available — fall back to browser
        import webbrowser
        webbrowser.open(url)
        print(f"FinanceKit is running at {url}")
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
