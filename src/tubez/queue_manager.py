import threading
import time
import subprocess
import re
from queue import Queue
from . import DOWNLOAD_FOLDER

# Global queue and task state dictionary
DOWNLOAD_QUEUE = Queue()
DOWNLOAD_TASKS = {} # This will now store status for queued and active downloads

def download_worker_thread():
    """The single worker thread that processes the download queue."""
    while True:
        task_id, command, title = DOWNLOAD_QUEUE.get() # This will block until an item is available
        
        print(f"Worker picked up task: {task_id} ({title})")
        
        DOWNLOAD_TASKS[task_id]['status'] = 'downloading'
        DOWNLOAD_TASKS[task_id]['stage'] = 'Initializing...'
        
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1)
            
            progress_regex = re.compile(r"\[download\]\s+(?P<percent>[\d.]+)%\s+of\s+(?:~)?\s*(?P<size>[\d.]+\w+B)\s+at\s+(?P<speed>[\d.]+\w+B/s)\s+ETA\s+(?P<eta>[\d:]+)")
            destination_regex = re.compile(r"\[download\] Destination: (.*)")
            post_process_regex = re.compile(r"\[(Merger|ExtractAudio|ffmpeg)\]")
            
            for line in iter(process.stdout.readline, ''):
                prog_match, dest_match, post_match = progress_regex.search(line), destination_regex.search(line), post_process_regex.search(line)
                if prog_match:
                    data = prog_match.groupdict()
                    DOWNLOAD_TASKS[task_id].update({'progress': float(data['percent']), 'size': data['size'], 'speed': data['speed'], 'eta': data['eta'], 'stage': 'Downloading...'})
                    continue
                if dest_match: DOWNLOAD_TASKS[task_id]['stage'] = 'Downloading...'; continue
                if post_match: DOWNLOAD_TASKS[task_id]['stage'], DOWNLOAD_TASKS[task_id]['progress'] = f'{post_match.group(1).capitalize()} files...', 100.0; continue
            
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                error_msg = stderr.strip().split('ERROR:')[-1].strip()
                DOWNLOAD_TASKS[task_id]['status'], DOWNLOAD_TASKS[task_id]['error'] = 'error', error_msg or "Unknown yt-dlp error."
            else:
                DOWNLOAD_TASKS[task_id]['status'], DOWNLOAD_TASKS[task_id]['progress'], DOWNLOAD_TASKS[task_id]['stage'] = 'completed', 100.0, 'Finished'
        except Exception as e:
            DOWNLOAD_TASKS[task_id]['status'], DOWNLOAD_TASKS[task_id]['error'] = 'error', str(e)
        
        DOWNLOAD_QUEUE.task_done()

# Start the worker thread in the background when this module is imported
worker = threading.Thread(target=download_worker_thread, daemon=True)
worker.start()
