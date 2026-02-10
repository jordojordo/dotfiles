#!/usr/bin/env python3
"""
Konsole Theme Switcher - Automatically switches Konsole profiles
when KDE Plasma changes its color scheme (light/dark).

Monitors ~/.config/kdeglobals for changes and updates all running
Konsole windows via DBus.
"""

import sys
import os
import time

# Ensure unbuffered output for systemd journal
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
import subprocess
import pyinotify
from pathlib import Path


KDEGLOBALS_PATH = Path.home() / ".config" / "kdeglobals"
KDEGLOBALS_NAME = "kdeglobals"
KONSOLERC_PATH = Path.home() / ".config" / "konsolerc"
LIGHT_PROFILE = "Light"
DARK_PROFILE = "Dark"


def get_kde_color_scheme() -> str:
    """Get the current KDE color scheme name."""
    try:
        result = subprocess.run(
            ["kreadconfig6", "--group", "General", "--key", "ColorScheme"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def is_dark_scheme(scheme_name: str) -> bool:
    """Determine if a color scheme is dark based on its name."""
    # Common dark scheme indicators
    dark_indicators = ["dark", "night", "black", "monokai", "dracula", "nord"]
    scheme_lower = scheme_name.lower()
    return any(indicator in scheme_lower for indicator in dark_indicators)


def get_target_profile() -> str:
    """Get the appropriate Konsole profile for the current KDE theme."""
    scheme = get_kde_color_scheme()
    if is_dark_scheme(scheme):
        return DARK_PROFILE
    return LIGHT_PROFILE


def get_konsole_pids() -> list[int]:
    """Get PIDs of all running Konsole instances."""
    try:
        result = subprocess.run(
            ["pgrep", "-x", "konsole"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return [int(pid) for pid in result.stdout.strip().split("\n") if pid]
    except (subprocess.CalledProcessError, ValueError):
        pass
    return []


def get_konsole_sessions(pid: int) -> list[str]:
    """Get all session paths for a Konsole instance via DBus."""
    sessions = []
    service = f"org.kde.konsole-{pid}"

    try:
        # List all sessions under /Sessions
        result = subprocess.run(
            ["qdbus-qt6", service, "/Sessions"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # Output format: /Sessions/1, /Sessions/2, etc.
            for line in result.stdout.strip().split("\n"):
                if line.startswith("/Sessions/"):
                    sessions.append(line)
    except subprocess.CalledProcessError:
        pass

    return sessions


def set_session_profile(pid: int, session_path: str, profile: str) -> bool:
    """Set the profile for a Konsole session via DBus."""
    service = f"org.kde.konsole-{pid}"

    try:
        subprocess.run(
            ["qdbus-qt6", service, session_path, "setProfile", profile],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def update_konsolerc_default_profile(profile: str) -> None:
    """Update the default profile in konsolerc."""
    try:
        subprocess.run(
            [
                "kwriteconfig6",
                "--file", str(KONSOLERC_PATH),
                "--group", "Desktop Entry",
                "--key", "DefaultProfile",
                f"{profile}.profile",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to update konsolerc: {e}")


def switch_all_konsoles(profile: str) -> None:
    """Switch all running Konsole windows to the specified profile."""
    pids = get_konsole_pids()
    switched_count = 0

    for pid in pids:
        sessions = get_konsole_sessions(pid)
        for session in sessions:
            if set_session_profile(pid, session, profile):
                switched_count += 1

    print(f"Switched {switched_count} Konsole session(s) to '{profile}' profile")


def on_kdeglobals_changed() -> None:
    """Handle changes to kdeglobals file."""
    profile = get_target_profile()
    print(f"KDE theme changed. Switching to '{profile}' profile...")
    switch_all_konsoles(profile)
    update_konsolerc_default_profile(profile)


class KdeGlobalsHandler(pyinotify.ProcessEvent):
    """Handler for kdeglobals file events with debouncing."""

    DEBOUNCE_SECONDS = 0.5  # Ignore events within this window

    def __init__(self):
        super().__init__()
        self._last_switch_time = 0
        self._last_profile = None

    def _should_process(self, event) -> bool:
        """Check if this event should be processed (is kdeglobals file)."""
        # Only process events for the kdeglobals file
        return event.name == KDEGLOBALS_NAME

    def _debounced_switch(self) -> None:
        """Switch theme with debouncing to avoid rapid repeated switches."""
        now = time.monotonic()
        if now - self._last_switch_time < self.DEBOUNCE_SECONDS:
            return

        profile = get_target_profile()
        # Also skip if profile hasn't actually changed
        if profile == self._last_profile:
            return

        self._last_switch_time = now
        self._last_profile = profile
        print(f"KDE theme changed. Switching to '{profile}' profile...")
        switch_all_konsoles(profile)
        update_konsolerc_default_profile(profile)

    def process_IN_CLOSE_WRITE(self, event):
        """Called when kdeglobals is written and closed."""
        if self._should_process(event):
            self._debounced_switch()

    def process_IN_MOVED_TO(self, event):
        """Called when a file is moved to kdeglobals (atomic write)."""
        if self._should_process(event):
            self._debounced_switch()


def main():
    """Main entry point - start monitoring kdeglobals."""
    print("Konsole Theme Switcher starting...")

    # Apply current theme on startup
    profile = get_target_profile()
    print(f"Current KDE theme detected. Setting '{profile}' profile...")
    switch_all_konsoles(profile)
    update_konsolerc_default_profile(profile)

    # Set up inotify watcher
    wm = pyinotify.WatchManager()
    handler = KdeGlobalsHandler()
    handler._last_profile = profile  # Initialize to avoid redundant switch on first event
    notifier = pyinotify.Notifier(wm, handler)

    # Watch the config directory (for atomic writes that replace the file)
    config_dir = KDEGLOBALS_PATH.parent
    mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO
    wm.add_watch(str(config_dir), mask)

    print(f"Watching {KDEGLOBALS_PATH} for changes...")

    try:
        notifier.loop()
    except KeyboardInterrupt:
        print("\nShutting down...")
        notifier.stop()


if __name__ == "__main__":
    main()
