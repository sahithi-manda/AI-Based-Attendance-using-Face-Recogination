# AI Attendance System (Light Theme)

A comprehensive, automated student attendance management system built in Python. This desktop application leverages AI and facial recognition to track attendance, prevent proxy spoofing, and provide deep analytics, all wrapped in a modern, lightweight GUI. 

## Features

- **Live Attendance Scanner:** Automatically recognizes enrolled faces via webcam and logs their attendance.
- **Robust Anti-Spoofing:** Built-in safeguards to differentiate between live individuals and photos/screens (requires proof of life/blinking).
- **Student Registration:** Easily enroll new students and train the face recognition model with their webcam captures.
- **Dashboard Overview:** A clean interface to see total enrolled students and today's attendance metrics at a glance.
- **Search & Verify Tools:** Manually verify and mark attendance by Roll Number or Name.
- **Automated Email Notifications:** Instantly send absence notifications and status updates via email.
- **Reporting & Exporting:** Generate detailed DataFrames and export daily, monthly, and overall attendance logs as `.csv` files.
- **Advanced Analytics:** 
    - Identify **At-Risk** students (those with an attendance drop of >15% over the last 14 days).
    - Gain **Predictive Alerts** for students projected to fall below a 75% attendance threshold.

## Requirements

Ensure your environment is set up with Python 3.x. The project uses the following major libraries:
- `customtkinter` (for the Light UI implementation)
- `opencv-python` (`cv2`)
- `Pillow` (`PIL`)
- `pandas`
- `numpy`
*(You may also need `face_recognition` / `dlib` depending on your `core.face_engine` backend).*

## Project Structure

- `main.py`: The entry point for the application. It initializes directories and database placeholders.
- `gui/`: Contains the `customtkinter` frontend layouts, frames, and styling configurations (`app.py`).
- `core/`: Houses the backend engines for face recognition (`face_engine.py`), anti-spoofing (`anti_spoofing.py`), analytics (`analytics.py`), email handling (`email_handler.py`), and the database interface (`db_handler.py`).

## Getting Started

1. **Clone or Download the Repository.**
2. **Install Dependencies:**
   ```bash
   pip install customtkinter opencv-python pillow pandas numpy
   ```
   *(Ensure any native extensions required by your face engine are also installed).*
3. **Run the Application:**
   ```bash
   python main.py
   ```
4. **Initial Setup:** On the first launch, the app will automatically generate necessary folders (`core`, `gui`, `dataset`) and `.csv` registry files (`students.csv`, `attendance_log.csv`). 
5. Navigate to the **"Register Student"** tab to capture and save your first facial encoding.

## Theme Configuration
The application is pre-configured with a clean, readable **Light Theme**. This setting overrides standard Dark variants by injecting specific `#ffffff`, `#e0e0e0`, and `#000000` text properties within the `apply_hover_and_zebra` tree styling and CustomTkinter configuration parameters explicitly defined in `gui/app.py`.
