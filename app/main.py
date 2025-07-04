import streamlit as st
from utils.auth import login_page, register_page
from utils.user_utils import is_logged_in, is_admin


def main():
    st.set_page_config(page_title="📷 Face Attendance App", layout="centered")

    if "page" not in st.session_state:
        st.session_state.page = "login"

    # Kiểm tra trạng thái đăng nhập
    if not is_logged_in():
        if st.session_state.page == "register":
            register_page()
        else:
            login_page()
    else:
        # Nếu là admin → chuyển sang trang quản trị
        if is_admin():
            # ⚠ Đặt đúng tên như trong st.set_page_config(page_title="...")
            st.switch_page("Trang quản trị viên")
        else:
            # Người dùng thông thường
            st.sidebar.title("Điều hướng")
            st.sidebar.text(f"👤 Đăng nhập: {st.session_state.username}")
            st.sidebar.text(f"🔐 Quyền: Người dùng")

            # Điều hướng đơn giản
            page = st.sidebar.radio("Chọn trang", ["Điểm danh"], index=0)

            # Lần đầu đăng nhập xong thì chuyển hướng
            if st.session_state.get("just_logged_in", False):
                st.session_state.page = "Điểm danh"
                st.session_state.just_logged_in = False
                st.rerun()

            # ⚠ Đúng tên như đặt ở `page_title` trong `attendance.py`
            st.switch_page("Trang điểm danh")


if __name__ == "__main__":
    main()
