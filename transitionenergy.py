import librosa
import numpy as np
from scipy.signal import medfilt
from pydub import AudioSegment
import matplotlib.pyplot as plt
import json
import os

# === CONFIGURATION ===
AUDIO_FILE = "funeralmix.mp3"
OUTPUT_DIR = "beat_change_splits"
WINDOW_SECONDS = 10
TEMPO_CHANGE_THRESHOLD = 10
MIN_SEGMENT_DURATION_SEC = 30

# === STEP 1: LOAD AUDIO ===
print("🎵 Loading audio...")
y, sr = librosa.load(AUDIO_FILE, sr=None)
duration_sec = librosa.get_duration(y=y, sr=sr)

# === STEP 2: ANALYZE TEMPO PATTERNS ===
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

# === STEP 3: DETECT TEMPO CHANGES ===
split_times = [0.0]
for i in range(1, len(tempos)):
    delta = abs(tempos[i] - tempos[i - 1])
    if delta >= TEMPO_CHANGE_THRESHOLD:
        if times[i] - split_times[-1] > MIN_SEGMENT_DURATION_SEC:
            split_times.append(times[i])
split_times.append(duration_sec)

split_ms = [int(t * 1000) for t in split_times]

# === STEP 4: EXPORT SPLITS ===
print(f"\n✂️ Splitting into {len(split_ms)-1} segments...")
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
    print(f"✅ Exported: {filename} ({start//1000}s → {end//1000}s)")

    segments_metadata.append({
        "track": i + 1,
        "filename": filename,
        "start_sec": start // 1000,
        "end_sec": end // 1000,
        "duration_sec": (end - start) // 1000
    })

# === STEP 5: EXPORT TIMESTAMPS TO JSON & TXT ===
with open(os.path.join(OUTPUT_DIR, "split_timestamps.json"), "w") as f:
    json.dump(segments_metadata, f, indent=2)

with open(os.path.join(OUTPUT_DIR, "split_timestamps.txt"), "w") as f:
    for segment in segments_metadata:
      f.write(f"Track {segment['track']:02}: {segment['start_sec']}s -> {segment['end_sec']}s ({segment['duration_sec']}s)\n")

# === STEP 6: PLOT TEMPO CHANGES ===
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

print("\n📁 All tracks, timestamp logs, and tempo graph saved to:", OUTPUT_DIR)
