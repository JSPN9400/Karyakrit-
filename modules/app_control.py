"""
App Control Module

Controls application launching, with cross-platform support
(Windows, macOS, Linux). Instead of relying solely on a hardcoded
name -> executable map, this module also scans the OS's normal
"installed apps" locations (the same places Windows Start Menu search,
macOS Spotlight, and Linux app launchers read from) so it can open any
installed application by approximate name, not just a fixed list.
"""

import os
import platform
import subprocess
import time
import webbrowser
from shutil import which
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process

# A small set of well-known shortcuts that should always work even if OS
# scanning fails or finds nothing (e.g. sandboxed/minimal environments).
# These are also useful aliases (e.g. "calc" -> the real calculator name
# differs per OS/locale).
_KNOWN_ALIASES = {
    'Windows': {
        'notepad': 'notepad.exe',
        'calc': 'calc.exe',
        'calculator': 'calc.exe',
        'paint': 'mspaint.exe',
        'explorer': 'explorer.exe',
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe',
        'firefox': 'firefox.exe',
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe',
        'outlook': 'outlook.exe',
        'cmd': 'cmd.exe',
        'terminal': 'wt.exe',
        'powershell': 'powershell.exe',
        'settings': 'ms-settings:',
    },
    'Darwin': {
        'notepad': 'TextEdit',
        'calc': 'Calculator',
        'calculator': 'Calculator',
        'paint': 'Preview',
        'explorer': 'Finder',
        'terminal': 'Terminal',
    },
    'Linux': {
        'notepad': 'gedit',
        'calc': 'gnome-calculator',
        'calculator': 'gnome-calculator',
        'terminal': 'gnome-terminal',
    },
}

# Browser-only "apps" that are really just websites. Kept separate from
# desktop-app discovery so they always work even with no browser shortcut
# installed locally.
_WEB_TARGETS = {
    'whatsapp': 'https://web.whatsapp.com/',
    'linkedin': 'https://www.linkedin.com/',
    'github': 'https://github.com/',
    'youtube': 'https://www.youtube.com/',
    'gmail': 'https://mail.google.com/',
    'instagram': 'https://www.instagram.com/',
}

_CACHE_TTL_SECONDS = 300  # rescan installed apps at most every 5 minutes
_app_cache: Dict[str, Tuple[float, Dict[str, str]]] = {}


def _scan_windows_apps() -> Dict[str, str]:
    """
    Scan Windows Start Menu shortcut folders for installed apps.
    Returns {lowercase display name: path to .lnk or executable}.
    """
    apps: Dict[str, str] = {}
    start_menu_dirs = [
        os.path.join(os.environ.get('ProgramData', r'C:\ProgramData'),
                     r'Microsoft\Windows\Start Menu\Programs'),
        os.path.join(os.environ.get('APPDATA', ''),
                     r'Microsoft\Windows\Start Menu\Programs') if os.environ.get('APPDATA') else '',
    ]
    for base in start_menu_dirs:
        if not base or not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for name in files:
                if name.lower().endswith('.lnk'):
                    display = os.path.splitext(name)[0].lower()
                    apps[display] = os.path.join(root, name)
    return apps


def _scan_macos_apps() -> Dict[str, str]:
    """Scan /Applications and ~/Applications for .app bundles."""
    apps: Dict[str, str] = {}
    dirs = ['/Applications', os.path.expanduser('~/Applications')]
    for base in dirs:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            if name.endswith('.app'):
                display = name[:-4].lower()
                apps[display] = os.path.join(base, name)
    return apps


def _scan_linux_apps() -> Dict[str, str]:
    """
    Scan standard XDG .desktop application directories.
    Returns {lowercase display name: app id usable with `gtk-launch`/`xdg-open`,
    falling back to the Exec= command if needed}.
    """
    apps: Dict[str, str] = {}
    dirs = [
        '/usr/share/applications',
        '/usr/local/share/applications',
        os.path.expanduser('~/.local/share/applications'),
    ]
    for base in dirs:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            if not name.endswith('.desktop'):
                continue
            path = os.path.join(base, name)
            display = name[:-len('.desktop')].lower()
            exec_cmd = None
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
                    for line in handle:
                        if line.startswith('Name=') and display not in apps:
                            # Prefer the human-readable Name= for matching too
                            human = line[len('Name='):].strip().lower()
                            if human:
                                apps.setdefault(human, name)  # store desktop id
                        if line.startswith('Exec='):
                            exec_cmd = line[len('Exec='):].strip()
            except OSError:
                continue
            apps[display] = name  # desktop file id, launched via gtk-launch
            if exec_cmd:
                # also index by the bare command name as a fallback alias
                bare = exec_cmd.split()[0].split('/')[-1].lower()
                apps.setdefault(bare, name)
    return apps


def _get_installed_apps(system: str) -> Dict[str, str]:
    """Return a cached (or freshly scanned) map of installed app names -> launch targets."""
    now = time.time()
    cached = _app_cache.get(system)
    if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    if system == 'Windows':
        scanned = _scan_windows_apps()
    elif system == 'Darwin':
        scanned = _scan_macos_apps()
    elif system == 'Linux':
        scanned = _scan_linux_apps()
    else:
        scanned = {}

    _app_cache[system] = (now, scanned)
    return scanned


def find_installed_app(app_name: str, system: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Find the closest-matching installed app by name.

    Returns (matched_display_name, launch_target) or None if nothing
    reasonably close was found.
    """
    system = system or platform.system()
    installed = _get_installed_apps(system)
    if not installed:
        return None

    key = app_name.strip().lower()
    if key in installed:
        return key, installed[key]

    # Fuzzy match against all known installed app display names.
    match = process.extractOne(key, list(installed.keys()), scorer=fuzz.WRatio)
    if match and match[1] >= 72:
        matched_name = match[0]
        return matched_name, installed[matched_name]
    return None


def list_installed_apps(system: Optional[str] = None, limit: int = 30) -> List[str]:
    """Return a sorted list of discovered installed app display names (for `list apps`)."""
    system = system or platform.system()
    installed = _get_installed_apps(system)
    return sorted(installed.keys())[:limit]


def _launch_windows_lnk(path: str) -> bool:
    os.startfile(path)  # noqa: Windows-only, guarded by caller
    return True


def _launch_macos_app(path_or_name: str) -> bool:
    _detached_popen(['open', '-a', path_or_name])
    return True


def _desktop_file_path(desktop_id: str) -> Optional[str]:
    """Find the full path to a .desktop file by its id/filename."""
    dirs = [
        '/usr/share/applications',
        '/usr/local/share/applications',
        os.path.expanduser('~/.local/share/applications'),
    ]
    name = desktop_id if desktop_id.endswith('.desktop') else f'{desktop_id}.desktop'
    for base in dirs:
        candidate = os.path.join(base, name)
        if os.path.isfile(candidate):
            return candidate
    return None


def _exec_command_from_desktop_file(path: str) -> Optional[List[str]]:
    """Extract a runnable command list from a .desktop file's Exec= line."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
            for line in handle:
                if line.startswith('Exec='):
                    raw = line[len('Exec='):].strip()
                    # Strip desktop-entry field codes like %f %U %i etc.
                    cleaned = ' '.join(part for part in raw.split() if not part.startswith('%'))
                    if cleaned:
                        return cleaned.split()
    except OSError:
        return None
    return None


def _detached_popen(command: List[str]):
    """
    Launch a subprocess fully detached from this process's stdout/stderr.

    Without this, a launched GUI app that writes enough startup output can
    block waiting for a full pipe if it inherits our stdout/stderr, which
    in turn blocks the assistant itself.
    """
    return subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )


def _launch_linux_app(desktop_id_or_name: str) -> bool:
    # Prefer gtk-launch when available (correctly honors the .desktop file's
    # Exec= line, terminal flag, etc.).
    if which('gtk-launch'):
        target = desktop_id_or_name
        if target.endswith('.desktop'):
            target = target[: -len('.desktop')]
        result = subprocess.run(
            ['gtk-launch', target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        if result.returncode == 0:
            return True

    # gtk-launch missing or failed: parse the .desktop file's Exec= line
    # ourselves and run that directly.
    desktop_path = _desktop_file_path(desktop_id_or_name)
    if desktop_path:
        command = _exec_command_from_desktop_file(desktop_path)
        if command and which(command[0]):
            _detached_popen(command)
            return True

    # Last resort: try it as a bare executable on PATH.
    if which(desktop_id_or_name):
        _detached_popen([desktop_id_or_name])
        return True

    raise FileNotFoundError(desktop_id_or_name)


def open_app(app_name: str) -> bool:
    """
    Open an application by approximate name, on whichever OS we're running on.

    Resolution order:
      1. Known web-only targets (whatsapp, linkedin, github, youtube, gmail, instagram)
         open in the default browser.
      2. Known short aliases (calc, notepad, terminal, ...) for fast, reliable launches.
      3. OS-wide installed-app discovery (Start Menu shortcuts on Windows,
         /Applications on macOS, .desktop files on Linux) with fuzzy name matching,
         so any installed app can be opened by approximate name.
      4. Last resort: try the literal name as a command on PATH.

    Args:
        app_name: Name of the app to open (e.g. 'notepad', 'vs code', 'spotify').

    Returns:
        bool: True if a launch was attempted successfully, False otherwise.
    """
    if not app_name:
        print("Please specify an app name.")
        return False

    key = app_name.strip().lower()
    system = platform.system()  # 'Windows', 'Darwin', or 'Linux'

    # 1. Web-only targets
    if key in _WEB_TARGETS:
        webbrowser.open(_WEB_TARGETS[key])
        print(f"Opening {app_name} in your browser...")
        return True

    # 2. Known aliases for this OS
    aliases = _KNOWN_ALIASES.get(system, {})
    target = aliases.get(key)
    if target:
        return _launch(system, app_name, target)

    # 3. OS-wide installed app discovery
    found = find_installed_app(key, system)
    if found:
        matched_name, launch_target = found
        if matched_name != key:
            print(f"Found closest match: {matched_name}")
        return _launch(system, matched_name, launch_target)

    # 4. Last resort: try it literally as a PATH executable
    print(f"Couldn't find an installed app matching '{app_name}'. Trying it as a direct command...")
    return _launch(system, app_name, app_name.strip())


def _launch(system: str, display_name: str, target: str) -> bool:
    try:
        if target.startswith(('http://', 'https://')):
            webbrowser.open(target)
            print(f"Opening {display_name}...")
            return True

        if system == 'Windows':
            try:
                if target.lower().endswith('.lnk') or os.path.isabs(target):
                    _launch_windows_lnk(target)
                else:
                    os.startfile(target)  # noqa: Windows-only path
            except OSError:
                executable = which(target) or which(f"{target}.exe")
                if executable:
                    _detached_popen([executable])
                else:
                    _detached_popen(['cmd', '/c', 'start', '', target])
        elif system == 'Darwin':
            _launch_macos_app(target)
        elif system == 'Linux':
            _launch_linux_app(target)
        else:
            _detached_popen([target])

        print(f"Opening {display_name}...")
        return True
    except FileNotFoundError:
        print(f"Could not find '{target}' on this system. Is it installed and on PATH?")
        return False
    except Exception as e:
        print(f"Error opening app: {e}")
        return False
