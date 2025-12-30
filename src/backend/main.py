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
import base64
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

from contextlib import asynccontextmanager

# Global system state
system = None
model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'action.h5')
actions = np.array(['Hello', 'ThankYou', 'Help', 'Please'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    global system
    print(f"[Startup] Loading system from: {model_path}")
    try:
        # CLOUD MODE: Pass capture_source=None so the server doesn't try to open a webcam.
        system = SignLanguageSystem(model_path, actions, capture_source=None)
        print("[Startup] System loaded successfully.")
    except Exception as e:
        print(f"[Startup] CRITICAL ERROR: Failed to load system: {e}")
        # We don't exit here so the server can at least start and report the error
    
    yield
    
    print("[Shutdown] Releasing system...")
    if system:
        system.release()

app = FastAPI(lifespan=lifespan)

def generate_frames():
    """Video streaming generator function (Legacy Local Mode)."""
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
    """Video streaming route (Legacy Local Mode)."""
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Wait for data from Client
            data_in = await websocket.receive_text()
            
            try:
                # Check if it's JSON (Cloud Mode)
                packet = json.loads(data_in)
                
                if "image" in packet:
                    # CLOUD MODE: Client sends image
                    # 1. Decode Base64
                    encoded_data = packet["image"].split(',')[1]
                    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # 2. Process
                    _, sentence, pred_data = system.process_frame(img)
                    
                    # 3. Respond
                    response = {
                        "sentence": " ".join(sentence),
                        "prediction": -1, # Deprecated for frontend, use class name below if needed
                        "confidence": pred_data["confidence"]
                    }
                    if pred_data["class"]:
                         # Find index for frontend compatibility if needed, or just send text
                         # Frontend expects 'prediction' index. Let's find it.
                         # This is a bit inefficient (search), but safe.
                         idx = np.where(actions == pred_data["class"])[0]
                         if len(idx) > 0:
                             response["prediction"] = int(idx[0])
                             
                    await websocket.send_json(response)
                    
            except json.JSONDecodeError:
                # Legacy polling fallback (if client sends empty triggers or old protocol)
                # But we really expect JSON now.
                pass
            
    except Exception as e:
        print(f"WebSocket Error: {e}")
