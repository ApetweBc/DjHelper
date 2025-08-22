from pydub import AudioSegment
import os

# Settings
MIN_PAUSE_DBFS = -35          # Threshold: anything below this dBFS is considered a pause
PAUSE_DURATION_MS = 2000       # How long the low-volume needs to last (e.g. 2 seconds)
CHUNK_SIZE_MS = 100            # Window size for checking volume
MIN_SONG_LENGTH_MS = 10000     # Minimum duration of a song (10 seconds)

# Load audio
audio = AudioSegment.from_mp3("funeralmix.mp3")
length = len(audio)

# Track low-volume regions
potential_splits = []
current_silence = 0

for i in range(0, length, CHUNK_SIZE_MS):
    chunk = audio[i:i + CHUNK_SIZE_MS]
    if chunk.dBFS < MIN_PAUSE_DBFS:
        current_silence += CHUNK_SIZE_MS
        if current_silence >= PAUSE_DURATION_MS:
            potential_splits.append(i)
            current_silence = 0  # reset
    else:
        current_silence = 0

# Deduplicate splits and make sure they are spaced
clean_splits = []
prev_split = 0
for split in potential_splits:
    if split - prev_split >= MIN_SONG_LENGTH_MS:
        clean_splits.append(split)
        prev_split = split

# Always include start and end
split_points = [0] + clean_splits + [length]

# Export
output_folder = "volume_split_songs"
os.makedirs(output_folder, exist_ok=True)

for i in range(len(split_points) - 1):
    start = split_points[i]
    end = split_points[i+1]
    segment = audio[start:end]
    segment.export(os.path.join(output_folder, f"song_{i+1}.mp3"), format="mp3")
    print(f"Exported song_{i+1}.mp3 from {start//1000}s to {end//1000}s")
