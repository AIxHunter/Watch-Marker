#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file, session
import os
from pathlib import Path
from video_tracker import VideoTracker, find_videos
import mimetypes

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

tracker = VideoTracker()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/last-folder')
def get_last_folder():
    """Get the last opened folder"""
    last_folder = tracker.get_last_folder()
    
    if last_folder and os.path.exists(last_folder):
        session['selected_folder'] = last_folder
        videos = find_videos(last_folder)
        
        video_list = []
        for video_path in videos:
            progress_data = tracker.get_progress(video_path)
            
            rel_path = os.path.relpath(video_path, last_folder)
            video_info = {
                'path': video_path,
                'display_name': rel_path,
                'filename': os.path.basename(video_path)
            }
            
            if progress_data:
                position = progress_data[0]
                duration = progress_data[1]
                remarks = progress_data[2] if len(progress_data) > 2 else None
                
                if duration:
                    percent = (position / duration) * 100
                    video_info['progress'] = {
                        'position': position,
                        'duration': duration,
                        'percent': round(percent, 1)
                    }
                else:
                    video_info['progress'] = None
                
                video_info['remarks'] = remarks
            else:
                video_info['progress'] = None
                video_info['remarks'] = None
            
            video_list.append(video_info)
        
        return jsonify({
            'folder': last_folder,
            'folder_name': os.path.basename(last_folder),
            'videos': video_list,
            'count': len(video_list)
        })
    
    return jsonify({'folder': None})

@app.route('/api/folder-history')
def get_folder_history():
    """Get folder history"""
    history = tracker.get_folder_history()
    return jsonify({'folders': history})

@app.route('/api/folder-history/<path:folder_path>', methods=['DELETE'])
def delete_folder_from_history(folder_path):
    """Remove folder from history"""
    folder_path = '/' + folder_path
    tracker.remove_folder_from_history(folder_path)
    return jsonify({'success': True})

@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    """Set the selected folder"""
    data = request.get_json()
    folder_path = data.get('folder_path')
    
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({'error': 'Invalid folder path'}), 400
    
    if not os.path.isdir(folder_path):
        return jsonify({'error': 'Path is not a directory'}), 400
    
    # Save as last folder and add to history
    tracker.save_last_folder(folder_path)
    tracker.add_folder_to_history(folder_path)
    
    session['selected_folder'] = folder_path
    videos = find_videos(folder_path)
    
    # Get progress for each video
    video_list = []
    for video_path in videos:
        progress_data = tracker.get_progress(video_path)
        
        rel_path = os.path.relpath(video_path, folder_path)
        video_info = {
            'path': video_path,
            'display_name': rel_path,
            'filename': os.path.basename(video_path)
        }
        
        if progress_data:
            position = progress_data[0]
            duration = progress_data[1]
            remarks = progress_data[2] if len(progress_data) > 2 else None
            
            if duration:
                percent = (position / duration) * 100
                video_info['progress'] = {
                    'position': position,
                    'duration': duration,
                    'percent': round(percent, 1)
                }
            else:
                video_info['progress'] = None
            
            video_info['remarks'] = remarks
        else:
            video_info['progress'] = None
            video_info['remarks'] = None
        
        video_list.append(video_info)
    
    return jsonify({
        'folder': folder_path,
        'folder_name': os.path.basename(folder_path),
        'videos': video_list,
        'count': len(video_list)
    })

@app.route('/api/videos')
def get_videos():
    """Get list of videos from selected folder"""
    folder_path = session.get('selected_folder')
    
    if not folder_path:
        return jsonify({'error': 'No folder selected'}), 400
    
    videos = find_videos(folder_path)
    
    video_list = []
    for video_path in videos:
        progress_data = tracker.get_progress(video_path)
        
        rel_path = os.path.relpath(video_path, folder_path)
        video_info = {
            'path': video_path,
            'display_name': rel_path,
            'filename': os.path.basename(video_path)
        }
        
        if progress_data and progress_data[1]:
            position, duration = progress_data
            percent = (position / duration) * 100
            video_info['progress'] = {
                'position': position,
                'duration': duration,
                'percent': round(percent, 1)
            }
        else:
            video_info['progress'] = None
        
        video_list.append(video_info)
    
    return jsonify({'videos': video_list})

@app.route('/api/video/<path:video_path>')
def stream_video(video_path):
    """Stream video file with range support"""
    video_path = '/' + video_path  # Restore absolute path
    
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video not found'}), 404
    
    # Get file size
    file_size = os.path.getsize(video_path)
    
    # Parse range header
    range_header = request.headers.get('Range', None)
    
    if not range_header:
        return send_file(video_path, mimetype='video/mp4')
    
    # Parse range
    byte_start = 0
    byte_end = file_size - 1
    
    match = range_header.replace('bytes=', '').split('-')
    if match[0]:
        byte_start = int(match[0])
    if match[1]:
        byte_end = int(match[1])
    
    length = byte_end - byte_start + 1
    
    # Read the chunk
    with open(video_path, 'rb') as f:
        f.seek(byte_start)
        chunk = f.read(length)
    
    # Get mime type
    mime_type = mimetypes.guess_type(video_path)[0] or 'video/mp4'
    
    response = app.response_class(
        chunk,
        206,
        mimetype=mime_type,
        direct_passthrough=True
    )
    
    response.headers.add('Content-Range', f'bytes {byte_start}-{byte_end}/{file_size}')
    response.headers.add('Accept-Ranges', 'bytes')
    response.headers.add('Content-Length', str(length))
    
    return response

@app.route('/api/progress', methods=['GET', 'POST'])
def handle_progress():
    """Get or save video progress"""
    if request.method == 'GET':
        video_path = request.args.get('video_path')
        if not video_path:
            return jsonify({'error': 'No video path provided'}), 400
        
        progress = tracker.get_progress(video_path)
        if progress:
            return jsonify({
                'position': progress[0],
                'duration': progress[1],
                'remarks': progress[2] if len(progress) > 2 else None
            })
        return jsonify({'position': 0, 'duration': None, 'remarks': None})
    
    else:  # POST
        data = request.get_json()
        video_path = data.get('video_path')
        position = data.get('position')
        duration = data.get('duration')
        
        if not video_path or position is None:
            return jsonify({'error': 'Invalid data'}), 400
        
        tracker.save_progress(video_path, int(position), int(duration) if duration else None)
        return jsonify({'success': True})

@app.route('/api/remarks', methods=['GET', 'POST'])
def handle_remarks():
    """Get or save video remarks"""
    if request.method == 'GET':
        video_path = request.args.get('video_path')
        if not video_path:
            return jsonify({'error': 'No video path provided'}), 400
        
        remark = tracker.get_remark(video_path)
        return jsonify({'remark': remark})
    
    else:  # POST
        data = request.get_json()
        video_path = data.get('video_path')
        remark = data.get('remark', '')
        
        if not video_path:
            return jsonify({'error': 'No video path provided'}), 400
        
        tracker.save_remark(video_path, remark)
        return jsonify({'success': True})

@app.route('/api/clear-completed', methods=['POST'])
def clear_completed():
    """Clear completed videos"""
    tracker.clear_completed_videos()
    return jsonify({'success': True})

@app.route('/api/browse')
def browse_filesystem():
    """Browse filesystem for folder selection"""
    path = request.args.get('path', str(Path.home()))
    
    if not os.path.exists(path):
        path = str(Path.home())
    
    try:
        items = []
        
        # Add parent directory option
        parent = os.path.dirname(path)
        if parent != path:  # Not at root
            items.append({
                'name': '..',
                'path': parent,
                'is_dir': True,
                'is_parent': True
            })
        
        # List directories
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            
            # Skip hidden files/folders
            if item.startswith('.'):
                continue
            
            if os.path.isdir(item_path):
                items.append({
                    'name': item,
                    'path': item_path,
                    'is_dir': True,
                    'is_parent': False
                })
        
        return jsonify({
            'current_path': path,
            'items': items
        })
    
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

