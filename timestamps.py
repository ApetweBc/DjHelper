from pydub import AudioSegment
import os

# === CONFIGURATION ===
AUDIO_FILE = "funeralmix.mp3"
MIN_PAUSE_DBFS = -35          # Consider anything below this as a volume drop
PAUSE_DURATION_MS = 2000      # Duration the volume must stay low
CHUNK_SIZE_MS = 100
MIN_SONG_LENGTH_MS = 10000    # Skip splitting if segments are shorter than this

# === LOAD AUDIO ===
audio = AudioSegment.from_mp3(AUDIO_FILE)
length = len(audio)

# === FIND SPLIT POINTS BASED ON VOLUME DROPS ===
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

# === FILTER TOO-CLOSE SPLITS AND PREPARE FINAL SPLITS ===
final_splits = [0]
for point in split_points:
    if point - final_splits[-1] >= MIN_SONG_LENGTH_MS:
        final_splits.append(point)
final_splits.append(length)

# === PREVIEW SPLIT TIMES ===
print("\n🕒 Split Preview:")
for i in range(len(final_splits) - 1):
    start_sec = final_splits[i] // 1000
    end_sec = final_splits[i+1] // 1000
    duration = end_sec - start_sec
    print(f"  Song {i+1}: {start_sec}s → {end_sec}s ({duration} seconds)")

# === ASK TO EXPORT ===
confirm = input("\nExport all these segments as separate MP3s? (y/n): ").strip().lower()
if confirm == 'y':
    output_dir = "volume_split_songs"
    os.makedirs(output_dir, exist_ok=True)

    for i in range(len(final_splits) - 1):
        start = final_splits[i]
        end = final_splits[i+1]
        segment = audio[start:end]
        output_file = os.path.join(output_dir, f"song_{i+1}.mp3")
        segment.export(output_file, format="mp3")
        print(f"✅ Exported: {output_file}")
else:
    print("\n❌ Export canceled. You can adjust parameters and re-run.")
