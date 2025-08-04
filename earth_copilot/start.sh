#!/bin/bash

# Custom startup script for PromptFlow deployment
# This script patches the PromptFlow library and then starts the server

echo "Starting PromptFlow deployment with patch..."

# Apply the PromptFlow patch
echo "Applying PromptFlow patch..."
python patch_promptflow.py

if [ $? -eq 0 ]; then
    echo "Patch applied successfully"
else
    echo "Warning: Patch failed, but continuing with startup"
fi

# Start the PromptFlow server
echo "Starting PromptFlow server..."
exec python -m promptflow._cli._pf.entry serve --source . --port 80 --host 0.0.0.0
