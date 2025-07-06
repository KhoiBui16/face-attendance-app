import cv2
import numpy as np
import os
import pickle
from skimage.feature import hog
from core.face_detection.detector import detect_faces
from core.config import HOG_CONFIG
import albumentations as A


def augment_image(image):
    if not isinstance(image, np.ndarray):
        print(f"[ERROR] Input image is not a NumPy array: {type(image)}")
        return []

    augmented_images = [image]

    transforms = [
        A.HorizontalFlip(p=1.0),
        A.ColorJitter(brightness=(1.2, 1.2), p=1.0),
        A.ColorJitter(brightness=(0.8, 0.8), p=1.0),
    ]

    for transform in transforms:
        try:
            augmented = transform(image=image)
            augmented_images.append(augmented["image"])
        except Exception as e:
            print(f"[ERROR] Error during augmentation: {e}")

    return augmented_images


def extract_hog_features(roi, size=(100, 100)):
    if roi.shape[0] < 10 or roi.shape[1] < 10:
        return None
    try:
        resized = cv2.resize(roi, size)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        features, _ = hog(
            gray, pixels_per_cell=(8, 8), cells_per_block=(2, 2), visualize=True
        )
        if features.shape[0] != HOG_CONFIG["expected_hog_size"]:
            return None
        return features
    except Exception as e:
        print(f"[ERROR] Lỗi khi trích xuất HOG: {e}")
        return None


def is_good_quality(frame, x, y, w, h):
    roi = frame[y : y + h, x : x + w]
    if roi.shape[0] < 10 or roi.shape[1] < 10:
        return False
    try:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        brightness = gray.mean()
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        return brightness > 50 and sharpness > 100
    except Exception as e:
        print(f"[ERROR] Lỗi khi kiểm tra chất lượng: {e}")
        return False


def collect_face_data(
    cap, name, save_dir="data/dataset", num_samples=10, display_callback=None
):
    os.makedirs(save_dir, exist_ok=True)

    collected_faces = []
    collected_labels = []
    original_count = 0
    num_original_samples = num_samples // 4

    try:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Không thể đọc khung hình từ webcam/video")
            return False
        height, width = frame.shape[:2]
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        while cap.isOpened() and len(collected_faces) < num_samples:
            ret, frame = cap.read()
            if not ret:
                break

            faces = detect_faces(frame)

            for x, y, w, h in faces:
                if is_good_quality(frame, x, y, w, h):
                    roi = frame[y : y + h, x : x + w]
                    augmented_images = augment_image(roi)
                    for aug_img in augmented_images:
                        hog_features = extract_hog_features(aug_img)
                        if hog_features is not None:
                            collected_faces.append(hog_features)
                            collected_labels.append(name)

                    original_count += 1
                    if len(collected_faces) >= num_samples:
                        break
                else:
                    if display_callback:
                        cv2.putText(
                            frame,
                            "Poor quality",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 0, 255),
                            2,
                        )
                if len(collected_faces) >= num_samples:
                    break
            if display_callback:
                for x, y, w, h in faces:
                    frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"{len(collected_faces)}/{num_samples}",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                display_callback(frame, len(collected_faces), num_samples)

    except Exception as e:
        print(f"[ERROR] Lỗi khi thu thập dữ liệu: {e}")
        return False
    finally:
        cap.release()

    if not collected_faces:
        print("[ERROR] Không thu thập được khuôn mặt.")
        return False

    collected_faces = np.array(collected_faces)

    face_path = os.path.join(save_dir, "faces.pkl")
    label_path = os.path.join(save_dir, "names.pkl")
    expected_size = HOG_CONFIG["expected_hog_size"]

    try:
        if len(collected_faces) > 0 and collected_faces.shape[1] != expected_size:
            return False
        old_faces = np.array([]).reshape(0, expected_size)
        old_labels = []
        if os.path.exists(face_path):
            with open(face_path, "rb") as f:
                old_faces = pickle.load(f)
            if old_faces.shape[1] != expected_size:
                return False
        if os.path.exists(label_path):
            with open(label_path, "rb") as f:
                old_labels = pickle.load(f)

        collected_faces = (
            np.vstack([old_faces, collected_faces])
            if old_faces.size
            else collected_faces
        )

        collected_labels = old_labels + collected_labels
        if collected_faces.shape[0] != len(collected_labels):
            return False
        with open(face_path, "wb") as f:
            pickle.dump(collected_faces, f)
        with open(label_path, "wb") as f:
            pickle.dump(collected_labels, f)

        print(f"[SUCCESS] Đã lưu {len(collected_labels)} ảnh và nhãn.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save dataset: {e}")
        return False
