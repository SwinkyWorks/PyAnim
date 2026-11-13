#!/usr/bin/env python3
"""Build PyAnim into a standalone, ad-hoc-signed macOS .app bundle.

Usage:
    python3 build.py            # build dist/PyAnim.app
    python3 build.py --test     # build, then smoke-test it headlessly

Why bundle at all: macOS AMFI re-verifies code signatures every time a dylib
is dlopen'd, so a venv whose PySide6 Qt plugins were written in place gets
rejected ("Could not find the Qt platform plugin"). A frozen app ships its own
copy of every library and gets one consistent ad-hoc signature over the whole
bundle, which macOS does not break.

Read-only resources (images, help) are bundled into the app. `plugins/` is
also bundled, but only as a *template*: on first launch the app copies it into
~/Library/Application Support/PyAnim/ so plugins stay editable Python without
rebuilding (see core/paths.py).
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "PyAnim"
DIST = ROOT / "dist"
APP_BUNDLE = DIST / f"{APP_NAME}.app"

#: (source dir, destination name inside the bundle's resource dir)
DATA_DIRS = ["images", "help", "plugins"]


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(c) for c in cmd))
    result = subprocess.run([str(c) for c in cmd], cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"Command failed with exit code {result.returncode}")


def clean() -> None:
    for path in (DIST, ROOT / "build", ROOT / f"{APP_NAME}.spec"):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def build() -> None:
    pyinstaller = Path(sys.executable).parent / "pyinstaller"
    if not pyinstaller.exists():
        pyinstaller = Path("pyinstaller")

    args = [
        pyinstaller,
        "--noconfirm",
        "--clean",
        "--windowed",          # .app bundle, no terminal
        "--onedir",            # faster startup + inspectable internals vs onefile
        f"--name={APP_NAME}",
        "--exclude-module=test_visibility",
    ]
    for name in DATA_DIRS:
        source = ROOT / name
        if not source.exists():
            sys.exit(f"Missing resource directory to bundle: {source}")
        args.append(f"--add-data={source}{os.pathsep}{name}")

    # imageio-ffmpeg ships a standalone ffmpeg binary that a plain import
    # analysis would miss entirely.
    args += ["--collect-binaries=imageio_ffmpeg",
             "--collect-data=imageio_ffmpeg"]

    args.append(str(ROOT / "main.py"))
    run(args)


def sign() -> None:
    """Ad-hoc re-sign the whole bundle so every nested dylib agrees.

    This is the step that keeps AMFI happy without an Apple Developer ID.

    The signing has to happen OUTSIDE the project directory: when the repo
    lives in an iCloud-synced folder (~/Documents, ~/Desktop), the FileProvider
    re-stamps `com.apple.FinderInfo` onto directories mid-signing, and codesign
    aborts with "resource fork, Finder information, or similar detritus not
    allowed". So we copy to a local temp dir, strip xattrs, sign there, then
    copy the finished bundle back. A signed bundle survives being copied back —
    only *signing in place* loses the race.
    """
    with tempfile.TemporaryDirectory(prefix="pyanim-sign-") as tmp:
        staging = Path(tmp) / f"{APP_NAME}.app"
        run(["ditto", str(APP_BUNDLE), str(staging)])
        # Clear provenance/FinderInfo/quarantine that iCloud and copy add.
        run(["xattr", "-cr", str(staging)])
        run(["codesign", "--force", "--deep", "--sign", "-",
             "--timestamp=none", str(staging)])
        run(["codesign", "--verify", "--deep", "--strict", str(staging)])
        # Replace the unsigned bundle with the freshly signed one.
        shutil.rmtree(APP_BUNDLE)
        run(["ditto", str(staging), str(APP_BUNDLE)])

    # Verify the copy that actually ships.
    run(["codesign", "--verify", "--deep", "--strict", str(APP_BUNDLE)])


def smoke_test() -> None:
    """Launch the frozen app offscreen and confirm it initialises fully."""
    binary = APP_BUNDLE / "Contents" / "MacOS" / APP_NAME
    if not binary.exists():
        sys.exit(f"Bundle executable not found: {binary}")

    env = dict(os.environ, QT_QPA_PLATFORM="offscreen",
               PYANIM_SMOKE_TEST="1")
    print("+ QT_QPA_PLATFORM=offscreen PYANIM_SMOKE_TEST=1", binary)
    process = subprocess.Popen(
        [str(binary)], cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        output, _ = process.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
        print(output[-4000:])
        sys.exit("Smoke test timed out: the bundle never exited on its own.")

    print(output[-4000:])
    if "App fully initialized!" not in output:
        sys.exit("Smoke test failed: 'App fully initialized!' never printed.")
    if process.returncode != 0:
        sys.exit(f"Smoke test failed: bundle exited with {process.returncode}")
    print("✅ Smoke test passed: the frozen app initialised cleanly.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true",
                        help="smoke-test the bundle after building it")
    parser.add_argument("--no-sign", action="store_true",
                        help="skip the ad-hoc codesign step")
    parser.add_argument("--no-clean", action="store_true",
                        help="keep previous build output")
    args = parser.parse_args()

    if not args.no_clean:
        clean()
    build()
    if not args.no_sign:
        sign()

    print(f"\nBuilt: {APP_BUNDLE}")
    if args.test:
        print()
        smoke_test()


if __name__ == "__main__":
    main()
