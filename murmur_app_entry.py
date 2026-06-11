#!/usr/bin/env python3
"""
Entry point for the Murmur.app bundle.

This file is the main script that py2app bundles into the .app.
It sets up the environment so that the bundled app behaves correctly,
then delegates to the normal murmur.main:main entry point.
"""

import os
import sys


def _patch_sys_executable_for_subprocesses():
    """
    Murmur launches Settings, Vocabulary, and Fix windows as subprocesses
    using `sys.executable -m murmur.settings_window`. Inside a py2app bundle,
    sys.executable points to the bundle's Python, which is correct.

    However, we also need to make sure the subprocess can find the murmur
    package. We do this by ensuring the bundle's Resources/lib directory
    is on sys.path (py2app normally handles this, but we verify it here).
    """
    if getattr(sys, "frozen", False):
        # Running inside a py2app bundle
        bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
        resources_dir = os.path.join(bundle_dir, "Resources")
        lib_dir = os.path.join(resources_dir, "lib")

        # Ensure the bundled lib directories are on the path
        for d in [resources_dir, lib_dir]:
            if os.path.isdir(d) and d not in sys.path:
                sys.path.insert(0, d)

        # Also look for lib/pythonX.Y
        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        pylib = os.path.join(lib_dir, pyver)
        if os.path.isdir(pylib) and pylib not in sys.path:
            sys.path.insert(0, pylib)

        site_packages = os.path.join(pylib, "site-packages")
        if os.path.isdir(site_packages) and site_packages not in sys.path:
            sys.path.insert(0, site_packages)


def _setup_environment():
    """
    Set environment variables needed by the bundled app.
    """
    # Ensure Hugging Face model cache uses the standard location,
    # not somewhere inside the app bundle.
    if "HF_HOME" not in os.environ:
        os.environ["HF_HOME"] = os.path.expanduser("~/.cache/huggingface")

    # Ensure the config directory exists
    if sys.platform == "darwin":
        config_dir = os.path.expanduser("~/.murmur")
        os.makedirs(config_dir, exist_ok=True)


def main():
    _patch_sys_executable_for_subprocesses()
    _setup_environment()

    _sub = {"--permissions", "--settings", "--vocabulary", "--fix"}
    if _sub & set(sys.argv):
        if "--permissions" in sys.argv:
            from murmur.permissions import _has_access, _show_onboarding
            if not _has_access():
                _show_onboarding()
            sys.exit(0)
        if "--settings" in sys.argv:
            from murmur.settings_window import SettingsWindow
            SettingsWindow()
            sys.exit(0)
        if "--vocabulary" in sys.argv:
            from murmur.vocabulary_window import VocabularyWindow
            VocabularyWindow()
            sys.exit(0)
        if "--fix" in sys.argv:
            from murmur.fix_window import FixWindow
            FixWindow()
            sys.exit(0)

    from murmur.main import main as murmur_main
    murmur_main()


if __name__ == "__main__":
    main()
