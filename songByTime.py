import json
import os
from pydub import AudioSegment

# === CONFIGURATION ===
AUDIO_FILE = "funeralmix.mp3"
OUTPUT_DIR = "time_splits"
TIMECUT_JSON = "timecut_metadata.json"  # Your updated JSON

# === LOAD TIME CUTS FROM JSON ===
with open(TIMECUT_JSON, "r", encoding="utf-8") as f:
    metadata = json.load(f)

# === LOAD AUDIO ===
print("🎵 Loading audio...")
audio = AudioSegment.from_mp3(AUDIO_FILE)
audio_length_ms = len(audio)

# === CONVERT START TIMES: MINUTES → MILLISECONDS ===
start_times = [int(entry["start_time"] * 60 * 1000) for entry in metadata]
end_times = start_times[1:] + [audio_length_ms]  # Last song ends at end of file

# === CREATE OUTPUT DIR ===
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === SPLIT AND EXPORT ===
segments_metadata = []

for i in range(len(metadata)):
    start = start_times[i]
    end = end_times[i]

    artist = metadata[i].get("artist", "Unknown Artist").strip()
    title = metadata[i].get("title", f"Track_{i+1:02}").strip()
    filename = f"{artist} - {title}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    segment = audio[start:end]
    segment.export(filepath, format="mp3")
    print(f"✅ Exported: {filename} ({start // 1000}s → {end // 1000}s)")

    segments_metadata.append({
        "track": i + 1,
        "filename": filename,
        "artist": artist,
        "title": title,
        "start_min": metadata[i]["start_time"],
        "start_sec": start // 1000,
        "end_sec": end // 1000,
        "duration_sec": (end - start) // 1000
    })

# === SAVE METADATA ===
with open(os.path.join(OUTPUT_DIR, "split_timestamps.json"), "w", encoding="utf-8") as f:
    json.dump(segments_metadata, f, indent=2, ensure_ascii=False)

with open(os.path.join(OUTPUT_DIR, "split_timestamps.txt"), "w", encoding="utf-8") as f:
    for s in segments_metadata:
        f.write(f"{s['track']:02d}. {s['artist']} - {s['title']} ({s['start_sec']}s → {s['end_sec']}s)\n")

print("\n📁 All segments and metadata saved to:", OUTPUT_DIR)
