# 📷 Face Attendance App
---

## 📑 Table of Contents
- [📷 Face Attendance App](#-face-attendance-app)
  - [📑 Table of Contents](#-table-of-contents)
  - [📝 Project Description](#-project-description)
  - [📁 Project Structure](#-project-structure)
  - [🔐 Features](#-features)
  - [🎥 Demo Video](#-demo-video)
  - [📊 Sample Dataset](#-sample-dataset)
  - [🚀 How to Run Locally](#-how-to-run-locally)
  - [🛠 Tech Stack](#-tech-stack)
  - [📬 Contact](#-contact)

---

## 📝 Project Description

The `face-attendance-app` is a secure and user-friendly Streamlit application for face-based attendance detection and identification, featuring user authentication and admin access control. The application supports real-time face detection and identification for seamless attendance tracking. Key details include:

- **Technology**: Utilizes HAAR cascades for face detection, HOG features for face representation, and SVM or AdaBoost for classification.
- **User Authentication**: Users must log in to perform check-in and check-out, with each action restricted to once per day.
- **Attendance System**: 
  - Supports check-in/check-out via three methods: webcam, uploaded video, or URL.
  - Displays attendance details including name, check-in/check-out date and time, working hours, and position.
  - Stores attendance data in CSV files.
- **Admin Features**: 
  - Collect face data for new users using webcam, uploaded videos, or URLs.
  - Train face detection and recognition models after adding new members.
  - Manage user accounts by approving access for new registrations.
  - View a table of all members' attendance (username, check-in time, check-out time, working hours, position).
  - Delete user data and attendance logs.
  - Store attendance data in CSV files and user credentials (username, password) in `users.json`.
- **Model Performance**: The face recognition model achieves an accuracy of approximately 60–70% on the test set.

---

## 📁 Project Structure

```
face-attendance-app/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── data_collector/
│   │   │   ├── __init__.py
│   │   │   ├── face_data_collector.py
│   │   │   ├── video_data_collector.py
│   │   │   └── webcam_data_collector.py
│   │   ├── face_detection/
│   │   │   ├── __init__.py
│   │   │   ├── detector.py
│   │   │   └── recognizer.py
│   │   ├── config.py
│   │   ├── recognize_and_log.py
│   │   ├── train_model.py
│   │   └── haarcascade_frontalface_default.xml
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   └── attendance.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── helpers.py
│   │   └── user_utils.py
│   └── data/
│       ├── dataset/
│       │   ├── faces.pkl
│       │   └── names.pkl
│       ├── logs/
│       │   ├── images/
│       │   │   └── by_date/
│       │   │       └── [date]/
│       │   │           └── [image_files]
│       │   ├── videos/
│       │   │   └── by_date/
│       │   │       └── [date]/
│       │   │           └── [video_files]
│       │   └── attendances_[username].csv
│       ├── models/
│       │   └── model.pkl
│       └── users.json
├── image/
│   ├── train/
│   │   └── [username].mp4
│   ├── test/
│   │   └── [username].mp4
├── requirements.txt
├── packages.txt
├── .gitignore
└── README.md
```

---

## 🔐 Features

- **User Registration and Login**: Users can create accounts, await admin approval, and log in to the system.
- **Admin Panel**:
  - Approve or delete user accounts.
  - Collect face data for new users via webcam, uploaded videos, or URLs.
  - Train face detection and recognition models after adding new members.
  - View and delete attendance logs for all users, including username, check-in/check-out times, working hours, and position.
  - Store attendance data in CSV files and user credentials (username, password) in `users.json`.
- **Attendance Detection and Identification**: Users can check-in/check-out (once per day) using face recognition via webcam, uploaded videos, or URLs, with details like name, date, time, working hours, and position stored in CSV files.
- **Attendance History**: Stores attendance records (including images and videos) in CSV files and allows users to view their personal history.

---

## 🎥 Demo Video

[Link to demo video](https://youtu.be/sJ8fBIhxHO8)

---

## 📊 Sample Dataset

- [Link to sample dataset train](https://github.com/KhoiBui16/face-attendance-app/tree/main/image/train)
- [Link to sample dataset test](https://github.com/KhoiBui16/face-attendance-app/tree/main/image/test)
- [Link to user's accounts and passwords demo](https://github.com/KhoiBui16/face-attendance-app/blob/main/app/data/users.json)

The sample dataset contains video files and face data for testing or training the recognition model.

---

## 🚀 How to Run Locally

Follow these steps to clone and run the app on your local machine.

### 1. Clone the repository

```bash
git clone https://github.com/KhoiBui16/face-attendance-app.git
cd face-attendance-app
```

### 2. Set up your environment

**On Windows**:
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```

**On macOS/Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install dependencies

Make sure you have **pip** installed, then run:

```bash
pip install -r requirements.txt
```

On Ubuntu, install `libgl1-mesa-glx` for OpenCV:

```bash
sudo apt-get install libgl1-mesa-glx
```

On macOS, you may need to install OpenCV via Homebrew if issues arise:

```bash
brew install opencv
```

### 4. Run the app

Once everything is installed, run the following command to launch the app:

```bash
cd app
streamlit run main.py
```

After a few seconds, your browser should open at:

```bash
http://localhost:8501
```

---

## 🛠 Tech Stack

- Python 3.x
- Streamlit
- OpenCV
- Scikit-learn
- Albumentations
- Scikit-image
- Pandas
- NumPy

---

## 📬 Contact

For suggestions, feedback, or issues:

- 📧 Email: khoib1601@gmail.com
- 🐛 Report an issue or submit a pull request on GitHub
