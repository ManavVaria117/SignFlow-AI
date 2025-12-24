import cv2
import numpy as np
import os
import time
from hand_tracking import HandDetector
from feature_extractor import extract_features

# Path for exported data, numpy arrays
DATA_PATH = os.path.join('d:/aiProject/data')

# Actions that we try to detect
# You can change these or add more
actions = ['Hello', 'ThankYou', 'Help', 'Please']

# Thirty videos worth of data
no_sequences = 30

# Videos are going to be 30 frames in length
sequence_length = 30

def collect_data(action_name):
    detector = HandDetector(detectionCon=0.8, maxHands=1)
    cap = cv2.VideoCapture(0)
    
    # Create folder for action if it doesn't exist
    action_folder = os.path.join(DATA_PATH, action_name)
    if not os.path.exists(action_folder):
        os.makedirs(action_folder)

    print(f"Collecting data for '{action_name}'")
    print(f"Press 's' to start collection. You will collect {no_sequences} sequences of {sequence_length} frames.")
    
    # Wait for start
    while True:
        success, img = cap.read()
        if not success: continue
        cv2.putText(img, f"Collecting: {action_name}", (100, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0,255, 0), 2)
        cv2.putText(img, "Press 's' to start", (100, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0,255, 0), 2)
        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('s'):
            break

    for sequence in range(no_sequences):
        window = []
        frame_num = 0
        while frame_num < sequence_length:
            success, img = cap.read()
            if not success: continue
            
            img = detector.findHands(img)
            lmList = detector.findPosition(img, draw=False)
            
            if lmList:
                features = extract_features(lmList)
                window.append(features)
                
                # Visual feedback
                cv2.putText(img, f"Seq: {sequence} Frame: {frame_num}", (15,12), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                
                frame_num += 1
            else:
                 cv2.putText(img, "No Hand - Pause", (15,12), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            
            cv2.imshow("Image", img)
            cv2.waitKey(1)
        
        # Save sequence
        npy_path = os.path.join(action_folder, str(sequence))
        np.save(npy_path, np.array(window))
        print(f"Saved sequence {sequence} for {action_name}")
        
        # Pause between sequences
        print("Rest script for 2 seconds...")
        cv2.putText(img, "Rest...", (100, 100), cv2.FONT_HERSHEY_PLAIN, 3, (0,255, 255), 3)
        cv2.imshow("Image", img)
        cv2.waitKey(2000)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        collect_data(action)
    else:
        print("Usage: python src/collect_data.py <ActionName>")
        print("Example: python src/collect_data.py Hello")
