import os
import streamlit as st
import requests
from core.recognize_and_log import recognize_and_log
from utils.helpers import get_path, load_attendance_history, display_message
from utils.auth import logout
from utils.user_utils import is_logged_in


def main():
    # Sidebar
    if is_logged_in():
        st.sidebar.title("Điều hướng")
        st.sidebar.text(f"👤 Tài khoản: {st.session_state.get('username', 'N/A')}")
        st.sidebar.text(
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

    # Làm mới attendance_df mỗi khi username thay đổi hoặc trang tải lại
    if (
        "attendance_df" not in st.session_state
        or st.session_state.get("last_username") != username
    ):
        st.session_state.attendance_df = load_attendance_history(username=username)
        st.session_state.last_username = username
        print(
            f"[DEBUG] Refreshed attendance_df for {username}, shape={st.session_state.attendance_df.shape}"
        )

    # Khởi tạo session state cho result_message
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
    input_source = st.radio(
        "Nguồn điểm danh:", ["Webcam", "Tải video", "URL"], horizontal=True
    )
    video_file = None
    video_url = None

    if input_source == "Tải video":
        video_file = st.file_uploader(
            "Tải lên video khuôn mặt (mp4, avi)", type=["mp4", "avi"]
        )
    elif input_source == "URL":
        video_url = st.text_input(
            "Nhập URL video (mp4, avi):", placeholder="https://example.com/video.mp4"
        )
        if video_url:
            # Convert GitHub URL to raw URL if necessary
            if "github.com" in video_url and "blob" in video_url:
                video_url = video_url.replace(
                    "github.com", "raw.githubusercontent.com"
                ).replace("/blob/", "/")
            st.success("✅ URL đã được nhập, sẵn sàng để điểm danh.")

    col1, col2 = st.columns(2)

    def handle_check_in(input_source, video_file, video_url, username):
        """
        Xử lý hành động check-in.
        - input_source: "Webcam", "Tải video", hoặc "URL"
        - video_file: File video upload (nếu có)
        - video_url: URL video (nếu có)
        - username: Tên người dùng
        """
        temp_video_path = None
        if input_source == "Tải video" and video_file is None:
            st.session_state.result_message = (
                "❌ Vui lòng tải lên video trước khi check-in."
            )
            st.session_state.last_action = "check-in"
            display_message(st.session_state.result_message, is_success=False)
        elif input_source == "URL" and not video_url:
            st.session_state.result_message = (
                "❌ Vui lòng nhập URL video trước khi check-in."
            )
            st.session_state.last_action = "check-in"
            display_message(st.session_state.result_message, is_success=False)
        else:
            with st.spinner("Đang nhận diện..."):
                try:
                    if input_source == "URL":
                        try:
                            # Download video from URL
                            response = requests.get(video_url, stream=True)
                            if response.status_code != 200:
                                st.session_state.result_message = f"❌ Lỗi khi tải video từ URL: HTTP {response.status_code}"
                                st.session_state.last_action = "check-in"
                                display_message(
                                    st.session_state.result_message, is_success=False
                                )
                                return
                            # Check if content type is video
                            content_type = response.headers.get("content-type", "")
                            if not content_type.startswith("video/"):
                                st.session_state.result_message = (
                                    "❌ URL không dẫn đến tệp video hợp lệ (mp4, avi)."
                                )
                                st.session_state.last_action = "check-in"
                                display_message(
                                    st.session_state.result_message, is_success=False
                                )
                                return
                            # Save video temporarily
                            temp_video_path = get_path(
                                f"data/temp/{username}_temp_checkin.mp4"
                            )
                            os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)
                            with open(temp_video_path, "wb") as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            video_file = temp_video_path
                        except Exception as e:
                            st.session_state.result_message = (
                                f"❌ Lỗi khi tải video từ URL: {e}"
                            )
                            st.session_state.last_action = "check-in"
                            display_message(
                                st.session_state.result_message, is_success=False
                            )
                            return

                    success, message = recognize_and_log(
                        action="check-in",
                        video_file=(
                            video_file if input_source in ["Tải video", "URL"] else None
                        ),
                    )
                    st.session_state.result_message = message
                    st.session_state.last_action = "check-in"
                    display_message(message=message, is_success=success)
                    if success:
                        st.session_state.attendance_df = load_attendance_history(
                            username=username
                        )
                        st.session_state.result_message = None
                        st.session_state.last_action = None
                        st.rerun()
                finally:
                    # Clean up temporary video file if created
                    if temp_video_path and os.path.exists(temp_video_path):
                        os.remove(temp_video_path)

    def handle_check_out(input_source, video_file, video_url, username):
        """
        Xử lý hành động check-out.
        - input_source: "Webcam", "Tải video", hoặc "URL"
        - video_file: File video upload (nếu có)
        - video_url: URL video (nếu có)
        - username: Tên người dùng
        """
        temp_video_path = None
        if input_source == "Tải video" and video_file is None:
            st.session_state.result_message = (
                "❌ Vui lòng tải lên video trước khi check-out."
            )
            st.session_state.last_action = "check-out"
            display_message(st.session_state.result_message, is_success=False)
        elif input_source == "URL" and not video_url:
            st.session_state.result_message = (
                "❌ Vui lòng nhập URL video trước khi check-out."
            )
            st.session_state.last_action = "check-out"
            display_message(st.session_state.result_message, is_success=False)
        else:
            with st.spinner("Đang nhận diện..."):
                try:
                    if input_source == "URL":
                        try:
                            # Download video from URL
                            response = requests.get(video_url, stream=True)
                            if response.status_code != 200:
                                st.session_state.result_message = f"❌ Lỗi khi tải video từ URL: HTTP {response.status_code}"
                                st.session_state.last_action = "check-out"
                                display_message(
                                    st.session_state.result_message, is_success=False
                                )
                                return
                            # Check if content type is video
                            content_type = response.headers.get("content-type", "")
                            if not content_type.startswith("video/"):
                                st.session_state.result_message = (
                                    "❌ URL không dẫn đến tệp video hợp lệ (mp4, avi)."
                                )
                                st.session_state.last_action = "check-out"
                                display_message(
                                    st.session_state.result_message, is_success=False
                                )
                                return
                            # Save video temporarily
                            temp_video_path = get_path(
                                f"data/temp/{username}_temp_checkout.mp4"
                            )
                            os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)
                            with open(temp_video_path, "wb") as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            video_file = temp_video_path
                        except Exception as e:
                            st.session_state.result_message = (
                                f"❌ Lỗi khi tải video từ URL: {e}"
                            )
                            st.session_state.last_action = "check-out"
                            display_message(
                                st.session_state.result_message, is_success=False
                            )
                            return

                    success, message = recognize_and_log(
                        action="check-out",
                        video_file=(
                            video_file if input_source in ["Tải video", "URL"] else None
                        ),
                    )
                    st.session_state.result_message = message
                    st.session_state.last_action = "check-out"
                    display_message(message=message, is_success=success)
                    if success:
                        st.session_state.attendance_df = load_attendance_history(
                            username=username
                        )
                        st.session_state.result_message = None
                        st.session_state.last_action = None
                        st.rerun()
                finally:
                    # Clean up temporary video file if created
                    if temp_video_path and os.path.exists(temp_video_path):
                        os.remove(temp_video_path)

    with col1:
        if st.button("Check-in"):
            handle_check_in(
                input_source=input_source,
                video_file=video_file,
                video_url=video_url,
                username=username,
            )

    with col2:
        if st.button("Check-out"):
            handle_check_out(
                input_source=input_source,
                video_file=video_file,
                video_url=video_url,
                username=username,
            )

    # Hiển thị kết quả nhận diện
    if st.session_state.result_message:
        if st.session_state.result_message.startswith("✅"):
            pass  # Bỏ hiển thị lặp vì đã hiển thị trong Check-in/Check-out
        elif (
            st.session_state.last_action == "check-in"
            and st.session_state.result_message
            == "❌ Khuôn mặt không xác định (unknown)"
        ):
            display_message(st.session_state.result_message, is_success=False)
            if st.button("Thử lại"):
                st.session_state.result_message = None
                st.session_state.last_action = None
                if input_source == "Tải video":
                    st.file_uploader(
                        "Tải lên video khuôn mặt (mp4, avi)",
                        type=["mp4", "avi"],
                        key="video_uploader_reset",
                    )
                elif input_source == "URL":
                    st.text_input(
                        "Nhập URL video (mp4, avi):",
                        placeholder="https://example.com/video.mp4",
                        key="url_reset",
                    )
                st.rerun()
        else:
            display_message(st.session_state.result_message, is_success=False)


if __name__ == "__main__":
    main()
