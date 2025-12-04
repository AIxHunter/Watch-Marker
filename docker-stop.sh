#!/bin/bash

# Determine which docker compose command to use
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

echo "Stopping Watch Marker..."
$DOCKER_COMPOSE stop

echo ""
echo "✓ Watch Marker stopped"
echo ""
echo "To start again: ./docker-run.sh"
echo "To remove completely: $DOCKER_COMPOSE down"

