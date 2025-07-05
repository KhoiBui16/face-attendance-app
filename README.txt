📷 Face Attendance App with Auth

📑 Table of Contents

📷 Face Attendance App with Auth
📝 Project Description
📁 Project Structure
🔐 Features
🎥 Demo Video
📊 Sample Dataset
🚀 How to Run Locally
🔐 Note
🛠 Tech Stack
📬 Contact


📝 Project Description
The face-attendance-app-with-auth is a secure and user-friendly Streamlit application for face-based attendance detection and identification, featuring user authentication and admin access control. The application supports real-time face detection and identification for seamless attendance tracking. Key details include:

Technology: Utilizes HAAR cascades for face detection, HOG features for face representation, and SVM or AdaBoost for classification.
User Authentication: Users must log in to perform check-in and check-out, with each action restricted to once per day.
Attendance System: 
Supports check-in/check-out via three methods: webcam, uploaded video, or URL.
Displays attendance details including name, check-in/check-out date and time, working hours, and position.
Stores attendance data in CSV files.


Admin Features: 
Collect face data for new users using webcam, uploaded videos, or URLs.
Train face detection and recognition models after adding new members.
Manage user accounts by approving access for new registrations.
View a table of all members' attendance (username, check-in time, check-out time, working hours, position).
Delete user data and attendance logs.
Store attendance data in CSV files and user credentials (username, password) in users.json.


Model Performance: The face recognition model achieves an accuracy of 70% on the test set.


📁 Project Structure
face-attendance-app-with-auth/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── data_collector/
│   │   │   ├── face_data_collector.py
│   │   │   ├── video_data_collector.py
│   │   │   └── webcam_data_collector.py
│   │   ├── face_detection/
│   │   │   ├── detector.py
│   │   │   └── recognizer.py
│   │   ├── config.py
│   │   ├── recognize_and_log.py
│   │   └── train_model.py
│   ├── pages/
│   Platonum: 5, Gold: 3
│   │   ├── admin.py
│   │   └── attendance.py
│   └── utils/
│       ├── auth.py
│       ├── helpers.py
│       └── user_utils.py
├── data/
│   ├── dataset/
│   │   ├── faces.pkl
│   │   └── names.pkl
│   ├── logs/
│   │   ├── images/
│   │   │   └── by_date/
│   │   │       └── [date]/
│   │   │           └── [image_files]
│   │   ├── videos/
│   │   │   └── by_date/
│   │   │       └── [date]/
│   │   │           └── [video_files]
│   │   └── attendances_[username].csv
│   ├── models/
│   │   └── model.pkl
│   ├── test/
│   │   └── [username].mp4
│   ├── train/
│   │   └── [username].mp4
│   └── users.json
├── requirements.txt
├── packages.txt
├── .gitignore
└── README.md


🔐 Features

User Registration and Login: Users can create accounts, await admin approval, and log in to the system.
Admin Panel:
Approve or delete user accounts.
Collect face data for new users via webcam, uploaded videos, or URLs.
Train face detection and recognition models after adding new members.
View and delete attendance logs for all users, including username, check-in/check-out times, working hours, and position.
Store attendance data in CSV files and user credentials (username, password) in users.json.


Attendance Detection and Identification: Users can check-in/check-out (once per day) using face recognition via webcam, uploaded videos, or URLs, with details like name, date, time, working hours, and position stored in CSV files.
Attendance History: Stores attendance records (including images and videos) in CSV files and allows users to view their personal history.


🎥 Demo Video
Link to demo video 

📊 Sample Dataset

Link: Link to sample dataset 
Password: [password] 

The sample dataset contains video files and face data for testing or training the recognition model.

🚀 How to Run Locally
Follow these steps to clone and run the app on your local machine.
1. Clone the repository
git clone https://github.com/yourusername/face-attendance-app-with-auth.git
cd face-attendance-app-with-auth

2. Set up your environment

On Windows:
python -m venv venv
venv\Scripts\activate


On macOS/Linux:
python3 -m venv venv
source venv/bin/activate



3. Install dependencies
Make sure you have pip installed, then run:
pip install -r requirements.txt

On Ubuntu, install libgl1-mesa-glx for OpenCV:
sudo apt-get install libgl1-mesa-glx

On macOS, you may need to install OpenCV via Homebrew if issues arise:
brew install opencv

4. Run the app
Once everything is installed, run the following command to launch the app:
cd app
streamlit run main.py

After a few seconds, your browser should open at:
http://localhost:8501


🔐 Note

Do not push users.json or data/ directory to GitHub.These contain sensitive user data and face datasets.Ensure .gitignore includes users.json and data/ to prevent accidental commits.


🛠 Tech Stack

Python 3.x
Streamlit
OpenCV
Scikit-learn
Albumentations
Scikit-image
Pandas
NumPy


📬 Contact
For suggestions, feedback, or issues:

📧 Email: [your-email@example.com]
🐛 Report an issue or submit a pull request on GitHub
