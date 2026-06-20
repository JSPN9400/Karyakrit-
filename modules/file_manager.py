"""
File Manager Module

Handles file operations.
"""

# Placeholder for file management features
# Can be extended to list files, move, copy, etc.

def list_files(directory='.'):
    """
    List files in a directory.

    Args:
        directory (str): Directory to list.
    """
    import os
    try:
        files = os.listdir(directory)
        print(f"Files in {directory}:")
        for f in files:
            print(f"  {f}")
    except Exception as e:
        print(f"Error listing files: {e}")