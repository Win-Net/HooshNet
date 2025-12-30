#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Starting VPN Bot and Web Application...${NC}"

# Start services
sudo systemctl start vpn-bot
sudo systemctl start vpn-webapp

# Wait a moment for services to initialize
sleep 2

# Check status
BOT_STATUS=$(systemctl is-active vpn-bot)
WEB_STATUS=$(systemctl is-active vpn-webapp)

if [ "$BOT_STATUS" == "active" ]; then
    echo -e "Bot Service: ${GREEN}ACTIVE${NC}"
else
    echo -e "Bot Service: ${RED}FAILED${NC} (Status: $BOT_STATUS)"
fi

if [ "$WEB_STATUS" == "active" ]; then
    echo -e "Web Service: ${GREEN}ACTIVE${NC}"
else
    echo -e "Web Service: ${RED}FAILED${NC} (Status: $WEB_STATUS)"
fi

echo -e ""
echo -e "Check full logs with: ${BLUE}journalctl -u vpn-bot -f${NC} or ${BLUE}journalctl -u vpn-webapp -f${NC}"
