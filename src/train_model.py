import numpy as np
import os
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import TensorBoard
from dataset_loader import load_data, actions
from sklearn.model_selection import train_test_split

def train():
    X, y, found_actions = load_data()
    if X is None:
        print("Dataset empty. Run collect_data.py first.")
        return

    print(f"Data shape: {X.shape}, Labels shape: {y.shape}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

    model = Sequential()
    # 63 features (21 landmarks * 3 coords)
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 63)))
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(LSTM(64, return_sequences=False, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(len(actions), activation='softmax'))

    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])
    
    log_dir = os.path.join('Logs')
    tb_callback = TensorBoard(log_dir=log_dir)

    model.fit(X_train, y_train, epochs=100, callbacks=[tb_callback], validation_data=(X_test, y_test))
    
    model.summary()
    
    model_path = os.path.join('d:/aiProject/models', 'action.h5')
    if not os.path.exists('d:/aiProject/models'):
         os.makedirs('d:/aiProject/models')
         
    model.save(model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train()
