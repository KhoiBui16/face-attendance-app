import os
import streamlit as st
from core.recognize_and_log import recognize_and_log
from utils.helpers import get_path, load_attendance_history, display_message
from utils.auth import logout
from utils.user_utils import is_logged_in

# Sidebar
if is_logged_in():
    st.sidebar.title("Điều hướng")
    st.sidebar.write(f"👤 Tài khoản: {st.session_state.get('username', 'N/A')}")
    st.sidebar.write(
        f"🔐Quyền: {'Admin' if st.session_state.get('is_admin', False) else 'Người dùng'}"
    )
    if st.sidebar.button("Đăng xuất"):
        logout()
        st.rerun()

st.title("Trang điểm danh")

# Kiểm tra đăng nhập
if not is_logged_in():
    st.warning("Vui lòng đăng nhập để sử dụng trang điểm danh.")
    st.stop()

# Kiểm tra mô hình
model_path = get_path("data/models/model.pkl")
if not os.path.exists(model_path):
    st.error(
        "Mô hình nhận diện chưa được huấn luyện. Vui lòng liên hệ admin để thu thập dữ liệu và huấn luyện."
    )
    st.stop()

# Kiểm tra username
username = st.session_state.get("username", "N/A")
if username == "N/A":
    st.error("❌ Lỗi: Không tìm thấy tên người dùng. Vui lòng đăng nhập lại.")
    st.stop()


# THAY ĐỔI: Làm mới attendance_df mỗi khi username thay đổi hoặc trang tải lại
if (
    "attendance_df" not in st.session_state
    or st.session_state.get("last_username") != username
):
    st.session_state.attendance_df = load_attendance_history(username=username)
    st.session_state.last_username = username
    print(
        f"[DEBUG] Refreshed attendance_df for {username}, shape={st.session_state.attendance_df.shape}"
    )

# THAY ĐỔI: Khởi tạo session state cho result_message
if "result_message" not in st.session_state:
    st.session_state.result_message = None
if "last_action" not in st.session_state:
    st.session_state.last_action = None


# Hiển thị lịch sử điểm danh của user
st.subheader(f"Lịch sử điểm danh của {username}")
if st.session_state.attendance_df.empty:
    st.info("Không có dữ liệu điểm danh nào cho bạn.")
else:
    st.dataframe(st.session_state.attendance_df, use_container_width=True)


# Chọn phương thức điểm danh
st.subheader("Chọn phương thức điểm danh")
input_source = st.radio("Nguồn điểm danh:", ["Webcam", "Tải video"], horizontal=True)
video_file = None

if input_source == "Tải video":
    video_file = st.file_uploader(
        "Tải lên video khuôn mặt (mp4, avi)", type=["mp4", "avi"]
    )

col1, col2 = st.columns(2)

def handle_check_in(input_source, video_file, username):
    """
    Xử lý hành động check-in.
    - input_source: "Webcam" hoặc "Tải video"
    - video_file: File video upload (nếu có)
    - username: Tên người dùng
    """
    if input_source == "Tải video" and video_file is None:
        st.session_state.result_message = "❌ Vui lòng tải lên video trước khi check-in."
        st.session_state.last_action = "check-in"
        display_message(st.session_state.result_message, is_success=False)
    else:
        with st.spinner("Đang nhận diện..."):
            success, message = recognize_and_log(
                action="check-in",
                video_file=video_file if input_source == "Tải video" else None,
            )
            st.session_state.result_message = message
            st.session_state.last_action = "check-in"
            display_message(message=message, is_success=success)
            if success:
                st.session_state.attendance_df = load_attendance_history(username=username)
                st.session_state.result_message = None
                st.session_state.last_action = None
                st.rerun()
                
def handle_check_out(input_source, video_file, username):
    """
    Xử lý hành động check-out.
    - input_source: "Webcam" hoặc "Tải video"
    - video_file: File video upload (nếu có)
    - username: Tên người dùng
    """
    if input_source == "Tải video" and video_file is None:
        st.session_state.result_message = "❌ Vui lòng tải lên video trước khi check-out."
        st.session_state.last_action = "check-out"
        display_message(st.session_state.result_message, is_success=False)
    else:
        with st.spinner("Đang nhận diện..."):
            success, message = recognize_and_log(
                action="check-out",
                video_file=video_file if input_source == "Tải video" else None,
            )
            st.session_state.result_message = message
            st.session_state.last_action = "check-out"
            display_message(message=message, is_success=success)
            if success:
                st.session_state.attendance_df = load_attendance_history(username=username)
                st.session_state.result_message = None
                st.session_state.last_action = None
                st.rerun()

with col1:
    if st.button("Check-in"):
        handle_check_in(input_source=input_source, video_file=video_file, username=username)
        

with col2:
    if st.button("Check-out"):
        handle_check_out(input_source=input_source, video_file=video_file, username=username)

# Hiển thị kết quả nhận diện
if st.session_state.result_message:
    # THAY ĐỔI: Chỉ hiển thị nút "Thử lại" khi check-in và lỗi là "Khuôn mặt không xác định (unknown)"
    if st.session_state.result_message.startswith("✅"):
        pass  # Bỏ hiển thị lặp vì đã hiển thị trong Check-in/Check-out
    elif (
        st.session_state.last_action == "check-in"
        and st.session_state.result_message == "❌ Khuôn mặt không xác định (unknown)"
    ):
        display_message(st.session_state.result_message, is_success=False)
        # Nút "Thử lại"
        if st.button("Thử lại"):
            st.session_state.result_message = None
            st.session_state.last_action = None
            if input_source == "Tải video":
                st.file_uploader(
                    "Tải lên video khuôn mặt (mp4, avi)",
                    type=["mp4", "avi"],
                    key="video_uploader_reset",
                )
            st.rerun()
    else:
        display_message(st.session_state.result_message, is_success=False)  # Hiển thị lỗi khác, không có nút "Thử lại"
