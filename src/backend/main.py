# d:/aiProject/src/backend/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import asyncio
import json
import os
import sys

# Ensure d:/aiProject/src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import SignLanguageSystem
import numpy as np

app = FastAPI()

# CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engine
model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'action.h5')
actions = np.array(['Hello', 'ThankYou', 'Help', 'Please'])

print(f"Loading system from: {model_path}")
system = SignLanguageSystem(model_path, actions)

@app.on_event("shutdown")
def shutdown_event():
    system.release()

def generate_frames():
    """Video streaming generator function."""
    while True:
        img, _, _ = system.get_frame()
        if img is None:
            continue
        
        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        
        # MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.get("/video_feed")
async def video_feed():
    """Video streaming route. Put this in the src of an img tag."""
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # We don't need to process frame here (it's done in video loop or we can decouple)
            # Better architecture: The generate_frames loop drives the system.
            # But the WebSocket needs access to the latest result.
            
            # Simple polling for this demo (low latency enough)
            # In a prod system, we'd use an event or queue from the engine
            
            # Accessing the latest prediction from system state
            # Note: This relies on generate_frames being active (i.e. someone watching the video)
            # If no video watcher, the camera reads might stall if we don't thread them independently.
            # But ThreadedCamera handles the reading. We need to CALL get_frame() somewhere.
            
            # To fix "Zombie" state if no video feed:
            # We can rely on the fact that the camera thread is running.
            # But get_frame() triggers the PREDICTION queueing.
            # So we need to ensure get_frame() is called. 
            # For this MVP, we assume the Frontend loads both Video and WS.
            
            await asyncio.sleep(0.05) # 20 Hz update for UI
            
            data = {
                "sentence": " ".join(system.sentence),
                "prediction": int(system.predictions[-1]) if system.predictions else -1,
                # "class": actions[system.predictions[-1]] if system.predictions else "",
                # We can construct a cleaner object
            }
            
            # Get latest strong prediction (handled in engine logic essentially)
            # Let's peek at the engine internal state or return it from get_frame
            # For now, let's just send the sentence and latest "live" class
            
            await websocket.send_json(data)
            
    except Exception as e:
        print(f"WebSocket Error: {e}")
