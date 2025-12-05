# Watch Marker - Video Progress Tracker

A web-based application that helps you track your progress while watching tutorial videos or TV shows downloaded locally in your PC. It automatically remembers where you left off in each video and lets you resume from that point.

## 🚀 Quick Start (Docker)

```bash
./docker-run.sh
```

Then open: **http://localhost:5000**

## 🌐 Web UI (Recommended)

The app features a modern **web-based interface** that runs in your browser!

## Features

- 📁 **Folder Browser**: Select any folder containing videos (supports nested subfolders)
- ▶️ **Video Player**: Built-in video player with playback controls
- 💾 **Auto-Save Progress**: Automatically saves your position every 5 seconds
- 🔄 **Resume Playback**: Asks if you want to resume from where you left off
- 📊 **Progress Tracking**: Shows completion percentage for each video
- ⏭️ **Navigation**: Easy navigation between videos with Next/Previous buttons
- ⌨️ **Keyboard Shortcuts**: Control playback with keyboard
- 🎚️ **Playback Speed**: Adjust playback speed from 0.5x to 2.0x
- 🗑️ **Clear Completed**: Remove videos that are 95%+ complete from tracking

## Supported Video Formats

- MP4
- AVI
- MKV
- MOV
- WMV
- FLV
- WEBM

## Installation

### Prerequisites

**Python 3.8 or higher**

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or:

```bash
pip install Flask
```

## Usage

### 🐳 Option 1: Run with Docker (Easiest)

**Prerequisites:** Docker and Docker Compose

```bash
# Build and start the container
./docker-run.sh

# Or manually:
docker-compose up -d
```

Then open: **http://localhost:5000**

**Docker Commands:**
```bash
# Stop the container
./docker-stop.sh
# or: docker-compose stop

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Remove container and image
docker-compose down
docker-compose down --rmi all
```

**Important:** Edit `docker-compose.yml` to mount your video folders:
```yaml
volumes:
  - /path/to/your/videos:/path/to/your/videos:ro
  - /home/user:/home/user:ro
```

### 🌐 Option 2: Run Directly (Python)

```bash
./run_web.sh
```

Or:

```bash
python3 app.py
```

Then open your browser and go to: **http://localhost:5000**

### 🖥️ Option 3: Desktop Application (Alternative)

If you prefer a desktop GUI (requires VLC):

```bash
python3 main.py
```

### How to Use

1. **Select Folder**: Click "Select Folder" and choose the directory containing your videos
2. **Choose Video**: Click on any video in the list to load it
3. **Play**: The video will start playing automatically
4. **Resume**: If you've watched the video before, you'll be asked if you want to resume
5. **Navigation**: Use the Previous/Next buttons or keyboard shortcuts to navigate between videos

### Keyboard Shortcuts

- `Space`: Play/Pause
- `Left Arrow`: Rewind 5 seconds
- `Right Arrow`: Forward 5 seconds
- `Up Arrow`: Next video
- `Down Arrow`: Previous video

### Video Progress Display

Videos in the list show their completion percentage:
```
[45%] 01 Introduction/001 Introduction.mp4
[0%] 01 Introduction/002 Data Pipeline.mp4
```

## Database

The application stores progress in a SQLite database (`video_progress.db`) in the same directory as the script. This file is created automatically and contains:

- Video file paths
- Last watched position (in milliseconds)
- Video duration
- Last watched timestamp
- Watch count

## Project Structure

```
Watch-Marker/
├── app.py               # Flask web server (main)
├── main.py              # Desktop GUI application (alternative)
├── video_tracker.py     # Database operations and video scanning
├── templates/
│   └── index.html      # Web UI template
├── static/
│   ├── style.css       # Web UI styles
│   └── app.js          # Web UI JavaScript
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── .dockerignore        # Docker ignore file
├── docker-run.sh        # Docker launcher script
├── docker-stop.sh       # Docker stop script
├── requirements.txt     # Python dependencies
├── run_web.sh          # Web server launcher
├── install.sh          # Installation script
├── README.md           # This file
├── data/               # Docker volume data (created automatically)
└── video_progress.db   # SQLite database (created automatically)
```

## Troubleshooting

### Docker Issues

**Can't find videos in the container:**
- Make sure you mounted your video folders in `docker-compose.yml`
- The paths inside the container must match where your videos are
- Example: `-/home/user/Videos:/home/user/Videos:ro`

**Permission errors in Docker:**
```bash
# Make sure the data directory is writable
chmod -R 777 data/
```

**Container won't start:**
```bash
# Check logs
docker-compose logs

# Rebuild the image
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Port 5000 already in use:**
Edit `docker-compose.yml` and change:
```yaml
ports:
  - "5001:5000"  # Use port 5001 instead
```

### Python/Web Issues

**"No module named 'flask'" error:**
```bash
pip install Flask
```

**Video not playing in browser:**
- Make sure your browser supports HTML5 video
- Try using Chrome or Firefox
- Check browser console for errors (F12)

**Can't access from other devices:**
The server runs on `0.0.0.0` so it's accessible from other devices:
1. Find your local IP: `ip addr` or `ifconfig`
2. Access from other devices: `http://YOUR_IP:5000`
3. Make sure firewall allows port 5000

**Permission denied:**
```bash
chmod +x *.sh
```

### Desktop App Issues

The desktop version requires VLC:
```bash
sudo apt install vlc python3-tk
pip install python-vlc
```

## Tips

- The app auto-saves your position every 5 seconds, so you can close it anytime
- Use "Clear Completed" to remove finished videos from the tracking database
- The app works with any folder structure - videos can be in the root or nested subfolders
- Progress is tracked per file path, so moving videos will reset their progress

## License

MIT License - Feel free to use and modify as needed!

