"""
Excel Generator Module

Creates sample Excel files using pandas.
"""

import pandas as pd
import os

def create_excel(filename):
    """
    Create a sample Excel file.

    Args:
        filename (str): Name of the Excel file to create.
    """
    # Sample data
    data = {
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['New York', 'London', 'Tokyo']
    }

    df = pd.DataFrame(data)

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    filepath = os.path.join('data', filename)
    df.to_excel(filepath, index=False)
    print(f"Excel file created: {filepath}")