import numpy as np

def extract_features(lmList):
    """
    Extracts normalized features from a list of 21 landmarks.
    Expected lmList: list of [x, y, z] (normalized 0-1 from MediaPipe)
    
    Returns:
        numpy array of shape (63,) containing centered and scaled coordinates.
        Or vectors/angles if we choose that approach. 
        For now, let's use relative coordinates to wrist (landmark 0) to be position invariant.
    """
    if not lmList or len(lmList) != 21:
        return np.zeros(63) # Return zero vector if no hand found or incomplete

    # Convert to numpy array
    landmarks = np.array(lmList) # Shape (21, 3)

    # 1. Center to Wrist (Landmark 0)
    wrist = landmarks[0]
    centered_landmarks = landmarks - wrist

    # 2. Scale Invariance
    # Find max distance from wrist to any other landmark to normalize size
    distances = np.linalg.norm(centered_landmarks, axis=1)
    max_dist = np.max(distances)
    
    if max_dist > 0:
        normalized_landmarks = centered_landmarks / max_dist
    else:
        normalized_landmarks = centered_landmarks

    # Flatten
    features = normalized_landmarks.flatten()
    
    return features
