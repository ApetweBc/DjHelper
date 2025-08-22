import librosa
import numpy as np
from pydub import AudioSegment
import os

# === CONFIGURATION ===
AUDIO_FILE = "funeralmix.mp3"
MIN_GAP_BETWEEN_BEATS = 0  # seconds — gap threshold to trigger split
OUTPUT_DIR = "beat_split_songs"

# === STEP 1: DETECT BEATS ===
print("🔍 Loading audio and detecting beats...")
y, sr = librosa.load(AUDIO_FILE, sr=None)
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

# === STEP 2: FIND SPLIT POINTS ===
split_times = [0.0]
for i in range(1, len(beat_times)):
    if beat_times[i] - beat_times[i - 1] >= MIN_GAP_BETWEEN_BEATS:
        split_times.append(beat_times[i])
split_times.append(len(y) / sr)

# Convert seconds to milliseconds for pydub
split_ms = [int(t * 1000) for t in split_times]

# === STEP 3: SPLIT AND EXPORT ===
print(f"\n🎵 Splitting {AUDIO_FILE} into {len(split_ms) - 1} segments...")
audio = AudioSegment.from_mp3(AUDIO_FILE)
os.makedirs(OUTPUT_DIR, exist_ok=True)

for i in range(len(split_ms) - 1):
    start_ms = split_ms[i]
    end_ms = split_ms[i+1]
    segment = audio[start_ms:end_ms]
    output_path = os.path.join(OUTPUT_DIR, f"track_{i+1:02}.mp3")
    segment.export(output_path, format="mp3")
    print(f"✅ Exported: track_{i+1:02}.mp3 ({start_ms//1000}s to {end_ms//1000}s)")

print("\n✅ Done! All split tracks saved to:", OUTPUT_DIR)
