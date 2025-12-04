#!/bin/bash

echo "======================================"
echo "Watch Marker - Docker Setup"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker found"

# Determine which docker compose command to use
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "✓ Docker Compose (v1) found"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
    echo "✓ Docker Compose (v2) found"
else
    echo "❌ Docker Compose is not installed."
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""

# Create data directory if it doesn't exist
mkdir -p data

echo "Building Docker image..."
$DOCKER_COMPOSE build

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Build complete!"
    echo ""
    echo "Starting Watch Marker..."
    echo ""
    $DOCKER_COMPOSE up -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Watch Marker is running!"
        echo ""
        echo "🌐 Access the app at: http://localhost:5000"
        echo ""
        echo "Useful commands:"
        echo "  Stop:     $DOCKER_COMPOSE stop"
        echo "  Restart:  $DOCKER_COMPOSE restart"
        echo "  Logs:     $DOCKER_COMPOSE logs -f"
        echo "  Remove:   $DOCKER_COMPOSE down"
        echo ""
    else
        echo ""
        echo "❌ Failed to start container"
        exit 1
    fi
else
    echo ""
    echo "❌ Build failed"
    exit 1
fi

