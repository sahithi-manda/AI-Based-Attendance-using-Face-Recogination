# Face Recognition Attendance System

A Python desktop application that marks student attendance automatically by recognizing enrolled faces from a live webcam feed. It also flags students whose attendance is slipping.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?logo=opencv&logoColor=white)
![dlib](https://img.shields.io/badge/face__recognition-dlib-008080)
![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white)

## Problem

Manual roll calls take class time and allow proxy attendance. Attendance records also tend to sit in registers, where nobody spots a student who is falling behind until it is too late.

## Objectives

- Recognize enrolled students from a webcam feed and record attendance without manual input.
- Keep recognition responsive on an ordinary laptop CPU.
- Turn attendance logs into early warnings: who is dropping, and who is on track to fall below the 75% requirement.

## Features

| Area | What it does |
|---|---|
| **Registration** | Captures a student's face from the webcam and stores a 128-dimension face encoding with their roll number and name. |
| **Live scanner** | Detects faces in each frame, matches them against enrolled encodings and marks recognized students present. Unmatched faces are labelled *Unknown*. |
| **Search and verify** | Finds students by name or roll number and lets an admin mark attendance manually. |
| **Reports** | Daily, monthly and overall attendance tables with CSV export. |
| **Analytics** | **At-risk:** attendance dropped by 15 or more percentage points in the last 14 days compared with the 14 days before. **Predictive alert:** projects each student's end-of-semester rate from their recent trend and flags anyone projected below 75%. |
| **Email notifications** | Optional absence emails to students not marked present, sent over SMTP sent in a background thread so the UI doesn't freeze. |
| **Admin login** | Passwords are stored as salted PBKDF2-HMAC-SHA512 hashes (100,000 iterations). |

## How recognition works

```
Webcam frame (OpenCV, BGR)
   │  downscale to 1/4 resolution  ← keeps detection fast on CPU
   ▼
face_recognition.face_locations()      → bounding boxes (HOG detector, dlib)
face_recognition.face_encodings()      → 128-d embedding per face
   │
   ▼
NumPy: Euclidean distance to every enrolled encoding (vectorized)
   │  closest match ≤ 0.55  → student;  otherwise → "Unknown"
   ▼
db_handler.mark_attendance()  → attendance_log.csv  (once per student per day)
```

The match tolerance is 0.55, slightly stricter than the library default of 0.6 (a lower distance threshold means fewer false matches). Raise it if enrolled students are missed in poor lighting; lower it if you see false matches.

## Project structure

```
├── main.py              # Entry point: creates data files, launches the GUI
├── core/
│   ├── face_engine.py    # Detection, encoding and matching
│   ├── db_handler.py     # CSV-backed student and attendance storage
│   ├── analytics.py      # At-risk and predictive attendance analysis
│   ├── email_handler.py  # SMTP notifications (credentials from env vars)
│   ├── auth.py           # PBKDF2 password hashing for admin login
│   └── anti_spoofing.py  # Placeholder: liveness detection not implemented yet
├── gui/
│   ├── app.py            # CustomTkinter app: dashboard, register, scanner, reports, analytics
│   └── login.py          # Admin login window
├── install_pi.sh        # Setup script for Raspberry Pi (dlib build)
├── run_app.bat          # One-click setup and launch on Windows
└── test_analytics.py    # Smoke test for the analytics module
```

## Installation

`face_recognition` depends on **dlib**, which builds from source and needs CMake and a C++ compiler.

```bash
git clone https://github.com/sahithi-manda/AI-Based-Attendance-using-Face-Recogination.git
cd AI-Based-Attendance-using-Face-Recogination
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install cmake
pip install -r requirements.txt
```

On Windows you can run `run_app.bat` instead. On a Raspberry Pi, run `install_pi.sh`.

## Usage

```bash
python main.py
```

1. Log in as `admin`. The default password is `admin`; change it after your first login.
2. **Register Student:** enter roll number and name, then capture the face.
3. **Scanner:** start the camera. Recognized students are marked present once per day.
4. **Reports / Analytics:** review attendance, export CSVs, check at-risk students and predictive alerts.

### Optional: email notifications

Set these environment variables before starting the app. Use a [Gmail app password](https://support.google.com/accounts/answer/185833), never your account password.

```bash
export SMTP_SENDER_EMAIL="your.address@gmail.com"
export SMTP_APP_PASSWORD="your-16-character-app-password"
```

Without them, the app runs normally and skips sending email.

## Data and privacy

Face encodings, student records and attendance logs are stored locally (`encodings.pickle`, `students.csv`, `attendance_log.csv`) and are excluded from Git by `.gitignore`. Nothing is uploaded.

## Sanity check

The recognition engine (`FaceEngine.recognize_faces`) was run on still photos from a public 9-person face dataset. Three people were enrolled from a single photo each, then probed with 10 other photos per person:

| Probe | Result |
|---|---|
| Enrolled person 1 | 9 of 9 detected faces recognized (1 photo: no face detected) |
| Enrolled person 2 | 10 of 10 recognized |
| Enrolled person 3 | 6 of 10 recognized, 4 returned *Unknown* |
| A person who was **not** enrolled | 0 of 10 false matches, all *Unknown* |

This is a small test, not a benchmark, and it used photos rather than a live webcam. With a single enrollment photo, the strict 0.55 tolerance prefers *Unknown* over a wrong name, which is the safer failure for attendance.

## Limitations

- **No liveness detection yet.** `core/anti_spoofing.py` is a placeholder that accepts every face, so a printed photo could be marked present.
- Accuracy has only been sanity-checked (above), not measured on a live classroom. It depends on lighting, camera quality and how many students are enrolled.
- CSV storage is fine for a single classroom but not for concurrent use.

## Future improvements

- Blink-based liveness detection using eye aspect ratio from facial landmarks.
- Measure precision and recall on a labelled test set to tune the 0.55 tolerance.
- Move storage from CSV to SQLite.
- Use multiple encodings per student to improve robustness to angle and lighting.
