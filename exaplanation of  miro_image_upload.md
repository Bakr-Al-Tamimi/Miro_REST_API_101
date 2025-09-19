# `miro_image_uploader.py`: Automatic Image Sync to Miro

## Overview

This Python script creates an automated workflow that watches a specific local folder. When a new image is added to that folder, the script automatically uploads it to a designated Miro board.

It uses the Miro REST API, which requires images to be available at a public URL. The script cleverly solves this by running a temporary local web server and exposing it to the internet with `ngrok`.

## Features

- **Automatic Uploads**: Monitors a folder and uploads new images without manual intervention.
- **Detailed Logging**: Provides debug-level logging for deep analysis of `ngrok` and Miro API interactions.
- **Clean Shutdown**: Uses a `Ctrl+Q` hotkey for a graceful shutdown, preventing orphaned `ngrok` processes.
- **Robust Configuration**: Includes validation for all required credentials and settings.
- **URL Safe**: Automatically handles filenames with spaces or special characters.

---

## 1. Full Setup and Configuration Guide

This guide contains everything you need to get the script running, from installation to final configuration.

### Step 1.1: Create a Virtual Environment

Isolating project dependencies is a best practice. From the project directory, create and activate a virtual environment:

```bash
# Create the virtual environment
python -m venv miro-sync-env

# Activate the environment (on Windows PowerShell)
.\miro-sync-env\Scripts\activate
```

### Step 1.2: Install Dependencies

With the virtual environment active, install all required packages from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### Step 1.3: Configure the Miro Application

The script needs to authenticate with Miro as a specific application.

1.  **Create a Miro App**:
    *   Go to your [Miro Profile settings](https://miro.com/app/settings/user-profile/apps).
    *   Select the **Your apps** tab and click **Create new app**.
    *   Give your app a name (e.g., "Image Uploader Script").
    *   Scroll to the **Permissions** section and select **`boards:write`**. This is essential.

2.  **Get Your Access Token**:
    *   On the same app configuration page, click **"Install app and get OAuth token"**.
    *   Follow the prompts to install it for your team.
    *   At the end, Miro will display an **access token**. This is the token you need. Copy it immediately.

3.  **Install the App on Your Board**:
    *   Open the Miro board where you want the images to appear.
    *   Click the board name (top-left) -> **Apps** -> find your new app and click it.
    *   Click **"Install app and authorize"**.

### Step 1.4: Configure the `.env` File

This file stores all your credentials. If it doesn't exist, rename `DOTenvFILE.txt` to `.env`. Then, fill in the following values:

| Variable            | Required | Description                                                                                                                               |
|---------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `MIRO_ACCESS_TOKEN` | Yes      | The access token you generated in the previous step.                                                                                      |
| `MIRO_BOARD_ID`     | Yes      | The ID of your target Miro board. **This is the most common point of error.** Get it from the board's URL (e.g., `uXjVJG-eINY=` from `https://miro.com/app/board/uXjVJG-eINY=/`). |
| `WATCH_FOLDER`      | Yes      | The absolute path to the local folder to monitor for new images (e.g., `C:/Users/YourUser/Desktop/MiroUploads`). Use forward slashes (`/`). |
| `NGROK_AUTHTOKEN`   | Yes      | Your ngrok authentication token from the [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).                                                              |

---

## 2. How to Run the Script

1.  **Activate the virtual environment**: `.\miro-sync-env\Scripts\activate`
2.  **Run the script**: `python .\miro_image_uploader.py`
3.  **Add images**: Drop image files into the folder you defined as your `WATCH_FOLDER`.
4.  **Stop the script**: Press **`Ctrl+Q`** to shut down gracefully.

---

## 3. Troubleshooting

If you encounter issues, check here first.

### Problem: Images don't appear on my board.

This is usually one of two issues:

*   **Solution 1: Incorrect Board ID (Most Likely)**
    The script is successfully uploading images, but to the wrong board. Double-check that the `MIRO_BOARD_ID` in your `.env` file exactly matches the ID of the board you are looking at in your browser.

*   **Solution 2: Image is Off-Screen**
    The script places images at a random position. On your Miro board, use the "Zoom to fit" feature (often `Ctrl+1`) to see the entire canvas. Your image may be far from the center.

### Problem: Script crashes with `ERR_NGROK_108` ("1 simultaneous ngrok agent sessions").

*   **Cause**: This happens when a previous `ngrok` process was not shut down correctly. The free tier of ngrok only allows one session at a time.
*   **Immediate Fix**: Go to your [ngrok agent sessions dashboard](https://dashboard.ngrok.com/agents/sessions) and click "Stop" on any active sessions.
*   **Prevention**: Always use the **`Ctrl+Q`** hotkey to stop the script. This ensures a clean shutdown.

### Problem: Miro API returns a `401 Unauthorized` error.

*   **Cause**: Your `MIRO_ACCESS_TOKEN` is incorrect, has expired, or the app does not have the right permissions.
*   **Solution**: Go back through **Step 1.3** and **Step 1.4**. Ensure your app has `boards:write` permission, that it's installed on the correct board, and that the token in your `.env` file is correct.
