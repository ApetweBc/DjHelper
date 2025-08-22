from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

# Load your MP3 file
audio = AudioSegment.from_mp3("funeralmix.mp3")

# Optional: Normalize audio to make silence detection more consistent
# audio = match_target_amplitude(audio, -20.0)

# Split on silence
chunks = split_on_silence(
    audio,
    min_silence_len=1500,     # silence must be at least 1.5 seconds long
    silence_thresh=-40        # adjust based on your audio volume
)

# Create output folder
output_folder = "split_songs"
os.makedirs(output_folder, exist_ok=True)

# Export each chunk
for i, chunk in enumerate(chunks):
    out_file = os.path.join(output_folder, f"song_{i+1}.mp3")
    chunk.export(out_file, format="mp3")
    print(f"Exported {out_file}")
