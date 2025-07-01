import os
import streamlit as st
from core.recognize_and_log import recognize_and_log
from utils.helpers import get_path
from utils.auth import logout
from utils.user_utils import is_logged_in

# Sidebar
if is_logged_in():
    st.sidebar.title("Điều hướng")
    st.sidebar.write(f"👤 Tài khoản: {st.session_state.get('username', 'N/A')}")
    st.sidebar.write(f"🔐Quyền: {'Admin' if st.session_state.get('is_admin', False) else 'Người dùng'}")
    if st.sidebar.button("Đăng xuất"):
        logout()
        st.rerun()


st.title("Trang điểm danh")
# Nút Đăng xuất trong nội dung chính, chỉ hiển thị khi đã đăng nhập
if is_logged_in():
    # if st.button("Đăng xuất", key="logout_main"):
    #     logout()
    # st.rerun()
    pass
else:
    st.warning("Vui lòng đăng nhập để sử dụng trang điểm danh.")
    st.stop()


model_path = get_path("data/models/model.pkl")
if not os.path.exists(model_path):
    st.error("Mô hình nhận diện chưa được huấn luyện. Vui lòng liên hệ admin để thu thập dữ liệu và huấn luyện.")
    st.stop()

st.subheader("Chọn phương thức điểm danh")
input_source = st.radio("Nguồn điểm danh:", ["Webcam", "Tải video"], horizontal=True)
video_file = None

if input_source == "Tải video":
    video_file = st.file_uploader("Tải lên video khuôn mặt (mp4, avi)", type=["mp4", "avi"])

col1, col2 = st.columns(2)

with col1:
    if st.button("Check-in"):
        with st.spinner("Đang nhận diện..."):
            success, message = recognize_and_log(action="check-in", video_file=video_file if input_source == "Tải video" else None)
            if success:
                st.success(message)
            else:
                st.error(message)

with col2:
    if st.button("Check-out"):
        with st.spinner("Đang nhận diện..."):
            success, message = recognize_and_log(action="check-out", video_file=video_file if input_source == "Tải video" else None)
            if success:
                st.success(message)
            else:
                st.error(message)