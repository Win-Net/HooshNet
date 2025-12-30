#!/bin/bash
# Docker Restart Script for VPN Bot
# Use this script to rebuild and restart the Docker containers

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}    VPN Bot Docker Restart Script${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed!${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed!${NC}"
    exit 1
fi

# Use docker compose if available, otherwise docker-compose
COMPOSE_CMD="docker-compose"
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

# Stop containers
echo -e "${YELLOW}Stopping containers...${NC}"
$COMPOSE_CMD down || true

# Remove old images
echo -e "${YELLOW}Removing old images...${NC}"
docker image prune -f || true

# Build and start
echo -e "${GREEN}Building and starting containers...${NC}"
$COMPOSE_CMD up --build -d

# Wait for services to start
echo -e "${YELLOW}Waiting for services to initialize...${NC}"
sleep 10

# Check status
echo -e "${BLUE}Container Status:${NC}"
$COMPOSE_CMD ps

# Check logs
echo -e "${BLUE}Recent logs:${NC}"
$COMPOSE_CMD logs --tail=50

echo -e ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}    Restart Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e ""
echo -e "Useful commands:"
echo -e "  ${BLUE}$COMPOSE_CMD logs -f${NC}          - View live logs"
echo -e "  ${BLUE}$COMPOSE_CMD logs vpn-bot${NC}     - View vpn-bot logs"
echo -e "  ${BLUE}$COMPOSE_CMD exec vpn-bot bash${NC} - Open shell in container"
echo -e "  ${BLUE}$COMPOSE_CMD restart${NC}          - Restart containers"
echo -e ""
echo -e "Debug commands:"
echo -e "  ${BLUE}$COMPOSE_CMD exec vpn-bot python3 debug_webapp.py${NC} - Run debug tool"
echo -e ""
