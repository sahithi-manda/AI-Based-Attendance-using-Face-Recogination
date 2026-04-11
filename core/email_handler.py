import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

# ==========================================
# IMPORTANT: CONFIGURE YOUR CREDENTIALS HERE
# ==========================================
SENDER_EMAIL = "REMOVED_SENDER_EMAIL" 
SENDER_PASSWORD = "REMOVED_SMTP_APP_PASSWORD"

def send_email_async(receiver_email, subject, body):
    def _send():
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = receiver_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Assuming Gmail. Port 587
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"Email sent successfully to {receiver_email}")
        except Exception as e:
            print(f"Failed to send email to {receiver_email}: {e}")
            
    threading.Thread(target=_send, daemon=True).start()

def send_attendance_email(roll_number, name, status, date, time):
    """Builds the email template based on attendance status and triggers the async dispatcher"""
    receiver_email = f"{str(roll_number).strip().lower()}@sreyas.ac.in"
    
    if status.lower() == "present":
        subject = f"Attendance Marked: {date}"
        body = f"Dear {name},\n\nYour attendance has been successfully marked as PRESENT on {date} at {time}.\n\nIf you believe this is an error, please contact administration.\n\nThank you,\nAI Attendance System"
    else:
        subject = f"Absence Notice: {date}"
        body = f"Dear {name},\n\nYou have been marked as ABSENT for {date}.\n\nIf you were present and this was due to a technical glitch, please notify the administration immediately so this can be corrected.\n\nThank you,\nAI Attendance System"
        
    send_email_async(receiver_email, subject, body)
