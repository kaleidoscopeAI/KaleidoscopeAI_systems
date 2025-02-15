#!/usr/bin/env bash
set -e -o pipefail

# ------------------------------------------------------------------------------
# run.sh - Launcher script for Kaleidoscope AI system
# ------------------------------------------------------------------------------
# This script ensures that the correct conda environment is active,
# sets the PYTHONPATH to include the project root,
# verifies (and creates if missing) required directories,
# and then launches the web application.
# ------------------------------------------------------------------------------

# 1. Check if the correct conda environment is active.
if [ "$CONDA_DEFAULT_ENV" != "kaleidoscope" ]; then
    echo "ERROR: The 'kaleidoscope' conda environment is not active."
    echo "Please run: conda activate kaleidoscope"
    exit 1
fi

# 2. Add the project root to PYTHONPATH.
PROJECT_ROOT=$(pwd)
export PYTHONPATH="$PYTHONPATH:$PROJECT_ROOT"
echo "Project root ($PROJECT_ROOT) added to PYTHONPATH."

# 3. Verify that critical directories exist; create them if missing.
REQUIRED_DIRS=("core" "web" "config" "data" "results")
for DIR in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$PROJECT_ROOT/$DIR" ]; then
        echo "Directory '$DIR' not found. Creating it..."
        mkdir -p "$PROJECT_ROOT/$DIR" || { echo "ERROR: Failed to create directory '$DIR'."; exit 1; }
    fi
done

# 4. Launch the web application using module mode.
echo "Launching the Kaleidoscope AI web application..."
python -m web.app || { echo "ERROR: Failed to launch the web application."; exit 1; }
