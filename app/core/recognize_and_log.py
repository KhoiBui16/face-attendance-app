import cv2
import pickle
import os
import time
import tempfile
import streamlit as st
from core.face_detection.detector import detect_faces
from core.data_collector.face_data_collector import extract_hog_features
from utils.helpers import (
    get_path,
    append_attendance_log,
    is_action_allowed,
    has_trained_data,
    display_message,
)
from utils.user_utils import is_logged_in
from core.data_collector.face_data_collector import is_good_quality


def check_prerequisites(username):
    """
    Kiểm tra các điều kiện tiên quyết: đăng nhập, dữ liệu khuôn mặt, và mô hình nhận diện.
    - Trả về: (success, message, recognizer).
    """
    if not is_logged_in():
        return False, "❌ Vui lòng đăng nhập để thực hiện hành động này.", None

    if not username:
        return False, "❌ Không tìm thấy username trong phiên đăng nhập.", None

    print(f"[DEBUG] Username from session: {username}")

    if not has_trained_data(username):
        return (
            False,
            f"❌ Dữ liệu khuôn mặt cho {username} chưa được thu thập. Vui lòng liên hệ admin.",
            None,
        )

    model_path = get_path("data/models/model.pkl")
    if not os.path.exists(model_path):
        return False, "❌ Mô hình chưa huấn luyện. Vui lòng liên hệ admin.", None

    try:
        with open(model_path, "rb") as f:
            recognizer = pickle.load(f)
        return True, "", recognizer
    except Exception as e:
        return False, f"❌ Lỗi tải mô hình: {e}", None


def load_labels():
    """
    Tải nhãn từ names.pkl để debug.
    - Trả về: labels (hoặc None nếu lỗi).
    """
    names_path = get_path("data/dataset/names.pkl")
    try:
        with open(names_path, "rb") as f:
            labels = pickle.load(f)
        print(f"[DEBUG] Loaded labels: {labels}")
        return labels
    except Exception as e:
        print(f"[ERROR] Failed to load names.pkl: {e}")
        return None


def initialize_video_source(video_file):
    """
    Khởi tạo nguồn video (webcam hoặc file upload).
    - Trả về: (cap, temp_file_path, error_message).
    """
    cap = None
    temp_file_path = None
    start_time = time.time()  # THAY ĐỔI: Thêm log thời gian

    if video_file is None:
        for index in range(3):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                print(f"[DEBUG] Webcam opened with index {index}")
                break
            cap.release()
        if not cap or not cap.isOpened():
            return None, None, "❌ Không mở được webcam."
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_file.read())
            temp_file_path = tmp.name
        cap = cv2.VideoCapture(temp_file_path)
        if not cap.isOpened():
            return None, temp_file_path, "❌ Không thể đọc file video."

    # Kiểm tra độ phân giải
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Không thể đọc khung hình từ webcam/video")
        cap.release()
        return None, temp_file_path, "❌ Không thể đọc khung hình từ webcam/video"
    height, width = frame.shape[:2]
    if width < 640 or height < 480:
        print(
            f"[WARNING] Độ phân giải thấp ({width}x{height}), có thể ảnh hưởng đến phát hiện khuôn mặt"
        )
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset về khung hình đầu tiên

    print(
        f"[DEBUG] Time to initialize video source: {time.time() - start_time:.2f} seconds"
    )  # THAY ĐỔI: Log thời gian
    return cap, temp_file_path, None


def process_frame_and_recognize(
    cap, recognizer, username, action, video_placeholder, video_file
):
    """
    Xử lý khung hình, nhận diện khuôn mặt, và lưu log điểm danh.
    - Thêm tham số video_file để debug nguồn video.
    - Trả về: (recognized, result_message).
    """
    # THAY ĐỔI: Thêm tham số video_file để sử dụng trong debug
    recognized = False
    result_message = ""
    max_attempts = 10  # Số khung hình tối đa để thử nhận diện
    start_time = time.time()  # THAY ĐỔI: Thêm log thời gian

    try:
        attempt = 0
        while cap.isOpened() and not recognized and attempt < max_attempts:
            ret, frame = cap.read()
            if not ret:
                result_message = "❌ Không lấy được khung hình."
                print(
                    f"[DEBUG] Failed to read frame from {'video' if video_file else 'webcam'}"
                )
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(
                frame_rgb, caption="🔍 Đang nhận diện...", use_container_width=True
            )

            frame_start_time = time.time()  # THAY ĐỔI: Thêm log thời gian khung hình
            faces = detect_faces(frame)
            print(f"[DEBUG] Number of faces detected: {len(faces)}")
            if len(faces) == 0:
                print("[DEBUG] No faces detected in frame")
                attempt += 1
                continue

            for x, y, w, h in faces:
                roi = frame[y : y + h, x : x + w]
                hog_features = extract_hog_features(roi, size=(100, 100))

                try:
                    name, confidence = recognizer.predict_with_confidence(hog_features)
                    print(
                        f"[DEBUG] Nhận diện: name={name}, confidence={confidence}, username={username}"
                    )

                    label = name if name == username else "unknown"
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"{label} ({confidence:.2f})",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    video_placeholder.image(
                        frame_rgb,
                        caption="🔍 Đang nhận diện...",
                        use_container_width=True,
                    )

                    if label == username:
                        if confidence >= 0.5:
                            if st.session_state.get("is_admin", False):
                                result_message = f"✅ [DEMO] Nhận diện: {username}"
                                print(f"[DEBUG] Admin demo mode: {username}")
                                recognized = True
                                break

                            is_allowed, check_msg = is_action_allowed(username, action)
                            if not is_allowed:
                                result_message = check_msg
                                print(
                                    f"[DEBUG] is_action_allowed returned False: {check_msg}"
                                )
                                recognized = True
                                break
                            else:
                                success, msg = append_attendance_log(
                                    username, roi, "attendance", action
                                )
                                result_message = f"✅ {msg}" if success else f"❌ {msg}"
                                print(
                                    f"[DEBUG] append_attendance_log result: success={success}, message={msg}"
                                )
                                recognized = True
                                break
                        else:
                            result_message = (
                                "❌ Độ tin cậy thấp. Vui lòng check-in lại."
                            )
                            print(
                                f"[DEBUG] Confidence {confidence} below threshold 0.6"
                            )
                            recognized = True
                            display_message(
                                result_message,
                                is_success=True,
                                placeholder=video_placeholder,
                            )
                            break
                    else:
                        result_message = "❌ Khuôn mặt không xác định (unknown)"
                        print(
                            f"[DEBUG] Skipping face: label={label}, not matching username={username}"
                        )
                        recognized = True
                        break

                except Exception as e:
                    print(f"[DEBUG] Lỗi nhận diện: {e}")
                    result_message = f"❌ Lỗi nhận diện: {e}"
                    attempt += 1
                    continue

            attempt += 1
            if cv2.waitKey(10) == 27:  # ESC để thoát (chỉ cho webcam)
                result_message = "❌ Đã hủy nhận diện."
                recognized = True
                break

        if not recognized and not result_message:
            result_message = (
                "❌ Không nhận diện được khuôn mặt sau nhiều lần thử. Vui lòng thử lại."
            )

    except Exception as e:
        result_message = f"❌ Lỗi trong quá trình nhận diện: {e}"
        print(f"[ERROR] Exception in process_frame_and_recognize: {e}")

    print(f"[DEBUG] Total processing time: {time.time() - start_time:.2f} seconds")
    return recognized, result_message


def cleanup_video(cap, video_file, temp_file_path, video_placeholder):
    """
    Dọn dẹp tài nguyên: đóng video, xóa file tạm, xóa placeholder.
    """
    if cap is not None:
        cap.release()
    video_placeholder.empty()
    try:
        cv2.destroyAllWindows()
    except cv2.error:
        pass  
    if video_file is not None and temp_file_path:
        try:
            os.unlink(temp_file_path)
            print(f"[DEBUG] Đã xóa file video tạm: {temp_file_path}")
        except Exception as e:
            print(f"[ERROR] Lỗi khi xóa file tạm: {e}")


def recognize_and_log(action="check-in", video_file=None):
    """
    Nhận diện khuôn mặt và lưu log điểm danh.
    - action: Hành động ("check-in" hoặc "check-out").
    - video_file: File video upload (nếu có).
    - Trả về: (success, message).
    """
    username = st.session_state.get("username", None)
    success, message, recognizer = check_prerequisites(username)

    if not success:
        return False, message

    # Tải nhãn để debug
    labels = load_labels()
    if labels is None:
        print("[DEBUG] Continuing without labels for debugging purposes")

    # Khởi tạo nguồn video
    cap, temp_file_path, error_message = initialize_video_source(video_file)
    if error_message:
        return False, error_message

    # Xử lý khung hình và nhận diện
    recognized, result_message = process_frame_and_recognize(
        cap, recognizer, username, action, st.empty(), video_file
    )

    # Dọn dẹp
    cleanup_video(cap, video_file, temp_file_path, st.empty())

    return recognized, result_message
