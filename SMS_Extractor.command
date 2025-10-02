#!/bin/bash

# SMS Extractor Desktop Launcher
# Double-click to start SMS Extractor

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Open Terminal and run the start script
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$DIR' && ./start.sh"
end tell
EOF
