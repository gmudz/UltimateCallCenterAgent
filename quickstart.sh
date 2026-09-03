#!/usr/bin/env bash
# ==============================================================================
# Ultimate AI Sales Copilot — Quick Start Script
# Automated setup, dependency installation, and server startup.
# ==============================================================================

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "================================================================================"
echo "    🤖 ULTIMATE AI SALES COPILOT — FINANCIAL BROKERAGE CALL CENTER AGENT      "
echo "================================================================================"
echo -e "${NC}"

# 1. Determine script directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 2. Check for Python 3
echo -e "${BLUE}▶ Checking Python installation...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python 3 is not installed or not in PATH. Please install Python 3.10+ and re-run.${NC}"
    exit 1
fi

PY_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Found Python ${PY_VERSION} (${PYTHON_CMD})${NC}"

# 3. Create or verify virtual environment
VENV_DIR="$PROJECT_ROOT/venv"
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "${BLUE}▶ Creating Python virtual environment in ./venv...${NC}"
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created.${NC}"
else
    # Check if virtual environment python works
    if ! "$VENV_DIR/bin/python" -c 'import sys' &>/dev/null; then
        echo -e "${YELLOW}⚠️  Existing venv appears incompatible. Recreating...${NC}"
        rm -rf "$VENV_DIR"
        $PYTHON_CMD -m venv "$VENV_DIR"
        echo -e "${GREEN}✓ Virtual environment recreated.${NC}"
    else
        echo -e "${GREEN}✓ Existing virtual environment detected.${NC}"
    fi
fi

# 4. Activate virtual environment
source "$VENV_DIR/bin/activate"

# 5. Upgrade pip & install dependencies
echo -e "${BLUE}▶ Installing dependencies from requirements.txt...${NC}"
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed successfully.${NC}"

# 6. Setup .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}▶ No .env file found. Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file.${NC}"
    fi
fi

# 7. Ensure data directory structure
mkdir -p data/uploads data/recordings
if [ ! -f "data/uploads/_manifest.json" ]; then
    echo "[]" > data/uploads/_manifest.json
fi

# 8. Detect configured port
PORT="${PORT:-8000}"
if [ -f ".env" ]; then
    ENV_PORT=$(grep -E '^PORT=' .env | cut -d '=' -f2 | tr -d ' "')
    if [ -n "$ENV_PORT" ]; then
        PORT="$ENV_PORT"
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}================================================================================"
echo "    🚀 Ready to launch AI Sales Copilot!                                        "
echo "================================================================================${NC}"
echo -e "${CYAN}• Live Dashboard:       ${BOLD}http://localhost:${PORT}/${NC}"
echo -e "${CYAN}• Admin Management:     ${BOLD}http://localhost:${PORT}/admin${NC}"
echo -e "${CYAN}• Sales Training:       ${BOLD}http://localhost:${PORT}/training${NC}"
echo -e "${CYAN}• Analytics & Reports:  ${BOLD}http://localhost:${PORT}/analytics${NC}"
echo -e "${CYAN}• API Documentation:    ${BOLD}http://localhost:${PORT}/docs${NC}"
echo ""
echo -e "${YELLOW}🔑 Default Admin Account:${NC}"
echo -e "   Username: ${BOLD}admin${NC}"
echo -e "   Password: ${BOLD}admin123${NC}"
echo ""
echo -e "${BLUE}💡 Tip: Add your Google Gemini API key to .env (GEMINI_API_KEY) or in the Admin UI${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# 9. Start server
echo -e "${GREEN}▶ Starting Uvicorn server on http://0.0.0.0:${PORT}...${NC}"
exec uvicorn main.py:app --host 0.0.0.0 --port "$PORT" --reload
