import cv2
import os
import streamlit as st
from core.data_collector.face_data_collector import collect_face_data
from utils.helpers import get_path

def collect_data_from_uploaded_video(
    video_path, name, save_dir="data/dataset", num_samples=100
):
    """
    Thu thập dữ liệu khuôn mật từ video upload.
    - video_path: Đường dẫn đến file video.
    - name: Tên người cần gắn nhãn.
    - save_dir: Thư mục lưu dữ liệu.
    - num_samples: Số lượng mẫu thu thập.
    """
    video_path = get_path(video_path)
    if not os.path.exists(video_path):
        st.error(f"❌ Video không tồn tại tại: {video_path}")
        print(f"[ERROR] Video file does not exist: {video_path}")
        return False

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        st.error("❌ Không thể đọc file video.")
        print(f"[ERROR] Failed to open video: {video_path}")
        return False

    # Kiểm tra thông tin video
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[DEBUG] Video info: FPS={fps}, Total frames={frame_count}")

    progress = st.progress(0)
    display = st.empty()

    def display_callback(frame, collected, total):
        """Hiển thị khung hình qua Streamlit."""
        try:
            display.image(
                cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                caption=f"Thu thập {collected}/{total}",
                use_container_width=True,
            )
            progress.progress(min(collected / total, 1.0))
        except Exception as e:
            print(f"[ERROR] Lỗi khi hiển thị khung hình qua Streamlit: {e}")

    try:
        result = collect_face_data(cap, name, save_dir, num_samples, display_callback)
        if result:
            st.success(f"✅ Thu thập thành công {num_samples} mẫu cho {name}")
            print(f"[SUCCESS] Thu thập thành công cho {name}")
        else:
            st.error(f"❌ Không thu thập được dữ liệu cho {name}. Vui lòng kiểm tra video (đảm bảo có khuôn mặt rõ ràng, ánh sáng tốt).")
            print(f"[ERROR] Thu thập thất bại cho {name}")
        return result
    except Exception as e:
        st.error(f"❌ Lỗi khi thu thập dữ liệu từ video: {e}")
        print(f"[ERROR] Lỗi khi thu thập dữ liệu từ video: {e}")
        return False
    finally:
        cap.release()
        display.empty()
        progress.empty()