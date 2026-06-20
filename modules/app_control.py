"""
App Control Module

Controls application launching, with cross-platform support
(Windows, macOS, Linux).
"""

import platform
import subprocess

# Map a friendly app name to the command/executable used to launch it,
# per platform. Extend these dicts to support more apps.
_APP_COMMANDS = {
    'Windows': {
        'notepad': 'notepad.exe',
        'calc': 'calc.exe',
        'calculator': 'calc.exe',
        'paint': 'mspaint.exe',
        'explorer': 'explorer.exe',
    },
    'Darwin': {  # macOS
        'notepad': 'TextEdit',
        'calc': 'Calculator',
        'calculator': 'Calculator',
        'paint': 'Preview',
        'explorer': 'Finder',
    },
    'Linux': {
        'notepad': 'gedit',
        'calc': 'gnome-calculator',
        'calculator': 'gnome-calculator',
    },
}


def open_app(app_name: str) -> bool:
    """
    Open an application by friendly name, on whichever OS we're running on.

    Args:
        app_name: Name of the app to open (e.g. 'notepad', 'calc').

    Returns:
        bool: True if a launch was attempted successfully, False otherwise.
    """
    if not app_name:
        print("Please specify an app name.")
        return False

    system = platform.system()  # 'Windows', 'Darwin', or 'Linux'
    commands = _APP_COMMANDS.get(system, {})
    key = app_name.strip().lower()
    target = commands.get(key)

    if not target:
        supported = ', '.join(sorted(commands.keys())) or 'none configured for this OS'
        print(f"App '{app_name}' not supported on {system}. Supported: {supported}.")
        return False

    try:
        if system == 'Windows':
            import os
            os.startfile(target)  # noqa: only valid on Windows, guarded above
        elif system == 'Darwin':
            subprocess.Popen(['open', '-a', target])
        else:  # Linux and anything else we attempt via subprocess
            subprocess.Popen([target])
        print(f"Opening {app_name}...")
        return True
    except FileNotFoundError:
        print(f"Could not find '{target}' on this system. Is it installed and on PATH?")
        return False
    except Exception as e:
        print(f"Error opening app: {e}")
        return False
