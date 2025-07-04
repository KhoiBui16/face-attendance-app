import cv2
import numpy as np
import os
import pickle
from skimage.feature import hog
from core.face_detection.detector import detect_faces
from utils.helpers import get_path
from core.config import HOG_CONFIG
import imgaug.augmenters as iaa

def augment_image(image):
    if not isinstance(image, np.ndarray):
        print(f"[ERROR] Input image is not a NumPy array: {type(image)}")
        return []
    augmented_images = [image]
    augmented_images.append(iaa.Fliplr(1.0).augment_image(image))
    augmented_images.append(iaa.Multiply(1.2).augment_image(image))
    augmented_images.append(iaa.Multiply(0.8).augment_image(image))
    return augmented_images


def extract_hog_features(roi, size=(100, 100)):
    """
    Trích xuất đặc trưng HOG từ vùng ảnh (ROI).
    - roi: Vùng ảnh chứa khuôn mặt (BGR).
    - size: Kích thước resize ảnh (mặc định 100x100).
    - Trả về: Đặc trưng HOG dạng vector.
    """
    
    if roi.shape[0] < 10 or roi.shape[1] < 10:
        print(f"[ERROR] ROI quá nhỏ: {roi.shape}")
        return None
    try:
        
        resized = cv2.resize(roi, size)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        features, _ = hog(
            gray, 
            pixels_per_cell=(8, 8), 
            cells_per_block=(2, 2), 
            visualize=True
        )
        print(f"[DEBUG] HOG features shape: {features.shape}")
        if features.shape[0] != HOG_CONFIG["expected_hog_size"]:
            print(f"[ERROR] Kích thước HOG ({features.shape[0]}) không khớp với kỳ vọng ({HOG_CONFIG['expected_hog_size']})")
            return None
        return features
    except Exception as e:
        print(f"[ERROR] Lỗi khi trích xuất HOG: {e}")
        return None

def is_good_quality(frame, x, y, w, h):
    """Kiểm tra chất lượng ảnh khuôn mặt dựa trên độ sáng và độ nét."""
    roi = frame[y:y+h, x:x+w]
    if roi.shape[0] < 10 or roi.shape[1] < 10:
        print(f"[ERROR] ROI quá nhỏ: {roi.shape}")
        return False
    
    try:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        brightness = gray.mean()
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        print(f"[DEBUG] Brightness: {brightness}, Sharpness: {sharpness}")
        return brightness > 50 and sharpness > 100
    except Exception as e:
        print(f"[ERROR] Lỗi khi kiểm tra chất lượng: {e}")
        return False


def collect_face_data(cap, name, save_dir="data/dataset", num_samples=10, display_callback=None):
    save_dir = get_path(save_dir)
    os.makedirs(save_dir, exist_ok=True)
    
    collected_faces = []
    collected_labels = []
    original_count = 0  # Đếm số khuôn mặt gốc thu thập
    num_original_samples = num_samples // 4 # Mỗi mẫu gốc tạo 4 mẫu (gốc + 3 tăng cường)
    print(f"[INFO] Bắt đầu thu thập dữ liệu cho '{name}'...")

    try:
        # THAY ĐỔI: Kiểm tra độ phân giải khung hình
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Không thể đọc khung hình từ webcam/video")
            return False
        height, width = frame.shape[:2]
        if width < 640 or height < 480:
            print(f"[WARNING] Độ phân giải thấp ({width}x{height}), có thể ảnh hưởng đến phát hiện khuôn mặt")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset về khung hình đầu tiên


        while cap.isOpened() and len(collected_faces) < num_samples:
            ret, frame = cap.read()
            if not ret:
                print("[DEBUG] Failed to read frame.")
                break
            
            faces = detect_faces(frame)
            print(f"[DEBUG] Detected {len(faces)} faces")
            
            for (x, y, w, h) in faces:
                print(f"[DEBUG] Face ROI: x={x}, y={y}, w={w}, h={h}")
                
                if is_good_quality(frame, x, y, w, h):
                    roi = frame[y:y+h, x:x+w]
                    augmented_images = augment_image(roi)
                    for aug_img in augmented_images:
                        hog_features = extract_hog_features(aug_img)
                        if hog_features is not None:
                            collected_faces.append(hog_features)
                            collected_labels.append(name)
                            print(f"[DEBUG] Collected face {len(collected_faces)}/{num_samples}")
                    
                    original_count += 1  # Tăng đếm khuôn mặt gốc
                    print(f"[DEBUG] Original faces collected: {original_count}/{num_original_samples}")
                    if len(collected_faces) >= num_samples:
                        break
                else:
                    print("[DEBUG] Skipping low-quality face")
                    if display_callback:
                        cv2.putText(frame, "Poor quality", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if len(collected_faces) >= num_samples:
                    break
            if display_callback:
                for (x, y, w, h) in faces:
                    frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{len(collected_faces)}/{num_samples}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                display_callback(frame, len(collected_faces), num_samples)
            if cv2.waitKey(10) == 27:
                print("[DEBUG] Collection stopped by user (ESC)")
                break
    except Exception as e:
        print(f"[ERROR] Lỗi khi thu thập dữ liệu: {e}")
        return False
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if not collected_faces:
        print("[ERROR] Không thu thập được khuôn mặt.")
        return False

    collected_faces = np.array(collected_faces)
    print(f"[DEBUG] Collected faces shape: {collected_faces.shape}")
    print(f"[DEBUG] Collected labels length: {len(collected_labels)}")

    face_path = os.path.join(save_dir, "faces.pkl")
    label_path = os.path.join(save_dir, "names.pkl")
    expected_size = HOG_CONFIG["expected_hog_size"]

    try:
        if len(collected_faces) > 0 and collected_faces.shape[1] != expected_size:
            print(f"[ERROR] HOG size mismatch: {collected_faces.shape[1]} vs {expected_size}")
            return False
        old_faces = np.array([]).reshape(0, expected_size)
        old_labels = []
        if os.path.exists(face_path):
            with open(face_path, 'rb') as f:
                old_faces = pickle.load(f)
            print(f"[DEBUG] Old faces shape: {old_faces.shape}")
            if old_faces.shape[1] != expected_size:
                print(f"[ERROR] Old faces size mismatch: {old_faces.shape[1]} vs {expected_size}")
                print(f"[INFO] Please delete {face_path} and {label_path}")
                return False
        if os.path.exists(label_path):
            with open(label_path, 'rb') as f:
                old_labels = pickle.load(f)
            print(f"[INFO] Existing labels: {set(old_labels)}")
        collected_faces = np.vstack([old_faces, collected_faces]) if old_faces.size else collected_faces
        collected_labels = old_labels + collected_labels
        if collected_faces.shape[0] != len(collected_labels):
            print(f"[ERROR] Mismatch: faces={collected_faces.shape[0]}, labels={len(collected_labels)}")
            return False
        with open(face_path, 'wb') as f:
            pickle.dump(collected_faces, f)
        with open(label_path, 'wb') as f:
            pickle.dump(collected_labels, f)
        print(f"[SUCCESS] Đã lưu {len(collected_labels)} ảnh và nhãn.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save dataset: {e}")
        return False