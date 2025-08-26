import customtkinter as ctk
from tkinter import filedialog


# --- Tool Frame Example ---

# --- Generic Tool Frame ---


class ToolFrame(ctk.CTkFrame):
    def __init__(self, master, tool_name):
        super().__init__(master)
        self.tool_name = tool_name
        self.pack(fill="both", expand=True)
        label = ctk.CTkLabel(self, text=f"{tool_name} Tool", font=("Arial", 18))
        label.pack(pady=10)

        # Tabs for main/advanced options
        self.tabview = ctk.CTkTabview(self, width=600, height=350)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)
        self.tabview.add("Main")
        self.tabview.add("Advanced")

        # Main tab widgets
        main_tab = self.tabview.tab("Main")
        self.input_label = ctk.CTkLabel(main_tab, text="Input File/Folder:")
        self.input_label.pack(pady=2)
        self.input_var = ctk.StringVar()
        self.input_entry = ctk.CTkEntry(main_tab, textvariable=self.input_var, width=350)
        self.input_entry.pack(pady=2)
        self.browse_btn = ctk.CTkButton(main_tab, text="Browse", command=self.browse_input)
        self.browse_btn.pack(pady=2)
        self.output_label = ctk.CTkLabel(main_tab, text="Output File/Folder:")
        self.output_label.pack(pady=2)
        self.output_var = ctk.StringVar()
        self.output_entry = ctk.CTkEntry(main_tab, textvariable=self.output_var, width=350)
        self.output_entry.pack(pady=2)
        self.browse_out_btn = ctk.CTkButton(main_tab, text="Browse", command=self.browse_output)
        self.browse_out_btn.pack(pady=2)

        # Context-aware: time input for time-based tools
        if tool_name in ["Song By Time", "Timestamps"]:
            self.time_label = ctk.CTkLabel(main_tab, text="Enter start times (comma separated, seconds or mm:ss):")
            self.time_label.pack(pady=2)
            self.time_var = ctk.StringVar()
            self.time_entry = ctk.CTkEntry(main_tab, textvariable=self.time_var, width=350)
            self.time_entry.pack(pady=2)

        self.run_btn = ctk.CTkButton(main_tab, text="Run", command=self.run_tool)
        self.run_btn.pack(pady=10)

        self.result_text = ctk.CTkTextbox(main_tab, height=120, width=500)
        self.result_text.pack(pady=10)

        # Advanced tab widgets
        adv_tab = self.tabview.tab("Advanced")
        self.param_label = ctk.CTkLabel(adv_tab, text="Parameters (key=value, optional):")
        self.param_label.pack(pady=2)
        self.param_var = ctk.StringVar()
        self.param_entry = ctk.CTkEntry(adv_tab, textvariable=self.param_var, width=350)
        self.param_entry.pack(pady=2)

    def browse_input(self):
        file = filedialog.askopenfilename()
        if file:
            self.input_var.set(file)

    def browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_var.set(folder)

    def run_tool(self):
        import traceback
        import os
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        tool = getattr(self, 'tool_name', None)
        tool_name = getattr(self, 'tool_name', self.__class__.__name__)
        # Get input/output/params
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()
        params = self.param_var.get().strip()
        result_lines = []
        try:
            if tool_name == "Audio Level":
                from pydub import AudioSegment
                import matplotlib.pyplot as plt
                chunk_size_ms = 100
                if params:
                    try:
                        chunk_size_ms = int(params)
                    except:
                        pass
                audio = AudioSegment.from_mp3(input_path)
                length = len(audio)
                times, volumes = [], []
                for i in range(0, length, chunk_size_ms):
                    chunk = audio[i:i + chunk_size_ms]
                    db = chunk.dBFS if chunk.dBFS != float("-inf") else -90
                    volumes.append(db)
                    times.append(i / 1000)
                plt.figure(figsize=(15, 5))
                plt.plot(times, volumes, label="Volume (dBFS)")
                plt.axhline(y=-45, color='r', linestyle='--', label='Suggested Threshold (-45 dBFS)')
                plt.title("Volume Profile of Audio Over Time")
                plt.xlabel("Time (seconds)")
                plt.ylabel("Volume (dBFS)")
                plt.ylim(-90, 0)
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.show()
                result_lines.append("Volume plot displayed.")
            elif tool_name == "Beat Split":
                import librosa
                import numpy as np
                from pydub import AudioSegment
                AUDIO_FILE = input_path
                MIN_GAP_BETWEEN_BEATS = float(params) if params else 0
                OUTPUT_DIR = output_path or "beat_split_songs"
                y, sr = librosa.load(AUDIO_FILE, sr=None)
                tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
                beat_times = librosa.frames_to_time(beat_frames, sr=sr)
                split_times = [0.0]
                for i in range(1, len(beat_times)):
                    if beat_times[i] - beat_times[i - 1] >= MIN_GAP_BETWEEN_BEATS:
                        split_times.append(beat_times[i])
                split_times.append(len(y) / sr)
                split_ms = [int(t * 1000) for t in split_times]
                audio = AudioSegment.from_mp3(AUDIO_FILE)
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                for i in range(len(split_ms) - 1):
                    start_ms = split_ms[i]
                    end_ms = split_ms[i+1]
                    segment = audio[start_ms:end_ms]
                    output_path_file = os.path.join(OUTPUT_DIR, f"track_{i+1:02}.mp3")
                    segment.export(output_path_file, format="mp3")
                    result_lines.append(f"Exported: track_{i+1:02}.mp3 ({start_ms//1000}s to {end_ms//1000}s)")
                result_lines.append(f"Done! All split tracks saved to: {OUTPUT_DIR}")
            elif tool_name == "Low Volume Split":
                from pydub import AudioSegment
                MIN_PAUSE_DBFS = -35
                PAUSE_DURATION_MS = 2000
                CHUNK_SIZE_MS = 100
                MIN_SONG_LENGTH_MS = 10000
                if params:
                    try:
                        for kv in params.split(","):
                            k, v = kv.split("=")
                            if k == "min_dbfs": MIN_PAUSE_DBFS = float(v)
                            elif k == "pause_ms": PAUSE_DURATION_MS = int(v)
                            elif k == "chunk_ms": CHUNK_SIZE_MS = int(v)
                            elif k == "min_song_ms": MIN_SONG_LENGTH_MS = int(v)
                    except:
                        pass
                audio = AudioSegment.from_mp3(input_path)
                length = len(audio)
                potential_splits = []
                current_silence = 0
                for i in range(0, length, CHUNK_SIZE_MS):
                    chunk = audio[i:i + CHUNK_SIZE_MS]
                    if chunk.dBFS < MIN_PAUSE_DBFS:
                        current_silence += CHUNK_SIZE_MS
                        if current_silence >= PAUSE_DURATION_MS:
                            potential_splits.append(i)
                            current_silence = 0
                    else:
                        current_silence = 0
                clean_splits = []
                prev_split = 0
                for split in potential_splits:
                    if split - prev_split >= MIN_SONG_LENGTH_MS:
                        clean_splits.append(split)
                        prev_split = split
                split_points = [0] + clean_splits + [length]
                output_folder = output_path or "volume_split_songs"
                os.makedirs(output_folder, exist_ok=True)
                for i in range(len(split_points) - 1):
                    start = split_points[i]
                    end = split_points[i+1]
                    segment = audio[start:end]
                    out_file = os.path.join(output_folder, f"song_{i+1}.mp3")
                    segment.export(out_file, format="mp3")
                    result_lines.append(f"Exported song_{i+1}.mp3 from {start//1000}s to {end//1000}s")
            elif tool_name == "Process":
                from pydub import AudioSegment
                from pydub.silence import split_on_silence
                audio = AudioSegment.from_mp3(input_path)
                min_silence_len = 1500
                silence_thresh = -40
                if params:
                    try:
                        for kv in params.split(","):
                            k, v = kv.split("=")
                            if k == "min_silence_len": min_silence_len = int(v)
                            elif k == "silence_thresh": silence_thresh = int(v)
                    except:
                        pass
                chunks = split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
                output_folder = output_path or "split_songs"
                os.makedirs(output_folder, exist_ok=True)
                for i, chunk in enumerate(chunks):
                    out_file = os.path.join(output_folder, f"song_{i+1}.mp3")
                    chunk.export(out_file, format="mp3")
                    result_lines.append(f"Exported {out_file}")
            elif tool_name == "Song By Time":
                from pydub import AudioSegment
                import os
                import json
                audio = AudioSegment.from_mp3(input_path)
                audio_length_ms = len(audio)
                # Parse time input
                timestr = getattr(self, 'time_var', None)
                if timestr:
                    timestr = self.time_var.get().strip()
                    start_times = []
                    for t in timestr.split(","):
                        t = t.strip()
                        if ":" in t:
                            mm, ss = t.split(":")
                            start_times.append(int(mm)*60*1000 + int(ss)*1000)
                        else:
                            start_times.append(int(float(t)*1000))
                    end_times = start_times[1:] + [audio_length_ms]
                    output_dir = output_path or "time_splits"
                    os.makedirs(output_dir, exist_ok=True)
                    for i in range(len(start_times)):
                        start = start_times[i]
                        end = end_times[i]
                        segment = audio[start:end]
                        out_file = os.path.join(output_dir, f"song_{i+1}.mp3")
                        segment.export(out_file, format="mp3")
                        result_lines.append(f"Exported: song_{i+1}.mp3 ({start//1000}s → {end//1000}s)")
                else:
                    result_lines.append("No time input provided.")
            elif tool_name == "Timestamps":
                from pydub import AudioSegment
                MIN_PAUSE_DBFS = -35
                PAUSE_DURATION_MS = 2000
                CHUNK_SIZE_MS = 100
                MIN_SONG_LENGTH_MS = 10000
                audio = AudioSegment.from_mp3(input_path)
                length = len(audio)
                split_points = []
                current_silence = 0
                for i in range(0, length, CHUNK_SIZE_MS):
                    chunk = audio[i:i + CHUNK_SIZE_MS]
                    db = chunk.dBFS if chunk.dBFS != float("-inf") else -90
                    if db < MIN_PAUSE_DBFS:
                        current_silence += CHUNK_SIZE_MS
                        if current_silence >= PAUSE_DURATION_MS:
                            split_points.append(i)
                            current_silence = 0
                    else:
                        current_silence = 0
                final_splits = [0]
                for point in split_points:
                    if point - final_splits[-1] >= MIN_SONG_LENGTH_MS:
                        final_splits.append(point)
                final_splits.append(length)
                output_dir = output_path or "volume_split_songs"
                os.makedirs(output_dir, exist_ok=True)
                for i in range(len(final_splits) - 1):
                    start = final_splits[i]
                    end = final_splits[i+1]
                    segment = audio[start:end]
                    out_file = os.path.join(output_dir, f"song_{i+1}.mp3")
                    segment.export(out_file, format="mp3")
                    result_lines.append(f"Exported: song_{i+1}.mp3 ({start//1000}s → {end//1000}s)")
            elif tool_name == "Transition Energy":
                import librosa
                import numpy as np
                from scipy.signal import medfilt
                from pydub import AudioSegment
                import matplotlib.pyplot as plt
                import json
                AUDIO_FILE = input_path
                OUTPUT_DIR = output_path or "beat_change_splits"
                WINDOW_SECONDS = 10
                TEMPO_CHANGE_THRESHOLD = 10
                MIN_SEGMENT_DURATION_SEC = 30
                y, sr = librosa.load(AUDIO_FILE, sr=None)
                duration_sec = librosa.get_duration(y=y, sr=sr)
                hop_length = 512
                onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
                frame_times = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr, hop_length=hop_length)
                window_hops = int(WINDOW_SECONDS * sr / hop_length)
                tempos = []
                times = []
                for i in range(0, len(onset_env) - window_hops, window_hops):
                    segment = onset_env[i:i + window_hops]
                    if len(segment) < 10:
                        continue
                    tempo, _ = librosa.beat.beat_track(onset_envelope=segment, sr=sr, hop_length=hop_length)
                    tempos.append(tempo)
                    times.append(frame_times[i])
                tempos = medfilt(tempos, kernel_size=3)
                tempos = np.array(tempos)
                times = np.array(times)
                split_times = [0.0]
                for i in range(1, len(tempos)):
                    delta = abs(tempos[i] - tempos[i - 1])
                    if delta >= TEMPO_CHANGE_THRESHOLD:
                        if times[i] - split_times[-1] > MIN_SEGMENT_DURATION_SEC:
                            split_times.append(times[i])
                split_times.append(duration_sec)
                split_ms = [int(t * 1000) for t in split_times]
                audio = AudioSegment.from_mp3(AUDIO_FILE)
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                segments_metadata = []
                for i in range(len(split_ms) - 1):
                    start = split_ms[i]
                    end = split_ms[i + 1]
                    segment = audio[start:end]
                    filename = f"track_{i+1:02}.mp3"
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    segment.export(filepath, format="mp3")
                    result_lines.append(f"Exported: {filename} ({start//1000}s → {end//1000}s)")
                    segments_metadata.append({
                        "track": i + 1,
                        "filename": filename,
                        "start_sec": start // 1000,
                        "end_sec": end // 1000,
                        "duration_sec": (end - start) // 1000
                    })
                with open(os.path.join(OUTPUT_DIR, "split_timestamps.json"), "w") as f:
                    json.dump(segments_metadata, f, indent=2)
                with open(os.path.join(OUTPUT_DIR, "split_timestamps.txt"), "w") as f:
                    for segment in segments_metadata:
                        f.write(f"Track {segment['track']:02}: {segment['start_sec']}s -> {segment['end_sec']}s ({segment['duration_sec']}s)\n")
                plt.figure(figsize=(14, 5))
                plt.plot(times, tempos, marker='o', label="Tempo (BPM)")
                for split in split_times[1:-1]:
                    plt.axvline(x=split, color='r', linestyle='--', alpha=0.5)
                plt.title("Detected Beat Pattern Changes Over Time")
                plt.xlabel("Time (s)")
                plt.ylabel("Tempo (BPM)")
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(OUTPUT_DIR, "tempo_plot.png"))
                plt.show()
                result_lines.append(f"All tracks, timestamp logs, and tempo graph saved to: {OUTPUT_DIR}")
            elif tool_name == "YouTube to MP3":
                result_lines.append("YouTube to MP3 logic not implemented yet.")
            else:
                result_lines.append("Tool not implemented.")
        except Exception as e:
            result_lines.append(f"Error: {e}")
            result_lines.append(traceback.format_exc())
        self.result_text.insert("end", "\n".join(result_lines))
        self.result_text.configure(state="disabled")

class SidebarApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DJ Helper Suite")
        self.geometry("900x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar_buttons = {}
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", fill="both", expand=True)

        # Tool names and Frame classes

        self.tools = [
            ("Audio Level", ToolFrame),
            ("Beat Split", ToolFrame),
            ("Low Volume Split", ToolFrame),
            ("Process", ToolFrame),
            ("Song By Time", ToolFrame),
            ("Timestamps", ToolFrame),
            ("Transition Energy", ToolFrame),
            ("YouTube to MP3", ToolFrame)
        ]
        for i, (name, frame_class) in enumerate(self.tools):
            btn = ctk.CTkButton(self.sidebar, text=name, command=lambda n=name, f=frame_class: self.show_tool(n, f))
            btn.pack(pady=8, padx=4, fill="x")
            self.sidebar_buttons[name] = btn

        self.current_tool_frame = None
        self.show_welcome()

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_welcome(self):
        self.clear_main()
        label = ctk.CTkLabel(self.main_frame, text="Welcome to DJ Helper Suite!\nSelect a tool from the sidebar.", font=("Arial", 20))
        label.pack(expand=True)

    def show_tool(self, name, frame_class):
        self.clear_main()
        if frame_class:
            self.current_tool_frame = frame_class(self.main_frame, name)
        else:
            label = ctk.CTkLabel(self.main_frame, text=f"{name} tool GUI goes here.")
            label.pack(pady=20)

if __name__ == "__main__":
    app = SidebarApp()
    app.mainloop()
