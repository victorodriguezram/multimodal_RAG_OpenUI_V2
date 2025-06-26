#!/bin/bash

# Multimodal RAG System - Script Launcher
# This launches the interactive script menu

echo "🚀 Launching Multimodal RAG Script Manager..."
echo ""

# Check if scripts directory exists
if [ ! -d "scripts" ]; then
    echo "❌ Error: scripts directory not found!"
    echo "Please make sure you're running this from the project root directory."
    exit 1
fi

# Make menu script executable and run it
chmod +x scripts/menu.sh
./scripts/menu.sh
