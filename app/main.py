import streamlit as st
import os
from utils.auth import login_page, register_page
from utils.user_utils import is_logged_in, is_admin

def main():
    st.set_page_config(page_title="📷 Face Attendance App", layout="centered")

    if "page" not in st.session_state:
        st.session_state.page = "login"

    # Debug trạng thái
    # st.write(f"[DEBUG] Trạng thái: logged_in={st.session_state.get('logged_in', False)}, "
            #  f"username={st.session_state.get('username', 'N/A')}, "
            #  f"is_admin={st.session_state.get('is_admin', False)}, "
            #  f"is_allowed={st.session_state.get('is_allowed', False)}")

    if not is_logged_in():
        if st.session_state.page == "register":
            register_page()
        else:
            login_page()
    else:
        if is_admin():
            if os.path.exists("pages/admin.py"):
                st.switch_page("pages/admin.py")
            else:
                st.error("Không tìm thấy trang quản trị. Kiểm tra file `pages/admin.py`.")
                st.stop()
        else:
            st.sidebar.title("Điều hướng")
            st.sidebar.text(f"Đăng nhập với: {st.session_state.username}")
            st.sidebar.text(f"Quyền: Người dùng")

            page = st.sidebar.radio("Chọn trang", ["Điểm danh"], index=0)
            # st.write(f"[DEBUG] Trang được chọn: {page}")

            if st.session_state.get("just_logged_in", False):
                st.session_state.page = "Điểm danh"
                st.session_state.just_logged_in = False
                st.rerun()

            if os.path.exists("pages/attendance.py"):
                st.switch_page("pages/attendance.py")
            else:
                st.error("Không tìm thấy trang điểm danh. Kiểm tra file `pages/attendance.py`.")
                st.stop()

if __name__ == "__main__":
    main()