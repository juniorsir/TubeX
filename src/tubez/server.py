# src/tubez/server.py

import os
import json
import subprocess
import re
import uuid
import time
import threading
import requests
import urllib.parse
from flask import (
    render_template, request, redirect, url_for,
    send_from_directory, flash, jsonify, session
)
from youtubesearchpython import VideosSearch
from packaging.version import parse as parse_version
from functools import wraps

# --- Import from our package's __init__.py ---
from . import app, __version__, DOWNLOAD_FOLDER, HISTORY_FILE, CONFIG_FILE, load_config, DEFAULT_CONFIG
from .queue_manager import DOWNLOAD_QUEUE, DOWNLOAD_TASKS

def login_required(f):
    """Decorator to protect routes with a password if one is set."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        password = app.config.get("PASSWORD")
        if password and not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def load_history():
    """Loads viewing history from the JSON file."""
    if not HISTORY_FILE.exists(): return []
    try:
        with open(HISTORY_FILE, 'r') as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return []

def save_history_item(video_info):
    """Adds an item to the history, ensuring no duplicates and trimming to the limit."""
    history = load_history()
    video_identifier = video_info.get('webpage_url') or video_info.get('id')
    new_item = {
        'id': video_identifier,
        'title': video_info.get('title'),
        'thumbnail': video_info.get('thumbnails', [{}])[-1].get('url')
    }
    if not new_item['id'] or not new_item['title']: return
    history = [item for item in history if item.get('id') != new_item['id']]
    history.insert(0, new_item)
    with open(HISTORY_FILE, 'w') as f: json.dump(history[:20], f, indent=4)

def get_video_info(url_or_id, playlist=False):
    """Gets video or playlist metadata using yt-dlp."""
    command = ['yt-dlp', '--dump-json', '--no-warnings']
    if playlist: command.append('--flat-playlist')
    command.extend(['--', url_or_id])
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True, timeout=25)
        if playlist:
            return [json.loads(line) for line in process.stdout.strip().split('\n') if line]
        return json.loads(process.stdout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        flash(f"Error fetching metadata: {e}", "error")
        return None

@app.template_filter('url_encode_path')
def url_encode_path_filter(s):
    """A template filter to safely encode a string for use in a URL path."""
    return urllib.parse.quote(s, safe='')

@app.route('/')
@login_required
def index():
    history = load_history()
    return render_template('index.html', history=history)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query: return redirect(url_for('index'))

    url_pattern = re.compile(r'https?://\S+')
    
 
    if url_pattern.match(query):
        if 'youtube.com' in query and 'list=RD' in query:
            match = re.search(r'v=([^&]+)', query) or re.search(r'list=RD([^&]+)', query)
            if match:
                video_id = match.group(1)
                flash("YouTube Mix playlists are not supported. Loading the starting video of the mix instead.", "info")
                return redirect(url_for('formats', video_id=video_id))
        playlist_indicators = ['list=', 'playlist?', '/c/', '/channel/', '/user/']
        if any(indicator in query for indicator in playlist_indicators):
            return redirect(url_for('playlist', playlist_url=query))
        
        video_id = query
        return redirect(url_for('formats', video_id=video_id))
    else:
        try:
            videos_search = VideosSearch(query, limit=12)
            results = videos_search.result()['result']
            return render_template('results.html', results=results, query=query)
        except Exception as e:
            flash(f"An error occurred during YouTube search: {e}", "error")
            return redirect(url_for('index'))

@app.route('/formats/<path:video_id>')
@login_required
def formats(video_id):
    video_id = urllib.parse.unquote(video_id)
    info = get_video_info(video_id)
    if not info: return redirect(request.referrer or url_for('index'))
    save_history_item(info)
    
    format_list = []
    for f in info.get('formats', []):
        if 'storyboard' in f.get('format_note', ''): continue
        if f.get('vcodec') == 'none' and f.get('acodec') == 'none': continue
        is_video_only = f.get('vcodec') != 'none' and f.get('acodec') == 'none'
        is_audio_only = f.get('vcodec') == 'none' and f.get('acodec') != 'none'
        desc = ""
        if is_audio_only: desc = f"{int(f.get('abr', 0))}k ({f.get('ext')}, Audio Only)"
        else:
            desc = f"{f.get('height', 0)}p ({f.get('ext')})"
            if is_video_only: desc += " (Video Only)"
            else: desc += " (Video + Audio)"
        filesize = f.get('filesize_approx') or f.get('filesize')
        size_str = f"{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        format_list.append({'id': f['format_id'], 'description': desc, 'size': size_str, 'is_video_only': is_video_only, 'is_audio_only': is_audio_only})
        
    return render_template('formats.html', formats=format_list, video_id=video_id, title=info.get('title', ''))

@app.route('/playlist')
@login_required
def playlist():
    playlist_url = request.args.get('playlist_url')
    if not playlist_url: return redirect(url_for('index'))
    playlist_items = get_video_info(playlist_url, playlist=True)
    if not playlist_items: return redirect(url_for('index'))
    playlist_title = playlist_items[0].get('playlist_title', 'Playlist')
    return render_template('playlist.html', videos=playlist_items, title=playlist_title, playlist_url=playlist_url)

@app.route('/play/<path:video_id>')
@login_required
def play(video_id):
    video_id = urllib.parse.unquote(video_id)
    title = request.args.get('title', 'Loading video...')
    return render_template('play.html', video_id=video_id, title=title)

@app.route('/files')
@login_required
def files():
    finished = sorted([task for task in DOWNLOAD_TASKS.values() if task['status'] in ['completed', 'error']], key=lambda x: x.get('timestamp', 0), reverse=True)
    try:
        completed_files = sorted([f for f in os.listdir(DOWNLOAD_FOLDER) if not f.startswith('.')], reverse=True)
    except FileNotFoundError:
        completed_files = []
    return render_template('files.html', completed_files=completed_files, finished_tasks=finished[:5])

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_config = load_config()
        current_config['DOWNLOAD_PATH'] = request.form.get('download_path', DEFAULT_CONFIG['DOWNLOAD_PATH'])
        current_config['DEFAULT_AUDIO_FORMAT'] = request.form.get('audio_format', DEFAULT_CONFIG['DEFAULT_AUDIO_FORMAT'])
        new_password = request.form.get('password')
        if new_password:
            current_config['PASSWORD'] = new_password
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=4)
        flash('Settings saved! Please restart the server for all changes to take effect.', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', config=load_config())

@app.route('/progress/<task_id>')
@login_required
def progress_page(task_id):
    task = DOWNLOAD_TASKS.get(task_id)
    if not task:
        flash("Task not found or has been cleared.", "warning")
        return redirect(url_for('files'))
    return render_template('progress.html', task_id=task_id, title=task.get('title'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    password = app.config.get("PASSWORD")
    if not password:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if request.form.get('password') == password:
            session['logged_in'] = True
            flash('You were successfully logged in!', 'success')
            return redirect(request.args.get('next') or url_for('index'))
        else:
            flash('Invalid password provided.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out.', 'success')
    return redirect(url_for('login'))

def add_to_download_queue(video_id, format_code, title, is_video_only=False, is_audio_only=False, sub_lang=None):
    """Helper function to add a download job to the global queue."""
    task_id = str(uuid.uuid4())
    output_template = str(DOWNLOAD_FOLDER / '%(title).200s - [%(id)s].%(ext)s')
    base_command = ['yt-dlp', '-o', output_template, '--progress', '--restrict-filenames']
    
    if is_audio_only:
        command = base_command + ['-f', format_code, '-x', '--audio-format', app.config.get("DEFAULT_AUDIO_FORMAT", "m4a"), '--', video_id]
    else:
        final_format_code = f"{format_code}+bestaudio[ext=m4a]/best" if is_video_only else format_code
       
        command = base_command + ['-f', final_format_code, '--merge-output-format', 'mp4', '--ppa', 'FFmpegMerger:"-o \\"%(filepath)q\\""', '--', video_id]
    
    if sub_lang and sub_lang != 'none':
       
        command = command[:-2] + ['--write-subs', '--sub-lang', sub_lang, '--embed-subs'] + command[-2:]

    DOWNLOAD_TASKS[task_id] = {'status': 'downloading', 'stage': 'Waiting in queue...', 'progress': 0, 'title': title, 'id': task_id, 'timestamp': time.time()}
    DOWNLOAD_QUEUE.put((task_id, command, title))
    return title

@app.route('/download', methods=['POST'])
@login_required
def download():
    title = add_to_download_queue(
        video_id=request.form.get('video_id'),
        format_code=request.form.get('format_code'),
        title=request.form.get('title', 'Untitled'),
        is_video_only=request.form.get('is_video_only') == 'true',
        is_audio_only=request.form.get('is_audio_only') == 'true',
        sub_lang=request.form.get('sub_lang')
    )
    flash(f'"{title}" added to the download queue!', 'success')
    return redirect(url_for('files'))

@app.route('/quick_download_audio/<path:video_id>', methods=['POST'])
@login_required
def quick_download_audio(video_id):
    video_id = urllib.parse.unquote(video_id)
    info = get_video_info(video_id)
    if not info: return redirect(request.referrer or url_for('index'))
    title = add_to_download_queue(
        video_id=video_id,
        format_code='bestaudio[ext=m4a]/bestaudio',
        title=info.get('title', 'Untitled Audio'),
        is_audio_only=True
    )
    flash(f'"{title}" (Audio) added to the download queue!', 'success')
    return redirect(url_for('files'))

@app.route('/download_playlist', methods=['POST'])
@login_required
def download_playlist():
    video_ids = request.form.getlist('video_ids')
    if not video_ids:
        flash('You did not select any videos to download.', 'warning')
        return redirect(request.referrer)
    
    count = 0
    for video_id in video_ids:
        info = get_video_info(video_id)
        if info:
            add_to_download_queue(
                video_id=video_id,
                format_code='bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                title=info.get('title', f'Playlist Video {video_id}'),
                is_video_only=True
            )
            count += 1
    
    flash(f'Successfully added {count} videos to the download queue!', 'success')
    return redirect(url_for('files'))

@app.route('/api/delete_file', methods=['POST'])
@login_required
def delete_file():
    filename = request.form.get('filename')
    if not filename: return jsonify({'success': False, 'error': 'No filename provided.'}), 400
    try:
        file_path = DOWNLOAD_FOLDER.joinpath(filename).resolve()
        if not file_path.is_file() or DOWNLOAD_FOLDER.resolve() not in file_path.parents:
            raise FileNotFoundError("Invalid path or file does not exist.")
        os.remove(file_path)
        flash(f'"{filename}" was deleted successfully.', 'success')
        return jsonify({'success': True})
    except Exception as e:
        flash(f'Error deleting file: {e}', 'danger')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_video_info/<path:video_id>')
@login_required
def api_get_video_info(video_id):
    video_id = urllib.parse.unquote(video_id)
    info = get_video_info(video_id)
    if not info: return jsonify({'error': "Failed to retrieve video metadata."}), 404
    save_history_item(info)
    return jsonify({'title': info.get('title', 'Untitled')})

@app.route('/api/get_stream_url/<path:video_id>')
@login_required
def api_get_stream_url(video_id):
    video_id = urllib.parse.unquote(video_id)
    command = ['yt-dlp', '-g', '-f', 'best[vcodec!=none][acodec!=none]', '--', video_id]
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True, timeout=20)
        stream_url = process.stdout.strip().split('\n')[0]
        if not stream_url.startswith('http'): return jsonify({'stream_url': None, 'playback_supported': False})
        return jsonify({'stream_url': stream_url, 'playback_supported': True})
    except: return jsonify({'stream_url': None, 'playback_supported': False})

@app.route('/api/get_subtitles/<path:video_id>')
@login_required
def api_get_subtitles(video_id):
    video_id = urllib.parse.unquote(video_id)
    try:
        sub_command = ['yt-dlp', '--list-subs', '--', video_id]
        subs_proc = subprocess.run(sub_command, capture_output=True, text=True, timeout=30)
        available_subs = sorted(list(set(re.findall(r'^([a-zA-Z-]+)', subs_proc.stdout, re.MULTILINE))))
        return jsonify({'subtitles': available_subs})
    except: return jsonify({'error': 'Subtitle check failed or timed out.'}), 500

@app.route('/api/get_active_tasks')
@login_required
def api_get_active_tasks():
    active_tasks = [task for task in DOWNLOAD_TASKS.values() if task['status'] in ['queued', 'downloading']]
    return jsonify(active_tasks)

@app.route('/status/<task_id>')
@login_required
def task_status(task_id):
    return jsonify(DOWNLOAD_TASKS.get(task_id, {'status': 'not_found'}))

@app.route('/download_file/<path:filename>')
@login_required
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/api/check_update')
def check_update():
    try:
        pypi_url = f"https://pypi.org/pypi/TubeZ/json"
        response = requests.get(pypi_url, timeout=5)
        response.raise_for_status()
        latest = response.json()['info']['version']
        update = parse_version(latest) > parse_version(__version__)
        return jsonify({'current_version': __version__, 'latest_version': latest, 'update_available': update})
    except: return jsonify({'error': 'Could not connect to update server.'}), 503

@app.route('/api/get_queue_count')
@login_required
def api_get_queue_count():
    """Returns the number of tasks currently in the queue or being downloaded."""
    count = DOWNLOAD_QUEUE.qsize() + sum(1 for task in DOWNLOAD_TASKS.values() if task['status'] == 'downloading')
    return jsonify({'count': count})
