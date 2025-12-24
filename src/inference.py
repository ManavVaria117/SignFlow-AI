import cv2
import numpy as np
import os
import time
import threading
import queue
import win32com.client

# NOTE: TensorFlow is imported inside the thread to avoid bottlenecks and conflicts
# import tensorflow as tf 
from hand_tracking import HandDetector
from feature_extractor import extract_features

# --- Threaded Camera Class ---
class ThreadedCamera:
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Mimimize buffer for lowest latency
        self.q = queue.Queue()
        self.status = False
        self.frame = None
        
        # Start reading thread
        self.thread = threading.Thread(target=self._reader)
        self.thread.daemon = True
        self.thread.start()

    def _reader(self):
        while True:
            status, frame = self.capture.read()
            if not status:
                break
            
            # Keep only the latest frame
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)
            self.status = status
            self.frame = frame

    def read(self):
        # Non-blocking read (returns latest or None if not ready)
        if not self.q.empty():
             return self.status, self.q.get()
        return self.status, self.frame

    def release(self):
        self.capture.release()

# --- Prediction Engine Thread ---
class PredictionEngine(threading.Thread):
    def __init__(self, model_path, actions):
        super().__init__()
        self.model_path = model_path
        self.actions = actions
        self.input_queue = queue.Queue()
        self.latest_result = None # (prob_array or None)
        self.daemon = True
        self.running = True
        self.start()

    def run(self):
        # Import TF here to keep main thread clean and fast
        print("[PredictionEngine] Loading TensorFlow...")
        import tensorflow as tf
        model = tf.keras.models.load_model(self.model_path)
        print("[PredictionEngine] Model Loaded. Ready.")
        
        while self.running:
             # Wait for input
            sequence = self.input_queue.get()
            
            try:
                # Predict
                input_data = np.expand_dims(sequence, axis=0)
                # Training=False is faster
                res = model(input_data, training=False).numpy()[0]
                self.latest_result = res
            except Exception as e:
                print(f"[PredictionEngine] Error: {e}")
            
            self.input_queue.task_done()

    def predict_async(self, sequence):
        # If queue is full (busy), empty it so we only process latest
        if not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
            except queue.Empty:
                pass
        self.input_queue.put(sequence)

    def get_result(self):
        return self.latest_result

# --- TTS Worker Thread ---
class TTSThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.daemon = True 
        self.start()

    def run(self):
        # Initialize COM library for this thread
        try:
            import pythoncom
            pythoncom.CoInitialize() 
        except ImportError:
            pass 

        try:
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            # Increase speed slightly for "Zap Quick" feel
            self.speaker.Rate = 2 
        except Exception:
            print("TTS Init Failed")
            self.speaker = None
        
        while True:
            text = self.queue.get()
            if text is None: break 
            
            try:
                if self.speaker:
                    # Async call to speaker so it doesn't block THIS thread either (if possible)
                    # 1 = SVSFlagsAsync
                    self.speaker.Speak(text, 1)
            except Exception as e:
                print(f"TTS Error: {e}")
            
            self.queue.task_done()

    def speak(self, text):
        self.queue.put(text)

# Initialize TTS
tts_worker = TTSThread()

# --- Main Application ---
def main():
    model_path = os.path.join('d:/aiProject/models', 'action.h5')
    if not os.path.exists(model_path):
        print("Model not found.")
        return

    actions = np.array(['Hello', 'ThankYou', 'Help', 'Please'])

    # Start Prediction Engine
    predictor = PredictionEngine(model_path, actions)

    # Initialize Vision - Lite Mode
    detector = HandDetector(detectionCon=0.8, maxHands=1, modelComplexity=0)

    # Initialize Camera
    camera = ThreadedCamera(0)

    sequence = []
    sentence = []
    predictions = [] # for stability
    threshold = 0.8
    sequence_length = 30
    
    # State tracking
    last_processed_time = 0
    
    print("Starting Inference...")
    
    # FPS Vars
    pTime = 0

    while True:
        success, img = camera.read()
        if not success or img is None:
            time.sleep(0.01) # Yield if no camera
            continue
        
        # Mirror
        img = cv2.flip(img, 1)
        
        # 1. Hand Tracking (Fast w/ Lite model)
        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)
        
        # UI Header
        cv2.putText(img, "Zap Quick - Silky Smooth", (15, 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)

        if lmList:
            features = extract_features(lmList)
            sequence.append(features)
            sequence = sequence[-sequence_length:] # Keep last 30 frames
            
            # Send to Brain if ready
            if len(sequence) == sequence_length:
                predictor.predict_async(sequence)

        # 2. Check for new thoughts from Brain (Instant check)
        res = predictor.get_result()
        
        if res is not None:
            # Process Result
            best_idx = np.argmax(res)
            conf = res[best_idx]
            
            predictions.append(best_idx)
            
            # Stability Check (Zap Quick = 5 frames)
            if len(predictions) > 5:
                last_n = predictions[-5:]
                if np.unique(last_n)[0] == best_idx: 
                    if conf > threshold: 
                        current_action = actions[best_idx]
                        
                        if len(sentence) > 0: 
                            if current_action != sentence[-1]: 
                                sentence.append(current_action)
                                tts_worker.speak(current_action) 
                        else:
                            sentence.append(current_action)
                            tts_worker.speak(current_action)
                            
            if len(sentence) > 5: 
                sentence = sentence[-5:]

            # UI - Confidence Bar
            bar_color = (0, 255, 0) if (conf > threshold) else (0, 0, 255)
            cv2.rectangle(img, (0, 440), (640, 480), (30, 30, 30), -1) 
            cv2.putText(img, f"Prediction: {actions[best_idx]}", (20, 470),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(img, f"{int(conf*100)}%", (540, 470),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, bar_color, 2, cv2.LINE_AA)


        # UI - Sentence
        cv2.rectangle(img, (0,0), (640, 60), (245, 117, 16), -1)
        cv2.putText(img, ' '.join(sentence), (20,45), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # FPS Calculation
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f"FPS: {int(fps)}", (520, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        
        cv2.imshow("Sign Language Translator", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
