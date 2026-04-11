import pandas as pd
import datetime
import os
import pickle
import numpy as np
import cv2
from core import email_handler
import numpy as np
import cv2

STUDENTS_CSV = 'students.csv'
ATTENDANCE_CSV = 'attendance_log.csv'
ENCODINGS_FILE = 'encodings.pickle'

def register_student(roll_number, name, face_encoding, image_path):
    """
    Registers a new student to the CSV and saves encoding to pickle.
    """
    try:
        # Load existing students
        df = pd.read_csv(STUDENTS_CSV)
        roll_number_str = str(roll_number)
        
        if roll_number_str in df['Roll_No'].astype(str).values:
            return False, f"Roll number {roll_number} already exists."
            
        # Append new student
        new_row = {
            'Roll_No': roll_number_str,
            'Name': name,
            'Image_Path': image_path,
            'Last_Attendance': ''
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(STUDENTS_CSV, index=False)
        
        # Save encoding
        encodings_data = []
        if os.path.exists(ENCODINGS_FILE) and os.path.getsize(ENCODINGS_FILE) > 0:
             try:
                 with open(ENCODINGS_FILE, 'rb') as f:
                     encodings_data = pickle.load(f)
             except (EOFError, pickle.UnpicklingError):
                 encodings_data = []
                 
        encodings_data.append({
            'Roll_No': roll_number_str,
            'Name': name,
            'encoding': face_encoding
        })
        
        with open(ENCODINGS_FILE, 'wb') as f:
            pickle.dump(encodings_data, f)
            
        return True, "Student registered successfully."
    except Exception as e:
        return False, str(e)

def get_all_student_encodings():
    """
    Returns a list of dicts: [{'student_id': roll_number, 'name': name, 'roll_number': roll, 'encoding': np.array}, ...]
    Note: mapping student_id to roll_number for compatibility with existing app logic.
    """
    if not os.path.exists(ENCODINGS_FILE) or os.path.getsize(ENCODINGS_FILE) == 0:
        return []
        
    try:
        with open(ENCODINGS_FILE, 'rb') as f:
            encodings_data = pickle.load(f)
            
        known_students = []
        for item in encodings_data:
            known_students.append({
                'student_id': item['Roll_No'], # Using Roll_No as student_id
                'roll_number': item['Roll_No'],
                'name': item['Name'],
                'encoding': item['encoding']
            })
        return known_students
    except Exception:
        return []

def mark_attendance(roll_number):
    """
    Marks attendance for a student for the current date in attendance_log.csv.
    Updates Last_Attendance in students.csv.
    """
    now = datetime.datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')
    roll_number_str = str(roll_number)
    
    try:
        # Load attendance log
        try:
            df_att = pd.read_csv(ATTENDANCE_CSV)
        except Exception:
            df_att = pd.DataFrame(columns=['Date', 'Time', 'Roll_No', 'Name', 'Status'])
        
        # Check if already marked today
        already_marked = df_att[(df_att['Roll_No'].astype(str) == roll_number_str) & (df_att['Date'] == current_date)]
        if not already_marked.empty:
            return False, "Attendance already marked for today."
            
        # Get Name from students.csv
        df_students = pd.read_csv(STUDENTS_CSV)
        student_match = df_students[df_students['Roll_No'].astype(str) == roll_number_str]
        
        if student_match.empty:
            return False, f"Roll number {roll_number} not found."
            
        name = student_match.iloc[0]['Name']
        
        # Add to attendance
        new_att = {
            'Date': current_date,
            'Time': current_time,
            'Roll_No': roll_number_str,
            'Name': name,
            'Status': 'Present'
        }
        df_att = pd.concat([df_att, pd.DataFrame([new_att])], ignore_index=True)
        df_att.to_csv(ATTENDANCE_CSV, index=False)
        
        # Update Last_Attendance
        df_students.loc[df_students['Roll_No'].astype(str) == roll_number_str, 'Last_Attendance'] = f"{current_date} {current_time}"
        df_students.to_csv(STUDENTS_CSV, index=False)
        
        return True, f"Attendance marked for {name}."
    except Exception as e:
        return False, f"File error: {str(e)}"

def search_student_by_name(name_query):
    """
    Returns a list of dicts matching the name query (case-insensitive partial match).
    """
    try:
        df = pd.read_csv(STUDENTS_CSV)
        matches = df[df['Name'].str.contains(name_query, case=False, na=False)]
        return matches.to_dict('records')
    except Exception:
        return []

def fetch_attendance_report(date_filter=None):
    """
    Fetches the attendance report including absentees. 
    Optionally filtered by date, otherwise groups by all dates present in the log.
    If no dates in log, creates a report for today where everyone is absent.
    """
    try:
        df_students = pd.read_csv(STUDENTS_CSV)
    except Exception:
        df_students = pd.DataFrame(columns=['Roll_No', 'Name'])
        
    try:
        df_att = pd.read_csv(ATTENDANCE_CSV)
    except Exception:
        df_att = pd.DataFrame(columns=['Date', 'Time', 'Roll_No', 'Name', 'Status'])
        
    if date_filter:
        dates_to_process = [date_filter]
    else:
        if not df_att.empty:
            dates_to_process = df_att['Date'].unique().tolist()
        else:
            dates_to_process = [datetime.datetime.now().strftime('%Y-%m-%d')]
            
    all_rows = []
    
    for date in dates_to_process:
        df_att_date = df_att[df_att['Date'] == date]
        present_rolls = [str(r).strip() for r in df_att_date['Roll_No'].astype(str).tolist()]
        
        # Add present students
        for index, row in df_att_date.iterrows():
            all_rows.append((row['Date'], row['Time'], row['Roll_No'], row['Name'], row['Status']))
            
        # Add absent students
        for index, s_row in df_students.iterrows():
            roll = str(s_row['Roll_No']).strip()
            if roll not in present_rolls:
                all_rows.append((date, "-", s_row['Roll_No'], s_row['Name'], "Absent"))
                
    df_result = pd.DataFrame(all_rows, columns=['Date', 'Time', 'Roll_No', 'Name', 'Status'])
    if not df_result.empty:
        # Sort by Date desc, Status desc (Present comes before Absent), Time desc
        df_result = df_result.sort_values(by=['Date', 'Status', 'Time'], ascending=[False, False, False])
        
        rows = []
        for index, row in df_result.iterrows():
            rows.append((row['Roll_No'], row['Name'], row['Status'], row['Date'], row['Time']))
        return rows
    return []

def get_dashboard_stats():
    """
    Returns basic stats for the dashboard.
    """
    try:
        df_students = pd.read_csv(STUDENTS_CSV)
        total_students = len(df_students)
    except Exception:
        total_students = 0
        
    try:
        df_att = pd.read_csv(ATTENDANCE_CSV)
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        today_present = len(df_att[df_att['Date'] == current_date])
    except Exception:
        today_present = 0
        
    return {
        'total_students': total_students,
        'today_present': today_present
    }

def update_encodings_from_csv(face_engine):
    """
    Scans students.csv and dataset/, adding any missing encodings to encodings.pickle.
    Returns the number of new encodings added.
    """
    if not os.path.exists(STUDENTS_CSV):
        return 0
        
    df = pd.read_csv(STUDENTS_CSV)
    
    # Load existing encodings
    encodings_data = []
    if os.path.exists(ENCODINGS_FILE) and os.path.getsize(ENCODINGS_FILE) > 0:
        try:
            with open(ENCODINGS_FILE, 'rb') as f:
                encodings_data = pickle.load(f)
        except (EOFError, pickle.UnpicklingError):
            encodings_data = []
            
    existing_rolls = [str(item['Roll_No']) for item in encodings_data]
    
    added_count = 0
    for index, row in df.iterrows():
        roll = str(row['Roll_No'])
        name = row['Name']
        image_path = row['Image_Path']
        
        if roll not in existing_rolls:
            if os.path.exists(image_path):
                image = cv2.imread(image_path)
                if image is not None:
                    try:
                        encoding = face_engine.get_face_encoding(image)
                        if encoding is not None:
                            encodings_data.append({
                                'Roll_No': roll,
                                'Name': name,
                                'encoding': encoding
                            })
                            added_count += 1
                    except Exception as e:
                        print(f"Error extracting encoding for {roll}: {e}")
                        
    if added_count > 0:
        with open(ENCODINGS_FILE, 'wb') as f:
            pickle.dump(encodings_data, f)
            
    return added_count
