#!/usr/bin/env python3
"""
Auto-fix for PromptFlow missing 'import os' bug
This module automatically fixes the issue when imported
"""

import os
import sys


def auto_fix_os_import():
    """Automatically fix the missing os import in static_web_blueprint"""
    try:
        # Import the problematic module
        from promptflow.core._serving.v1.blueprint import static_web_blueprint

        # Add the missing 'os' module to the static_web_blueprint namespace
        if not hasattr(static_web_blueprint, "os"):
            static_web_blueprint.os = os
            print("Auto-fixed missing 'os' import in static_web_blueprint")

        return True
    except Exception as e:
        print(f"Auto-fix failed: {e}")
        return False


# Apply the fix immediately when this module is imported
auto_fix_os_import()
