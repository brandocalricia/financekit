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

# Install dependencies if needed
if [ ! -f ".deps_installed" ]; then
    echo "  Installing dependencies (first time only)..."
    echo ""
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo "  [ERROR] Failed to install dependencies."
        echo "  Try running: pip3 install -r requirements.txt"
        exit 1
    fi
    touch .deps_installed
    echo ""
    echo "  Dependencies installed successfully!"
    echo ""
fi

echo "  Starting FinanceKit..."
echo "  The app will open in your browser automatically."
echo "  To stop, press Ctrl+C."
echo ""
python3 -m streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
