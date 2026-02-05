#!/bin/bash

# ==============================================
# Deployment script for Raspberry Pi
# ==============================================

# Configuration - modify these values
PI_USER="kelly"
PI_HOST="raspberrypi.local"  # or use IP address like "192.168.1.100"
PI_DEST="/home/kelly/development/testing_deployment"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Deploying src to ${PI_USER}@${PI_HOST}:${PI_DEST}"

# Create destination directory if it doesn't exist
ssh "${PI_USER}@${PI_HOST}" "mkdir -p ${PI_DEST}"

# Sync src directory using rsync
rsync -avz --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '.idea' \
    --exclude '*.log' \
    "${SCRIPT_DIR}/src/" \
    "${PI_USER}@${PI_HOST}:${PI_DEST}/src/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment successful!${NC}"
else
    echo -e "${RED}✗ Deployment failed${NC}"
    exit 1
fi

# Optionally sync requirements.txt and .env
rsync -avz "${SCRIPT_DIR}/requirements.txt" "${PI_USER}@${PI_HOST}:${PI_DEST}/"
rsync -avz "${SCRIPT_DIR}/.env" "${PI_USER}@${PI_HOST}:${PI_DEST}/" 2>/dev/null

echo -e "${GREEN}Done!${NC}"
