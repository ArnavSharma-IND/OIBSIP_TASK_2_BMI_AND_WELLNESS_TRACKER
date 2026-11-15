"""
PyInstaller Build Automation Script
Packages the BMI & Wellness Tracker into a self-contained Windows executable.
Ensures correct dynamic data path resolution, bundled assets, and windowed mode.
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def build():
    print("=" * 60)
    print("BMI & Wellness Tracker – Standalone Windows Build")
    print("=" * 60)

    try:
        import PyInstaller
        print(f"PyInstaller version {PyInstaller.__version__} detected.")
    except ImportError:
        print("PyInstaller is not currently installed in this environment.")
        print("Please install it by running: pip install pyinstaller")
        return False

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "BMI_Wellness_Tracker",
        "--add-data",
        f"{BASE_DIR / 'assets'};assets",
        str(BASE_DIR / "main.py"),
    ]

    print("Executing build command:")
    print(" ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode == 0:
        dist_path = BASE_DIR / "dist" / "BMI_Wellness_Tracker" / "BMI_Wellness_Tracker.exe"
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Executable output: {dist_path}")
        print("=" * 60)
        return True
    else:
        print("\nBuild failed with exit code:", result.returncode)
        return False


if __name__ == "__main__":
    build()
