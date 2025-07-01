import streamlit as st
import os
from core.data_collector import collect_data
from core.train_model import train_model
from core.data_collector_video import collect_data_from_uploaded_video
from utils.helpers import save_uploaded_video
from utils.helpers import read_attendance_csv, preprocess_attendance, get_path
from utils.auth import logout
from utils.user_utils import is_admin, is_logged_in
from utils.auth import load_users, save_users

# Sidebar
if is_logged_in():
    st.sidebar.title("Điều hướng")
    st.sidebar.write(f"Đăng nhập với: {st.session_state.get('username', 'N/A')}")
    st.sidebar.write(f"Quyền: {'Admin' if is_admin() else 'Người dùng'}")
    if st.sidebar.button("Đăng xuất"):
        logout()
        st.rerun()

st.title("Trang quản trị viên")

# Nút Đăng xuất trong nội dung chính, chỉ hiển thị khi đã đăng nhập
# if is_logged_in():
#     if st.button("Đăng xuất", key="logout_main"):
#         logout()
#         st.rerun()

if not is_admin():
    st.warning("Bạn không có quyền truy cập trang này.")
    # st.write(f"[DEBUG] is_admin: {st.session_state.get('is_admin', False)}, is_allowed: {st.session_state.get('is_allowed', False)}")
    st.stop()

# Thu thập dữ liệu mới và huấn luyện
st.subheader("Thu thập dữ liệu và huấn luyện")
name = st.text_input("Nhập tên nhân viên để thu thập:")

upload_option = st.radio("Chọn nguồn thu thập", ["Webcam", "Tải video"], horizontal=True)
video_file = None

if upload_option == "Tải video":
    video_file = st.file_uploader("Tải lên video khuôn mặt (mp4, avi)", type=["mp4", "avi"])
    if video_file is not None:
        saved_video_path = save_uploaded_video(
            video_file=video_file,
            username=st.session_state.username,
            action="collect"
        )
        st.success(f"✅ Video đã được lưu")

if st.button("Bắt đầu thu thập") and name:
    with st.spinner("Đang thu thập dữ liệu..."):
        try:
            if upload_option == "Webcam":
                success = collect_data(name, num_samples=10, save_dir=get_path("data/dataset"))
            else:
                if saved_video_path is None:
                    st.error("Vui lòng tải lên video trước.")
                    st.stop()
                success = collect_data_from_uploaded_video(
                    video_path=saved_video_path,
                    name=name,
                    save_dir=get_path("data/dataset"),
                    num_samples=10
                )

            if success:
                success_train = train_model(
                    face_path=get_path("data/dataset/faces.pkl"),
                    label_path=get_path("data/dataset/names.pkl"),
                    save_path=get_path("data/models/model.pkl")
                )
                if success_train:
                    st.success(f"Đã thu thập và huấn luyện xong cho: {name}")
                else:
                    st.error("Lỗi khi huấn luyện mô hình. Kiểm tra dữ liệu đầu vào.")
            else:
                st.error("Không thu thập được dữ liệu. Vui lòng kiểm tra video/webcam.")
        except Exception as e:
            st.error(f"Lỗi khi thu thập hoặc huấn luyện: {e}")



# ----------------------------------------
# 📋 HIỂN THỊ BẢNG ĐIỂM DANH
# ----------------------------------------
st.subheader("Bảng điểm danh")
try:
    data = read_attendance_csv()
    summary_df = preprocess_attendance(data)
    st.dataframe(summary_df, use_container_width=True)
    
except Exception as e:
    st.error(f"Lỗi khi đọc dữ liệu điểm danh: {e}")
    

# ----------------------------------------
# 🗑️ XOÁ DÒNG ĐIỂM DANH
# ----------------------------------------
with st.expander("Quản lý & xoá dữ liệu điểm danh"):
    try:
        raw_df = read_attendance_csv()  
        if raw_df.empty:
            st.info("Không có dòng nào để xoá.")
        else:
            st.markdown("### Chọn dòng để xoá")
            raw_df = raw_df.reset_index(drop=True)

            for idx, row in raw_df.iterrows():
                col1, col2, col3 = st.columns([4, 4, 1])
                col1.write(f"{row.get('name', '')}")
                col2.write(f"{row.get('date', '')}")
                if col3.button("Xoá", key=f"del_row_{idx}"):
                    raw_df.drop(index=idx, inplace=True)
                    raw_df.to_csv(get_path("data/logs/attendances.csv"), index=False)
                    st.success(f"Đã xoá dòng: {row.get('name', '')} - {row.get('date', '')}")
                    st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi xử lý xoá: {e}")

    
    
# Quản lý tài khoản
st.subheader("Duyệt tài khoản")
users = load_users()
updated = False

for user in users:
    if not user.get("is_admin", False):
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(user["username"])
        allow = col2.checkbox("Cho phép", value=user.get("is_allowed", False), key=user["username"])
        if allow != user.get("is_allowed", False):
            user["is_allowed"] = allow
            updated = True
        if col3.button("Xoá", key="del_" + user["username"]):
            users.remove(user)
            updated = True
            break
if updated:
    try:
        save_users(users)
        st.success("Đã cập nhật tài khoản")
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi lưu tài khoản: {e}")