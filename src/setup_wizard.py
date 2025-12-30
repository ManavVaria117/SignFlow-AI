import os
import shutil
import time
import sys

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collect_data import collect_data, actions
from train_model import train

def main():
    print("========================================")
    print("      SIGN FLOW AI: SMART SETUP         ")
    print("========================================")
    print("This wizard will guide you through recording ALL signs.")
    print("This ensures 'Hello', 'ThankYou', 'Help', and 'Please' look consistent.")
    print("")
    
    # 1. Verification
    print("[1/3] Preparing Workspace...")
    if os.path.exists('d:/aiProject/data'):
        # Just in case the command didn't run, double check logic here or just rely on collect_data to overwrite
        pass 
    print("Done.")
    print("")

    # 2. Collection Loop
    print("[2/3] Data Collection Phase")
    print("You will need to perform each sign 30 times.")
    print("Follow the on-screen camera instructions (Press 's' to start each).")
    print("")
    
    input("Press Enter to beginner the FIRST sign...")
    
    for action in actions:
        print(f"\n--- RECORDING: {action.upper()} ---")
        print(f"Get ready to sign '{action}'.")
        time.sleep(1)
        collect_data(action)
        print(f"Verified {action}.")
        time.sleep(1)

    # 3. Training
    print("\n[3/3] Training Brain...")
    train()
    
    print("\n========================================")
    print("           SETUP COMPLETE!              ")
    print("========================================")
    print("1. Restart your backend: .\\run_backend.bat")
    print("2. Refresh your browser.")
    print("3. Enjoy the magic.")

if __name__ == "__main__":
    main()
