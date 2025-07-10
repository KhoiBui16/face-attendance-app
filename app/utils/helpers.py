import os
import time
import pandas as pd
from datetime import datetime
import cv2
import pickle
import streamlit as st


def read_attendance_csv(username=None):
    """Đọc dữ liệu điểm danh từ tệp của người dùng hoặc tệp chung (cho admin)."""
    
    if username:
        log_file = f"data/logs/attendances_{username}.csv"
    else:
        log_file = "data/logs/attendances.csv"

    try:
        if not os.path.exists(log_file):
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            df = pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
            df.to_csv(log_file, index=False)
            return df

        df = pd.read_csv(log_file)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
        df["time-check-in"] = pd.to_datetime(df["time-check-in"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df["time-check-out"] = pd.to_datetime(df["time-check-out"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

        return df

    except Exception as e:
        print(f"[ERROR] Failed to read attendance CSV: {e}")
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])


def read_all_attendance_csv():
    """Tải và gộp dữ liệu điểm danh từ tất cả các tệp của người dùng."""
    
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    all_dfs = []
    user_files = {}

    try:
        for file_name in os.listdir(log_dir):
            if file_name.startswith("attendances_") and file_name.endswith(".csv"):
                username = file_name.replace("attendances_", "").replace(".csv", "")
                file_path = os.path.join(log_dir, file_name)
                user_files[username] = file_path
                
                try:
                    df = read_attendance_csv(username=username)
                    if not df.empty:
                        df = df.assign(username=username)
                        all_dfs.append(df)

                except Exception as e:
                    print(f"[ERROR] Failed to read {file_path}: {e}")

        if not all_dfs:
            return (pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"]), {})

        combined_df = pd.concat(all_dfs, ignore_index=True)
        return combined_df, user_files

    except Exception as e:
        print(f"[ERROR] Failed to read attendance CSVs: {e}")
        
        return (pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"]), {})


def preprocess_attendance(df):
    """Preprocess attendance data for display."""
    
    if df.empty:
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
    
    return df[["name", "date", "time-check-in", "time-check-out", "time-working", "position"]]


def append_attendance_log(name, image, position, action):
    """Append or update attendance log and save image."""
    
    log_file = f"data/logs/attendances_{name}.csv"
    date = datetime.now().strftime("%Y-%m-%d")
    image_dir = f"data/logs/images/by_date/{date}"
    os.makedirs(image_dir, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    image_name = f"{name}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    image_path = os.path.join(image_dir, image_name)

    if image is not None:
        try:
            cv2.imwrite(image_path, image)
        except Exception as e:
            print(f"[ERROR] Failed to save image {image_path}: {e}")

    df = read_attendance_csv(username=name)
    if action == "check-in":
        mask = ((df["name"] == name) & (df["date"].dt.date == pd.to_datetime(date).date()) & (df["time-check-in"].notna()))
        
        if mask.any():
            return False, f"{name} đã check-in hôm nay rồi."

        new_record = pd.DataFrame({ "name": [name], "date": [date],  "time-check-in": [timestamp], "time-check-out": [pd.NA], "time-working": [pd.NA], "position": [position]})
        
        if df.empty:
            df = new_record
        else:
            df = pd.concat([df.dropna(how="all"), new_record], ignore_index=True)

    elif action == "check-out":
        mask = ((df["name"] == name) & (df["date"].dt.date == pd.to_datetime(date).date()) & (df["time-check-in"].notna()) & (df["time-check-out"].isna()))

        if mask.any():
            df.loc[mask, "time-check-out"] = timestamp
            df.loc[mask, "time-working"] = df.loc[mask].apply(
                lambda row: round((pd.to_datetime(row["time-check-out"]) - pd.to_datetime(row["time-check-in"])).total_seconds() / 3600, 2, ), axis=1)
        else:
            return False, f"Không tìm thấy bản ghi check-in cho ngày hôm nay."

    try:
        if os.path.exists(log_file):
            if not os.access(log_file, os.W_OK):
                return False, f"Không có quyền ghi vào file {log_file}"

        df.to_csv(log_file, index=False)
        return True, f"Điểm danh {action} thành công cho {name}"
    
    except Exception as e:
        print(f"[ERROR] Failed to save attendance log: {e}")
        return False, f"Lỗi khi lưu log điểm danh: {e}"


def is_action_allowed(name: str, action: str) -> tuple[bool, str]:
    """Kiểm tra xem hành động check-in/check-out có được phép thực hiện không."""
    
    username = st.session_state.get("username", name)

    df = read_attendance_csv(username=username)
    if df.empty:
        if action == "check-in":
            return True, ""
        else:
            return False, f"{username} chưa check-in nên không thể check-out."

    today = datetime.now().date()
    df_today = df[(df["name"] == username) & (df["date"].dt.date == today)]

    if action == "check-in":
        if not df_today.empty and df_today["time-check-in"].notna().any():
            return False, f"{username} đã check-in hôm nay rồi."
        else:
            return True, ""
        
    elif action == "check-out":
        if df_today.empty or not df_today["time-check-in"].notna().any():
            return False, f"{username} chưa check-in nên không thể check-out."
        
        elif df_today["time-check-out"].notna().any():
            return False, f"{username} đã check-out hôm nay rồi."
        else:
            return True, ""
    return False, "Hành động không hợp lệ."


def has_trained_data(username):
    """Kiểm tra xem username có dữ liệu khuôn mặt trong names.pkl hay không."""
    
    label_path = "data/dataset/names.pkl"
    if not os.path.exists(label_path):
        return False
    try:
        with open(label_path, "rb") as f:
            labels = pickle.load(f)
        has_data = username in labels
        return has_data
    except Exception as e:
        return False


def load_attendance_history(username):
    """Tải lịch sử điểm danh cho người dùng cụ thể."""
    
    attendance_path = f"data/logs/attendances_{username}.csv"
    log_dir = "data/logs"

    try:
        if not os.access(log_dir, os.W_OK) and os.path.exists(log_dir):
            print(f"[ERROR] No write permission for directory {log_dir}")
            return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])

        if not os.path.exists(attendance_path):
            os.makedirs(log_dir, exist_ok=True)
            df = pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
            
            try:
                df.to_csv(attendance_path, index=False)

            except Exception as e:
                print(f"[ERROR] Failed to create CSV {attendance_path}: {e}")
                return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
            return df

        df = pd.read_csv(attendance_path)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
        df["time-check-in"] = pd.to_datetime(df["time-check-in"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df["time-check-out"] = pd.to_datetime(df["time-check-out"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df_user = df[["name", "date", "time-check-in", "time-check-out", "time-working", "position"]]

        return df_user

    except Exception as e:
        print(f"[ERROR] Lỗi khi tải lịch sử điểm danh cho {username}: {e}")
        
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])


def save_uploaded_video(video_file, username, action, base_folder="data/logs/videos/by_date"):
    """Lưu video upload vào thư mục theo ngày."""
    
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = os.path.join(base_folder, date_str)
        os.makedirs(folder, exist_ok=True)

        filename = f"{username}_{action}_{timestamp}.mp4"
        save_path = os.path.join(folder, filename)

        video_file.seek(0)
        with open(save_path, "wb") as f:
            f.write(video_file.read())

        return save_path
    except Exception as e:
        print(f"[ERROR] Lỗi khi lưu video: {e}")
        return None


def display_message(message, is_success=True, placeholder=None, duration=1):
    """Hiển thị thông báo bằng st.success hoặc st.error và giữ trong thời gian duration (giây)."""
    
    if placeholder is not None:
        placeholder.empty()
    if is_success:
        st.success(message)
    else:
        st.error(message)
    time.sleep(duration)

