import pickle
import os
import pandas as pd
from datetime import datetime
import cv2

def get_project_root():
    """Get the absolute path to the project root directory."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    # print(f"[DEBUG] Project root: {root}")
    return root

def get_path(relative_path):
    """Get absolute path from project root."""
    path = os.path.join(get_project_root(), relative_path)
    # print(f"[DEBUG] Resolved path for {relative_path}: {path}")
    return path

def read_attendance_csv():
    log_file = get_path("data/logs/attendances.csv")  # Cập nhật đường dẫn
    try:
        if not os.path.exists(log_file):
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            df = pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
            df.to_csv(log_file, index=False)
            # print(f"[DEBUG] Created new attendance CSV: {log_file}")
            return df
        
        df = pd.read_csv(log_file)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["time-check-in"] = pd.to_datetime(df["time-check-in"], errors="coerce")
        df["time-check-out"] = pd.to_datetime(df["time-check-out"], errors="coerce")
        return df
    
    except Exception as e:
        print(f"[ERROR] Failed to read attendance CSV: {e}")
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])

def preprocess_attendance(df):
    """Preprocess attendance data for display."""
    if df.empty:
        return pd.DataFrame(columns=["name", "date", "time-check-in", "time-check-out", "time-working", "position"])
    return df[["name", "date", "time-check-in", "time-check-out", "time-working", "position"]]

def append_attendance_log(name, image, position, action):
    """Append or update attendance log and save image."""
    log_file = get_path("data/logs/attendances.csv")  # Cập nhật đường dẫn
    date = datetime.now().strftime("%Y-%m-%d")
    image_dir = get_path(f"data/logs/images/by_date/{date}")  # Lưu ảnh theo ngày
    os.makedirs(image_dir, exist_ok=True)
    
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    image_name = f"{name}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    image_path = os.path.join(image_dir, image_name)
    
    if image is not None:
        cv2.imwrite(image_path, image)
    
    df = read_attendance_csv()
    
    if action == "check-in":
        new_record = pd.DataFrame({
            "name": [name],
            "date": [date],
            "time-check-in": [timestamp],
            "time-check-out": [pd.NA],
            "time-working": [pd.NA],
            "position": [position]
        })
        df = pd.concat([df, new_record], ignore_index=True)
    elif action == "check-out":
        mask = (df["name"] == name) & (df["date"] == date) & (df["time-check-in"].notna()) & (df["time-check-out"].isna())
        
        if mask.any():
            df.loc[mask, "time-check-out"] = timestamp
            df.loc[mask, "time-working"] = df.loc[mask].apply(
                lambda row: round((pd.to_datetime(row["time-check-out"]) - pd.to_datetime(row["time-check-in"])).total_seconds() / 3600, 2),
                axis=1
            )
        else:
            return False, "Không tìm thấy bản ghi check-in cho ngày hôm nay."
    
    try:
        df.to_csv(log_file, index=False)
        return True, f"Điểm danh {action} thành công cho {name}"
    except Exception as e:
        return False, f"Lỗi khi lưu log điểm danh: {e}"
    
def is_action_allowed(name: str, action: str) -> tuple[bool, str]:
    """
    Kiểm tra xem hành động check-in/check-out có được phép thực hiện không.

    Trả về:
        (True, "") nếu hợp lệ,
        (False, lý do) nếu không được phép.
    """
    
    df = read_attendance_csv()
    if df.empty:
        if action == "check-in":
            return True, ""
        else:
            return False, f"{name} chưa check-in nên không thể check-out."

    today = datetime.now().date()
    df_today = df[(df["name"] == name) & (df["date"].dt.date == today)]

    if action == "check-in":
        if not df_today.empty and df_today["time-check-in"].notna().any():
            return False, f"{name} đã check-in hôm nay rồi."
        else:
            return True, ""

    elif action == "check-out":
        if df_today.empty or not df_today["time-check-in"].notna().any():
            return False, f"{name} chưa check-in nên không thể check-out."
        elif df_today["time-check-out"].notna().any():
            return False, f"{name} đã check-out hôm nay rồi."
        else:
            return True, ""

    return False, "Hành động không hợp lệ."


def save_uploaded_video(video_file, username, action, base_folder="data/logs/videos/by_date"):
    """
    Lưu video upload vào thư mục theo ngày, ví dụ:
    data/logs/videos/by_date/2025-07-01/username_action_timestamp.mp4

    Parameters:
    - video_file: tệp video từ Streamlit uploader
    - username: tên người dùng
    - action: check-in hoặc check-out
    - base_folder: thư mục gốc để lưu video (default: data/logs/videos/by_date)

    Returns:
    - Đường dẫn tuyệt đối đến video đã lưu, hoặc None nếu lỗi
    """
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = get_path(os.path.join(base_folder, date_str))
        os.makedirs(folder, exist_ok=True)

        filename = f"{username}_{action}_{timestamp}.mp4"
        save_path = os.path.join(folder, filename)

        video_file.seek(0)  # đảm bảo đọc từ đầu file
        with open(save_path, "wb") as f:
            f.write(video_file.read())

        return save_path
    except Exception as e:
        print(f"[ERROR] Lỗi khi lưu video: {e}")
        return None


def has_trained_data(username):
    label_path = get_path("data/dataset/names.pkl")
    if not os.path.exists(label_path):
        return False
    with open(label_path, "rb") as f:
        labels = pickle.load(f)
    return username in labels