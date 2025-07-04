import pickle
import streamlit as st
from core.train_model import train_model
from core.data_collector.webcam_data_collector import collect_data_from_webcam
from core.data_collector.video_data_collector import collect_data_from_uploaded_video
from utils.helpers import (
    read_attendance_csv,
    preprocess_attendance,
    get_path,
    save_uploaded_video,
    read_all_attendance_csv,
    append_attendance_log,
)
from utils.auth import logout, load_users, save_users
from utils.user_utils import is_admin, is_logged_in

# Sidebar
if is_logged_in():
    st.sidebar.title("Điều hướng")
    st.sidebar.write(f"Đăng nhập với: {st.session_state.get('username', 'N/A')}")
    st.sidebar.write(f"Quyền: {'Admin' if is_admin() else 'Người dùng'}")
    if st.sidebar.button("Đăng xuất"):
        logout()
        st.rerun()

st.title("Trang quản trị viên")


if not is_admin():
    st.warning("Bạn không có quyền truy cập trang này.")
    # st.write(f"[DEBUG] is_admin: {st.session_state.get('is_admin', False)}, is_allowed: {st.session_state.get('is_allowed', False)}")
    st.stop()


# Thu thập dữ liệu mới và huấn luyện
st.subheader("Thu thập dữ liệu và huấn luyện")
name = st.text_input("Nhập tên nhân viên để thu thập:")
upload_option = st.radio(
    "Chọn nguồn thu thập", ["Webcam", "Tải video"], horizontal=True
)
video_file = None

# Khởi tạo biến lưu video tạm trong session_state
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None

if upload_option == "Tải video":
    video_file = st.file_uploader(
        "Tải lên video khuôn mặt (mp4, avi)", type=["mp4", "avi"]
    )
    if video_file is not None:
        # THAY ĐỔI: Lưu video tạm vào session_state thay vì lưu ngay vào thư mục
        st.session_state.uploaded_video = video_file
        st.success("✅ Video đã được tải lên, sẵn sàng để thu thập.")
    else:
        # Xóa video tạm nếu không có file mới
        st.session_state.uploaded_video = None


if st.button("Bắt đầu thu thập") and name:
    if not name:
        st.error("Vui lòng nhập tên nhân viên trước khi thu thập.")
        st.stop()

    with st.spinner("Đang thu thập dữ liệu..."):
        try:
            saved_video_path = None
            if upload_option == "Tải video":
                
                if st.session_state.uploaded_video is None:
                    st.error("Vui lòng tải lên video trước.")
                    st.stop()
                    
                # THAY ĐỔI: Lưu video vào thư mục chỉ khi nhấn "Bắt đầu thu thập"
                saved_video_path = save_uploaded_video(
                    video_file=st.session_state.uploaded_video,
                    username=name,
                    action="collect",
                )
                
                if not saved_video_path:
                    st.error("❌ Lỗi khi lưu video.")
                    st.stop()

            # Thu thập dữ liệu
            if upload_option == "Webcam":
                success = collect_data_from_webcam(
                    name, num_samples=30, save_dir=get_path("data/dataset")
                )
            else:
                success = collect_data_from_uploaded_video(
                    video_path=saved_video_path,
                    name=name,
                    save_dir=get_path("data/dataset"),
                    num_samples=30,
                )

            if success:
                label_path = get_path("data/dataset/names.pkl")
                with open(label_path, "rb") as f:
                    labels = pickle.load(f)
                if len(set(labels)) < 2:
                    st.warning(
                        f"Chỉ có {len(set(labels))} nhãn ({set(labels)}). Cần ≥2 nhãn để huấn luyện. Dữ liệu đã lưu, vui lòng thu thập thêm."
                    )
                else:
                    success_train = train_model(
                        face_path=get_path("data/dataset/faces.pkl"),
                        label_path=label_path,
                        save_path=get_path("data/models/model.pkl"),
                        model_type="svm",
                    )

                    if success_train:
                        st.success(f"Đã thu thập và huấn luyện xong cho: {name}")
                        # if saved_video_path:
                        #     st.success(f"✅ Video đã được lưu tại {saved_video_path}")
                    else:
                        st.error("Lỗi khi huấn luyện mô hình.")
            else:
                st.error("Không thu thập được dữ liệu. Vui lòng kiểm tra video/webcam.")
        except Exception as e:
            st.error(f"Lỗi khi thu thập hoặc huấn luyện: {e}")


# Hiển thị bảng điểm danh
st.subheader("Bảng điểm danh")
try:
    data, _ = read_all_attendance_csv()
    summary_df = preprocess_attendance(data)
    st.dataframe(summary_df, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi khi đọc dữ liệu điểm danh: {e}")


# Xóa dòng điểm danh
with st.expander("Quản lý & xoá dữ liệu điểm danh"):
    try:
        raw_df, user_files = read_all_attendance_csv()
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
                    username = row.get("username")
                    if username in user_files:
                        user_df = read_attendance_csv(username=username)
                        # Tìm bản ghi tương ứng trong user_df
                        mask = (
                            (user_df["name"] == row.get("name"))
                            & (user_df["date"] == row.get("date"))
                            & (user_df["time-check-in"] == row.get("time-check-in"))
                        )
                        if mask.any():
                            user_df = user_df[~mask].reset_index(drop=True)
                            user_df.to_csv(user_files[username], index=False)
                            st.success(
                                f"Đã xoá dòng: {row.get('name', '')} - {row.get('date', '')}"
                            )
                            st.rerun()
                        else:
                            st.error(f"Không tìm thấy bản ghi tương ứng cho {username}")
                    else:
                        st.error(f"Không tìm thấy tệp điểm danh cho {username}")
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
        allow = col2.checkbox(
            "Cho phép", value=user.get("is_allowed", False), key=user["username"]
        )
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
