import cv2
from .face_data_collector import collect_face_data
import streamlit as st

def collect_data_from_webcam(name, save_dir="data/dataset", num_samples=10, camera_index=0):
    """
    Thu thập dữ liệu khuôn mặt từ webcam.
    - name: Tên người cần gắn nhãn.
    - save_dir: Thư mục lưu dữ liệu.
    - num_samples: Số lượng mẫu thu thập.
    - camera_index: Chỉ số webcam.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        st.error(f"❌ Không mở được webcam với index {camera_index}.")
        print(f"[ERROR] Failed to open webcam with index {camera_index}")
        return False

    print(f"[DEBUG] Webcam opened with index {camera_index}")
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
            st.error(f"❌ Không thu thập được dữ liệu cho {name}. Vui lòng kiểm tra webcam.")
            print(f"[ERROR] Thu thập thất bại cho {name}")
        return result
    except Exception as e:
        st.error(f"❌ Lỗi khi thu thập dữ liệu: {e}")
        print(f"[ERROR] Lỗi khi thu thập dữ liệu từ webcam: {e}")
        return False
    finally:
        cap.release()
        display.empty()
        progress.empty()
