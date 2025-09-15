import os
import json
from pathlib import Path
from flask import Flask

# --- Package Information ---
__version__ = "1.0.1" # Version bump for new features

# --- Default Configuration ---
DEFAULT_CONFIG = {
    "DOWNLOAD_PATH": str(Path.home() / 'Downloads' / 'TubeX'),
    "PORT": 8089,
    "DEFAULT_AUDIO_FORMAT": "m4a",
    "THEME": "dark",
    "PASSWORD": "" # Empty means no password protection
}

# --- User-specific Paths ---
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / '.config' / 'tubex'
CONFIG_FILE = CONFIG_DIR / 'config.json'
HISTORY_FILE = CONFIG_DIR / 'history.json'

# --- Configuration Loading ---
def load_config():
    """Loads user config, falling back to defaults."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            user_config = json.load(f)
        # Ensure all keys are present, add defaults for missing ones
        config = DEFAULT_CONFIG.copy()
        config.update(user_config)
        return config
    except (json.JSONDecodeError, TypeError):
        return DEFAULT_CONFIG

# --- Load Config and Create App Instance ---
config = load_config()
DOWNLOAD_FOLDER = Path(config['DOWNLOAD_PATH'])
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'a_very_secret_key_change_me'
app.config.update(config) # Make config accessible in routes via app.config

# --- Import server routes after app creation ---
from . import server
