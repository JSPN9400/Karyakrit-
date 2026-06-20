"""
App Control Module

Controls application launching.
"""

import os
import subprocess

def open_app(app_name):
    """
    Open an application.

    Args:
        app_name (str): Name of the app to open.
    """
    if not app_name:
        print("Please specify an app name.")
        return

    try:
        # Simple way to open apps on Windows
        if app_name.lower() == 'notepad':
            os.startfile('notepad.exe')
        elif app_name.lower() == 'calc':
            os.startfile('calc.exe')
        else:
            print(f"App '{app_name}' not supported. Try 'notepad' or 'calc'.")
    except Exception as e:
        print(f"Error opening app: {e}")