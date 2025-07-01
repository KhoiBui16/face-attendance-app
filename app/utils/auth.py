import streamlit as st
import json
import os
from utils.helpers import get_path
from utils.user_utils import is_logged_in

USERS_FILE = get_path("data/users.json")

def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Lỗi khi đọc file users.json: {e}")
        return []

def save_users(users):
    try:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Lỗi khi lưu file users.json: {e}")

def ensure_admin_user():
    users = load_users()
    if not any(u.get("is_admin", False) for u in users):
        users.append({
            "username": "admin",
            "password": "admin",
            "is_admin": True,
            "is_allowed": True
        })
        save_users(users)
        st.info("Tài khoản admin mặc định đã được tạo.")

def login_page():
    ensure_admin_user()
    st.title("Đăng nhập")
    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")

    if st.button("Đăng nhập"):
        if not username or not password:
            st.warning("Vui lòng nhập đầy đủ thông tin")
            return

        users = load_users()
        user = next((u for u in users if u["username"] == username), None)
        if not user:
            st.error("Tên đăng nhập không tồn tại.")
            return

        if user["password"] != password:
            st.error("Sai mật khẩu.")
            return

        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.is_admin = user.get("is_admin", False)
        st.session_state.is_allowed = user.get("is_allowed", False)
        st.session_state.just_logged_in = True
        # st.write(f"[DEBUG] Đăng nhập thành công: username={username}, is_admin={st.session_state.is_admin}, is_allowed={st.session_state.is_allowed}")
        st.rerun()

    # Nút Đăng ký
    if st.button("Đăng ký"):
        st.session_state.page = "register"
        st.rerun()

    # Nút Quay lại (chuyển về attendance.py, chỉ hiển thị nếu đã đăng nhập)
    if is_logged_in():
        if st.button("Quay lại trang điểm danh"):
            if os.path.exists("pages/attendance.py"):
                st.switch_page("pages/attendance.py")
            else:
                st.error("Không tìm thấy trang điểm danh. Kiểm tra file `pages/attendance.py`.")

def register_page():
    st.title("Đăng ký tài khoản")
    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")
    confirm = st.text_input("Nhập lại mật khẩu", type="password")

    if st.button("Đăng ký"):
        if not username or not password or not confirm:
            st.warning("Vui lòng nhập đầy đủ thông tin!")
            return
        if password != confirm:
            st.error("Mật khẩu không khớp.")
            return

        users = load_users()
        if any(u["username"] == username for u in users):
            st.error("Tên đăng nhập đã tồn tại!")
            return

        users.append({
            "username": username,
            "password": password,
            "is_allowed": False,
            "is_admin": False
        })
        save_users(users)
        st.success("Đăng ký thành công! Vui lòng chờ admin duyệt tài khoản.")

    if st.button("Quay lại đăng nhập"):
        st.session_state.page = "login"
        st.rerun()

def logout():
    for key in ["logged_in", "username", "is_admin", "is_allowed", "just_logged_in", "page"]:
        st.session_state.pop(key, None)
    st.rerun()
    
