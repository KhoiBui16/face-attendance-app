# recognize_and_log.py
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
from core.face_detection.recognizer import FaceRecognizer


def check_prerequisites(username, model_type="svm"):
    """
    Kiểm tra các điều kiện tiên quyết: đăng nhập, dữ liệu khuôn mặt, và mô hình nhận diện.
    - Trả về: (success, message, recognizer).
    """
    if not is_logged_in():
        return False, "❌ Vui lòng đăng nhập để thực hiện hành động này.", None

    if not username:
        return False, "❌ Không tìm thấy username trong phiên đăng nhập.", None

    print(f"[GỠ LỖI] Username từ phiên: {username}")

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
        recognizer = FaceRecognizer.load(model_path, model_type=model_type)
        if not hasattr(recognizer, "predict_with_confidence"):
            print("[LỖI] recognizer không có phương thức predict_with_confidence")
            return (
                False,
                "❌ Mô hình không hợp lệ: thiếu phương thức predict_with_confidence",
                None,
            )
        if recognizer.classes_ is None:
            print("[LỖI] Mô hình đã tải không có thuộc tính classes_")
            return False, "❌ Mô hình không chứa thông tin classes_", None
        print(f"[GỠ LỖI] Đã tải classes: {recognizer.classes_}")
        return True, "", recognizer
    except Exception as e:
        print(f"[LỖI] Lỗi tải mô hình: {e}")
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
        print(f"[GỠ LỖI] Đã tải nhãn: {labels}")
        return labels
    except Exception as e:
        print(f"[LỖI] Lỗi khi tải names.pkl: {e}")
        return None


def initialize_video_source(video_file):
    """
    Khởi tạo nguồn video (webcam hoặc file upload).
    - Trả về: (cap, temp_file_path, error_message).
    """
    cap = None
    temp_file_path = None
    start_time = time.time()

    if video_file is None:
        for index in range(3):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                print(f"[GỠ LỖI] Webcam đã được mở với index {index}")
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
        print("[LỖI] Không thể đọc khung hình từ webcam/video")
        cap.release()
        return None, temp_file_path, "❌ Không thể đọc khung hình từ webcam/video"
    height, width = frame.shape[:2]
    if width < 640 or height < 480:
        print(
            f"[CẢNH BÁO] Độ phân giải thấp ({width}x{height}), có thể ảnh hưởng đến phát hiện khuôn mặt"
        )
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset về khung hình đầu tiên

    print(
        f"[GỠ LỖI] Thời gian khởi tạo nguồn video: {time.time() - start_time:.2f} giây"
    )
    return cap, temp_file_path, None


def process_frame_and_recognize(
    cap, recognizer, username, action, video_placeholder, video_file
):
    """
    Xử lý khung hình, nhận diện khuôn mặt, và lưu log điểm danh.
    - Trả về: (recognized, result_message).
    """
    recognized = False
    result_message = ""
    max_attempts = 10  # Số khung hình tối đa để thử nhận diện
    start_time = time.time()

    try:
        attempt = 0
        while cap.isOpened() and not recognized and attempt < max_attempts:
            ret, frame = cap.read()
            if not ret:
                result_message = "❌ Không lấy được khung hình."
                print(
                    f"[GỠ LỖI] Không đọc được khung hình từ {'video' if video_file else 'webcam'}"
                )
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(
                frame_rgb, caption="🔍 Đang nhận diện...", use_container_width=True
            )

            frame_start_time = time.time()
            faces = detect_faces(frame)
            print(f"[GỠ LỖI] Số lượng khuôn mặt được phát hiện: {len(faces)}")
            if len(faces) == 0:
                print("[GỠ LỖI] Không phát hiện khuôn mặt trong khung hình")
                attempt += 1
                continue

            for x, y, w, h in faces:
                roi = frame[y : y + h, x : x + w]
                hog_features = extract_hog_features(roi, size=(100, 100))
                if hog_features is None:
                    print("[GỠ LỖI] Không thể trích xuất HOG features")
                    attempt += 1
                    continue

                try:
                    name, confidence = recognizer.predict_with_confidence(hog_features)
                    print(
                        f"[GỠ LỖI] Nhận diện: name={name}, confidence={confidence}, username={username}"
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
                                print(f"[GỠ LỖI] Chế độ demo admin: {username}")
                                recognized = True
                                break

                            is_allowed, check_msg = is_action_allowed(username, action)
                            if not is_allowed:
                                result_message = check_msg
                                print(
                                    f"[GỠ LỖI] is_action_allowed trả về False: {check_msg}"
                                )
                                recognized = True
                                break
                            else:
                                success, msg = append_attendance_log(
                                    username, roi, "attendance", action
                                )
                                result_message = f"✅ {msg}" if success else f"❌ {msg}"
                                print(
                                    f"[GỠ LỖI] Kết quả append_attendance_log: success={success}, message={msg}"
                                )
                                recognized = True
                                break
                        else:
                            result_message = (
                                "❌ Độ tin cậy thấp. Vui lòng check-in lại."
                            )
                            print(f"[GỠ LỖI] Confidence {confidence} dưới ngưỡng 0.5")
                            recognized = True
                            display_message(
                                result_message,
                                is_success=False,  # Sửa thành False cho thông báo lỗi
                                placeholder=video_placeholder,
                            )
                            break
                    else:
                        result_message = "❌ Khuôn mặt không xác định (unknown)"
                        print(
                            f"[GỠ LỖI] Bỏ qua khuôn mặt: label={label}, không khớp với username={username}"
                        )
                        recognized = True
                        break

                except Exception as e:
                    print(f"[GỠ LỖI] Lỗi nhận diện: {e}")
                    result_message = f"❌ Lỗi nhận diện: {e}"
                    attempt += 1
                    continue

            attempt += 1

        if not recognized and not result_message:
            result_message = (
                "❌ Không nhận diện được khuôn mặt sau nhiều lần thử. Vui lòng thử lại."
            )

    except Exception as e:
        result_message = f"❌ Lỗi trong quá trình nhận diện: {e}"
        print(f"[LỖI] Ngoại lệ trong process_frame_and_recognize: {e}")

    print(f"[GỠ LỖI] Tổng thời gian xử lý: {time.time() - start_time:.2f} giây")
    return recognized, result_message


def cleanup_video(cap, video_file, temp_file_path, video_placeholder):
    """
    Dọn dẹp tài nguyên: đóng video, xóa file tạm, xóa placeholder.
    """
    try:
        if cap is not None:
            cap.release()
    except Exception as e:
        print(f"[CẢNH BÁO] Lỗi khi đóng video: {e}")

    try:
        if video_placeholder:
            video_placeholder.empty()
    except Exception as e:
        print(f"[CẢNH BÁO] Lỗi khi xóa placeholder: {e}")

    try:
        if video_file is not None and temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"[GỠ LỖI] Đã xóa file video tạm: {temp_file_path}")
    except Exception as e:
        print(f"[LỖI] Lỗi khi xóa file tạm: {e}")


def recognize_and_log(action="check-in", video_file=None):
    """
    Nhận diện khuôn mặt và lưu log điểm danh.
    - action: Hành động ("check-in" hoặc "check-out").
    - video_file: File video upload (nếu có).
    - Trả về: (success, message).
    """
    username = st.session_state.get("username", None)
    success, message, recognizer = check_prerequisites(username, model_type="svm")

    if not success:
        return False, message

    # Tải nhãn để debug
    labels = load_labels()
    if labels is None:
        print("[GỠ LỖI] Tiếp tục mà không có nhãn để gỡ lỗi")

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
