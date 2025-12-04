let videos = [];
let currentVideoIndex = -1;
let currentVideoPath = null;
let selectedFolder = null;
let progressSaveInterval = null;

const videoPlayer = document.getElementById('video-player');
const noVideoDisplay = document.getElementById('no-video');
const videoTitle = document.getElementById('video-title');
const progressFill = document.getElementById('progress-fill');
const currentTimeDisplay = document.getElementById('current-time');
const durationDisplay = document.getElementById('duration');
const playPauseBtn = document.getElementById('play-pause-btn');
const volumeBtn = document.getElementById('volume-btn');
const volumeSlider = document.getElementById('volume-slider');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupVideoListeners();
    loadFolderHistory();
    loadLastFolder();
});

function setupVideoListeners() {
    // Time update
    videoPlayer.addEventListener('timeupdate', () => {
        if (videoPlayer.duration) {
            const progress = (videoPlayer.currentTime / videoPlayer.duration) * 100;
            progressFill.style.width = progress + '%';
            currentTimeDisplay.textContent = formatTime(videoPlayer.currentTime);
            durationDisplay.textContent = formatTime(videoPlayer.duration);
        }
    });

    // Play/Pause button update
    videoPlayer.addEventListener('play', () => {
        playPauseBtn.textContent = '⏸️';
    });

    videoPlayer.addEventListener('pause', () => {
        playPauseBtn.textContent = '▶️';
    });

    // Video ended - play next
    videoPlayer.addEventListener('ended', () => {
        nextVideo();
    });

    // Progress bar click
    document.querySelector('.progress-bar').addEventListener('click', (e) => {
        const rect = e.target.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        videoPlayer.currentTime = percent * videoPlayer.duration;
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Don't capture keyboard shortcuts when typing in input fields or textarea
        if (e.target.tagName === 'INPUT' || 
            e.target.tagName === 'SELECT' || 
            e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        switch(e.key) {
            case ' ':
                e.preventDefault();
                togglePlay();
                break;
            case 'ArrowLeft':
                videoPlayer.currentTime -= 5;
                break;
            case 'ArrowRight':
                videoPlayer.currentTime += 5;
                break;
            case 'ArrowUp':
                e.preventDefault();
                nextVideo();
                break;
            case 'ArrowDown':
                e.preventDefault();
                previousVideo();
                break;
        }
    });
}

async function loadFolderHistory() {
    try {
        const response = await fetch('/api/folder-history');
        const data = await response.json();
        
        renderFolderHistory(data.folders);
    } catch (error) {
        console.error('Error loading folder history:', error);
    }
}

function renderFolderHistory(folders) {
    const historyContainer = document.getElementById('folder-history');
    historyContainer.innerHTML = '';
    
    if (!folders || folders.length === 0) {
        historyContainer.innerHTML = '<p class="empty-state">No folders yet</p>';
        return;
    }
    
    folders.forEach(folder => {
        const div = document.createElement('div');
        div.className = 'folder-history-item';
        if (selectedFolder === folder.path) {
            div.classList.add('active');
        }
        
        const name = document.createElement('div');
        name.className = 'folder-history-name';
        name.textContent = folder.name;
        name.title = folder.path; // Show full path on hover
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'folder-remove-btn';
        removeBtn.textContent = '×';
        removeBtn.title = 'Remove from history';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            removeFolderFromHistory(folder.path);
        };
        
        div.appendChild(name);
        div.appendChild(removeBtn);
        
        div.onclick = () => loadFolderFromHistory(folder.path);
        
        historyContainer.appendChild(div);
    });
}

async function loadFolderFromHistory(folderPath) {
    try {
        const response = await fetch('/api/select-folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ folder_path: folderPath })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        
        videos = data.videos;
        selectedFolder = folderPath;
        document.getElementById('folder-name').textContent = `Folder: ${data.folder_name}`;
        document.getElementById('video-count').textContent = `(${data.count})`;
        
        renderVideoList();
        loadFolderHistory(); // Refresh history to update active state
        
    } catch (error) {
        console.error('Error loading folder:', error);
        alert('Error loading folder: ' + error.message);
    }
}

async function removeFolderFromHistory(folderPath) {
    if (!confirm('Remove this folder from history?')) {
        return;
    }
    
    try {
        const encodedPath = folderPath.substring(1); // Remove leading /
        await fetch(`/api/folder-history/${encodedPath}`, {
            method: 'DELETE'
        });
        
        loadFolderHistory();
    } catch (error) {
        console.error('Error removing folder:', error);
    }
}

async function loadLastFolder() {
    try {
        const response = await fetch('/api/last-folder');
        const data = await response.json();
        
        if (data.folder && data.videos) {
            videos = data.videos;
            selectedFolder = data.folder;
            document.getElementById('folder-name').textContent = `Folder: ${data.folder_name}`;
            document.getElementById('video-count').textContent = `(${data.count})`;
            renderVideoList();
            loadFolderHistory(); // Refresh history to update active state
            console.log('Loaded last folder:', data.folder_name);
        }
    } catch (error) {
        console.log('No previous folder found or error loading:', error);
    }
}

function showFolderBrowser() {
    const modal = document.getElementById('folder-modal');
    modal.classList.add('active');
    
    // Start browsing from last folder or home
    const startPath = selectedFolder || '/home';
    browsePath(startPath);
}

function closeFolderBrowser() {
    const modal = document.getElementById('folder-modal');
    modal.classList.remove('active');
}

async function browsePath(path) {
    try {
        const response = await fetch(`/api/browse?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        document.getElementById('current-path').textContent = data.current_path;
        selectedFolder = data.current_path;
        
        const folderList = document.getElementById('folder-list');
        folderList.innerHTML = '';
        
        data.items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'folder-item';
            div.onclick = () => browsePath(item.path);
            
            const icon = document.createElement('span');
            icon.className = 'folder-icon';
            icon.textContent = item.is_parent ? '⬆️' : '📁';
            
            const name = document.createElement('span');
            name.textContent = item.name;
            
            div.appendChild(icon);
            div.appendChild(name);
            folderList.appendChild(div);
        });
        
    } catch (error) {
        console.error('Error browsing folder:', error);
        alert('Error browsing folder: ' + error.message);
    }
}

async function confirmFolder() {
    if (!selectedFolder) return;
    
    closeFolderBrowser();
    
    try {
        const response = await fetch('/api/select-folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ folder_path: selectedFolder })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        
        videos = data.videos;
        document.getElementById('folder-name').textContent = `Folder: ${data.folder_name}`;
        document.getElementById('video-count').textContent = `(${data.count})`;
        
        renderVideoList();
        loadFolderHistory(); // Refresh folder history
        
    } catch (error) {
        console.error('Error selecting folder:', error);
        alert('Error selecting folder: ' + error.message);
    }
}

function renderVideoList() {
    const videoList = document.getElementById('video-list');
    videoList.innerHTML = '';
    
    if (videos.length === 0) {
        videoList.innerHTML = '<p class="empty-state">No videos found in this folder</p>';
        return;
    }
    
    videos.forEach((video, index) => {
        const div = document.createElement('div');
        div.className = 'video-item';
        if (index === currentVideoIndex) {
            div.classList.add('active');
        }
        div.onclick = () => loadVideoByIndex(index);
        
        const title = document.createElement('div');
        title.className = 'video-item-title';
        title.textContent = video.display_name;
        
        div.appendChild(title);
        
        // Always show progress info
        const progressDiv = document.createElement('div');
        progressDiv.className = 'video-item-progress';
        
        const miniBar = document.createElement('div');
        miniBar.className = 'mini-progress';
        const miniFill = document.createElement('div');
        miniFill.className = 'mini-progress-fill';
        
        let percentText = document.createElement('span');
        
        if (video.progress && video.progress.percent > 0) {
            // Has progress
            miniFill.style.width = video.progress.percent + '%';
            
            if (video.progress.percent >= 95) {
                percentText.textContent = '✓ Done';
                percentText.className = 'progress-completed';
                miniFill.style.background = '#10b981'; // Green
            } else {
                percentText.textContent = Math.round(video.progress.percent) + '%';
            }
        } else {
            // Not started
            miniFill.style.width = '0%';
            percentText.textContent = '○ New';
            percentText.className = 'progress-new';
        }
        
        miniBar.appendChild(miniFill);
        progressDiv.appendChild(miniBar);
        progressDiv.appendChild(percentText);
        div.appendChild(progressDiv);
        
        videoList.appendChild(div);
    });
}

async function loadVideoByIndex(index) {
    if (index < 0 || index >= videos.length) return;
    
    currentVideoIndex = index;
    const video = videos[index];
    currentVideoPath = video.path;
    
    // Update UI
    videoTitle.textContent = video.filename;
    noVideoDisplay.classList.add('hidden');
    
    // Update remarks field
    updateRemarksField(video);
    
    // Set video source
    videoPlayer.src = `/api/video${video.path}`;
    
    // Check for saved progress
    try {
        const response = await fetch(`/api/progress?video_path=${encodeURIComponent(video.path)}`);
        const data = await response.json();
        
        if (data.position > 0 && data.duration) {
            const percent = (data.position / data.duration) * 100;
            if (percent < 95) {
                videoPlayer.addEventListener('loadedmetadata', function resumePlayback() {
                    videoPlayer.currentTime = data.position / 1000;
                    videoPlayer.removeEventListener('loadedmetadata', resumePlayback);
                });
            }
        }
    } catch (error) {
        console.error('Error loading progress:', error);
    }
    
    // Play video
    videoPlayer.play();
    
    // Update list
    renderVideoList();
    
    // Start auto-save progress
    startProgressTracking();
}

function updateRemarksField(video) {
    const remarksContainer = document.getElementById('video-remarks');
    remarksContainer.innerHTML = '';
    
    const label = document.createElement('label');
    label.textContent = '📝 Notes:';
    label.className = 'remarks-label';
    
    const textarea = document.createElement('textarea');
    textarea.className = 'remarks-textarea';
    textarea.placeholder = 'Add your notes about this video here...';
    textarea.value = video.remarks || '';
    textarea.rows = 3;
    
    const saveIndicator = document.createElement('span');
    saveIndicator.className = 'remarks-save-indicator';
    saveIndicator.style.opacity = '0';
    
    // Save remark on change
    let saveTimeout;
    textarea.addEventListener('input', (e) => {
        clearTimeout(saveTimeout);
        saveIndicator.textContent = '💾 Saving...';
        saveIndicator.style.opacity = '1';
        
        saveTimeout = setTimeout(async () => {
            await saveRemark(video.path, e.target.value, currentVideoIndex);
            saveIndicator.textContent = '✓ Saved';
            setTimeout(() => {
                saveIndicator.style.opacity = '0';
            }, 2000);
        }, 1000);
    });
    
    remarksContainer.appendChild(label);
    remarksContainer.appendChild(textarea);
    remarksContainer.appendChild(saveIndicator);
}

async function saveRemark(videoPath, remark, videoIndex) {
    try {
        await fetch('/api/remarks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_path: videoPath,
                remark: remark
            })
        });
        
        // Update local video data
        if (videos[videoIndex]) {
            videos[videoIndex].remarks = remark;
        }
    } catch (error) {
        console.error('Error saving remark:', error);
    }
}

function startProgressTracking() {
    // Clear existing interval
    if (progressSaveInterval) {
        clearInterval(progressSaveInterval);
    }
    
    // Save progress every 5 seconds
    progressSaveInterval = setInterval(() => {
        if (currentVideoPath && videoPlayer.currentTime > 0) {
            saveProgress();
        }
    }, 5000);
}

async function saveProgress() {
    if (!currentVideoPath) return;
    
    try {
        await fetch('/api/progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_path: currentVideoPath,
                position: Math.floor(videoPlayer.currentTime * 1000),
                duration: Math.floor(videoPlayer.duration * 1000)
            })
        });
    } catch (error) {
        console.error('Error saving progress:', error);
    }
}

function togglePlay() {
    if (videoPlayer.paused) {
        videoPlayer.play();
    } else {
        videoPlayer.pause();
    }
}

function previousVideo() {
    if (currentVideoIndex > 0) {
        loadVideoByIndex(currentVideoIndex - 1);
    }
}

function nextVideo() {
    if (currentVideoIndex < videos.length - 1) {
        loadVideoByIndex(currentVideoIndex + 1);
    }
}

function changeSpeed() {
    const speed = document.getElementById('speed-select').value;
    videoPlayer.playbackRate = parseFloat(speed);
}

function toggleMute() {
    videoPlayer.muted = !videoPlayer.muted;
    volumeBtn.textContent = videoPlayer.muted ? '🔇' : '🔊';
}

function changeVolume() {
    videoPlayer.volume = volumeSlider.value / 100;
    if (videoPlayer.volume === 0) {
        volumeBtn.textContent = '🔇';
    } else {
        volumeBtn.textContent = '🔊';
        videoPlayer.muted = false;
    }
}

async function refreshVideos() {
    if (!selectedFolder) {
        alert('Please select a folder first');
        return;
    }
    
    try {
        const response = await fetch('/api/videos');
        const data = await response.json();
        
        videos = data.videos;
        renderVideoList();
        
    } catch (error) {
        console.error('Error refreshing videos:', error);
        alert('Error refreshing videos: ' + error.message);
    }
}

async function clearCompleted() {
    if (!confirm('Remove all videos that are 95% or more completed from tracking?')) {
        return;
    }
    
    try {
        await fetch('/api/clear-completed', { method: 'POST' });
        refreshVideos();
        alert('Completed videos cleared');
    } catch (error) {
        console.error('Error clearing completed:', error);
        alert('Error clearing completed videos: ' + error.message);
    }
}

function formatTime(seconds) {
    if (isNaN(seconds)) return '00:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Save progress when leaving page
window.addEventListener('beforeunload', () => {
    if (currentVideoPath && videoPlayer.currentTime > 0) {
        saveProgress();
    }
});

