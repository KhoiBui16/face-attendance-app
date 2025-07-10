import streamlit as st
import time
from utils.auth import login_page, register_page
from utils.user_utils import is_logged_in, is_admin
from modules.admin import main as admin_main
from modules.attendance import main as attendance_main


def main():
    st.set_page_config(page_title="📷 Ứng dụng điểm danh khuôn mặt", layout="centered")

    if "page" not in st.session_state:
        st.session_state.page = "login"

    if "last_page" not in st.session_state:
        st.session_state.last_page = None
    if "last_login_state" not in st.session_state:
        st.session_state.last_login_state = None
    if "last_user_role" not in st.session_state:
        st.session_state.last_user_role = None
    if "last_action_trigger" not in st.session_state:
        st.session_state.last_action_trigger = 0
    if "last_printed_state" not in st.session_state:
        st.session_state.last_printed_state = None
    if "last_print_time" not in st.session_state:
        st.session_state.last_print_time = 0

    current_page = st.session_state.page
    current_login_state = is_logged_in()
    current_user_role = ("admin" if is_admin() else "user" if current_login_state else None)
    
    last_page = st.session_state.last_page
    last_login_state = st.session_state.last_login_state
    last_user_role = st.session_state.last_user_role

    current_state_key = f"{current_page}_{current_login_state}_{current_user_role}"
    if (current_page != last_page or current_login_state != last_login_state or current_user_role != last_user_role):
        if (st.session_state.last_printed_state != current_state_key and time.time() - st.session_state.last_print_time > 1):
            if not current_login_state:
                if current_page == "register":
                    print("\n[TRANG ĐĂNG KÝ]...")
                else:
                    print("\n[TRANG ĐĂNG NHẬP]...")
            else:
                if is_admin():
                    print("[ADMIN] đang thực hiện...")
                else:
                    print("[USER] đang thực hiện...")
            st.session_state.last_printed_state = current_state_key
            st.session_state.last_print_time = time.time()

        st.session_state.last_page = current_page
        st.session_state.last_login_state = current_login_state
        st.session_state.last_user_role = current_user_role
        st.session_state.last_action_trigger += 1

    if not is_logged_in():
        if st.session_state.page == "register":
            register_page()
        else:
            login_page()
    else:
        if is_admin():
            admin_main()
        else:
            if st.session_state.get("just_logged_in", False):
                st.session_state.page = "Điểm danh"
                st.session_state.just_logged_in = False
                st.rerun()
            attendance_main()


if __name__ == "__main__":
    main()
