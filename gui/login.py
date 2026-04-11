import customtkinter as ctk
from core import auth
from tkinter import messagebox

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_success_callback, **kwargs):
        super().__init__(master, fg_color="#f0f2f5", **kwargs)
        
        self.on_success_callback = on_success_callback
        
        # Ensure we have default admin if no file exists
        auth.init_admin()
        
        # Main Frame setup
        self.main_frame = ctk.CTkFrame(self, width=500, height=600, corner_radius=25, fg_color="white", border_width=2, border_color="#e0e0e0")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.main_frame.pack_propagate(False) # Keep fixed size
        
        # Logo or Title Label
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="Welcome Back\nAdmin Portal", 
            font=ctk.CTkFont(size=32, weight="bold", family="Helvetica"),
            justify="center",
            text_color="#1f538d"
        )
        self.title_label.pack(pady=(60, 40))
        
        # Username Frame
        self.user_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.user_frame.pack(pady=(10, 20), padx=60, fill="x")
        self.user_label = ctk.CTkLabel(self.user_frame, text="Username", font=ctk.CTkFont(size=15, weight="bold"), text_color="#333333")
        self.user_label.pack(anchor="w", pady=(0, 5))
        self.username_entry = ctk.CTkEntry(
            self.user_frame, 
            placeholder_text="Enter admin username",
            height=45,
            font=ctk.CTkFont(size=14),
            border_color="#cccccc",
            fg_color="#f9f9f9"
        )
        self.username_entry.pack(fill="x")
        
        # Password Frame
        self.pass_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pass_frame.pack(pady=(10, 30), padx=60, fill="x")
        self.pass_label = ctk.CTkLabel(self.pass_frame, text="Password", font=ctk.CTkFont(size=15, weight="bold"), text_color="#333333")
        self.pass_label.pack(anchor="w", pady=(0, 5))
        self.password_entry = ctk.CTkEntry(
            self.pass_frame, 
            placeholder_text="Enter admin password",
            show="*",
            height=45,
            font=ctk.CTkFont(size=14),
            border_color="#cccccc",
            fg_color="#f9f9f9"
        )
        self.password_entry.pack(fill="x")
        
        # Error Label
        self.error_label = ctk.CTkLabel(
            self.main_frame, 
            text="", 
            text_color="#cc0000",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.error_label.pack(pady=(0, 15))
        
        # Login Button
        self.login_button = ctk.CTkButton(
            self.main_frame, 
            text="LOGIN", 
            command=self.attempt_login,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.login_button.pack(padx=60, fill="x", pady=(10, 15))
        
        # Change Password Button
        self.change_pass_btn = ctk.CTkButton(
            self.main_frame,
            text="Change Password",
            fg_color="transparent",
            text_color="#777777",
            hover_color="#f0f0f0",
            font=ctk.CTkFont(size=13, underline=True),
            command=self.open_change_password
        )
        self.change_pass_btn.pack(pady=(0, 20))
        
        # Bind Enter key to login
        self.username_entry.bind('<Return>', lambda event: self.attempt_login())
        self.password_entry.bind('<Return>', lambda event: self.attempt_login())
        
        # Set focus to username entry
        self.username_entry.focus()
        
    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.error_label.configure(text="Please fill in both fields")
            return
            
        if auth.verify_login(username, password):
            # Success
            self.error_label.configure(text="Login successful!", text_color="green")
            self.update()
            
            # Briefly sleep or instantly load next window, we just call callback
            self.after(500, self.proceed_to_app)
        else:
            # Failure
            self.error_label.configure(text="Invalid Username or Password!", text_color="#cc0000")
            
    def proceed_to_app(self):
        if self.on_success_callback:
            self.on_success_callback()

    def open_change_password(self):
        ChangePasswordWindow(self)

class ChangePasswordWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Change Admin Password")
        self.geometry("400x500")
        self.resizable(False, False)
        
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        
        self.update_idletasks()
        app_win = parent.winfo_toplevel()
        x = app_win.winfo_rootx() + (app_win.winfo_width() // 2) - (self.winfo_width() // 2)
        y = app_win.winfo_rooty() + (app_win.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self.lbl_title = ctk.CTkLabel(self, text="Change Password", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.pack(pady=(30, 20))
        
        self.entry_user = ctk.CTkEntry(self, placeholder_text="Username (e.g. admin)", height=40)
        self.entry_user.pack(padx=40, fill="x", pady=(10, 10))
        
        self.entry_old = ctk.CTkEntry(self, placeholder_text="Old Password", show="*", height=40)
        self.entry_old.pack(padx=40, fill="x", pady=(10, 10))
        
        self.entry_new = ctk.CTkEntry(self, placeholder_text="New Password", show="*", height=40)
        self.entry_new.pack(padx=40, fill="x", pady=(10, 10))
        
        self.entry_confirm = ctk.CTkEntry(self, placeholder_text="Confirm New Password", show="*", height=40)
        self.entry_confirm.pack(padx=40, fill="x", pady=(10, 20))
        
        self.error_label = ctk.CTkLabel(self, text="", text_color="#cc0000", font=ctk.CTkFont(size=12, weight="bold"))
        self.error_label.pack(pady=(0, 10))
        
        self.btn_submit = ctk.CTkButton(self, text="Submit", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.submit)
        self.btn_submit.pack(padx=40, fill="x", pady=10)

    def submit(self):
        user = self.entry_user.get().strip()
        old = self.entry_old.get().strip()
        new = self.entry_new.get().strip()
        confirm = self.entry_confirm.get().strip()
        
        if not user or not old or not new or not confirm:
            self.error_label.configure(text="Please fill all fields", text_color="#cc0000")
            return
            
        if new != confirm:
            self.error_label.configure(text="New passwords do not match", text_color="#cc0000")
            return
            
        if not auth.verify_login(user, old):
            self.error_label.configure(text="Invalid username or old password", text_color="#cc0000")
            return
            
        success, msg = auth.update_password(user, new)
        if success:
            messagebox.showinfo("Success", "Password changed successfully!")
            self.destroy()
        else:
            self.error_label.configure(text=msg, text_color="#cc0000")

if __name__ == "__main__":
    def dummy_success():
        print("Login success callback triggered")
    
    app = ctk.CTk()
    app.geometry("1100x700")
    frame = LoginFrame(app, dummy_success)
    frame.pack(expand=True, fill="both")
    app.mainloop()
