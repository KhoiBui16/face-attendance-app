# core/data_collector_video.py

import cv2
import numpy as np
import pickle
import os
from core.face_detection.detector import detect_faces
from utils.helpers import get_path
import streamlit as st


def collect_data_from_uploaded_video(
    video_path, name, save_dir="data/dataset", num_samples=30
):
    if not os.path.exists(video_path):
        st.warning("❌ Video không tồn tại.")
        return False

    save_dir = get_path(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    collected_faces = []

    progress = st.progress(0)
    display = st.empty()

    while cap.isOpened() and len(collected_faces) < num_samples:
        ret, frame = cap.read()
        if not ret:
            break

        faces = detect_faces(frame)
        for x, y, w, h in faces:
            roi = frame[y : y + h, x : x + w]
            resized = cv2.resize(roi, (50, 50))
            collected_faces.append(resized)

            # Vẽ khung khuôn mặt
            frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if len(collected_faces) >= num_samples:
                break

        # Hiển thị tiến trình
        display.image(
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
            caption=f"Thu thập {len(collected_faces)}/{num_samples}",
            use_container_width=True,
        )
        progress.progress(min(len(collected_faces) / num_samples, 1.0))

    cap.release()
    display.empty()
    progress.empty()

    if len(collected_faces) == 0:
        st.error("❌ Không thu được khuôn mặt nào.")
        return False

    collected_faces = np.array(collected_faces).reshape(len(collected_faces), -1)
    face_path = os.path.join(save_dir, "faces.pkl")
    name_path = os.path.join(save_dir, "names.pkl")

    try:
        # Gộp dữ liệu nếu đã tồn tại
        if os.path.exists(face_path):
            with open(face_path, "rb") as f:
                old_faces = pickle.load(f)
            all_faces = np.append(old_faces, collected_faces, axis=0)
        else:
            all_faces = collected_faces

        if os.path.exists(name_path):
            with open(name_path, "rb") as f:
                old_names = pickle.load(f)
            all_names = old_names + [name] * len(collected_faces)
        else:
            all_names = [name] * len(collected_faces)

        with open(face_path, "wb") as f:
            pickle.dump(all_faces, f)
        with open(name_path, "wb") as f:
            pickle.dump(all_names, f)

        return True

    except Exception as e:
        st.error(f"❌ Lỗi khi lưu dữ liệu: {e}")
        return False
