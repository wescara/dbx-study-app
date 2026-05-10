#!/usr/bin/env python3
"""
Quick launcher for the Databricks Study App
"""
import subprocess
import sys
import os

os.chdir(r"C:\dbx-study-app")
print("🚀 Launching Databricks Study App...")
print("Opening at: http://localhost:8501")
print("\nPress Ctrl+C to stop the app\n")

try:
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
except KeyboardInterrupt:
    print("\n\nApp stopped.")
except Exception as e:
    print(f"Error launching app: {e}")
    sys.exit(1)
