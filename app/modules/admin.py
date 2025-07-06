import pickle
import streamlit as st
import requests
import os
from urllib.parse import urlparse
from core.train_model import train_model
from core.data_collector.webcam_data_collector import collect_data_from_webcam
from core.data_collector.video_data_collector import collect_data_from_uploaded_video
from utils.auth import logout, load_users, save_users
from utils.user_utils import is_admin, is_logged_in
from utils.helpers import (
    read_attendance_csv,
    preprocess_attendance,
    save_uploaded_video,
    read_all_attendance_csv,
)

# -------------------------------------------------------------
# ONE‑SHOT callback để thu thập & huấn luyện
# -------------------------------------------------------------


def _collect_and_train(name: str, upload_option: str, uploaded_video, video_url):
    """Callback cho nút Thu thập – chạy đúng 1 lần, tránh log trùng."""
    if not name:
        st.error("Vui lòng nhập tên nhân viên trước khi thu thập.")
        return

    if st.session_state.get("is_collecting", False):
        st.warning("Đang có tiến trình thu thập khác. Vui lòng đợi…")
        return

    st.session_state.is_collecting = True

    try:
        print(f"\n[INFO] Bắt đầu thu thập dữ liệu cho '{name}'…")

        # ----------------- Lấy và lưu video nguồn -----------------
        saved_video_path = None
        if upload_option == "Tải video":
            if uploaded_video is None:
                st.error("Vui lòng tải video trước.")
                return
            saved_video_path = save_uploaded_video(
                video_file=uploaded_video,
                username=name,
                action="collect",
            )
            if not saved_video_path:
                st.error("❌ Lỗi khi lưu video.")
                return

        elif upload_option == "URL":
            if not video_url:
                st.error("Vui lòng nhập URL video trước.")
                return
            parsed = urlparse(video_url)
            if not parsed.scheme or not parsed.netloc:
                st.error("❌ URL video không hợp lệ (thiếu http/https).")
                return
            resp = requests.get(video_url, stream=True, timeout=30)
            if resp.status_code != 200:
                st.error(f"❌ Không tải được video: HTTP {resp.status_code}")
                return
            temp_video_path = f"data/temp/{name}_temp_video.mp4"
            os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)
            with open(temp_video_path, "wb") as fp:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        fp.write(chunk)
            saved_video_path = temp_video_path

        # ----------------- Thu thập dữ liệu -----------------------
        with st.spinner("Đang thu thập dữ liệu…"):
            if upload_option == "Webcam":
                success = collect_data_from_webcam(
                    name, num_samples=30, save_dir="data/dataset"
                )
            else:
                success = collect_data_from_uploaded_video(
                    video_path=saved_video_path,
                    name=name,
                    save_dir="data/dataset",
                    num_samples=30,
                )

        # Dọn temp
        if (
            upload_option == "URL"
            and saved_video_path
            and os.path.exists(saved_video_path)
        ):
            os.remove(saved_video_path)

        # ----------------- Huấn luyện & LOG SUCCESS --------------
        if success:
            with open("data/dataset/names.pkl", "rb") as f:
                labels = pickle.load(f)

            if st.session_state.get("logged_collect_success") != name:
                print(f"[SUCCESS] Đã lưu {len(labels)} ảnh và nhãn.")
                print(f"[SUCCESS] Thu thập & huấn luyện thành công cho {name}")
                st.session_state.logged_collect_success = name

            if len(set(labels)) >= 2:
                with st.spinner("Huấn luyện model…"):
                    ok = train_model(
                        face_path="data/dataset/faces.pkl",
                        label_path="data/dataset/names.pkl",
                        save_path="data/models/model.pkl",
                        model_type="svm",
                    )
                if ok:
                    st.success(f"Đã hoàn tất cho: {name}")
            else:
                st.warning(
                    f"Chỉ có {len(set(labels))} nhãn ({set(labels)}). Cần ≥2 để huấn luyện. Vui lòng thu thập thêm."
                )
        else:
            st.error("Không thu thập được dữ liệu. Kiểm tra nguồn video/webcam.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
    finally:
        st.session_state.is_collecting = False


# -------------------------------------------------------------
# MAIN ADMIN PAGE
# -------------------------------------------------------------


def main():
    if "admin_page_entered" not in st.session_state:
        print("[TRANG QUẢN TRỊ] Đã vào trang admin…")
        st.session_state.admin_page_entered = True

    # ---------- Sidebar & Auth ----------
    if is_logged_in():
        st.sidebar.title("Điều hướng")
        st.sidebar.text(f"Đăng nhập: {st.session_state.get('username', 'N/A')}")
        st.sidebar.text("Quyền: Admin" if is_admin() else "Quyền: Người dùng")
        if st.sidebar.button("Đăng xuất"):
            logout()
            st.rerun()

    st.title("Trang quản trị viên")
    if not is_admin():
        st.warning("Bạn không có quyền truy cập trang này.")
        return

    # ---------- Thu thập dữ liệu ----------
    st.subheader("Thu thập dữ liệu và huấn luyện")
    name = st.text_input("Nhập tên nhân viên:")
    upload_option = st.radio(
        "Nguồn thu thập", ["Webcam", "Tải video", "URL"], horizontal=True
    )

    # Holder cho video/url
    if "uploaded_video" not in st.session_state:
        st.session_state.uploaded_video = None

    uploaded_video = None
    video_url = None

    if upload_option == "Tải video":
        uploaded_video = st.file_uploader(
            "Chọn video (mp4/avi)", type=["mp4", "avi"], key="video_uploader"
        )
        if uploaded_video is not None:
            st.session_state.uploaded_video = uploaded_video
            st.success("✅ Đã tải video.")
        else:
            st.session_state.uploaded_video = None

    elif upload_option == "URL":
        video_url = st.text_input("URL video")
        if video_url:
            if "github.com" in video_url and "blob" in video_url:
                video_url = video_url.replace(
                    "github.com", "raw.githubusercontent.com"
                ).replace("/blob/", "/")
            st.session_state.uploaded_video = video_url
            st.success("✅ Đã nhập URL.")

    if st.button("Bắt đầu thu thập"):
        _collect_and_train(
            name=name,
            upload_option=upload_option,
            uploaded_video=st.session_state.uploaded_video,
            video_url=video_url,
        )

    # ---------- Bảng điểm danh ----------
    st.subheader("Bảng điểm danh")
    try:
        data, _ = read_all_attendance_csv()
        summary_df = preprocess_attendance(data)
        st.dataframe(summary_df, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi khi đọc dữ liệu điểm danh: {e}")

    # ---------- Xoá điểm danh ----------
    with st.expander("Quản lý & xoá dữ liệu điểm danh"):
        try:
            raw_df, user_files = read_all_attendance_csv()
            if raw_df.empty:
                st.info("Không có dòng nào để xoá.")
            else:
                raw_df = raw_df.reset_index(drop=True)
                for idx, row in raw_df.iterrows():
                    col1, col2, col3 = st.columns([4, 4, 1])
                    col1.write(row.get("name", ""))
                    col2.write(row.get("date", ""))
                    if col3.button("Xoá", key=f"del_row_{idx}"):
                        username = row.get("username")
                        if username in user_files:
                            user_df = read_attendance_csv(username=username)
                            mask = (
                                (user_df["name"] == row.get("name"))
                                & (user_df["date"] == row.get("date"))
                                & (user_df["time-check-in"] == row.get("time-check-in"))
                            )
                            if mask.any():
                                user_df = user_df[~mask].reset_index(drop=True)
                                user_df.to_csv(user_files[username], index=False)
                                st.success("Đã xoá bản ghi.")
                                st.rerun()
                            else:
                                st.error("Không tìm thấy bản ghi tương ứng.")
                        else:
                            st.error("Không tìm thấy tệp của người dùng.")
        except Exception as e:
            st.error(f"Lỗi khi xử lý xoá: {e}")

    # ---------- Duyệt tài khoản ----------
    st.subheader("Duyệt tài khoản")
    users = load_users()
    updated = False
    for user in users:
        if not user.get("is_admin", False):
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.text(user["username"])
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


if __name__ == "__main__":
    main()
