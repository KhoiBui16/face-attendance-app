import os
import numpy as np
import pickle
from core.face_detection.recognizer import FaceRecognizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def validate_data(face_path, label_path):
    """Kiểm tra dữ liệu khuôn mặt và nhãn có khớp nhau không."""
    try:
        with open(face_path, "rb") as f:
            faces = pickle.load(f)
        with open(label_path, "rb") as f:
            labels = pickle.load(f)

        if len(faces) != len(labels):
            return False

        if len(faces) == 0 or len(labels) == 0:
            return False

        unique_labels = set(labels)
        print(f"[THÔNG TIN] Tìm thấy {len(unique_labels)} nhãn: {unique_labels}")
        if len(unique_labels) < 2:
            print(f"[THÔNG TIN] Cần ≥2 nhãn để huấn luyện. Dữ liệu đã lưu, chờ thêm nhãn.")
            return False
        return True
    
    except Exception as e:
        print(f"[LỖI] Lỗi khi kiểm tra dữ liệu: {e}")
        return False


def train_model(model_type="svm", face_path="data/dataset/faces.pkl", label_path="data/dataset/names.pkl", save_path="data/models/model.pkl"):
    """Huấn luyện mô hình và lưu vào file."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    if not os.path.exists(face_path) or not os.path.exists(label_path):
        print("[LỖI] Không tìm thấy dữ liệu khuôn mặt hoặc nhãn.")
        return False

    if not validate_data(face_path, label_path):
        return False

    try:
        recognizer = FaceRecognizer(model_type=model_type)
        recognizer.load_data(face_path, label_path)

        X_train, X_test, y_train, y_test = train_test_split(recognizer.faces, recognizer.labels, test_size=0.3, random_state=42, stratify=recognizer.labels)

        recognizer.model.fit(X_train, y_train)

        if not hasattr(recognizer.model, "classes_"):
            print(f"[LỖI] Mô hình {model_type} không có thuộc tính classes_")
            return False
        recognizer.classes_ = recognizer.model.classes_

        confidences = []
        predictions = []
        for x in X_test:
            pred, conf = recognizer.predict_with_confidence(x)
            predictions.append(pred)
            confidences.append(conf)

        recognizer.train()
        recognizer.save(save_path)

        return True
    except Exception as e:
        print(f"[LỖI] Lỗi khi huấn luyện mô hình: {e}")
        return False