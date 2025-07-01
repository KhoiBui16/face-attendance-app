import cv2
import numpy as np
import os
import pickle
from core.face_detection.detector import detect_faces  # Cập nhật import
from utils.helpers import get_path

def collect_data(name, save_dir="data/dataset", num_samples=30, camera_index=0):  # Cập nhật đường dẫn
    """
    Thu thập dữ liệu khuôn mặt từ webcam và lưu dưới dạng pickle.
    - name: tên người cần gắn nhãn
    - save_dir: thư mục lưu tập dữ liệu
    - num_samples: số lượng mẫu thu thập
    - camera_index: chỉ số camera (mặc định 0)
    """
    save_dir = get_path(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        print("[ERROR] Cannot open webcam.")
        return False

    collected_faces = []
    print(f"[INFO] Bắt đầu thu thập dữ liệu cho '{name}'... Nhấn ESC để dừng.")

    try:
        while len(collected_faces) < num_samples:
            ret, frame = camera.read()
            if not ret:
                print("[ERROR] Failed to capture frame.")
                break

            faces = detect_faces(frame)
            for (x, y, w, h) in faces:
                roi = frame[y:y+h, x:x+w]
                resized = cv2.resize(roi, (50, 50))
                collected_faces.append(resized)

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"{len(collected_faces)}/{num_samples}", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                if len(collected_faces) >= num_samples:
                    break

            cv2.imshow("Collecting Faces", frame)
            if cv2.waitKey(10) == 27:  # ESC để thoát
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

    if len(collected_faces) == 0:
        print("[ERROR] Không thu thập được khuôn mặt.")
        return False

    # Chuyển về dạng vector 1D
    collected_faces = np.array(collected_faces).reshape(len(collected_faces), -1)
    collected_labels = [name] * len(collected_faces)

    face_path = os.path.join(save_dir, "faces.pkl")
    label_path = os.path.join(save_dir, "names.pkl")

    try:
        if os.path.exists(face_path):
            with open(face_path, 'rb') as f:
                old_faces = pickle.load(f)
            collected_faces = np.vstack([old_faces, collected_faces])

        if os.path.exists(label_path):
            with open(label_path, 'rb') as f:
                old_labels = pickle.load(f)
            collected_labels = old_labels + collected_labels

        with open(face_path, 'wb') as f:
            pickle.dump(collected_faces, f)

        with open(label_path, 'wb') as f:
            pickle.dump(collected_labels, f)

        print(f"[SUCCESS] Đã lưu {len(collected_labels)} ảnh và nhãn.")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to save dataset: {e}")
        return False
