# `miro_image_uploader.py`: Automatic Image Sync to Miro

## Overview

This Python script creates an automated workflow that watches a specific local folder. When a new image is added to that folder, the script automatically uploads a copy of it to a designated Miro board.

It uses the Miro REST API, which requires images to be available at a public URL. The script cleverly solves this by running a temporary local web server (via Flask and Waitress) and exposing it to the internet with `ngrok`.

## Features

- **Automatic Uploads**: Monitors a folder and uploads new images without manual intervention.
- **Robust Error Handling**: Uses structured logging to provide clear feedback on successes and failures.
- **Configuration Validation**: Fails fast on startup if essential configuration is missing.
- **URL Safe**: Automatically handles filenames with spaces or special characters.
- **Production-Ready**: Uses a stable WSGI server (`waitress`) instead of Flask's development server.

## Setup and Installation

To get the script running, follow these steps.

### 1. Create a Virtual Environment

Isolating project dependencies is a best practice. Create and activate a virtual environment:

```bash
# Navigate to the project directory
cd /path/to/Miro_REST_API_101

# Create the virtual environment
python -m venv miro-sync-env

# Activate the environment
# On Windows (PowerShell):
.\miro-sync-env\Scripts\activate
# On macOS/Linux:
source miro-sync-env/bin/activate
```

### 2. Install Dependencies

With the virtual environment active, install all required packages from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 3. Configure Credentials

Rename the example `DOTenvFILE.txt` to `.env` and fill in your specific details.

| Variable            | Required | Description                                                                                             |
|---------------------|----------|---------------------------------------------------------------------------------------------------------|
| `MIRO_ACCESS_TOKEN` | Yes      | Your Miro Developer API access token.                                                                   |
| `MIRO_BOARD_ID`     | Yes      | The ID of the target Miro board, found in the board's URL.                                              |
| `WATCH_FOLDER`      | Yes      | The absolute path to the local folder to monitor for new images. Use forward slashes (`/`).             |
| `NGROK_AUTHTOKEN`   | Yes      | Your ngrok authentication token. Required for all ngrok usage, even on free plans.                      |

## How It Works

1. **Initialization & Validation**: The script starts, reads the configuration from `.env`, and performs a "fail-fast" check to ensure all required variables (`MIRO_ACCESS_TOKEN`, `MIRO_BOARD_ID`, `WATCH_FOLDER`) are present. It then creates the `WATCH_FOLDER` if it doesn't exist.
2. **Local Server**: A production-grade `waitress` WSGI server is started in a background thread. It uses a `Flask` application to serve files from the `WATCH_FOLDER` over a local network port.
3. **Public Tunnel**: The `ngrok` service is initiated to create a secure, public URL that tunnels traffic directly to the local server. This makes images on your local machine temporarily accessible to the public internet.
4. **Folder Monitoring**: The `watchdog` library begins actively monitoring the `WATCH_FOLDER` for any newly created files.
5. **Image Detection & Upload**:
    - When a new file is added, `watchdog` triggers an event.
    - The script checks if the file has a supported image extension (e.g., `.png`, `.jpg`).
    - It **URL-encodes the filename** to safely handle special characters and constructs a public URL (e.g., `https://<ngrok_url>/images/new%20photo.jpg`).
    - The script sends a `POST` request to the Miro REST API with this public URL.
6. **Image Placement**: Miro's servers fetch the image from the `ngrok` URL and place it as a new widget on the specified Miro board at a randomized position.

## Core Components

The script integrates several key libraries to achieve its functionality.

| Component           | Library         | Role                                                                                                     |
|---------------------|-----------------|----------------------------------------------------------------------------------------------------------|
| WSGI Server         | `waitress`      | Runs a production-ready server to handle HTTP requests for the Flask app.                                |
| Web Framework       | `Flask`         | Provides routing to serve image files from the local folder.                                             |
| Public Tunnel       | `pyngrok`       | Exposes the local server to the internet with a temporary public URL.                                    |
| File Monitoring     | `watchdog`      | Observes the specified folder for file system events (specifically file creation).                       |
| API Communication   | `requests`      | Handles making the `POST` request to the Miro REST API.                                                  |
| Environment Mgmt.   | `python-dotenv` | Loads configuration variables from the `.env` file.                                                    |
| Structured Logging  | `logging`       | Provides formatted, level-based logging for diagnostics and error reporting.                           |

## How ngrok helps

There is no need to manually start an ngrok agent on your local machine before running the Python script. The beauty of the pyngrok library used in this script is that it manages the ngrok process for you.  

Behind the scenes: When your script calls ngrok.connect(PORT), the pyngrok library checks if the ngrok executable is available. If not, it downloads it for you. pyngrok then starts the ngrok executable as a background process. It's this background process (the "agent") that tries to connect to the ngrok cloud service to create the public tunnel.

## Summary

This script provides a robust and automated solution for syncing images from a local folder directly to a Miro board. By combining a local production-ready web server with a public tunnel, it elegantly works around the Miro API's requirement for publicly hosted image URLs, enabling a seamless and stable local-to-cloud workflow.

## Known Issues

Everything looks like it works, and even Miro says it received the pictures susccessfully, but the pictures do not show on the Miro Board!

That is a very confusing and frustrating situation! When your logs say everything is working perfectly, but the end result isn't there, it often points to a subtle issue in how the different services are communicating.

After lots of confudion, this what's actually had been happening : 

###The Root Cause: The ngrok Interstitial Page

The free tier of ngrok has a security feature where it shows a warning page to visitors, who must click a "Visit Site" button before they can see the content.

Here's the sequence of events

This Python script correctly detects the image and sends the public ngrok URL to the Miro API.
Miro's API server receives the URL and sends back a "Success" response to your script. This is why your log says ✅ Successfully uploaded.
Here's the problem: In the background, Miro's servers then try to download the image from your ngrok URL. However, instead of getting the image, they get the ngrok warning page. Since Miro's servers are automated, they can't "click" the button, so they fail to download the image, and nothing appears on your board.
The Solution
We can fix this by adding a special header to the files served by your local Flask web server. This header, ngrok-skip-browser-warning, is a direct instruction to the ngrok agent on your machine to not show the warning page for that specific request. This allows API consumers like Miro to access the file directly.

I've implemented this change for you below. It involves importing make_response from Flask and modifying the serve_image function to add the necessary header.

```python
from flask import Flask, send_from_directory, make_response

# ... other code ...

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serves an image and adds a header to bypass the ngrok warning page."""
    # Create a response object from the file
    response = make_response(send_from_directory(app.config["UPLOAD_FOLDER"], filename))
    
    # This header is the key to the solution.
    # It tells the ngrok agent not to show the interstitial "warning" page.
    response.headers["ngrok-skip-browser-warning"] = "true"
    
    return response
```