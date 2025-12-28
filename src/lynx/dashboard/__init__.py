"""Dashboard module for web-based run browsing and comparison."""

import signal
import time
import webbrowser
from threading import Event, Thread

# Global variable for tracking last request time (T072)
_last_request_time: float = 0.0
_shutdown_event: Event | None = None


def update_last_request_time() -> None:
    """Update the last request timestamp."""
    global _last_request_time
    _last_request_time = time.time()


def get_last_request_time() -> float:
    """Get the last request timestamp."""
    return _last_request_time


def launch_dashboard(
    port: int = 8501,
    open_browser: bool = True,
    idle_timeout: int = 1800,
) -> None:
    """Launch the Lynx dashboard web server.

    Args:
        port: Port number for the web server (default: 8501)
        open_browser: Whether to automatically open browser (default: True)
        idle_timeout: Shutdown server after this many seconds of inactivity.
                      Set to 0 to disable auto-shutdown. (default: 1800 = 30 min)

    Example:
        >>> import lynx
        >>> lynx.dashboard()  # Opens browser at http://localhost:8501
        >>> lynx.dashboard(idle_timeout=0)  # Disable auto-shutdown
    """
    import uvicorn

    from lynx.dashboard.server import app
    from lynx.storage import sqlite

    global _last_request_time, _shutdown_event

    # Ensure database is initialized
    sqlite.init_db()

    # Initialize last request time
    _last_request_time = time.time()
    _shutdown_event = Event()

    # Open browser in a separate thread after a short delay
    if open_browser:
        def open_browser_delayed():
            time.sleep(1)  # Wait for server to start
            webbrowser.open(f"http://localhost:{port}")

        Thread(target=open_browser_delayed, daemon=True).start()

    # Start idle checker thread if timeout is enabled (T074)
    if idle_timeout > 0:
        def idle_checker():
            check_interval = 60  # Check every 60 seconds
            while not _shutdown_event.is_set():
                time.sleep(check_interval)

                idle_time = time.time() - _last_request_time
                if idle_time > idle_timeout:
                    print(f"\n[Lynx] Server idle for {idle_time:.0f}s, shutting down...")
                    _shutdown_event.set()
                    # Signal the main process to exit gracefully
                    signal.raise_signal(signal.SIGINT)
                    break

        Thread(target=idle_checker, daemon=True).start()

    # Create uvicorn config with custom settings
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )

    # Run the server
    server = uvicorn.Server(config)

    try:
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        if _shutdown_event:
            _shutdown_event.set()


__all__ = ["launch_dashboard", "update_last_request_time", "get_last_request_time"]
