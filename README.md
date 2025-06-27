# AI-Powered Alertness System

A real-time, AI-driven system designed to monitor and detect signs of reduced alertness or attention using facial landmark analysis. This system aims to enhance safety and productivity in environments where sustained focus is critical, such as driving or operating machinery.

# 🚀 Features

Real-time Alertness Monitoring: Continuously analyzes facial features from a live camera feed.

Drowsiness Detection: Utilizes Eye Aspect Ratio (EAR) to detect closed eyes, indicating drowsiness.

Distraction Detection: Monitors head pose and gaze direction to identify prolonged periods of inattention.

Yawn Detection: Identifies yawning through Mouth Aspect Ratio (MAR) as another indicator of fatigue.

Web-based Interface: Provides a user-friendly interface accessible via a web browser.

User Authentication: Includes Login and Signup pages for secure access.

Scalable Architecture: Built with a Python Flask backend for robust processing and a responsive frontend using HTML, CSS, and JavaScript.


# 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.


# Prerequisites

Python 3.x (3.9 or higher recommended)

pip (Python package installer)

Installation
Clone the repository:

Bash

git clone https://github.com/[YourGitHubUsername]/[YourRepositoryName].git

cd [YourRepositoryName]/backend # Assuming your backend code is in a 'backend' folder

Create and activate a virtual environment (recommended):

Bash

python -m venv .venv

# On Windows:

.\.venv\Scripts\activate

# On macOS/Linux:

source ./.venv/bin/activate

Install the required Python packages:

Bash

pip install -r requirements.txt

Download Dlib's Pre-trained Model (if not already included):

Ensure shape_predictor_68_face_landmarks.dat is in your backend directory. If it's missing or you need to re-download, you can typically find it on the dlib GitHub release page or through tutorials that use dlib.

Important: This file is large and often not included directly in Git repositories. You might need to download it manually:

Go to http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

Download and extract the .bz2 file.

Place the shape_predictor_68_face_landmarks.dat file directly into your backend directory.

# Running the Application
Ensure your virtual environment is active.

Run the Flask application:

pip install -r backend/requirements.txt

Bash

python app.py

The application will typically run on http://127.0.0.1:5000/ or http://localhost:5000/.

Open your web browser and navigate to http://localhost:5000/landing (or http://localhost:5000/ if your app.py serves the landing page as default).

# 🛣️ Usage

Navigate to the landing.html page (e.g., http://localhost:5000/landing).

Sign up for a new account or log in with existing credentials.

Once logged in, you will be redirected to the main index.html page, which should display your camera feed and the alertness monitoring system.

The system will start analyzing your facial features in real-time. Alerts for drowsiness, distraction, or yawning will be displayed [describe how alerts are shown, e.g., on-screen, audible, etc.].

# 🤝 Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request



# 📞 Contact
Your Thabang Mthimkulu - [thabang23mthimkulu@gmail.com]

Project Link: https://github.com/mthimkulu23/Focus-Alertness-System