# src/tubez/cli.py

import argparse
import logging

# Use a relative import to get the app object and config from __init__.py
from . import app, DOWNLOAD_FOLDER, CONFIG_DIR

def main():
    """The main entry point for the command line interface."""
    
    # --- NEW: Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Run the TubeZ web server.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    parser.add_argument(
        '--debug',
        action='store_true', # This makes it a flag, e.g., `tubez --debug`
        help="""Enable debug mode.
This will:
  - Show detailed request logs in the terminal.
  - Automatically reload the server when code changes.
  - Provide detailed error pages in the browser."""
    )
    args = parser.parse_args()

    # --- NEW: Conditional Logic based on the --debug flag ---
    if args.debug:
        # --- DEBUG MODE (Verbose) ---
        print("⚠️  Starting in DEBUG mode. Auto-reloader is active.")
        print(f"📂 Downloads will be saved in: {DOWNLOAD_FOLDER}")
        print(f"🌐 Open http://127.0.0.1:8089 in your browser")
        # app.run with debug=True enables all the verbose features
        app.run(host='0.0.0.0', port=8089, threaded=True, debug=True)
    else:
        # --- NORMAL MODE (Silent) ---
        # Silence the default Werkzeug logger to stop request logs
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        print("🚀 TubeZ Server starting...")
        print(f"📂 Downloads will be saved in: {DOWNLOAD_FOLDER}")
        print(f"📂 History & Config is in: {CONFIG_DIR}")
        print(f"🌐 Open http://127.0.0.1:8089 in your browser")
        print("Press CTRL+C to quit.")
        
        # Run the production-ready server (we use Waitress for this)
        # Waitress is a production-quality WSGI server, better than Flask's default
        try:
            from waitress import serve
            serve(app, host='0.0.0.0', port=8089, threads=8)
        except ImportError:
            print("\n[WARNING] 'waitress' is not installed. Falling back to the Flask development server.")
            print("For a better experience, please run: pip install waitress\n")
            app.run(host='0.0.0.0', port=8089, threaded=True, debug=False)


if __name__ == '__main__':
    main()
