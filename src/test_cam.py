import cv2
import time
from hand_tracking import HandDetector
from feature_extractor import extract_features
import numpy as np

def main():
    cap = cv2.VideoCapture(0)
    detector = HandDetector()
    
    # Check if camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Starting camera... Press 'q' to quit.")

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to read frame.")
            break

        img = detector.findHands(img)
        lmList = detector.findPosition(img)

        if lmList:
            features = extract_features(lmList)
            # Print features of the first frame or periodically to verify
            # Just print the shape and first few values to avoid spam
            # print(f"Features shape: {features.shape}, First 5: {features[:5]}")
            
            # Visual feedback on screen
            cv2.putText(img, "Hand Detected", (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        else:
             cv2.putText(img, "No Hand", (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
