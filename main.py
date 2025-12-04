#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import vlc
import os
import threading
import time
from pathlib import Path
from video_tracker import VideoTracker, find_videos

class VideoPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Watch Marker - Video Progress Tracker")
        self.root.geometry("1200x700")
        
        self.tracker = VideoTracker()
        self.player = None
        self.current_video = None
        self.video_list = []
        self.is_playing = False
        self.progress_update_thread = None
        self.should_update = False
        self.selected_folder = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Top controls
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(control_frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        self.folder_label = ttk.Label(control_frame, text="No folder selected", foreground="gray")
        self.folder_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(control_frame, text="Refresh", command=self.refresh_videos).pack(side=tk.RIGHT, padx=5)
        ttk.Button(control_frame, text="Clear Completed", command=self.clear_completed).pack(side=tk.RIGHT, padx=5)
        
        # Left panel - Video list
        list_frame = ttk.LabelFrame(main_frame, text="Videos", padding="5")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Scrollbar for video list
        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_listbox = tk.Listbox(list_frame, yscrollcommand=list_scroll.set, width=40)
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.video_listbox.bind('<<ListboxSelect>>', self.on_video_select)
        list_scroll.config(command=self.video_listbox.yview)
        
        # Right panel - Video player
        player_frame = ttk.LabelFrame(main_frame, text="Player", padding="5")
        player_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        player_frame.columnconfigure(0, weight=1)
        player_frame.rowconfigure(0, weight=1)
        
        # Video display
        self.video_panel = tk.Frame(player_frame, bg="black", width=800, height=450)
        self.video_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.video_panel.columnconfigure(0, weight=1)
        self.video_panel.rowconfigure(0, weight=1)
        
        # Video info label
        self.info_label = ttk.Label(player_frame, text="No video loaded", foreground="gray")
        self.info_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(player_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                       variable=self.progress_var, command=self.on_progress_drag)
        self.progress_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Time labels
        time_frame = ttk.Frame(player_frame)
        time_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        time_frame.columnconfigure(1, weight=1)
        
        self.time_label = ttk.Label(time_frame, text="00:00 / 00:00")
        self.time_label.grid(row=0, column=0, sticky=tk.W)
        
        # Playback controls
        controls = ttk.Frame(player_frame)
        controls.grid(row=4, column=0, pady=10)
        
        ttk.Button(controls, text="⏮ Previous", command=self.previous_video).pack(side=tk.LEFT, padx=5)
        self.play_button = ttk.Button(controls, text="▶ Play", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="⏹ Stop", command=self.stop_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="⏭ Next", command=self.next_video).pack(side=tk.LEFT, padx=5)
        
        # Speed control
        speed_frame = ttk.Frame(player_frame)
        speed_frame.grid(row=5, column=0, pady=5)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_slider = ttk.Scale(speed_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL,
                                 variable=self.speed_var, command=self.change_speed)
        speed_slider.pack(side=tk.LEFT, padx=5)
        self.speed_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: self.toggle_play())
        self.root.bind('<Left>', lambda e: self.seek_relative(-5000))
        self.root.bind('<Right>', lambda e: self.seek_relative(5000))
        self.root.bind('<Up>', lambda e: self.next_video())
        self.root.bind('<Down>', lambda e: self.previous_video())
        
    def select_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(title="Select Video Folder")
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=f"Folder: {os.path.basename(folder)}", foreground="black")
            self.load_videos(folder)
    
    def load_videos(self, folder):
        """Load all videos from the selected folder"""
        self.video_list = find_videos(folder)
        self.update_video_list()
        
        if self.video_list:
            messagebox.showinfo("Videos Found", f"Found {len(self.video_list)} video(s)")
        else:
            messagebox.showwarning("No Videos", "No video files found in the selected folder")
    
    def update_video_list(self):
        """Update the video listbox"""
        self.video_listbox.delete(0, tk.END)
        
        for video_path in self.video_list:
            # Get relative path for display
            if self.selected_folder:
                display_name = os.path.relpath(video_path, self.selected_folder)
            else:
                display_name = os.path.basename(video_path)
            
            # Check if video has progress
            progress = self.tracker.get_progress(video_path)
            if progress and progress[1]:  # Has duration
                percent = (progress[0] / progress[1]) * 100
                display_name = f"[{percent:.0f}%] {display_name}"
            
            self.video_listbox.insert(tk.END, display_name)
    
    def on_video_select(self, event):
        """Handle video selection from list"""
        selection = self.video_listbox.curselection()
        if selection:
            index = selection[0]
            video_path = self.video_list[index]
            self.load_video(video_path)
    
    def load_video(self, video_path):
        """Load and play a video"""
        if not os.path.exists(video_path):
            messagebox.showerror("Error", "Video file not found")
            return
        
        # Stop current video if playing
        if self.player:
            self.stop_video()
        
        self.current_video = video_path
        
        # Create VLC instance and player
        instance = vlc.Instance()
        self.player = instance.media_player_new()
        
        # Set video output to the panel
        if os.name == 'nt':  # Windows
            self.player.set_hwnd(self.video_panel.winfo_id())
        else:  # Linux/Mac
            self.player.set_xwindow(self.video_panel.winfo_id())
        
        # Load media
        media = instance.media_new(video_path)
        self.player.set_media(media)
        
        # Update info
        filename = os.path.basename(video_path)
        self.info_label.config(text=f"Playing: {filename}", foreground="black")
        
        # Start playing
        self.player.play()
        self.is_playing = True
        self.play_button.config(text="⏸ Pause")
        
        # Wait for video to load
        time.sleep(0.5)
        
        # Check for saved progress and resume
        progress = self.tracker.get_progress(video_path)
        if progress and progress[0] > 0:
            position_ms = progress[0]
            duration_ms = progress[1] if progress[1] else self.player.get_length()
            
            # Only resume if not near the end (more than 5% remaining)
            if duration_ms and position_ms < duration_ms * 0.95:
                response = messagebox.askyesno("Resume", 
                    f"Resume from {self.format_time(position_ms)}?")
                if response:
                    self.player.set_time(position_ms)
        
        # Start progress update thread
        self.should_update = True
        self.progress_update_thread = threading.Thread(target=self.update_progress, daemon=True)
        self.progress_update_thread.start()
    
    def toggle_play(self):
        """Toggle play/pause"""
        if not self.player:
            return
        
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            self.play_button.config(text="▶ Play")
        else:
            self.player.play()
            self.is_playing = True
            self.play_button.config(text="⏸ Pause")
    
    def stop_video(self):
        """Stop the current video"""
        if self.player:
            # Save progress before stopping
            if self.current_video:
                position = self.player.get_time()
                duration = self.player.get_length()
                if position > 0:
                    self.tracker.save_progress(self.current_video, position, duration)
            
            self.should_update = False
            self.player.stop()
            self.is_playing = False
            self.play_button.config(text="▶ Play")
            self.progress_var.set(0)
            self.time_label.config(text="00:00 / 00:00")
    
    def next_video(self):
        """Play the next video in the list"""
        if not self.current_video or not self.video_list:
            return
        
        try:
            current_index = self.video_list.index(self.current_video)
            if current_index < len(self.video_list) - 1:
                next_video = self.video_list[current_index + 1]
                self.video_listbox.selection_clear(0, tk.END)
                self.video_listbox.selection_set(current_index + 1)
                self.video_listbox.see(current_index + 1)
                self.load_video(next_video)
        except ValueError:
            pass
    
    def previous_video(self):
        """Play the previous video in the list"""
        if not self.current_video or not self.video_list:
            return
        
        try:
            current_index = self.video_list.index(self.current_video)
            if current_index > 0:
                prev_video = self.video_list[current_index - 1]
                self.video_listbox.selection_clear(0, tk.END)
                self.video_listbox.selection_set(current_index - 1)
                self.video_listbox.see(current_index - 1)
                self.load_video(prev_video)
        except ValueError:
            pass
    
    def seek_relative(self, ms):
        """Seek relative to current position"""
        if self.player:
            current = self.player.get_time()
            new_time = max(0, current + ms)
            self.player.set_time(int(new_time))
    
    def on_progress_drag(self, value):
        """Handle progress bar dragging"""
        if self.player and self.player.get_length() > 0:
            duration = self.player.get_length()
            new_time = int((float(value) / 100) * duration)
            self.player.set_time(new_time)
    
    def change_speed(self, value):
        """Change playback speed"""
        speed = float(value)
        self.speed_label.config(text=f"{speed:.1f}x")
        if self.player:
            self.player.set_rate(speed)
    
    def update_progress(self):
        """Update progress bar and save progress periodically"""
        last_save = 0
        
        while self.should_update:
            if self.player and self.player.get_length() > 0:
                current_time = self.player.get_time()
                duration = self.player.get_length()
                
                # Update progress bar
                progress = (current_time / duration) * 100
                self.progress_var.set(progress)
                
                # Update time label
                self.time_label.config(
                    text=f"{self.format_time(current_time)} / {self.format_time(duration)}"
                )
                
                # Save progress every 5 seconds
                if time.time() - last_save > 5:
                    self.tracker.save_progress(self.current_video, current_time, duration)
                    last_save = time.time()
                
                # Check if video ended
                if current_time >= duration - 1000 and self.is_playing:
                    self.root.after(0, self.next_video)
            
            time.sleep(0.1)
    
    def refresh_videos(self):
        """Refresh the video list"""
        if self.selected_folder:
            self.load_videos(self.selected_folder)
        else:
            messagebox.showinfo("Info", "Please select a folder first")
    
    def clear_completed(self):
        """Clear completed videos from tracking"""
        response = messagebox.askyesno("Clear Completed", 
            "Remove all videos that are 95% or more completed?")
        if response:
            self.tracker.clear_completed_videos()
            self.update_video_list()
            messagebox.showinfo("Success", "Completed videos cleared")
    
    def format_time(self, ms):
        """Format milliseconds to MM:SS"""
        seconds = int(ms / 1000)
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
    
    def on_close(self):
        """Handle window close"""
        if self.player:
            self.stop_video()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = VideoPlayerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()

