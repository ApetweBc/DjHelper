# YouTube to MP3 Playlist Downloader

## Features
- Download all videos from a YouTube playlist or single video as MP3
- Automatically names zip file after playlist or video
- Deletes individual MP3s after zipping
- Shows progress for each download

## Requirements
- Windows OS
- Python 3.7+
- ffmpeg (must be installed and in PATH)
- yt-dlp (see requirements.txt)

## Installation
1. Install Python from https://www.python.org/
2. Install ffmpeg from https://ffmpeg.org/download.html and add to PATH
3. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the script:
   ```
   python youtubetomp3.py
   ```
2. Enter a YouTube playlist or video URL when prompted.
3. Find the zip file in the `youtubemp3` folder.

## Packaging as an EXE (Windows)
1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Build the executable:
   ```
   pyinstaller --onefile youtubetomp3.py
   ```
3. Distribute the generated `dist/youtubetomp3.exe` file.

---
For questions or issues, contact the author.
