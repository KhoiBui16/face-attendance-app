import cv2
import os
import streamlit as st
import imageio.v3 as iio
from .face_data_collector import collect_face_data


class ImageioWrapper:
    """Giả lập API tối thiểu như cv2.VideoCapture bằng imageio (RGB → BGR)."""
    def __init__(self, path):
        self.reader = iio.imiter(path)
        self._opened = True

    def isOpened(self):
        return self._opened

    def read(self):
        try:
            frame = next(self.reader)  # imageio trả về RGB
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return True, frame_bgr
        except StopIteration:
            return False, None

    def release(self):
        self._opened = False
        self.reader.close()


def collect_data_from_uploaded_video(
    video_path, name, save_dir="data/dataset", num_samples=100
):
    """
    Thu thập dữ liệu khuôn mặt từ video upload.
    - video_path: Đường dẫn đến file video.
    - name: Tên người cần gắn nhãn.
    - save_dir: Thư mục lưu dữ liệu.
    - num_samples: Số lượng mẫu thu thập.
    """
    if not os.path.exists(video_path):
        st.error(f"❌ Video không tồn tại tại: {video_path}")
        # print(f"[ERROR] Video file does not exist: {video_path}")
        return False

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        st.warning("⚠️ OpenCV không mở được video, thử dùng imageio…")
        try:
            cap = ImageioWrapper(video_path)
        except Exception:
            st.error("❌ Không thể đọc file video.")
            return False

    if isinstance(cap, cv2.VideoCapture):
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # print(f"[DEBUG] Video info: FPS={fps}, Total frames={frame_count}")

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
            st.error(
                f"❌ Không thu thập được dữ liệu cho {name}. Vui lòng kiểm tra video (đảm bảo có khuôn mặt rõ ràng, ánh sáng tốt)."
            )
            print(f"[ERROR] Thu thập thất bại cho {name}")
        return result
    except Exception as e:
        st.error(f"❌ Lỗi khi thu thập dữ liệu từ video: {e}")
        print(f"[ERROR] Lỗi khi thu thập dữ liệu từ video: {e}")
        return False
    finally:
        if hasattr(cap, "release"):
            cap.release()
        display.empty()
        progress.empty()
