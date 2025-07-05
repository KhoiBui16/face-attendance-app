import cv2
import os


def get_haar_cascade_path():
    # Đường dẫn tuyệt đối tính từ vị trí chạy script (app/)
    cascade_path = "/data/models/haarcascade_frontalface_default.xml"

    if not os.path.exists(cascade_path):
        raise FileNotFoundError(f"[ERROR] Không tìm thấy cascade: {cascade_path}")

    return cascade_path


def detect_faces(frame):
    """Detect faces using Haar Cascade from local XML."""
    cascade_file = get_haar_cascade_path()
    face_cascade = cv2.CascadeClassifier(cascade_file)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )
    return faces
