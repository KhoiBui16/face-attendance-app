import os
import numpy as np
import pickle
from core.face_detection.recognizer import FaceRecognizer
from utils.helpers import get_path
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
            print(
                f"[ERROR] Số lượng khuôn mặt ({len(faces)}) không khớp với nhãn ({len(labels)})"
            )
            return False

        if len(faces) == 0 or len(labels) == 0:
            print("[ERROR] Dữ liệu khuôn mặt hoặc nhãn rỗng.")
            return False

        unique_labels = set(labels)
        print(f"[INFO] Tìm thấy {len(unique_labels)} nhãn: {unique_labels}")
        if len(unique_labels) < 2:
            print(f"[INFO] Cần ≥2 nhãn để huấn luyện. Dữ liệu đã lưu, chờ thêm nhãn.")
            return False
        return True

    except Exception as e:
        print(f"[ERROR] Lỗi khi kiểm tra dữ liệu: {e}")
        return False


def train_model(
    model_type="adaboost",
    face_path="data/dataset/faces.pkl",
    label_path="data/dataset/names.pkl",
    save_path="data/models/model.pkl",
):

    face_path = get_path(face_path)
    label_path = get_path(label_path)
    save_path = get_path(save_path)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    # print(f"[DEBUG] Creating model directory: {os.path.dirname(save_path)}")

    if not os.path.exists(face_path) or not os.path.exists(label_path):
        print("[ERROR] Face or label data not found.")
        return False

    if not validate_data(face_path, label_path):
        return False

    try:
        recognizer = FaceRecognizer(model_type=model_type)
        recognizer.load_data(face_path, label_path)

        # Chia dữ liệu thành train/test với tỷ lệ 30% test
        X_train, X_test, y_train, y_test = train_test_split(
            recognizer.faces,
            recognizer.labels,
            test_size=0.3,
            random_state=42,
            stratify=recognizer.labels,
        )

        print(
            f"[DEBUG] Training set: {len(X_train)} samples, Test set: {len(X_test)} samples"
        )

        # Huấn luyện trên tập train
        recognizer.model.fit(X_train, y_train)

        # Đánh giá trên tập train
        train_predictions = recognizer.model.predict(X_train)
        train_accuracy = accuracy_score(y_train, train_predictions)
        print(f"[INFO] Độ chính xác trên tập train: {train_accuracy:.2f}")

        # Đánh giá trên tập test
        confidences = []
        predictions = []
        for x in X_test:
            pred, conf = recognizer.predict_with_confidence(x)
            predictions.append(pred)
            confidences.append(conf)

        test_accuracy = accuracy_score(y_test, predictions)
        mean_confidence = np.mean(confidences)
        print(f"[INFO] Độ chính xác trên tập test: {test_accuracy:.2f}")
        print(f"[INFO] Confidence trung bình trên tập test: {mean_confidence:.2f}")
        print(f"[INFO] Gợi ý ngưỡng confidence: {max(0.5, mean_confidence - 0.1):.2f}")

        # Kiểm tra overfitting
        if train_accuracy - test_accuracy > 0.15:
            print(
                "[WARNING] Mô hình có dấu hiệu overfitting (chênh lệch độ chính xác train/test > 0.15)"
            )

        if test_accuracy < 0.8:
            print("[ERROR] Độ chính xác trên tập test quá thấp. Không lưu mô hình.")
            return False

        # Huấn luyện lại trên toàn bộ dữ liệu
        recognizer.train()

        with open(save_path, "wb") as f:
            pickle.dump(recognizer, f)
        print(f"[DEBUG] Model '{model_type}' trained and saved to {save_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to train model: {e}")
        return False
