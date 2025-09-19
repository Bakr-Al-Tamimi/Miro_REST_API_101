import os
import time
import threading
import logging
import random
from pathlib import Path
from urllib.parse import quote
import keyboard
import requests
from dotenv import load_dotenv
from flask import Flask, make_response, send_from_directory
from pyngrok import ngrok, conf
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 1. Configuration ---
load_dotenv()

MIRO_ACCESS_TOKEN = os.getenv("MIRO_ACCESS_TOKEN")
MIRO_BOARD_ID = os.getenv("MIRO_BOARD_ID")
WATCH_FOLDER = os.getenv("WATCH_FOLDER")
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
PORT = 5001

# Miro image positioning settings
MIRO_RANDOM_X_RANGE = (-1500, 1500)
MIRO_RANDOM_Y_RANGE = (-1000, 1000)

# Supported image file extensions
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'}

# --- 2. Logging Setup ---
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# --- 3. Miro API Client ---
class MiroClient:
    """A client for interacting with the Miro REST API."""

    def __init__(self, access_token: str, board_id: str):
        self.api_url = f"https://api.miro.com/v2/boards/{board_id}"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def upload_image_from_url(self, image_url: str):
        """Posts a new image to the board from a public URL."""
        url = f"{self.api_url}/images"
        data = {
            "data": {"url": image_url},
            "position": {
                "x": random.randint(*MIRO_RANDOM_X_RANGE),
                "y": random.randint(*MIRO_RANDOM_Y_RANGE),
                "origin": "center",
            },
        }

        try:
            logging.debug(f"Sending POST request to Miro API: {url} with data: {data}")
            response = self.session.post(url, json=data)
            response.raise_for_status()
            logging.info(f"✅ Successfully sent {Path(image_url).name} to Miro board!")
            logging.debug(f"Miro API response: {response.json()}")
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Failed to upload image to Miro: {e}", exc_info=True)
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Miro API error response: {e.response.text}")


# --- 4. File System Watcher ---
class ImageFileHandler(FileSystemEventHandler):
     """Handles file system events for new images."""
 
     def __init__(self, public_url_base: str, miro_client: MiroClient):
         self.public_url_base = public_url_base
         self.miro_client = miro_client
 
     def on_created(self, event):
         if event.is_directory:
             return
 
         file_path = Path(event.src_path)
         if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
             logging.info(f"🔎 New image detected: {file_path.name}")
             # Give the file a moment to be fully written to disk
             time.sleep(1)
             # URL-encode the filename to handle special characters
             encoded_filename = quote(file_path.name)
             image_public_url = f"{self.public_url_base}/images/{encoded_filename}"
             logging.info(f"Constructed public URL for Miro: {image_public_url}")
             self.miro_client.upload_image_from_url(image_public_url)


# --- 5. Local Web Server (for ngrok) ---
app = Flask(__name__)

@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serves files from the watched folder and adds a header to bypass ngrok warnings."""
    response = make_response(send_from_directory(WATCH_FOLDER, filename))
    # This header is a signal to the ngrok agent to not show the interstitial page,
    # which can block API consumers like Miro from fetching the image.
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

def run_flask_app():
     """Runs the Flask app on a local port."""
     # Use a production-ready WSGI server for better performance and stability
     from waitress import serve
     serve(app, host="127.0.0.1", port=PORT)


# --- 6. Main Execution ---
def validate_config():
    """Checks for required environment variables at startup."""
    # As of recent ngrok policy changes, an authtoken is now required for all users.
    required_vars = ["MIRO_ACCESS_TOKEN", "MIRO_BOARD_ID", "WATCH_FOLDER", "NGROK_AUTHTOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logging.error("❌ Critical configuration missing. Check your .env file.")
        logging.error(f"   Missing required variables: {', '.join(missing_vars)}")
        if "NGROK_AUTHTOKEN" in missing_vars:
            logging.error("   NOTE: ngrok now requires an authtoken. Please get one from https://dashboard.ngrok.com/get-started/your-authtoken")
        exit(1)
    logging.info("✅ Configuration validated successfully.")


if __name__ == "__main__":
     validate_config()

     if not Path(WATCH_FOLDER).exists():
         logging.info(f"📂 Creating watch folder at: {WATCH_FOLDER}")
         Path(WATCH_FOLDER).mkdir(parents=True, exist_ok=True)
 
     # Set up and start ngrok
    # The validate_config function now ensures the token exists.
     conf.set_default(conf.PyngrokConfig(ngrok_path="c:\\BT-DTC\\CODE\\MiroREST_API\\Miro_REST_API_101\\miro-sync-env\\Scripts\\ngrok.exe"))
     ngrok.set_auth_token(NGROK_AUTHTOKEN)
     logging.info("🚀 Starting ngrok tunnel...")
     public_url = ngrok.connect(PORT).public_url
     logging.info(f"🌍 Public URL created: {public_url}")
     logging.debug(f"ngrok tunnel details: {ngrok.get_tunnels()}")

     # Instantiate the Miro client
     miro_client = MiroClient(access_token=MIRO_ACCESS_TOKEN, board_id=MIRO_BOARD_ID)

     # Start the Flask web server in a separate thread
     flask_thread = threading.Thread(target=run_flask_app, daemon=True)
     flask_thread.start()
     logging.info(f"🚀 Local web server started on port {PORT} in a background thread.")
 
     # Set up and start the file watcher
     event_handler = ImageFileHandler(public_url, miro_client)
     observer = Observer()
     observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
     observer.start()
     logging.info(f"👀 Watching for new images in: {WATCH_FOLDER}")
     
     print("\n✨ Application is running. Add images to the folder to upload them to Miro.")
     print("   Press Ctrl+Q to stop.\n")

     # Create a shutdown event
     shutdown_event = threading.Event()

     def shutdown():
         if not shutdown_event.is_set():
             shutdown_event.set()
             logging.info("\n🛑 Shutting down...")
             observer.stop()
             ngrok.disconnect(public_url)
             logging.info("👋 Goodbye!")
             observer.join()

     # Set up the hotkey
     keyboard.add_hotkey('ctrl+q', shutdown)

     # Keep the main thread alive until the shutdown event is set
     shutdown_event.wait()