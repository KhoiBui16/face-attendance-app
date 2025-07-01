# import cv2
# import pickle
# import os
# import streamlit as st
# from core.face_detection.detector import detect_faces  
# from utils.helpers import get_path, append_attendance_log, is_action_allowed

# def recognize_and_log(action="check-in"):
#     model_path = get_path("data/models/model.pkl")  
    
#     if not os.path.exists(model_path):
#         return False, "Mô hình nhận diện chưa được huấn luyện. Vui lòng liên hệ admin."
    
#     try:
#         with open(model_path, "rb") as f:
#             recognizer = pickle.load(f)
#     except Exception as e:
#         return False, f"Lỗi khi tải mô hình: {e}"
    
#     cap = None
#     for index in range(3):
#         cap = cv2.VideoCapture(index)
#         if cap.isOpened():
#             # print(f"[DEBUG] Webcam opened with index {index}")
#             break
#         cap.release()
        
#     if not cap or not cap.isOpened():
#         return False, "Không thể mở webcam. Vui lòng kiểm tra kết nối webcam."
    
#     video_placeholder = st.empty()
#     recognized = False
#     result_message = ""
    
#     try:
#         while not recognized:
#             ret, frame = cap.read()
#             if not ret:
#                 result_message = "Không thể lấy hình ảnh từ webcam."
#                 break
            
#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             video_placeholder.image(frame_rgb, caption="Đang nhận diện khuôn mặt...", use_container_width=True)
            
#             faces = detect_faces(frame)
#             for (x, y, w, h) in faces:
#                 roi = frame[y:y+h, x:x+w]
#                 resized = cv2.resize(roi, (50, 50)).flatten()
#                 try:
#                     name = recognizer.predict(resized) # chỉ dùng để detect -> ko có nhận dạng rõ the score
#                     # name, confidence = recognizer.predict_with_confidence(resized)

#                     # if confidence < 0.6:
#                     #     result_message = f"Không đủ độ tin cậy để nhận diện ({round(confidence*100)}%). Vui lòng thử lại."
#                     #     recognized = True
#                     #     break
                    
#                     # ✅ Nếu là admin → demo, không ghi log
#                     if st.session_state.get("is_admin", False):
#                         result_message = f"[DEMO] Nhận diện thành công: {name} (Admin demo)"
#                         recognized = True
#                         break
                    
#                     is_allowed, check_msg = is_action_allowed(name, action)
#                     if not is_allowed:
#                         result_message = check_msg
#                         recognized = True
#                         break
                    
#                     # ✅ Nếu là người dùng thường → ghi log
#                     position = "attendance"
#                     success, message = append_attendance_log(name, roi, position, action)
                    
#                     if success:
#                         result_message = f"Điểm danh {action} thành công cho {name}."
#                     else:
#                         result_message = f"Điểm danh {action} không thành công: {message}"
#                     recognized = True
#                     break
#                 except Exception as e:
#                     result_message = "Không nhận diện được khuôn mặt. Vui lòng thử lại."
            
#             if cv2.waitKey(1) & 0xFF == 27:
#                 result_message = "Đã hủy nhận diện."
#                 break
#     except Exception as e:
#         result_message = f"Lỗi trong quá trình nhận diện: {e}"
#     finally:
#         cap.release()
#         cv2.destroyAllWindows()
    
#     return recognized, result_message

import cv2
import pickle
import os
import tempfile
import streamlit as st
from core.face_detection.detector import detect_faces
from utils.helpers import get_path, append_attendance_log, is_action_allowed, has_trained_data
from utils.user_utils import is_logged_in

def recognize_and_log(action="check-in", video_file=None):
    if not is_logged_in():
        return False, "❌ Vui lòng đăng nhập để thực hiện hành động này."

    username = st.session_state.username
    if not has_trained_data(username):
        return False, f"❌ Dữ liệu khuôn mặt cho {username} chưa được thu thập. Vui lòng liên hệ admin."
    
    
    model_path = get_path("data/models/model.pkl")
    if not os.path.exists(model_path):
        return False, "❌ Mô hình chưa huấn luyện. Vui lòng liên hệ admin."

    try:
        with open(model_path, "rb") as f:
            recognizer = pickle.load(f)
    except Exception as e:
        return False, f"❌ Lỗi tải mô hình: {e}"

    if video_file is None:
        # Webcam
        cap = None
        for index in range(3):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                break
            cap.release()
        if not cap or not cap.isOpened():
            return False, "❌ Không mở được webcam."
    else:
        # Video file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_file.read())
            video_path = tmp.name
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False, "❌ Không thể đọc file video."

    video_placeholder = st.empty()
    recognized = False
    result_message = ""

    while cap.isOpened() and not recognized:
        ret, frame = cap.read()
        if not ret:
            result_message = "❌ Không lấy được khung hình."
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(frame_rgb, caption="🔍 Đang nhận diện...", use_container_width=True)

        faces = detect_faces(frame)
        for (x, y, w, h) in faces:
            roi = frame[y:y+h, x:x+w]
            resized = cv2.resize(roi, (50, 50)).flatten()

            try:
                # name = recognizer.predict(resized)
                name, confidence = recognizer.predict_with_confidence(resized)

                if confidence < 0.8:
                    result_message = f"Không đủ độ tin cậy để nhận diện ({round(confidence*100)}%). Vui lòng thử lại."
                    recognized = True
                    break
                
                # So sánh tên nhận diện với username
                if name != username:
                    result_message = f"❌ Khuôn mặt không khớp với tài khoản {username}."
                    recognized = True
                    break
                
                
                if st.session_state.get("is_admin", False):
                    result_message = f"✅ [DEMO] Nhận diện: {name}"
                    recognized = True
                    break

                is_allowed, check_msg = is_action_allowed(name, action)
                if not is_allowed:
                    result_message = check_msg
                    recognized = True
                    break

                success, msg = append_attendance_log(name, roi, "attendance", action)
                result_message = f"✅ {msg}" if success else f"❌ {msg}"
                recognized = True
                break

            except Exception as e:
                result_message = f"❌ Lỗi nhận diện: {e}"
                recognized = True
                break

    cap.release()
    video_placeholder.empty()
    cv2.destroyAllWindows()
    if video_file is not None:
        os.unlink(video_path)  # Xóa file tạm sau khi xử lý

    return recognized, result_message
