import os
import time
import pandas as pd
from datetime import datetime
import cv2
import pickle
import streamlit as st


def get_project_root():
    """Get the absolute path to the project root directory."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print(f"[DEBUG] Project root: {root}")
    return root

def get_path(relative_path):
    """Get absolute path from project root."""
    path = os.path.join(get_project_root(), relative_path)
    print(f"[DEBUG] Resolved path for {relative_path}: {path}")
    return path


def read_attendance_csv(username=None):
    """Đọc dữ liệu điểm danh từ tệp của người dùng hoặc tệp chung (cho admin)."""
    if username:
        # THAY ĐỔI: Đọc từ tệp riêng của người dùng
        log_file = get_path(f"data/logs/attendances_{username}.csv")
    else:
        # Tệp chung cho admin
        log_file = get_path("data/logs/attendances.csv")
        
    try:
        if not os.path.exists(log_file):
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            df = pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
            df.to_csv(log_file, index=False)
            print(f"[DEBUG] Created new attendance CSV: {log_file}")
            return df
        
        df = pd.read_csv(log_file)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
        df["time-check-in"] = pd.to_datetime(df["time-check-in"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df["time-check-out"] = pd.to_datetime(df["time-check-out"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        print(f"[DEBUG] Loaded attendance CSV: {log_file}, shape={df.shape}, columns={df.columns.tolist()}")
        return df
    
    except Exception as e:
        print(f"[ERROR] Failed to read attendance CSV: {e}")
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])

# Hàm tải và gộp dữ liệu điểm danh từ tất cả người dùng
def read_all_attendance_csv():
    """Tải và gộp dữ liệu điểm danh từ tất cả các tệp của người dùng."""
    log_dir = get_path("data/logs")
    os.makedirs(log_dir, exist_ok=True)
    all_dfs = []
    user_files = {}  # Lưu ánh xạ: username -> file_path
    
    try:
        # Tìm tất cả các tệp attendances_{username}.csv
        for file_name in os.listdir(log_dir):
            if file_name.startswith("attendances_") and file_name.endswith(".csv"):
                username = file_name.replace("attendances_", "").replace(".csv", "")
                file_path = os.path.join(log_dir, file_name)
                user_files[username] = file_path
                try:
                    df = read_attendance_csv(username=username)
                    if not df.empty:
                        # Thêm cột username để theo dõi nguồn dữ liệu
                        df = df.assign(username=username)
                        all_dfs.append(df)
                    print(f"[DEBUG] Loaded attendance CSV for {username}: {file_path}, shape={df.shape}")
                except Exception as e:
                    print(f"[ERROR] Failed to read {file_path}: {e}")
        
        if not all_dfs:
            print("[DEBUG] No attendance CSV files found")
            return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"]), {}
        
        # Gộp tất cả DataFrame
        combined_df = pd.concat(all_dfs, ignore_index=True)
        print(f"[DEBUG] Combined attendance CSV, shape={combined_df.shape}")
        return combined_df, user_files
    
    except Exception as e:
        print(f"[ERROR] Failed to read attendance CSVs: {e}")
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"]), {}

def preprocess_attendance(df):
    """Preprocess attendance data for display."""
    if df.empty:
        print(f"[DEBUG] DataFrame is empty in preprocess_attendance")
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
    return df[["name", "date", "time-check-in", "time-check-out", "time-working", "position"]]

def append_attendance_log(name, image, position, action):
    """Append or update attendance log and save image."""
    # THAY ĐỔI: Sử dụng tệp riêng cho người dùng
    log_file = get_path(f"data/logs/attendances_{name}.csv")
    date = datetime.now().strftime("%Y-%m-%d")
    image_dir = get_path(f"data/logs/images/by_date/{date}")
    os.makedirs(image_dir, exist_ok=True)
    
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    image_name = f"{name}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    image_path = os.path.join(image_dir, image_name)
    
    if image is not None:
        try:
            cv2.imwrite(image_path, image)
            print(f"[DEBUG] Saved image to {image_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save image {image_path}: {e}")
    
    df = read_attendance_csv(username=name)
    print(f"[DEBUG] Before append, DataFrame shape: {df.shape}, action={action}, name={name}")
    
    if action == "check-in":
        # THAY ĐỔI: Kiểm tra xem đã có bản ghi check-in hôm nay chưa
        mask = (df["name"] == name) & (df["date"].dt.date == pd.to_datetime(date).date()) & (df["time-check-in"].notna())
        if mask.any():
            print(f"[DEBUG] Check-in already exists for {name} on {date}")
            return False, f"{name} đã check-in hôm nay rồi."
        
        new_record = pd.DataFrame({
            "name": [name],
            "date": [date],
            "time-check-in": [timestamp],
            "time-check-out": [pd.NA],
            "time-working": [pd.NA],
            "position": [position]
        })
        if df.empty:
            df = new_record
        else:
            # THAY ĐỔI: Sử dụng concat để thêm bản ghi mới, tránh ghi đè
            df = pd.concat([df.dropna(how="all"), new_record], ignore_index=True)
            
    elif action == "check-out":
        mask = (df["name"] == name) & (df["date"].dt.date == pd.to_datetime(date).date()) & (df["time-check-in"].notna()) & (df["time-check-out"].isna())
        print(f"[DEBUG] Check-out mask: {mask.sum()} rows matched")
        
        if mask.any():
            df.loc[mask, "time-check-out"] = timestamp
            df.loc[mask, "time-working"] = df.loc[mask].apply(
                lambda row: round((pd.to_datetime(row["time-check-out"]) - pd.to_datetime(row["time-check-in"])).total_seconds() / 3600, 2),
                axis=1
            )
        else:
            print(f"[DEBUG] No matching check-in record for {name} on {date}")
            return False, f"Không tìm thấy bản ghi check-in cho ngày hôm nay."
    
    try:
        if os.path.exists(log_file):
            if not os.access(log_file, os.W_OK):
                print(f"[ERROR] No write permission for {log_file}")
                return False, f"Không có quyền ghi vào file {log_file}"
            
        # THAY ĐỔI: Ghi vào tệp riêng của người dùng
        df.to_csv(log_file, index=False)
        print(f"[DEBUG] Saved attendance log to {log_file}, new shape={df.shape}, data=\n{df.tail(1)}")
        return True, f"Điểm danh {action} thành công cho {name}"
    except Exception as e:
        print(f"[ERROR] Failed to save attendance log: {e}")
        return False, f"Lỗi khi lưu log điểm danh: {e}"

def is_action_allowed(name: str, action: str) -> tuple[bool, str]:
    """Kiểm tra xem hành động check-in/check-out có được phép thực hiện không."""
    username = st.session_state.get("username", name)
    print(f"[DEBUG] is_action_allowed: input_name={name}, username={username}, action={action}")
    
    # THAY ĐỔI: Đọc từ tệp riêng của người dùng
    df = read_attendance_csv(username = username)
    if df.empty:
        if action == "check-in":
            return True, ""
        else:
            print(f"[DEBUG] Empty DataFrame, cannot check-out for {username}")
            return False, f"{username} chưa check-in nên không thể check-out."

    today = datetime.now().date()
    df_today = df[(df["name"] == username) & (df["date"].dt.date == today)]
    print(f"[DEBUG] df_today rows: {df_today.shape[0]} for {username} on {today}")

    if action == "check-in":
        if not df_today.empty and df_today["time-check-in"].notna().any():
            print(f"[DEBUG] {username} already checked in today")
            return False, f"{username} đã check-in hôm nay rồi."
        else:
            return True, ""
    elif action == "check-out":
        if df_today.empty or not df_today["time-check-in"].notna().any():
            print(f"[DEBUG] No check-in found for {username} today")
            return False, f"{username} chưa check-in nên không thể check-out."
        elif df_today["time-check-out"].notna().any():
            print(f"[DEBUG] {username} already checked out today")
            return False, f"{username} đã check-out hôm nay rồi."
        else:
            return True, ""
    return False, "Hành động không hợp lệ."

def has_trained_data(username):
    """Kiểm tra xem username có dữ liệu khuôn mặt trong names.pkl hay không."""
    label_path = get_path("data/dataset/names.pkl")
    if not os.path.exists(label_path):
        print(f"[DEBUG] File {label_path} không tồn tại.")
        return False
    try:
        with open(label_path, "rb") as f:
            labels = pickle.load(f)
        has_data = username in labels
        print(f"[DEBUG] Kiểm tra dữ liệu khuôn mặt cho {username}: {has_data}")
        return has_data
    except Exception as e:
        print(f"[ERROR] Lỗi khi đọc {label_path}: {e}")
        return False

# Hàm tải lịch sử điểm danh cho người dùng cụ thể
def load_attendance_history(username):
    """
    Tải lịch sử điểm danh cho người dùng cụ thể.
    - THAY ĐỔI: Tạo file CSV mới nếu chưa tồn tại để tránh lỗi file không tìm thấy.
    - THAY ĐỔI: Thêm kiểm tra quyền ghi thư mục để phát hiện lỗi sớm.
    """
    
    attendance_path = get_path(f"data/logs/attendances_{username}.csv")
    log_dir = os.path.dirname(attendance_path)
    
    try:
        # Kiểm tra quyền ghi thư mục
        if not os.access(log_dir, os.W_OK) and os.path.exists(log_dir):
            print(f"[ERROR] No write permission for directory {log_dir}")
            return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
        
        if not os.path.exists(attendance_path):
            os.makedirs(log_dir, exist_ok=True)
            df = pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
            try:
                df.to_csv(attendance_path, index=False)
                print(f"[DEBUG] Created new attendance CSV for {username}: {attendance_path}")
            except Exception as e:
                print(f"[ERROR] Failed to create CSV {attendance_path}: {e}")
                return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
            return df
        
        df = pd.read_csv(attendance_path)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
        df["time-check-in"] = pd.to_datetime(df["time-check-in"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df["time-check-out"] = pd.to_datetime(df["time-check-out"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df_user = df[["name", "date", "time-check-in", "time-check-out", "time-working", "position"]]
        print(f"[DEBUG] Loaded attendance history for {username}, shape={df_user.shape}, data={df_user.to_dict()}")
        return df_user
    
    except Exception as e:
        print(f"[ERROR] Lỗi khi tải lịch sử điểm danh cho {username}: {e}")
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])

def save_uploaded_video(video_file, username, action, base_folder="data/logs/videos/by_date"):
    """Lưu video upload vào thư mục theo ngày."""
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = get_path(os.path.join(base_folder, date_str))
        os.makedirs(folder, exist_ok=True)

        filename = f"{username}_{action}_{timestamp}.mp4"
        save_path = os.path.join(folder, filename)

        video_file.seek(0)
        with open(save_path, "wb") as f:
            f.write(video_file.read())

        print(f"[DEBUG] Đã lưu video tại {save_path}")
        return save_path
    except Exception as e:
        print(f"[ERROR] Lỗi khi lưu video: {e}")
        return None
    
    
def display_message(message, is_success=True, placeholder=None, duration=1):
    """
    Hiển thị thông báo bằng st.success hoặc st.error và giữ trong thời gian duration (giây).
    - message: Nội dung thông báo.
    - is_success: True nếu thông báo thành công, False nếu lỗi.
    - placeholder: Streamlit placeholder để xóa (nếu có).
    - duration: Thời gian hiển thị (giây).
    """
    if placeholder is not None:
        placeholder.empty()
    if is_success:
        st.success(message)
    else:
        st.error(message)
    time.sleep(duration)
    print(f"[DEBUG] Displayed message: {message}, success={is_success}, duration={duration}")
