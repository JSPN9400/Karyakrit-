"""
Python helper features for local code execution.
"""

import os
import subprocess
import sys


def run_python_snippet(code: str) -> str:
    """Run a short Python snippet with the current interpreter."""
    snippet = code.strip()
    if not snippet:
        return "Please provide Python code to run."

    process = subprocess.run(
        [sys.executable, "-c", snippet],
        capture_output=True,
        text=True,
        cwd=os.getcwd(),
        timeout=30,
    )
    output = process.stdout.strip()
    error = process.stderr.strip()
    if process.returncode != 0:
        return error or "Python command failed."
    return output or "Python code ran successfully."


def run_python_file(file_path: str) -> str:
    """Run a Python file from the workspace."""
    target = file_path.strip()
    if not target:
        return "Please provide a Python file path."
    if not os.path.exists(target):
        return f"Python file not found: {target}"

    process = subprocess.run(
        [sys.executable, target],
        capture_output=True,
        text=True,
        cwd=os.getcwd(),
        timeout=60,
    )
    output = process.stdout.strip()
    error = process.stderr.strip()
    if process.returncode != 0:
        return error or "Python file execution failed."
    return output or f"Executed {target} successfully."
