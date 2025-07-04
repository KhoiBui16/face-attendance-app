import streamlit as st
from utils.auth import login_page, register_page
from utils.user_utils import is_logged_in, is_admin
from pages.admin import main as admin_main
from pages.attendance import main as attendance_main


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
            admin_main()
        else:
            # Người dùng thông thường

            # Lần đầu đăng nhập xong thì chuyển hướng
            if st.session_state.get("just_logged_in", False):
                st.session_state.page = "Điểm danh"
                st.session_state.just_logged_in = False
                st.rerun()

            attendance_main()


if __name__ == "__main__":
    main()
