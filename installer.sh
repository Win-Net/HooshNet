#!/bin/bash

# Professional VPN Bot Installer Wrapper
# This script delegates the installation to the new manager.sh script

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Clear screen
clear

echo -e "${GREEN}=================================================================${NC}"
echo -e "${GREEN}       Professional VPN Bot Installer (Docker Edition)           ${NC}"
echo -e "${GREEN}=================================================================${NC}"
echo ""
echo -e "${YELLOW}Redirecting to the new Manager Script...${NC}"
echo ""

# Ensure manager.sh is executable
chmod +x manager.sh

# Run the manager in install mode
./manager.sh install
