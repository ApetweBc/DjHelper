
import os
import sys
import shutil
import zipfile
from yt_dlp import YoutubeDL


def main():
	url = input('Enter YouTube video or playlist URL: ').strip()
	output_dir = os.path.join(os.path.dirname(__file__), 'youtubemp3')
	os.makedirs(output_dir, exist_ok=True)

	ydl_opts = {
		'format': 'bestaudio/best',
		'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
		'extractaudio': True,
		'audioformat': 'mp3',
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192',
		}],
		'noplaylist': False,
		'quiet': False,
	}
	print('Downloading...')
	try:
		with YoutubeDL(ydl_opts) as ydl:
			ydl.download([url])
	except Exception as e:
		print(f'Error downloading: {e}')
		sys.exit(1)

	# Zip all mp3 files in output_dir
	zip_path = os.path.join(output_dir, 'youtubemp3.zip')
	with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
		for fname in os.listdir(output_dir):
			if fname.endswith('.mp3'):
				zipf.write(os.path.join(output_dir, fname), fname)
	print(f'All MP3s zipped to {zip_path}')

if __name__ == '__main__':
	main()
