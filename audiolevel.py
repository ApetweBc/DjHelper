from pydub import AudioSegment
import matplotlib.pyplot as plt

# --- Settings ---
file_path = "funeralmix.mp3"
chunk_size_ms = 100  # How fine to sample (smaller = more detail)

# --- Load and Prepare Audio ---
audio = AudioSegment.from_mp3(file_path)
length = len(audio)
times = []
volumes = []

# --- Process audio in chunks ---
for i in range(0, length, chunk_size_ms):
    chunk = audio[i:i + chunk_size_ms]
    db = chunk.dBFS if chunk.dBFS != float("-inf") else -90  # Handle digital silence
    volumes.append(db)
    times.append(i / 1000)  # Convert to seconds

# --- Plotting ---
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
