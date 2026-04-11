import customtkinter as ctk
import cv2
from PIL import Image
import threading
import datetime
import pandas as pd
import os
import numpy as np
from tkinter import messagebox
from tkinter import ttk

from core import db_handler
from core.face_engine import FaceEngine
from core.anti_spoofing import SpoofDetector

def apply_hover_and_zebra(tree):
    # Define JupyterLab style Dark Themes
    tree.tag_configure('evenrow', background='#f2f2f2', foreground='#000000')
    tree.tag_configure('oddrow', background='#ffffff', foreground='#000000')
    tree.tag_configure('hover', background='#e5f1fb', foreground='#000000') 

    tree.previous_hover = None
    def on_motion(event):
        item = tree.identify_row(event.y)
        if item != getattr(tree, "previous_hover", None):
            if getattr(tree, "previous_hover", None):
                try:
                    tags = list(tree.item(tree.previous_hover, "tags"))
                    if 'hover' in tags:
                        tags.remove('hover')
                        tree.item(tree.previous_hover, tags=tags)
                except Exception: pass
            if item:
                try:
                    tags = list(tree.item(item, "tags"))
                    if 'hover' not in tags:
                        tags.append('hover')
                        tree.item(item, tags=tags)
                except Exception: pass
            tree.previous_hover = item
            
    def on_leave(event):
        if getattr(tree, "previous_hover", None):
            try:
                tags = list(tree.item(tree.previous_hover, "tags"))
                if 'hover' in tags:
                    tags.remove('hover')
                    tree.item(tree.previous_hover, tags=tags)
            except Exception: pass
            tree.previous_hover = None

    tree.bind("<Motion>", on_motion)
    tree.bind("<Leave>", on_leave)

def make_treeview_scroll_independent(tree):
    def on_mouse_wheel(event):
        if event.delta: # Windows / Mac
            tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
            
    def on_mouse_wheel_linux_up(event):
        tree.yview_scroll(-1, "units")
        return "break"
        
    def on_mouse_wheel_linux_down(event):
        tree.yview_scroll(1, "units")
        return "break"

    tree.bind("<MouseWheel>", on_mouse_wheel)
    tree.bind("<Button-4>", on_mouse_wheel_linux_up)
    tree.bind("<Button-5>", on_mouse_wheel_linux_down)

def get_camera_capture():
    """Safely initialize the camera, using V4L2 backend on Linux (Raspberry Pi) for better compatibility."""
    if os.name == 'posix':
        return cv2.VideoCapture(0, cv2.CAP_V4L2)
    return cv2.VideoCapture(0)

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Attendance System")
        self.geometry("1100x700")
        
        # Setup Global Treeview Styles
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("Treeview", background="#ffffff", foreground="#000000", rowheight=35, fieldbackground="#ffffff", borderwidth=0, font=("Helvetica", 14))
        self.style.map('Treeview', background=[('selected', '#3a7ebf')], foreground=[('selected', 'white')])
        self.style.configure("Treeview.Heading", background="#e0e0e0", foreground="#000000", relief="flat", font=("Helvetica", 15, "bold"), borderwidth=1, bordercolor="#cccccc")
        self.style.map("Treeview.Heading", background=[('active', '#d0d0d0')])
        
        # Initialize engines
        self.face_engine = FaceEngine()
        self.spoof_detector = SpoofDetector()
        
        # Grid layout (1x3)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=0) # Splitter
        self.grid_columnconfigure(2, weight=1) # Main content
        
        # Sidebar
        self.sidebar_width = 200
        self.sidebar_frame = ctk.CTkFrame(self, width=self.sidebar_width, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(8, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        
        # Splitter
        self.splitter = ctk.CTkFrame(self, width=4, corner_radius=0, fg_color="#cccccc", cursor="sb_h_double_arrow")
        self.splitter.grid(row=0, column=1, sticky="ns")
        self.splitter.bind("<B1-Motion>", self.resize_sidebar)
        self.splitter.bind("<Enter>", lambda e: self.splitter.configure(fg_color="#1f538d"))
        self.splitter.bind("<Leave>", lambda e: self.splitter.configure(fg_color="#cccccc"))
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AI Attendance", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=lambda: self.select_frame("dashboard"))
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_register = ctk.CTkButton(self.sidebar_frame, text="Register Student", command=lambda: self.select_frame("register"))
        self.btn_register.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_train = ctk.CTkButton(self.sidebar_frame, text="Train Model", command=self.train_model)
        self.btn_train.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_scanner = ctk.CTkButton(self.sidebar_frame, text="Live Scanner", command=lambda: self.select_frame("scanner"))
        self.btn_scanner.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_search = ctk.CTkButton(self.sidebar_frame, text="Search/Verify", command=lambda: self.select_frame("search"))
        self.btn_search.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_reports = ctk.CTkButton(self.sidebar_frame, text="Reports", command=lambda: self.select_frame("reports"))
        self.btn_reports.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_analytics = ctk.CTkButton(self.sidebar_frame, text="Advanced Analytics", command=lambda: self.select_frame("analytics"))
        self.btn_analytics.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_logout = ctk.CTkButton(self.sidebar_frame, text="Log Out", command=self.logout, fg_color="#b53333", hover_color="#8f2828")
        self.btn_logout.grid(row=9, column=0, padx=20, pady=20, sticky="ew")
        
        # Main frames
        self.frames = {}
        
        # Load the LoginFrame
        from gui.login import LoginFrame
        self.frames["login"] = LoginFrame(self, lambda: self.select_frame("dashboard"))
        
        # Dashboard Frame
        self.frames["dashboard"] = DashboardFrame(self)
        self.frames["register"] = RegisterFrame(self)
        self.frames["scanner"] = ScannerFrame(self)
        self.frames["search"] = SearchVerifyFrame(self)
        self.frames["reports"] = ReportsFrame(self)
        self.frames["analytics"] = AnalyticsFrame(self)
        
        # Start with dashboard
        self.current_frame = None
        self.select_frame("login")

    def select_frame(self, name):
        if self.current_frame:
            self.current_frame.grid_forget()
            if hasattr(self.current_frame, 'stop_webcam'):
                self.current_frame.stop_webcam()
                
        if name == "login":
            self.sidebar_frame.grid_remove()
            self.splitter.grid_remove()
            self.current_frame = self.frames[name]
            self.current_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
        else:
            self.sidebar_frame.grid()
            self.splitter.grid()
            self.current_frame = self.frames[name]
            self.current_frame.grid(row=0, column=2, sticky="nsew", padx=20, pady=20)
        
        if hasattr(self.current_frame, 'refresh_data'):
            self.current_frame.refresh_data()
            
    def resize_sidebar(self, event):
        new_width = self.winfo_pointerx() - self.winfo_rootx()
        if new_width < 150: new_width = 150
        if new_width > 500: new_width = 500
        self.sidebar_frame.configure(width=new_width)
        self.sidebar_width = new_width
            
    def train_model(self):
        self.btn_train.configure(state="disabled", text="Training (May take a while)...")
        self.update()
        
        try:
            added_count = db_handler.update_encodings_from_csv(self.face_engine)
            if added_count > 0:
                self.face_engine.reload_known_faces()
                messagebox.showinfo("Success", f"Successfully trained {added_count} new face(s)!")
            else:
                messagebox.showinfo("Info", "All database students are already trained, or no valid images found.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during training: {str(e)}")
        finally:
            self.btn_train.configure(state="normal", text="Train Model")

    def logout(self):
        answer = messagebox.askyesno("Log Out", "Are you sure you want to log out?")
        if answer:
            self.select_frame("login")

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master_app = master
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)
        
        lbl_title = ctk.CTkLabel(self, text="Dashboard Overview", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Stats cards
        self.card_students = ctk.CTkFrame(self, fg_color="#1f538d", border_color="#3a7ebf", border_width=2, corner_radius=15)
        self.card_students.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.lbl_total_students = ctk.CTkLabel(self.card_students, text="Total Students\n0", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        self.lbl_total_students.pack(expand=True, pady=30)
        
        self.card_attendance = ctk.CTkFrame(self, fg_color="#2b7b51", border_color="#43a06a", border_width=2, corner_radius=15)
        self.card_attendance.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")
        self.lbl_today_attendance = ctk.CTkLabel(self.card_attendance, text="Present Today\n0", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        self.lbl_today_attendance.pack(expand=True, pady=30)
        
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=2, column=0, columnspan=2, pady=10)
        self.btn_notify_absent = ctk.CTkButton(actions_frame, text="Notify Absentees (Today)", command=self.notify_absentees, fg_color="#b53333", hover_color="#8f2828", font=ctk.CTkFont(weight="bold", size=14))
        self.btn_notify_absent.grid(row=0, column=0, padx=10)
        self.btn_export = ctk.CTkButton(actions_frame, text="Export CSV", command=self.export_csv, font=ctk.CTkFont(weight="bold", size=14))
        self.btn_export.grid(row=0, column=1, padx=10)

        # Table (Treeview) for Today
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        self.table_frame.grid_rowconfigure(1, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
        lbl_table_title = ctk.CTkLabel(self.table_frame, text="Today's Attendance", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_table_title.grid(row=0, column=0, columnspan=2, pady=(10, 5))
        
        columns = ("Roll No", "Name", "Status", "Date", "Time")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", style="Treeview")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
            
        self.tree.grid(row=1, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")
        apply_hover_and_zebra(self.tree)
        

        
    def refresh_data(self):
        stats = db_handler.get_dashboard_stats()
        total = stats['total_students']
        present = stats['today_present']
        
        self.lbl_total_students.configure(text=f"Total Students\n{total}")
        self.lbl_today_attendance.configure(text=f"Present Today\n{present}")

        import datetime
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        rows = db_handler.fetch_attendance_report(date_filter=current_date)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for i, r in enumerate(rows):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]), tags=(tag,))

    def export_csv(self):
        from tkinter import messagebox
        import pandas as pd
        import datetime
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        rows = db_handler.fetch_attendance_report(date_filter=current_date)
        if not rows:
            messagebox.showinfo("Export", "No data to export for today.")
            return
            
        df = pd.DataFrame(rows, columns=['Roll Number', 'Name', 'Status', 'Date', 'Time'])
        filename = f"attendance_today_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Export Success", f"Today's report saved to {filename}")

    def notify_absentees(self):
        answer = messagebox.askyesno("Confirm", "Are you sure you want to send ABSENT emails to all students not marked present today?\n\n(Make sure your email credentials are set in email_handler.py)")
        if not answer:
            return
            
        try:
            from core import email_handler
            import datetime
            import pandas as pd
            import os
            
            self.btn_notify_absent.configure(state="disabled", text="Sending...")
            self.update()
            
            if not os.path.exists("students.csv"):
                messagebox.showerror("Error", "No students database found.")
                return
                
            df_students = pd.read_csv("students.csv")
            try:
                df_att = pd.read_csv("attendance_log.csv")
            except Exception:
                df_att = pd.DataFrame(columns=['Date', 'Time', 'Roll_No', 'Name', 'Status'])
                
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            today_att = df_att[df_att['Date'] == current_date]
            present_rolls = today_att['Roll_No'].astype(str).tolist()
            
            absent_count = 0
            for index, row in df_students.iterrows():
                roll = str(row['Roll_No'])
                name = row['Name']
                if roll not in present_rolls:
                    email_handler.send_attendance_email(roll, name, "Absent", current_date, "N/A")
                    absent_count += 1
                    
            messagebox.showinfo("Success", f"Triggered absent emails for {absent_count} student(s)!\n(Check your console for SMTP delivery status)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to notify absentees: {str(e)}")
        finally:
            self.btn_notify_absent.configure(state="normal", text="Notify Absentees (Today)")
        


class RegisterFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master_app = master
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)
        
        lbl_title = ctk.CTkLabel(self, text="Register New Student", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Form
        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ctk.CTkLabel(form_frame, text="Roll Number:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_roll = ctk.CTkEntry(form_frame, width=200)
        self.entry_roll.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(form_frame, text="Full Name:").grid(row=1, column=0, padx=10, pady=10)
        self.entry_name = ctk.CTkEntry(form_frame, width=200)
        self.entry_name.grid(row=1, column=1, padx=10, pady=10)
        
        # Webcam Feed for registration
        self.video_label = ctk.CTkLabel(self, text="Webcam Feed")
        self.video_label.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.btn_start_cam = ctk.CTkButton(btn_frame, text="Start Camera", command=self.start_webcam)
        self.btn_start_cam.pack(side="left", padx=10)
        
        self.btn_capture = ctk.CTkButton(btn_frame, text="Capture & Register", command=self.capture_and_register, state="disabled")
        self.btn_capture.pack(side="left", padx=10)
        
        self.cap = None
        self.is_running = False
        self.current_frame = None

    def start_webcam(self):
        if not self.is_running:
            self.cap = get_camera_capture()
            self.is_running = True
            self.btn_start_cam.configure(text="Stop Camera")
            self.btn_capture.configure(state="normal")
            self.update_webcam()
        else:
            self.stop_webcam()

    def stop_webcam(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.video_label.configure(image="", text="Webcam Feed Stopped")
        self.btn_start_cam.configure(text="Start Camera")
        self.btn_capture.configure(state="disabled")

    def update_webcam(self):
        if self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame.copy()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 360))
                self.video_label.configure(image=imgtk, text="")
            self.after(10, self.update_webcam)

    def capture_and_register(self):
        roll = self.entry_roll.get().strip()
        name = self.entry_name.get().strip()
        
        if not roll or not name:
            messagebox.showerror("Error", "Please enter Roll Number and Name.")
            return
            
        if self.current_frame is None:
            messagebox.showerror("Error", "No frame available from webcam.")
            return
            
        # Get face encoding
        encoding = self.master_app.face_engine.get_face_encoding(self.current_frame)
        if encoding is None:
            messagebox.showerror("Error", "No face detected! Please ensure your face is clearly visible.")
            return
            
        # Save image to dataset folder
        image_path = os.path.join("dataset", f"{roll}.jpg")
        cv2.imwrite(image_path, self.current_frame)
            
        success, msg = db_handler.register_student(roll, name, encoding, image_path)
        if success:
            messagebox.showinfo("Success", f"{name} registered successfully!")
            self.entry_roll.delete(0, 'end')
            self.entry_name.delete(0, 'end')
            self.master_app.face_engine.reload_known_faces()
            self.stop_webcam()
        else:
            messagebox.showerror("Database Error", msg)

class ScannerFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master_app = master
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)
        
        lbl_title = ctk.CTkLabel(self, text="Live Attendance Scanner", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, columnspan=2, pady=10)
        
        self.video_label = ctk.CTkLabel(self, text="Webcam Feed")
        self.video_label.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
        
        self.log_textbox = ctk.CTkTextbox(self, height=100)
        self.log_textbox.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10, padx=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.btn_start = ctk.CTkButton(btn_frame, text="Start Scanner", command=self.start_scanner)
        self.btn_start.pack()
        
        self.cap = None
        self.is_running = False
        
        # Track already marked students in this session to avoid spamming DB
        self.session_marked_ids = set()
        # Track students who have blinked in this session to prove liveness
        self.student_blink_status = {}

    def log(self, text):
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")

    def start_scanner(self):
        if not self.is_running:
            self.cap = get_camera_capture()
            self.is_running = True
            self.btn_start.configure(text="Stop Scanner", fg_color="red")
            self.session_marked_ids.clear()
            self.student_blink_status.clear()
            self.update_scanner()
        else:
            self.stop_webcam()

    def stop_webcam(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.video_label.configure(image="", text="Webcam Feed Stopped")
        self.btn_start.configure(text="Start Scanner", fg_color=["#3a7ebf", "#1f538d"]) # Restore original color

    def update_scanner(self):
        if self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 1. Recognize faces
                faces = self.master_app.face_engine.recognize_faces(frame)
                
                # 2. Run anti-spoofing heuristic over the whole frame
                # To keep it fast, we can extract face bounding boxes and pass them to anti-spoofing
                bboxes = [f['bbox'] for f in faces]
                spoof_results = []
                if bboxes:
                    spoof_results = self.master_app.spoof_detector.analyze_frame(frame, bboxes)
                
                # 3. Draw and logic
                for i, face in enumerate(faces):
                    top, right, bottom, left = face['bbox']
                    name = face['name']
                    student_id = face['student_id']
                    
                    color = (0, 0, 255) # Red default for unknown/spoof
                    label = "Unknown"
                    
                    if i < len(spoof_results):
                        s_res = spoof_results[i]
                        
                        is_real_passive = s_res.get('is_real', False)
                        is_blinking = s_res.get('blink_detected', False)
                        reason = s_res.get('reason', '')
                        
                        if name != "Unknown" and student_id is not None:
                            # Update blink status for the current recognized student
                            if is_blinking:
                                self.student_blink_status[student_id] = True
                                
                            has_blinked = self.student_blink_status.get(student_id, False)
                            
                            if not is_real_passive:
                                # Failed passive checks (texture, edge, glare)
                                label = f"SPOOF: {reason}"
                                color = (0, 0, 255) # Red
                            elif not has_blinked:
                                # Passed passive checks, but waiting for proof of life (blink)
                                label = f"{name} (WAITING FOR BLINK)"
                                color = (0, 165, 255) # Orange
                            else:
                                # Fully verified
                                label = f"{name} (LIVE)"
                                color = (0, 255, 0) # Green for verified
                                
                                # Mark attendance if not already marked in this GUI session
                                if student_id not in self.session_marked_ids:
                                    success, msg = db_handler.mark_attendance(student_id)
                                    if success:
                                        self.log(f"✅ [{datetime.datetime.now().strftime('%H:%M:%S')}] {name} Present.")
                                        self.session_marked_ids.add(student_id)
                                    else:
                                        # Already marked today in DB
                                        self.session_marked_ids.add(student_id)
                                        self.log(f"ℹ️ [{datetime.datetime.now().strftime('%H:%M:%S')}] {name} already marked today.")
                    
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

                # Show frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                # Resize keeping aspect ratio based on widget size to avoid stretching, 
                # but standard 640x480 is fine for display
                imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
                self.video_label.configure(image=imgtk, text="")
                
            self.after(20, self.update_scanner)

class SearchVerifyFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)
        
        lbl_title = ctk.CTkLabel(self, text="Search & Verify Attendance", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, columnspan=2, pady=10)
        
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew", padx=20)
        
        # Search by Name
        ctk.CTkLabel(search_frame, text="Search by Name:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_name = ctk.CTkEntry(search_frame, width=200)
        self.entry_name.grid(row=0, column=1, padx=10, pady=10)
        self.btn_search_name = ctk.CTkButton(search_frame, text="Search", command=self.search_by_name)
        self.btn_search_name.grid(row=0, column=2, padx=10, pady=10)
        
        # Verify by Roll No
        ctk.CTkLabel(search_frame, text="Verify by Roll No:").grid(row=1, column=0, padx=10, pady=10)
        self.entry_roll = ctk.CTkEntry(search_frame, width=200)
        self.entry_roll.grid(row=1, column=1, padx=10, pady=10)
        self.btn_verify_roll = ctk.CTkButton(search_frame, text="Mark Present", command=self.verify_by_roll)
        self.btn_verify_roll.grid(row=1, column=2, padx=10, pady=10)
        
        # Results Table
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
        columns = ("Roll No", "Name", "Last Attendance")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", style="Treeview")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
            
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        apply_hover_and_zebra(self.tree)
        
    def search_by_name(self):
        query = self.entry_name.get().strip()
        if not query:
            messagebox.showwarning("Input Error", "Please enter a name to search.")
            return
            
        results = db_handler.search_student_by_name(query)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not results:
            return
            
        for i, r in enumerate(results):
            last_att = str(r.get('Last_Attendance', ''))
            # Handle float nan which pandas might return for empty strings
            if last_att == 'nan':
                 last_att = 'Never'
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=(r['Roll_No'], r['Name'], last_att), tags=(tag,))
            
    def verify_by_roll(self):
        roll = self.entry_roll.get().strip()
        if not roll:
            messagebox.showwarning("Input Error", "Please enter a Roll Number.")
            return
            
        success, msg = db_handler.mark_attendance(roll)
        if success:
            messagebox.showinfo("Success", msg)
            self.entry_roll.delete(0, 'end')
        else:
            messagebox.showerror("Error", msg)

class ReportsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)
        
        lbl_title = ctk.CTkLabel(self, text="Attendance Reports", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Tools
        tools_frame = ctk.CTkFrame(self, fg_color="transparent")
        tools_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.btn_export = ctk.CTkButton(tools_frame, text="Export CSV", command=self.export_csv)
        self.btn_export.pack(side="left", padx=10)
        

        
        # Table (Treeview)
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
        columns = ("Roll No", "Name", "Status", "Date", "Time")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", style="Treeview")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
            
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        apply_hover_and_zebra(self.tree)
        
    def refresh_data(self):
        rows = db_handler.fetch_attendance_report()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for i, r in enumerate(rows):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]), tags=(tag,))

    def export_csv(self):
        rows = db_handler.fetch_attendance_report()
        if not rows:
            messagebox.showinfo("Export", "No data to export.")
            return
            
        df = pd.DataFrame(rows, columns=['Roll Number', 'Name', 'Status', 'Date', 'Time'])
        filename = f"attendance_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Export Success", f"Report saved to {filename}")



class AnalyticsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(self, text="Advanced Analytics", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, pady=(10, 0))
        
        # Tools Frame (Refresh)
        tools_frame = ctk.CTkFrame(self, fg_color="transparent")
        tools_frame.grid(row=0, column=0, sticky="e", padx=20, pady=(10, 0))
        self.btn_refresh = ctk.CTkButton(tools_frame, text="Refresh Data", command=self.refresh_data)
        self.btn_refresh.pack()
        
        # Top Section (At-Risk & Predictive)
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        top_frame.grid_columnconfigure((0, 1), weight=1)
        top_frame.grid_rowconfigure(1, weight=1)
        
        # At Risk
        risk_box = ctk.CTkFrame(top_frame)
        risk_box.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10)
        risk_box.grid_rowconfigure(1, weight=1)
        risk_box.grid_columnconfigure(0, weight=1)
        
        risk_header = ctk.CTkFrame(risk_box, fg_color="transparent")
        risk_header.grid(row=0, column=0, columnspan=2, sticky="ew")
        risk_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(risk_header, text="Download CSV", width=100, command=self.export_risk_csv).grid(row=0, column=0, padx=5, pady=(5,0))
        ctk.CTkLabel(risk_header, text="At-Risk Students (>15% Drop in last 14 days)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#d4a000").grid(row=1, column=0, pady=5, sticky="w")
        self.tree_risk = ttk.Treeview(risk_box, columns=("Roll No", "Name", "Drop %", "Recent %", "Prev %"), show="headings", style="Treeview")
        for col in ("Roll No", "Name", "Drop %", "Recent %", "Prev %"):
            self.tree_risk.heading(col, text=col)
            if col == "Name": width = 180
            elif col == "Roll No": width = 100
            else: width = 120
            self.tree_risk.column(col, width=width, minwidth=100, anchor="center", stretch=True)
        self.tree_risk.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        scroll_risk = ttk.Scrollbar(risk_box, orient="vertical", command=self.tree_risk.yview)
        self.tree_risk.configure(yscrollcommand=scroll_risk.set)
        scroll_risk.grid(row=1, column=1, sticky="ns", pady=(0, 5))
        apply_hover_and_zebra(self.tree_risk)
        
        # Predictive
        pred_box = ctk.CTkFrame(top_frame)
        pred_box.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10)
        pred_box.grid_rowconfigure(1, weight=1)
        pred_box.grid_columnconfigure(0, weight=1)
        
        pred_header = ctk.CTkFrame(pred_box, fg_color="transparent")
        pred_header.grid(row=0, column=0, columnspan=2, sticky="ew")
        pred_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(pred_header, text="Download CSV", width=100, command=self.export_pred_csv).grid(row=0, column=0, padx=5, pady=(5,0))
        ctk.CTkLabel(pred_header, text="Predictive Alerts (<75% Projected End)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#cc0000").grid(row=1, column=0, pady=5, sticky="w")
        self.tree_pred = ttk.Treeview(pred_box, columns=("Roll No", "Name", "Current %", "Projected %"), show="headings", style="Treeview")
        for col in ("Roll No", "Name", "Current %", "Projected %"):
            self.tree_pred.heading(col, text=col)
            if col == "Name": width = 180
            elif col == "Roll No": width = 100
            elif col == "Projected %": width = 140
            else: width = 120
            self.tree_pred.column(col, width=width, minwidth=100, anchor="center", stretch=True)
        self.tree_pred.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        scroll_pred = ttk.Scrollbar(pred_box, orient="vertical", command=self.tree_pred.yview)
        self.tree_pred.configure(yscrollcommand=scroll_pred.set)
        scroll_pred.grid(row=1, column=1, sticky="ns", pady=(0, 5))
        apply_hover_and_zebra(self.tree_pred)
        

        
    def refresh_data(self):
        from core import analytics
        
        # 1. At-Risk
        for item in self.tree_risk.get_children(): self.tree_risk.delete(item)
        at_risk = analytics.get_at_risk_students()
        for i, r in enumerate(at_risk):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree_risk.insert("", "end", values=(r["Roll_No"], r["Name"], f"{r['Drop_Percentage']}%", f"{r['Recent_Rate']}%", f"{r['Previous_Rate']}%"), tags=(tag,))
            
        # 2. Predictive
        for item in self.tree_pred.get_children(): self.tree_pred.delete(item)
        alerts = analytics.get_predictive_alerts()
        for i, a in enumerate(alerts):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree_pred.insert("", "end", values=(a["Roll_No"], a["Name"], f"{a['Current_Rate']}%", f"{a['Projected_Rate']}%"), tags=(tag,))

    def export_risk_csv(self):
        from core import analytics
        import pandas as pd
        import datetime
        from tkinter import messagebox
        
        data = analytics.get_at_risk_students()
        if not data:
            messagebox.showinfo("Export", "No at-risk data to export.")
            return
            
        df = pd.DataFrame(data)
        filename = f"at_risk_students_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Export Success", f"At-Risk List saved to {filename} (Can be opened in Excel)")

    def export_pred_csv(self):
        from core import analytics
        import pandas as pd
        import datetime
        from tkinter import messagebox
        
        data = analytics.get_predictive_alerts()
        if not data:
            messagebox.showinfo("Export", "No predictive alerts data to export.")
            return
            
        df = pd.DataFrame(data)
        filename = f"predictive_alerts_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Export Success", f"Predictive Alerts saved to {filename} (Can be opened in Excel)")


class ReportsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # --- SECTION 1: MONTHLY ATTENDANCE ---
        self.frame_monthly = ctk.CTkFrame(self)
        self.frame_monthly.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        self.frame_monthly.grid_rowconfigure(2, weight=1)
        self.frame_monthly.grid_columnconfigure(0, weight=1)
        
        lbl_monthly_title = ctk.CTkLabel(self.frame_monthly, text="Monthly Attendance Report", font=ctk.CTkFont(size=22, weight="bold"))
        lbl_monthly_title.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=15)
        
        tools_monthly = ctk.CTkFrame(self.frame_monthly, fg_color="transparent")
        tools_monthly.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        
        import datetime
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        
        self.lbl_month_bounds = ctk.CTkLabel(tools_monthly, text="From Date: YYYY-MM-DD  |  To Date: YYYY-MM-DD", font=ctk.CTkFont(weight="bold"))
        self.lbl_month_bounds.pack(side="left", padx=(0, 20))
        
        self.combo_month = ctk.CTkOptionMenu(tools_monthly, values=[str(m) for m in range(1, 13)], command=self.refresh_monthly)
        self.combo_month.set(str(current_month))
        self.combo_month.pack(side="left", padx=5)
        
        self.combo_year = ctk.CTkOptionMenu(tools_monthly, values=[str(y) for y in range(2020, 2030)], command=self.refresh_monthly)
        self.combo_year.set(str(current_year))
        self.combo_year.pack(side="left", padx=5)
        
        btn_export_monthly = ctk.CTkButton(tools_monthly, text="Download CSV", command=self.export_monthly)
        btn_export_monthly.pack(side="right")
        
        columns = ("Roll No", "Name", "Attended", "Total Classes", "Percentage")
        self.tree_monthly = ttk.Treeview(self.frame_monthly, columns=columns, show="headings", style="Treeview", height=8)
        for col in columns:
            self.tree_monthly.heading(col, text=col)
            self.tree_monthly.column(col, anchor="center")
        self.tree_monthly.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))
        
        scroll_m = ttk.Scrollbar(self.frame_monthly, orient="vertical", command=self.tree_monthly.yview)
        self.tree_monthly.configure(yscrollcommand=scroll_m.set)
        scroll_m.grid(row=2, column=1, sticky="ns", pady=(5, 15))
        apply_hover_and_zebra(self.tree_monthly)
        make_treeview_scroll_independent(self.tree_monthly)
        
        
        # --- SECTION 2: OVERALL ATTENDANCE ---
        self.frame_overall = ctk.CTkFrame(self)
        self.frame_overall.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        self.frame_overall.grid_rowconfigure(2, weight=1)
        self.frame_overall.grid_columnconfigure(0, weight=1)
        
        lbl_overall_title = ctk.CTkLabel(self.frame_overall, text="Overall Attendance Report", font=ctk.CTkFont(size=22, weight="bold"))
        lbl_overall_title.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=15)
        
        tools_overall = ctk.CTkFrame(self.frame_overall, fg_color="transparent")
        tools_overall.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        
        btn_export_overall = ctk.CTkButton(tools_overall, text="Download CSV", command=self.export_overall)
        btn_export_overall.pack(side="right")
        
        self.tree_overall = ttk.Treeview(self.frame_overall, columns=columns, show="headings", style="Treeview", height=8)
        for col in columns:
            self.tree_overall.heading(col, text=col)
            self.tree_overall.column(col, anchor="center")
        self.tree_overall.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))
        
        scroll_o = ttk.Scrollbar(self.frame_overall, orient="vertical", command=self.tree_overall.yview)
        self.tree_overall.configure(yscrollcommand=scroll_o.set)
        scroll_o.grid(row=2, column=1, sticky="ns", pady=(5, 15))
        apply_hover_and_zebra(self.tree_overall)
        make_treeview_scroll_independent(self.tree_overall)
        
    def refresh_data(self):
        self.refresh_monthly()
        self.refresh_overall()
        
    def refresh_monthly(self, *args):
        try:
            year = int(self.combo_year.get())
            month = int(self.combo_month.get())
            
            from core import analytics
            rows, start_date, end_date = analytics.get_monthly_attendance(year, month)
            
            self.lbl_month_bounds.configure(text=f"From Date: {start_date}  |  To Date: {end_date}")
            
            for item in self.tree_monthly.get_children():
                self.tree_monthly.delete(item)
                
            for i, r in enumerate(rows):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree_monthly.insert("", "end", values=(r['Roll_No'], r['Name'], r['Attended'], r['Total_Classes'], f"{r['Percentage']}%"), tags=(tag,))
        except Exception as e:
            print(f"Error in UI refresh_monthly: {e}")
            
    def refresh_overall(self):
        try:
            from core import analytics
            rows = analytics.get_overall_attendance()
            
            for item in self.tree_overall.get_children():
                self.tree_overall.delete(item)
                
            for i, r in enumerate(rows):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree_overall.insert("", "end", values=(r['Roll_No'], r['Name'], r['Attended'], r['Total_Classes'], f"{r['Percentage']}%"), tags=(tag,))
        except Exception as e:
            print(f"Error in UI refresh_overall: {e}")

    def export_monthly(self):
        from tkinter import messagebox
        import pandas as pd
        import datetime
        from core import analytics
        
        year = int(self.combo_year.get())
        month = int(self.combo_month.get())
        rows, _, _ = analytics.get_monthly_attendance(year, month)
        if not rows:
            messagebox.showinfo("Export", "No data available for this month.")
            return
            
        df = pd.DataFrame(rows)
        filename = f"monthly_attendance_{year}_{month:02d}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Export Success", f"Monthly report saved to {filename}")

    def export_overall(self):
        from tkinter import messagebox
        import pandas as pd
        import datetime
        from core import analytics
        
        rows = analytics.get_overall_attendance()
        if not rows:
            messagebox.showinfo("Export", "No attendance data available.")
            return
            
        df = pd.DataFrame(rows)
        filename = f"overall_attendance_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Export Success", f"Overall report saved to {filename}")
