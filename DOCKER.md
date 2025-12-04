# Docker Setup Guide

This guide will help you run Watch Marker in a Docker container.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

### 1. Configure Video Folders

Edit `docker-compose.yml` and add your video folder paths:

```yaml
volumes:
  # Add your video directories here
  - /home/d4rkc0de:/home/d4rkc0de:ro
  - /mnt/media:/mnt/media:ro
  # The :ro makes it read-only for safety
```

### 2. Build and Run

```bash
./docker-run.sh
```

Or manually:

```bash
docker-compose up -d
```

### 3. Access the App

Open your browser and go to: **http://localhost:5000**

## Docker Commands

### Start the Container
```bash
docker-compose up -d
```

### Stop the Container
```bash
docker-compose stop
# or
./docker-stop.sh
```

### View Logs
```bash
docker-compose logs -f
```

### Restart the Container
```bash
docker-compose restart
```

### Remove the Container
```bash
docker-compose down
```

### Remove Container and Image
```bash
docker-compose down --rmi all
```

### Rebuild the Image
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Volume Configuration

The Docker setup uses volumes for:

1. **Video Files** (read-only): Your video folders
2. **Database** (read-write): Progress tracking database

Example `docker-compose.yml`:

```yaml
volumes:
  # Your video folders (read-only)
  - /home/user/Videos:/home/user/Videos:ro
  - /media/tutorials:/media/tutorials:ro
  
  # Database persistence
  - ./video_progress.db:/app/video_progress.db
  - ./data:/data
```

## Network Access

### Local Access Only
Default configuration - access from `localhost:5000` only.

### Network Access (LAN)
Already configured! Access from any device on your network:
```
http://YOUR_IP_ADDRESS:5000
```

Find your IP:
```bash
ip addr show  # Linux
ifconfig      # Mac/Linux
ipconfig      # Windows
```

### Custom Port
Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

Then access at: `http://localhost:8080`

## Environment Variables

You can customize the container with environment variables in `docker-compose.yml`:

```yaml
environment:
  - FLASK_ENV=production
  - FLASK_DEBUG=0
```

## Data Persistence

The database is stored in:
- `./video_progress.db` (mounted volume)
- `./data/` (backup location)

Even if you remove the container, your progress data remains safe.

## Troubleshooting

### Videos Not Found
Make sure the paths in `docker-compose.yml` match your actual video locations:
```bash
# Check where your videos are
ls -la /path/to/videos

# Add that exact path to docker-compose.yml
volumes:
  - /path/to/videos:/path/to/videos:ro
```

### Permission Denied
```bash
chmod -R 777 data/
```

### Port Already in Use
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Kill that process or use a different port in docker-compose.yml
```

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Check container status
docker-compose ps

# Restart Docker service
sudo systemctl restart docker  # Linux
```

### Out of Disk Space
```bash
# Clean up Docker
docker system prune -a
```

## Security Notes

1. **Read-Only Volumes**: Video folders are mounted as `:ro` (read-only) for safety
2. **Database**: Only the database has write access
3. **Network**: Container runs on isolated network by default
4. **Firewall**: If exposing to internet, use a reverse proxy (nginx) with authentication

## Advanced Configuration

### Custom Dockerfile Build

```bash
docker build -t watch-marker:custom .
```

### Run Without Docker Compose

```bash
docker run -d \
  --name watch-marker \
  -p 5000:5000 \
  -v /home/user/Videos:/home/user/Videos:ro \
  -v ./video_progress.db:/app/video_progress.db \
  watch-marker:latest
```

### Multi-Architecture Build

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t watch-marker:latest .
```

## Production Deployment

For production use, consider:

1. **Use a reverse proxy** (nginx, Traefik)
2. **Add SSL/TLS** (Let's Encrypt)
3. **Add authentication** (Basic Auth, OAuth)
4. **Use environment variables** for secrets
5. **Set up backups** for the database
6. **Monitor logs** and resource usage

Example nginx configuration:
```nginx
server {
    listen 80;
    server_name watch-marker.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Updating

To update to a new version:

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

Your database will be preserved!

