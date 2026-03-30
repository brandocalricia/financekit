#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo "  ================================================"
echo "     FinanceKit - Personal Finance Toolkit"
echo "  ================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "  [ERROR] Python 3 is not installed."
    echo "  Install with: brew install python@3.11  (macOS)"
    echo "  Or: sudo apt install python3.11  (Linux)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

python3 run_app.py || {
    echo ""
    echo "  FinanceKit requires Python 3.11+."
    echo ""
    read -p "Press Enter to exit..."
}
