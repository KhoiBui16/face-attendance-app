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
                f"[LỖI] Số lượng khuôn mặt ({len(faces)}) không khớp với nhãn ({len(labels)})"
            )
            return False

        if len(faces) == 0 or len(labels) == 0:
            print("[LỖI] Dữ liệu khuôn mặt hoặc nhãn rỗng.")
            return False

        unique_labels = set(labels)
        print(f"[THÔNG TIN] Tìm thấy {len(unique_labels)} nhãn: {unique_labels}")
        if len(unique_labels) < 2:
            print(
                f"[THÔNG TIN] Cần ≥2 nhãn để huấn luyện. Dữ liệu đã lưu, chờ thêm nhãn."
            )
            return False
        return True
    except Exception as e:
        print(f"[LỖI] Lỗi khi kiểm tra dữ liệu: {e}")
        return False


def train_model(
    model_type="svm",
    face_path="data/dataset/faces.pkl",
    label_path="data/dataset/names.pkl",
    save_path="data/models/model.pkl",
):
    """Huấn luyện mô hình và lưu vào file."""
    face_path = get_path(face_path)
    label_path = get_path(label_path)
    save_path = get_path(save_path)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    if not os.path.exists(face_path) or not os.path.exists(label_path):
        print("[LỖI] Không tìm thấy dữ liệu khuôn mặt hoặc nhãn.")
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
            f"[GỠ LỖI] Tập huấn luyện: {len(X_train)} mẫu, Tập kiểm tra: {len(X_test)} mẫu"
        )

        # Huấn luyện trên tập train
        recognizer.model.fit(X_train, y_train)

        # Kiểm tra classes_ sau khi huấn luyện
        if not hasattr(recognizer.model, "classes_"):
            print(f"[LỖI] Mô hình {model_type} không có thuộc tính classes_")
            return False
        recognizer.classes_ = recognizer.model.classes_
        print(f"[GỠ LỖI] Classes: {recognizer.classes_}")

        # Đánh giá trên tập train
        train_predictions = recognizer.model.predict(X_train)
        train_accuracy = accuracy_score(y_train, train_predictions)
        print(f"[THÔNG TIN] Độ chính xác trên tập train: {train_accuracy:.2f}")

        # Đánh giá trên tập test
        confidences = []
        predictions = []
        for x in X_test:
            pred, conf = recognizer.predict_with_confidence(x)
            predictions.append(pred)
            confidences.append(conf)

        test_accuracy = accuracy_score(y_test, predictions)
        mean_confidence = np.mean(confidences)
        print(f"[THÔNG TIN] Độ chính xác trên tập test: {test_accuracy:.2f}")
        print(f"[THÔNG TIN] Confidence trung bình trên tập test: {mean_confidence:.2f}")
        print(
            f"[THÔNG TIN] Gợi ý ngưỡng confidence: {max(0.5, float(mean_confidence) - 0.1):.2f}"
        )

        # Kiểm tra overfitting
        if train_accuracy - test_accuracy > 0.15:
            print(
                "[CẢNH BÁO] Mô hình có dấu hiệu overfitting (chênh lệch độ chính xác train/test > 0.15)"
            )

        if test_accuracy < 0.9:
            print("[LỖI] Độ chính xác trên tập test quá thấp. Không lưu mô hình.")
            return False

        # Huấn luyện lại trên toàn bộ dữ liệu
        recognizer.train()

        # Lưu mô hình bằng phương thức save
        recognizer.save(save_path)
        print(
            f"[GỠ LỖI] Mô hình '{model_type}' đã được huấn luyện và lưu vào {save_path}"
        )
        return True
    except Exception as e:
        print(f"[LỖI] Lỗi khi huấn luyện mô hình: {e}")
        return False
