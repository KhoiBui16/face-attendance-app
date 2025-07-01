import os
import pickle
from core.face_detection.recognizer import FaceRecognizer  # Cập nhật import
from utils.helpers import get_path

def train_model(model_type='mlp', 
                face_path='data/dataset/faces.pkl', 
                label_path='data/dataset/names.pkl', 
                save_path='data/models/model.pkl'):  
    
    face_path = get_path(face_path)
    label_path = get_path(label_path)
    save_path = get_path(save_path)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    # print(f"[DEBUG] Creating model directory: {os.path.dirname(save_path)}")
    
    if not os.path.exists(face_path) or not os.path.exists(label_path):
        print("[ERROR] Face or label data not found.")
        return False
    
    try:
        recognizer = FaceRecognizer(model_type=model_type)
        recognizer.load_data(face_path, label_path)
        recognizer.train()
        with open(save_path, 'wb') as f:
            pickle.dump(recognizer, f)
        # print(f"[DEBUG] Model '{model_type}' trained and saved to {save_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to train model: {e}")
        return False