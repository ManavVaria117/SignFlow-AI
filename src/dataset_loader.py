import numpy as np
import os
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split

DATA_PATH = os.path.join('d:/aiProject/data')
actions = np.array(['Hello', 'ThankYou', 'Help', 'Please']) # Should match collect_data

def load_data():
    sequences, labels = [], []
    label_map = {label:num for num, label in enumerate(actions)}
    
    # We will try to scan the directory for actions present
    found_actions = []
    for action in actions:
        if os.path.exists(os.path.join(DATA_PATH, action)):
            found_actions.append(action)
    
    if not found_actions:
         print("No data found in d:/aiProject/data")
         return None, None, None

    print(f"Loading data for actions: {found_actions}")
    
    for action in found_actions:
        action_path = os.path.join(DATA_PATH, action)
        # List all npy files
        file_list = [f for f in os.listdir(action_path) if f.endswith('.npy')]
        
        for file_name in file_list:
            res = np.load(os.path.join(action_path, file_name))
            sequences.append(res)
            labels.append(label_map[action])
            
    X = np.array(sequences)
    y = to_categorical(labels).astype(int)
    
    return X, y, found_actions
