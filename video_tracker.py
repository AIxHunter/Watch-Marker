import sqlite3
import os
from pathlib import Path
from typing import List, Tuple, Optional

class VideoTracker:
    """Handles database operations for tracking video progress"""
    
    def __init__(self, db_path: str = None):
        # Use environment variable or default path
        if db_path is None:
            db_path = os.getenv('DB_PATH', 'video_progress.db')
        
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                last_position INTEGER NOT NULL,
                duration INTEGER,
                last_watched TEXT DEFAULT CURRENT_TIMESTAMP,
                watch_count INTEGER DEFAULT 1,
                remarks TEXT
            )
        """)
        
        # Migrate existing database: add remarks column if it doesn't exist
        cursor.execute("PRAGMA table_info(video_progress)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'remarks' not in columns:
            cursor.execute("ALTER TABLE video_progress ADD COLUMN remarks TEXT")
        
        conn.commit()
        conn.close()
    
    def save_progress(self, file_path: str, position: int, duration: int = None):
        """Save or update video progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO video_progress (file_path, last_position, duration, watch_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(file_path) DO UPDATE SET
                last_position = ?,
                duration = COALESCE(?, duration),
                last_watched = CURRENT_TIMESTAMP,
                watch_count = watch_count + 1
        """, (file_path, position, duration, position, duration))
        
        conn.commit()
        conn.close()
    
    def get_progress(self, file_path: str) -> Optional[Tuple[int, int, str]]:
        """Get saved progress for a video (position, duration, remarks)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT last_position, duration, remarks FROM video_progress
            WHERE file_path = ?
        """, (file_path,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result if result else None
    
    def get_all_videos_with_progress(self) -> List[Tuple[str, int, int, str]]:
        """Get all videos with their progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path, last_position, duration, last_watched
            FROM video_progress
            ORDER BY last_watched DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def clear_completed_videos(self, threshold: float = 0.95):
        """Remove videos that are 95% or more completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM video_progress
            WHERE duration IS NOT NULL 
            AND last_position >= duration * ?
        """, (threshold,))
        
        conn.commit()
        conn.close()
    
    def delete_progress(self, file_path: str):
        """Delete progress for a specific video"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM video_progress WHERE file_path = ?", (file_path,))
        
        conn.commit()
        conn.close()
    
    def save_last_folder(self, folder_path: str):
        """Save the last opened folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create settings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO settings (key, value)
            VALUES ('last_folder', ?)
            ON CONFLICT(key) DO UPDATE SET
                value = ?,
                updated_at = CURRENT_TIMESTAMP
        """, (folder_path, folder_path))
        
        conn.commit()
        conn.close()
    
    def get_last_folder(self) -> Optional[str]:
        """Get the last opened folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create settings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("SELECT value FROM settings WHERE key = 'last_folder'")
        result = cursor.fetchone()
        
        conn.close()
        
        if result and os.path.exists(result[0]):
            return result[0]
        return None
    
    def add_folder_to_history(self, folder_path: str):
        """Add folder to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create folder_history table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folder_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT UNIQUE NOT NULL,
                folder_name TEXT NOT NULL,
                last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1
            )
        """)
        
        folder_name = os.path.basename(folder_path)
        
        cursor.execute("""
            INSERT INTO folder_history (folder_path, folder_name)
            VALUES (?, ?)
            ON CONFLICT(folder_path) DO UPDATE SET
                last_accessed = CURRENT_TIMESTAMP,
                access_count = access_count + 1
        """, (folder_path, folder_name))
        
        conn.commit()
        conn.close()
    
    def get_folder_history(self, limit: int = 20):
        """Get folder history, ordered by last accessed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folder_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT UNIQUE NOT NULL,
                folder_name TEXT NOT NULL,
                last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            SELECT folder_path, folder_name, last_accessed, access_count
            FROM folder_history
            WHERE folder_path IS NOT NULL
            ORDER BY last_accessed DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        # Filter out folders that no longer exist
        valid_results = []
        for result in results:
            if os.path.exists(result[0]):
                valid_results.append({
                    'path': result[0],
                    'name': result[1],
                    'last_accessed': result[2],
                    'access_count': result[3]
                })
        
        return valid_results
    
    def remove_folder_from_history(self, folder_path: str):
        """Remove folder from history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM folder_history WHERE folder_path = ?", (folder_path,))
        
        conn.commit()
        conn.close()
    
    def save_remark(self, file_path: str, remark: str):
        """Save or update a remark for a video"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO video_progress (file_path, last_position, remarks)
            VALUES (?, 0, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                remarks = ?
        """, (file_path, remark, remark))
        
        conn.commit()
        conn.close()
    
    def get_remark(self, file_path: str) -> Optional[str]:
        """Get remark for a video"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT remarks FROM video_progress WHERE file_path = ?", (file_path,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result and result[0] else None

def find_videos(root_folder: str, extensions: tuple = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')) -> List[str]:
    """Recursively find all video files in a folder"""
    video_files = []
    
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(extensions):
                video_files.append(os.path.join(root, file))
    
    return sorted(video_files)

