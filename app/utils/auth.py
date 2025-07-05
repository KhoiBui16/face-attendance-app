# app/utils/auth.py
import streamlit as st
import json
import os
from utils.user_utils import is_logged_in

USERS_FILE = "data/users.json"


def load_users():
    """Tải danh sách người dùng từ file users.json."""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    st.error("File users.json phải chứa một mảng danh sách người dùng.")
                    return []
                print(f"[DEBUG] Đã tải {len(data)} người dùng từ {USERS_FILE}")
                return data
        print(f"[DEBUG] File {USERS_FILE} không tồn tại, trả về danh sách rỗng.")
        return []
    except json.JSONDecodeError as e:
        st.error(f"Lỗi cú pháp trong file users.json: {e}")
        print(f"[LỖI] Nội dung file users.json không hợp lệ: {e}")
        return []
    except Exception as e:
        st.error(f"Lỗi khi đọc file users.json: {e}")
        print(f"[LỖI] Lỗi khi đọc file users.json: {e}")
        return []


def save_users(users):
    """Lưu danh sách người dùng vào file users.json."""
    try:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] Đã lưu danh sách người dùng vào {USERS_FILE}")
    except Exception as e:
        st.error(f"Lỗi khi lưu file users.json: {e}")
        print(f"[LỖI] Lỗi khi lưu file users.json: {e}")


def ensure_admin_user():
    """Đảm bảo tài khoản admin mặc định tồn tại."""
    users = load_users()
    if not any(u.get("is_admin", False) for u in users):
        users.append(
            {
                "username": "admin",
                "password": "admin123",
                "is_admin": True,
                "is_allowed": True,
            }
        )
        save_users(users)
        print("[DEBUG] Tài khoản admin mặc định đã được tạo.")
        st.info("Tài khoản admin mặc định đã được tạo.")


def login_page():
    """Trang đăng nhập."""
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
        print(
            f"[DEBUG] Đăng nhập thành công: username={username}, is_admin={st.session_state.is_admin}, is_allowed={st.session_state.is_allowed}"
        )
        st.rerun()

    if st.button("Đăng ký"):
        st.session_state.page = "register"
        st.rerun()

    if is_logged_in():
        if st.button("Quay lại trang điểm danh"):
            if os.path.exists("pages/attendance.py"):
                st.switch_page("pages/attendance.py")
            else:
                st.error(
                    "Không tìm thấy trang điểm danh. Kiểm tra file `pages/attendance.py`."
                )


def register_page():
    """Trang đăng ký tài khoản."""
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

        users.append(
            {
                "username": username,
                "password": password,
                "is_allowed": False,
                "is_admin": False,
            }
        )
        save_users(users)
        st.success("Đăng ký thành công! Vui lòng chờ admin duyệt tài khoản.")

    if st.button("Quay lại đăng nhập"):
        st.session_state.page = "login"
        st.rerun()


def logout():
    """Đăng xuất người dùng."""
    for key in [
        "logged_in",
        "username",
        "is_admin",
        "is_allowed",
        "just_logged_in",
        "page",
    ]:
        st.session_state.pop(key, None)
    print("[DEBUG] Đã đăng xuất người dùng.")
    st.rerun()
