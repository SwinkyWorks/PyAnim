#!/usr/bin/env python3
"""Auto-healing launcher for PyAnim that reinstalls PySide6 when AMFI blocks it."""
import subprocess
import sys
import threading
import shutil
from pathlib import Path


def run_app():
    """Run the main app, showing output in real-time while capturing for error detection."""
    print("🚀 Launching PyAnim...")

    # Start process with pipes for both stdout and stderr
    process = subprocess.Popen(
        ["uv", "run", "python", "-u", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )

    # Storage for captured output
    stdout_lines = []
    stderr_lines = []

    def read_stream(stream, storage, prefix=""):
        """Read from stream line-by-line, print and store."""
        for line in stream:
            line = line.rstrip()
            if line:
                print(f"{prefix}{line}")
                storage.append(line)

    # Create threads to read both streams simultaneously
    stdout_thread = threading.Thread(
        target=read_stream,
        args=(process.stdout, stdout_lines)
    )
    stderr_thread = threading.Thread(
        target=read_stream,
        args=(process.stderr, stderr_lines, "")
    )

    # Start reading
    stdout_thread.start()
    stderr_thread.start()

    # Wait for process to complete
    exit_code = process.wait()

    # Wait for all output to be read
    stdout_thread.join()
    stderr_thread.join()

    # Combine output for error detection
    stdout_text = "\n".join(stdout_lines)
    stderr_text = "\n".join(stderr_lines)

    return exit_code, stderr_text, stdout_text


def clean_duplicate_files():
    """Remove duplicate numbered files created by failed UV uninstalls."""
    site_packages = Path(".venv/lib/python3.12/site-packages")
    venv_root = Path(".venv")

    if not site_packages.exists():
        return

    # Clean pyanim dist-info
    dist_info = site_packages / "pyanim-0.1.0.dist-info"
    if dist_info.exists():
        shutil.rmtree(dist_info, ignore_errors=True)

    # Clean numbered .pth files (pyanim 2.pth, pyanim 3.pth, etc.)
    for pth_file in site_packages.glob("pyanim *.pth"):
        pth_file.unlink(missing_ok=True)

    # Clean numbered lock files
    for lock_file in venv_root.glob(".lock *"):
        lock_file.unlink(missing_ok=True)

    # Clean numbered bin files
    for bin_file in Path(".venv/.bin").glob("pyside6"):
        bin_file.unlink(missing_ok=True)


def reinstall_pyside6():
    """Reinstall PySide6 to refresh signatures."""
    print("\n🔄 Detected PySide6 issue, reinstalling packages...")
    print("   (macOS occasionally blocks Qt libraries)")

    print("   Cleaning up duplicate files...")
    clean_duplicate_files()

    print("   Removing old packages...")
    subprocess.run(
        ["rm", "-r", "-x",
         ".venv/lib/python3.12/site-packages/PySide6",
         ".venv/lib/python3.12/site-packages/PySide6_Addons-6.8.3.dist-info",
         ".venv/lib/python3.12/site-packages/PySide6_Essentials-6.8.3.dist-info",
         ".venv/lib/python3.12/site-packages/PySide6-6.8.3.dist-info",
         ".venv/lib/python3.12/site-packages/shiboken6",
         ".venv/lib/python3.12/site-packages/shiboken6-6.8.3.dist-info"
         ], cwd=Path(__file__).resolve().parent
    )

    print("   Reinstalling PySide6...")
    result = subprocess.run(
        ["uv", "add", "PySide6==6.8.3", "shiboken6==6.8.3"]
    )

    if result.returncode != 0:
        print("❌ Failed to reinstall PySide6")
        return False

    print("✅ Reinstall complete!")
    return True


def is_pyside_error(stderr: str, stdout: str) -> bool:
    """Check if error is PySide6 related."""
    combined = stderr + stdout

    # Common PySide6/Qt errors
    patterns = [
        'Could not find the Qt platform plugin "cocoa"',
        'no Qt platform plugin could be initialized',
        'code signature',
        'not valid for use in process',
        'Trying to load an unsigned library',
        'ImportError: dlopen',
        'ModuleNotFoundError: ',
        "No module named '"
    ]

    return any(pattern in combined for pattern in patterns)


def main():
    """Launch PyAnim with auto-healing for signing issues."""
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print(f"\n🔄 Launch attempt {attempt}/{max_attempts}...\n")

        exit_code, stderr, stdout = run_app()

        # App launched successfully
        if exit_code == 0:
            print("✅ PyAnim closed normally")
            sys.exit(0)

        # Check for PySide6 errors
        elif is_pyside_error(stderr, stdout):
            print("\n❌ PySide6/Qt loading error detected")

            if attempt < max_attempts:
                if not reinstall_pyside6():
                    sys.exit(1)
                continue
            else:
                print("❌ Failed to launch after reinstalling.")
                print("\n⚠️  This usually means macOS AMFI is blocking the libraries.")
                print("   Solutions:")
                print("   • Get an Apple Developer certificate ($99/year)")
                print("   • Disable SIP in Recovery Mode (security risk)")
                print("   • Use a Linux VM for development")
                sys.exit(1)

        # Different error - show it and exit
        print(f"\n❌ App crashed with exit code {exit_code}")
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
