import os

app_path = r'c:\Users\hp\OneDrive\Desktop\ATTENDANCEC-LIGHT\gui\app.py'

with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    # apply_hover_and_zebra
    "tree.tag_configure('evenrow', background='#252526', foreground='#d4d4d4')": "tree.tag_configure('evenrow', background='#f2f2f2', foreground='#000000')",
    "tree.tag_configure('oddrow', background='#1e1e1e', foreground='#d4d4d4')": "tree.tag_configure('oddrow', background='#ffffff', foreground='#000000')",
    "tree.tag_configure('hover', background='#2a2d2e', foreground='white')": "tree.tag_configure('hover', background='#e5f1fb', foreground='#000000')",

    # Global treeview
    'self.style.configure("Treeview", background="#1e1e1e", foreground="#d4d4d4", rowheight=35, fieldbackground="#1e1e1e", borderwidth=0, font=("Helvetica", 14))': 'self.style.configure("Treeview", background="#ffffff", foreground="#000000", rowheight=35, fieldbackground="#ffffff", borderwidth=0, font=("Helvetica", 14))',
    'self.style.map(\'Treeview\', background=[(\'selected\', \'#3a7ebf\')], foreground=[(\'selected\', \'white\')])': 'self.style.map(\'Treeview\', background=[(\'selected\', \'#3a7ebf\')], foreground=[(\'selected\', \'white\')])',
    'self.style.configure("Treeview.Heading", background="#2d2d2d", foreground="#ffffff", relief="flat", font=("Helvetica", 15, "bold"), borderwidth=1, bordercolor="#444444")': 'self.style.configure("Treeview.Heading", background="#e0e0e0", foreground="#000000", relief="flat", font=("Helvetica", 15, "bold"), borderwidth=1, bordercolor="#cccccc")',
    'self.style.map("Treeview.Heading", background=[(\'active\', \'#3d3d3d\')])': 'self.style.map("Treeview.Heading", background=[(\'active\', \'#d0d0d0\')])',

    # Splitter
    'self.splitter = ctk.CTkFrame(self, width=4, corner_radius=0, fg_color="#333333", cursor="sb_h_double_arrow")': 'self.splitter = ctk.CTkFrame(self, width=4, corner_radius=0, fg_color="#cccccc", cursor="sb_h_double_arrow")',
    'self.splitter.bind("<Leave>", lambda e: self.splitter.configure(fg_color="#333333"))': 'self.splitter.bind("<Leave>", lambda e: self.splitter.configure(fg_color="#cccccc"))',

    # Analytics text
    ', text_color="#ffcc00")': ', text_color="#d4a000")',
    ', text_color="#ff4d4d")': ', text_color="#cc0000")'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Theme updated successfully!")
