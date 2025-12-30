# d:/aiProject/src/engine.py
import cv2
import numpy as np
import threading
import queue
import time
import os
from hand_tracking import HandDetector
from feature_extractor import extract_features

class ThreadedCamera:
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.q = queue.Queue()
        self.status = False
        self.frame = None
        self.stopped = False
        
        self.thread = threading.Thread(target=self._reader)
        self.thread.daemon = True
        self.thread.start()

    def _reader(self):
        while not self.stopped:
            status, frame = self.capture.read()
            if not status:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)
            self.status = status
            self.frame = frame

    def read(self):
        if not self.q.empty():
             return self.status, self.q.get()
        return self.status, self.frame

    def release(self):
        self.stopped = True
        self.capture.release()

class PredictionEngine(threading.Thread):
    def __init__(self, model_path, actions):
        super().__init__()
        self.model_path = model_path
        self.actions = actions
        self.input_queue = queue.Queue()
        self.latest_result = None 
        self.daemon = True
        self.running = True
        self.start()

    def run(self):
        print("[PredictionEngine] Loading TensorFlow...")
        import tensorflow as tf
        model = tf.keras.models.load_model(self.model_path)
        print("[PredictionEngine] Model Loaded.")
        
        while self.running:
            try:
                sequence = self.input_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            try:
                input_data = np.expand_dims(sequence, axis=0)
                res = model(input_data, training=False).numpy()[0]
                self.latest_result = res
            except Exception as e:
                print(f"[PredictionEngine] Error: {e}")
            
            self.input_queue.task_done()

    def predict_async(self, sequence):
        if not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
            except queue.Empty:
                pass
        self.input_queue.put(sequence)

    def get_result(self):
        return self.latest_result

    def stop(self):
        self.running = False


class SignLanguageSystem:
    """
    Facade to manage the Camera, HandDetector, and PredictionEngine together.
    Useful for both the CLI script and the Web Backend.
    """
    def __init__(self, model_path, actions, capture_source=0):
        self.detector = HandDetector(detectionCon=0.8, maxHands=1, modelComplexity=0)
        self.camera = None
        if capture_source is not None:
             self.camera = ThreadedCamera(capture_source)
        
        self.predictor = PredictionEngine(model_path, actions)
        
        self.sequence = []
        self.sequence_length = 30
        self.actions = actions
        
        # Stability / Logic state
        self.predictions = []
        self.sentence = []
        self.threshold = 0.85 
        
        # Per-class thresholds to prevent misfires
        self.class_thresholds = {
            "Help": 0.95,
            "Please": 0.85,
            "Hello": 0.85,
            "ThankYou": 0.85
        }
        
    def process_frame(self, img):
        """
        Core pipeline: Detection -> Features -> Prediction -> Logic.
        Input: img (OpenCV frame)
        Returns: (processed_img, sentence, prediction_data)
        """
        if img is None:
             return None, self.sentence, {}

        # Hand Tracking
        img = self.detector.findHands(img)
        lmList = self.detector.findPosition(img, draw=False)
        
        if lmList:
            features = extract_features(lmList)
            self.sequence.append(features)
            self.sequence = self.sequence[-self.sequence_length:]
            
            if len(self.sequence) == self.sequence_length:
                self.predictor.predict_async(self.sequence)
        
        # Check Result
        res = self.predictor.get_result()
        prediction_data = {"class": None, "confidence": 0.0}
        
        if res is not None:
            best_idx = np.argmax(res)
            conf = res[best_idx]
            
            self.predictions.append(best_idx)
            if len(self.predictions) > 8:
                # Optimized Stability: 8 frame hold required (~0.3s)
                last_n = self.predictions[-8:]
                if np.unique(last_n)[0] == best_idx: 
                    current_action = self.actions[best_idx]
                    required_conf = self.class_thresholds.get(current_action, self.threshold)
                    
                    if conf > required_conf: 
                        prediction_data = {"class": current_action, "confidence": float(conf)}
                        
                        # Sentence Logic
                        if len(self.sentence) > 0: 
                            if current_action != self.sentence[-1]: 
                                self.sentence.append(current_action)
                        else:
                            self.sentence.append(current_action)
                            
            if len(self.sentence) > 5:
                self.sentence = self.sentence[-5:]
                
        return img, self.sentence, prediction_data

    def get_frame(self):
        """
        Legacy: Captures from local USB camera.
        """
        if self.camera is None:
             raise RuntimeError("Camera not initialized in this instance")

        success, img = self.camera.read()
        if not success or img is None:
            return None, self.sentence, {}
            
        # Mirror for local view
        img = cv2.flip(img, 1)
        
        return self.process_frame(img)

    def release(self):
        if self.camera:
            self.camera.release()
        self.predictor.stop()
