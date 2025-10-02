#!/bin/bash

# SMS Extractor - Elegant Startup Script
# Author: SMS Extractor Team
# Date: 2025-10-02

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$PROJECT_DIR/sms_backend"

# Clear screen
clear

# Display welcome banner
echo -e "${CYAN}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║       ███████╗███╗   ███╗███████╗    ███████╗██╗  ██╗          ║
║       ██╔════╝████╗ ████║██╔════╝    ██╔════╝╚██╗██╔╝          ║
║       ███████╗██╔████╔██║███████╗    █████╗   ╚███╔╝           ║
║       ╚════██║██║╚██╔╝██║╚════██║    ██╔══╝   ██╔██╗           ║
║       ███████║██║ ╚═╝ ██║███████║    ███████╗██╔╝ ██╗          ║
║       ╚══════╝╚═╝     ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝          ║
║                                                                  ║
║              Systematic Review Management System                 ║
║                      Data Extraction Tool                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${WHITE}Version:${NC} 2.0.0 | ${WHITE}Django:${NC} 5.2.7 | ${WHITE}Python:${NC} 3.10+"
echo ""

# Check environment
echo -e "${YELLOW}[1/5]${NC} Checking runtime environment..."

# Check Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python not installed${NC}"
    exit 1
fi
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION}"

# Check project directory
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ Project directory not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Project directory"

# Check .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠ .env file not found, using default configuration${NC}"
else
    echo -e "${GREEN}✓${NC} Environment configuration"
fi

# Check dependencies
echo -e "\n${YELLOW}[2/5]${NC} Checking dependencies..."
cd "$BACKEND_DIR"

if python -c "import django" 2>/dev/null; then
    DJANGO_VERSION=$(python -c "import django; print(django.get_version())")
    echo -e "${GREEN}✓${NC} Django ${DJANGO_VERSION}"
else
    echo -e "${YELLOW}⚠ Django not installed, installing dependencies...${NC}"
    pip install -r "$PROJECT_DIR/requirements.txt" -q
fi

# Check database
echo -e "\n${YELLOW}[3/5]${NC} Checking database connection..."
if python manage.py check --database default 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Database connection OK"
else
    echo -e "${YELLOW}⚠ Database connection issue, attempting to apply migrations...${NC}"
    python manage.py migrate --no-input > /dev/null 2>&1
fi

# Check migrations
echo -e "\n${YELLOW}[4/5]${NC} Checking database migrations..."
PENDING_MIGRATIONS=$(python manage.py showmigrations --plan 2>/dev/null | grep "\[ \]" | wc -l)
if [ $PENDING_MIGRATIONS -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found ${PENDING_MIGRATIONS} pending migrations${NC}"
    read -p "Apply migrations now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python manage.py migrate
    fi
else
    echo -e "${GREEN}✓${NC} Database migrations up to date"
fi

# Start server
echo -e "\n${YELLOW}[5/5]${NC} Starting development server..."
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${WHITE}  🚀 SMS Extractor Started!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}  📱 Access URLs:${NC}"
echo -e "     ${WHITE}Home:${NC}          http://127.0.0.1:8000/"
echo -e "     ${WHITE}Paper Library:${NC} http://127.0.0.1:8000/papers/"
echo -e "     ${WHITE}AI Assistant:${NC}  http://127.0.0.1:8000/agents/chat/"
echo -e "     ${WHITE}Admin Panel:${NC}   http://127.0.0.1:8000/admin/"
echo ""
echo -e "${CYAN}  🔑 Admin Account:${NC}"
echo -e "     ${WHITE}Username:${NC} admin"
echo -e "     ${WHITE}Password:${NC} admin123"
echo ""
echo -e "${CYAN}  💡 Shortcuts:${NC}"
echo -e "     ${WHITE}Ctrl+C${NC}    - Stop server"
echo -e "     ${WHITE}Ctrl+Z${NC}    - Run in background"
echo ""
echo -e "${YELLOW}  ⚠️  WARNING: This is a development server. DO NOT use in production.${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start server
python manage.py runserver

# After server stopped
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${WHITE}  👋 Thank you for using SMS Extractor!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
