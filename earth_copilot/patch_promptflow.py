#!/usr/bin/env python3
"""
Patch script to fix the missing 'import os' in PromptFlow's static_web_blueprint.py
This script should be run before starting the PromptFlow server to fix the bug.
"""

import os
import sys
import importlib.util


def patch_static_web_blueprint():
    """Patch the static_web_blueprint.py file to add missing 'import os'"""

    # Find the promptflow package location
    try:
        import promptflow

        promptflow_path = promptflow.__path__[0]
    except ImportError:
        print("PromptFlow not found, skipping patch")
        return False

    # Path to the problematic file
    blueprint_file = os.path.join(
        promptflow_path,
        "core",
        "_serving",
        "v1",
        "blueprint",
        "static_web_blueprint.py",
    )

    if not os.path.exists(blueprint_file):
        print(f"Blueprint file not found at {blueprint_file}")
        return False

    # Read the current content
    with open(blueprint_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already patched
    if "import os" in content and content.find("import os") < content.find(
        "from pathlib import Path"
    ):
        print("PromptFlow already patched")
        return True

    # Apply the patch
    lines = content.split("\n")
    patched_lines = []

    for i, line in enumerate(lines):
        if line.strip() == "from pathlib import Path" and i > 0:
            # Insert 'import os' before 'from pathlib import Path'
            patched_lines.append("import os")
        patched_lines.append(line)

    # Write the patched content back
    try:
        with open(blueprint_file, "w", encoding="utf-8") as f:
            f.write("\n".join(patched_lines))
        print("PromptFlow successfully patched")
        return True
    except Exception as e:
        print(f"Failed to patch PromptFlow: {e}")
        return False


def apply_runtime_patch():
    """Apply runtime monkey patch as backup"""
    try:
        # Import the problematic module
        from promptflow.core._serving.v1.blueprint import static_web_blueprint
        
        # Add the missing 'os' module to the static_web_blueprint namespace
        if not hasattr(static_web_blueprint, 'os'):
            static_web_blueprint.os = os
            print("Applied runtime monkey patch for missing 'os' import")
        
        return True
    except Exception as e:
        print(f"Runtime patch failed: {e}")
        return False


if __name__ == "__main__":
    # Try file patch first
    file_patch_success = patch_static_web_blueprint()
    
    # Apply runtime patch as backup
    runtime_patch_success = apply_runtime_patch()
    
    # Exit with success if either patch worked
    success = file_patch_success or runtime_patch_success
    sys.exit(0 if success else 1)
