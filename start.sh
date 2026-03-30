#!/bin/bash
echo ""
echo "  ================================================"
echo "     FinanceKit - Personal Finance Toolkit"
echo "  ================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "  [ERROR] Python 3 is not installed."
    echo "  Install it from https://python.org or via your package manager."
    exit 1
fi

# Launch via launcher.py (handles deps, server, browser)
python3 launcher.py
