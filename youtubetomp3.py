
import os
import sys
import shutil
import zipfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
from yt_dlp import YoutubeDL



def get_video_urls_and_name(url):
	ydl_opts = {
		'quiet': True,
		'extract_flat': True,
		'forcejson': True,
		'dump_single_json': True,
	}
	with YoutubeDL(ydl_opts) as ydl:
		info = ydl.extract_info(url, download=False)
		if 'entries' in info:
			playlist_name = info.get('title', 'playlist')
			return [entry['url'] for entry in info['entries']], playlist_name
		else:
			video_title = info.get('title', 'video')
			return [url], video_title

def download_mp3(video_url, output_dir, idx, total, progress_callback=None, stop_event=None):
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
		'noplaylist': True,
		'quiet': True,
		'progress_hooks': [lambda d: show_progress(d, idx, total, progress_callback)],
	}
	try:
		if stop_event and stop_event.is_set():
			if progress_callback:
				progress_callback(f'Stopped before starting {video_url}')
			return
		with YoutubeDL(ydl_opts) as ydl:
			if stop_event and stop_event.is_set():
				if progress_callback:
					progress_callback(f'Stopped before starting {video_url}')
				return
			ydl.download([video_url])
	except Exception as e:
		if progress_callback:
			progress_callback(f'Error downloading {video_url}: {e}')
		else:
			print(f'Error downloading {video_url}: {e}')

def show_progress(d, idx, total, progress_callback=None):
	if d['status'] == 'downloading':
		percent = d.get('downloaded_bytes', 0) / max(d.get('total_bytes', 1), 1) * 100 if d.get('total_bytes') else 0
		msg = f"[{idx+1}/{total}] {d.get('filename', '')}: {percent:.1f}%"
		if progress_callback:
			progress_callback(msg)
		else:
			print(msg, end='\r')
	elif d['status'] == 'finished':
		msg = f"[{idx+1}/{total}] {d.get('filename', '')}: Done"
		if progress_callback:
			progress_callback(msg)
		else:
			print(msg)


# --- Tkinter GUI ---
class YouTubeMP3App:
	def __init__(self, root):
		self.root = root
		self.root.title('YouTube Playlist to MP3 Zipper')
		self.url_var = tk.StringVar()
		self.folder_var = tk.StringVar(value=os.path.join(os.path.dirname(__file__), 'youtubemp3'))
		self.status_var = tk.StringVar()
		self.progress_text = tk.Text(root, height=12, width=70)
		self.progress_text.config(state='disabled')
		self.stop_event = threading.Event()

		tk.Label(root, text='YouTube Playlist/Video URL:').pack(pady=4)
		tk.Entry(root, textvariable=self.url_var, width=60).pack(pady=2)

		tk.Label(root, text='Output Folder:').pack(pady=4)
		folder_frame = tk.Frame(root)
		folder_frame.pack()
		tk.Entry(folder_frame, textvariable=self.folder_var, width=50).pack(side='left')
		tk.Button(folder_frame, text='Browse', command=self.browse_folder).pack(side='left', padx=4)

		button_frame = tk.Frame(root)
		button_frame.pack(pady=8)
		self.start_button = tk.Button(button_frame, text='Start Download', command=self.start_download)
		self.start_button.pack(side='left', padx=4)
		self.stop_button = tk.Button(button_frame, text='Stop', command=self.stop_download, state='disabled')
		self.stop_button.pack(side='left', padx=4)

		tk.Label(root, textvariable=self.status_var, fg='blue').pack(pady=2)
		self.progress_text.pack(pady=4)

	def browse_folder(self):
		folder = filedialog.askdirectory()
		if folder:
			self.folder_var.set(folder)

	def start_download(self):
		# disable start button to prevent multiple clicks
		self.start_button.config(state='disabled')
		url = self.url_var.get().strip()
		output_dir = self.folder_var.get().strip()
		if not url:
			messagebox.showerror('Error', 'Please enter a YouTube URL.')
			self.start_button.config(state='normal')
			return
		if not os.path.isdir(output_dir):
			os.makedirs(output_dir, exist_ok=True)
		self.status_var.set('Extracting video URLs...')
		self.progress_text.config(state='normal')
		self.progress_text.delete(1.0, tk.END)
		self.progress_text.config(state='disabled')
		self.stop_event.clear()
		self.stop_button.config(state='normal')

		threading.Thread(target=self.download_and_zip, args=(url, output_dir), daemon=True).start()

	def stop_download(self):
		self.stop_event.set()
		self.status_var.set('Stopping download...')
		self.stop_button.config(state='disabled')
		self.start_button.config(state='normal')

	def update_progress(self, msg):
		self.progress_text.config(state='normal')
		self.progress_text.insert(tk.END, msg + '\n')
		self.progress_text.see(tk.END)
		self.progress_text.config(state='disabled')

	def download_and_zip(self, url, output_dir):
		try:
			video_urls, group_name = get_video_urls_and_name(url)
		except Exception as e:
			self.status_var.set(f'Error extracting URLs: {e}')
			return
		total = len(video_urls)
		self.status_var.set(f'Found {total} videos. Downloading...')

		def progress_callback(msg):
			self.root.after(0, self.update_progress, msg)

		with ThreadPoolExecutor(max_workers=4) as executor:
			futures = []
			for idx, video_url in enumerate(video_urls):
				if self.stop_event.is_set():
					self.root.after(0, self.update_progress, 'Download stopped by user.')
					self.status_var.set('Download stopped.')
					self.stop_button.config(state='disabled')
					self.start_button.config(state='normal')
					return
				futures.append(executor.submit(download_mp3, video_url, output_dir, idx, total, progress_callback, self.stop_event))
			for f in futures:
				if self.stop_event.is_set():
					self.root.after(0, self.update_progress, 'Download stopped by user.')
					self.status_var.set('Download stopped.')
					self.stop_button.config(state='disabled')
					self.start_button.config(state='normal')
					return
				f.result()
		self.stop_button.config(state='disabled')

		safe_name = "".join(c for c in group_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
		zip_path = os.path.join(output_dir, f'{safe_name}.zip')
		with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
			for fname in os.listdir(output_dir):
				if fname.endswith('.mp3'):
					zipf.write(os.path.join(output_dir, fname), fname)
		self.status_var.set(f'All MP3s zipped to {zip_path}')
		self.root.after(0, self.update_progress, f'All MP3s zipped to {zip_path}')
		self.start_button.config(state='normal')
		# Delete individual mp3 files
		for fname in os.listdir(output_dir):
			if fname.endswith('.mp3'):
				try:
					os.remove(os.path.join(output_dir, fname))
				except Exception as e:
					self.root.after(0, self.update_progress, f'Could not delete {fname}: {e}')

def main():
	root = tk.Tk()
	app = YouTubeMP3App(root)
	root.mainloop()

if __name__ == '__main__':
	main()
