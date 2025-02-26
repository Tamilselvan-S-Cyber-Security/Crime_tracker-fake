import os
import json
from datetime import datetime
import base64

# Create data directory if it doesn't exist
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def save_capture(image_data, audio_data, timestamp):
    """Save captured data to storage"""
    # Create capture directory
    capture_dir = os.path.join(DATA_DIR, timestamp)
    os.makedirs(capture_dir, exist_ok=True)

    # Save image
    image_path = os.path.join(capture_dir, "image.jpg")
    with open(image_path, "wb") as f:
        f.write(image_data.getbuffer())

    # Save audio if exists
    audio_path = None
    if audio_data:
        audio_path = os.path.join(capture_dir, "audio.wav")
        with open(audio_path, "wb") as f:
            f.write(audio_data)

    # Save metadata
    metadata = {
        "timestamp": timestamp,
        "has_audio": audio_data is not None,
        "capture_time": datetime.now().isoformat(),
        "file_info": {
            "image_size": os.path.getsize(image_path),
            "audio_size": os.path.getsize(audio_path) if audio_path else 0
        }
    }

    metadata_path = os.path.join(capture_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

def get_all_captures():
    """Retrieve all captures from storage"""
    captures = []

    # List all capture directories
    for timestamp in sorted(os.listdir(DATA_DIR), reverse=True):  # Most recent first
        capture_dir = os.path.join(DATA_DIR, timestamp)

        if not os.path.isdir(capture_dir):
            continue

        # Read image
        image_path = os.path.join(capture_dir, "image.jpg")
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Read audio if exists
            audio_data = None
            audio_path = os.path.join(capture_dir, "audio.wav")
            if os.path.exists(audio_path):
                with open(audio_path, "rb") as f:
                    audio_data = f.read()

            # Read metadata
            metadata_path = os.path.join(capture_dir, "metadata.json")
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)

            captures.append({
                "timestamp": timestamp,
                "image": image_data,
                "audio": audio_data,
                "metadata": metadata
            })

    return captures