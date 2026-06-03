import csv
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

VERSION = "1.1"

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def load_authenticator_csv(path):
    results = {}
    try:
        with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) < 3:
                    continue
                email = (row[1] or '').strip().lower()
                secret = (row[2] or '').strip()
                if email and secret:
                    if email not in results:
                        results[email] = []
                    if secret not in results[email]:
                        results[email].append(secret)
    except Exception as e:
        print(f"Error reading authenticator CSV: {e}")
    return results

def load_recover_csv(path):
    results = {}
    try:
        with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) < 4:
                    continue
                name_field = (row[2] or '').strip()
                secret = (row[3] or '').strip()
                email = ''
                if ':' in name_field:
                    email = name_field.split(':', 1)[1].strip().lower()
                else:
                    email = name_field.lower()
                if email and secret:
                    if email not in results:
                        results[email] = []
                    if secret not in results[email]:
                        results[email].append(secret)
    except Exception as e:
        print(f"Error reading recover CSV: {e}")
    return results

def find_csv_files(base):
    auth_path = None
    recover_path = None
    for f in os.listdir(base):
        fl = f.lower()
        if fl.endswith('.csv'):
            if 'authenticator' in fl:
                auth_path = os.path.join(base, f)
            elif 'recover' in fl or 'merged' in fl:
                recover_path = os.path.join(base, f)
    return auth_path, recover_path

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Secret Key Lookup v{VERSION}")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(False, False)

        w, h = 520, 500
        sx = (self.root.winfo_screenwidth() - w) // 2
        sy = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f'{w}x{h}+{sx}+{sy}')

        self.auth_data = {}
        self.recover_data = {}
        self.auth_path = None
        self.recover_path = None

        self._build_ui()
        self._try_load_csvs()

    def _build_ui(self):
        title = tk.Label(self.root, text="Secret Key Lookup", font=('Segoe UI', 16, 'bold'),
                         bg='#1a1a2e', fg='white')
        title.pack(pady=(16, 4))

        self.status_lbl = tk.Label(self.root, text="Loading...", font=('Segoe UI', 9),
                                    bg='#1a1a2e', fg='#6b7280')
        self.status_lbl.pack(pady=(0, 8))

        btn_frame = tk.Frame(self.root, bg='#1a1a2e')
        btn_frame.pack(padx=20, fill='x')

        self.load_auth_btn = tk.Button(btn_frame, text="Load Authenticator CSV",
                                        font=('Segoe UI', 9), bg='#16213e', fg='#a5b4fc',
                                        activebackground='#1e3a5f', activeforeground='white',
                                        relief='flat', cursor='hand2', padx=8, pady=2,
                                        command=self._pick_auth_csv)
        self.load_auth_btn.pack(side='left', padx=(0, 4))

        self.load_rec_btn = tk.Button(btn_frame, text="Load Recover CSV",
                                       font=('Segoe UI', 9), bg='#16213e', fg='#a5b4fc',
                                       activebackground='#1e3a5f', activeforeground='white',
                                       relief='flat', cursor='hand2', padx=8, pady=2,
                                       command=self._pick_recover_csv)
        self.load_rec_btn.pack(side='left')

        sep = tk.Frame(self.root, bg='#374151', height=1)
        sep.pack(fill='x', padx=20, pady=(8, 8))

        input_frame = tk.Frame(self.root, bg='#1a1a2e')
        input_frame.pack(padx=20, fill='x')

        tk.Label(input_frame, text="Email:", font=('Segoe UI', 10, 'bold'),
                 bg='#1a1a2e', fg='#a5b4fc').pack(side='left', padx=(0, 8))

        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(input_frame, textvariable=self.email_var,
                                     font=('Consolas', 11), width=32,
                                     bg='#16213e', fg='white', insertbackground='white',
                                     relief='flat', bd=0, highlightthickness=2,
                                     highlightbackground='#374151', highlightcolor='#4f46e5')
        self.email_entry.pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 8))
        self.email_entry.bind('<Return>', lambda e: self.do_search())

        self.search_btn = tk.Button(input_frame, text="Search", font=('Segoe UI', 10, 'bold'),
                                     bg='#4f46e5', fg='white', activebackground='#4338ca',
                                     activeforeground='white', relief='flat', cursor='hand2',
                                     padx=16, pady=4, command=self.do_search)
        self.search_btn.pack(side='left')

        result_frame = tk.Frame(self.root, bg='#1a1a2e')
        result_frame.pack(padx=20, pady=(12, 0), fill='both', expand=True)

        self.result_text = tk.Text(result_frame, font=('Consolas', 11),
                                    bg='#16213e', fg='#e2e8f0', relief='flat',
                                    bd=0, highlightthickness=1,
                                    highlightbackground='#374151',
                                    wrap='word', state='disabled',
                                    padx=10, pady=10)
        self.result_text.pack(fill='both', expand=True)

        self.result_text.tag_configure('header', foreground='#a5b4fc', font=('Segoe UI', 10, 'bold'))
        self.result_text.tag_configure('key', foreground='#22d3ee', font=('Consolas', 13, 'bold'))
        self.result_text.tag_configure('source', foreground='#6b7280', font=('Segoe UI', 9))
        self.result_text.tag_configure('error', foreground='#f87171', font=('Segoe UI', 10))
        self.result_text.tag_configure('success', foreground='#4ade80', font=('Segoe UI', 10, 'bold'))
        self.result_text.tag_configure('divider', foreground='#374151')

        hint = tk.Label(self.root, text="Place CSV files next to the EXE, or use the Load buttons above",
                        font=('Segoe UI', 8), bg='#1a1a2e', fg='#4b5563')
        hint.pack(pady=(4, 8))

        self.email_entry.focus_set()

    def _try_load_csvs(self):
        base = get_base_dir()
        auth_path, recover_path = find_csv_files(base)

        if auth_path:
            self.auth_data = load_authenticator_csv(auth_path)
            self.auth_path = auth_path
        if recover_path:
            self.recover_data = load_recover_csv(recover_path)
            self.recover_path = recover_path

        self._update_status()

    def _update_status(self):
        parts = []
        if self.auth_data:
            parts.append(f"Auth: {sum(len(v) for v in self.auth_data.values())} keys")
        else:
            parts.append("Auth: not loaded")
        if self.recover_data:
            parts.append(f"Recover: {sum(len(v) for v in self.recover_data.values())} keys")
        else:
            parts.append("Recover: not loaded")

        total = len(self.auth_data) + len(self.recover_data)
        color = '#4ade80' if total > 0 else '#f87171'
        self.status_lbl.configure(text=" | ".join(parts), fg=color)

    def _pick_auth_csv(self):
        path = filedialog.askopenfilename(title="Select Authenticator CSV",
                                           filetypes=[("CSV files", "*.csv")])
        if path:
            self.auth_data = load_authenticator_csv(path)
            self.auth_path = path
            self._update_status()

    def _pick_recover_csv(self):
        path = filedialog.askopenfilename(title="Select Recover CSV",
                                           filetypes=[("CSV files", "*.csv")])
        if path:
            self.recover_data = load_recover_csv(path)
            self.recover_path = path
            self._update_status()

    def do_search(self):
        email = self.email_var.get().strip().lower()
        if not email:
            return

        self.result_text.configure(state='normal')
        self.result_text.delete('1.0', 'end')

        if not self.auth_data and not self.recover_data:
            self.result_text.insert('end', "No CSV files loaded!\n\n", 'error')
            self.result_text.insert('end', "Use the 'Load' buttons above to select your\n", 'source')
            self.result_text.insert('end', "Authenticator and/or Recover CSV files.", 'source')
            self.result_text.configure(state='disabled')
            return

        auth_keys = self.auth_data.get(email, [])
        recover_keys = self.recover_data.get(email, [])

        all_keys = []
        for k in auth_keys:
            all_keys.append((k, 'Authenticator'))
        for k in recover_keys:
            found = False
            for existing_k, existing_src in all_keys:
                if existing_k == k:
                    found = True
                    break
            if not found:
                all_keys.append((k, 'Recover'))
            else:
                for i, (ek, es) in enumerate(all_keys):
                    if ek == k and 'Recover' not in es:
                        all_keys[i] = (ek, es + ' + Recover')

        if not all_keys:
            self.result_text.insert('end', f"No secret keys found for:\n", 'error')
            self.result_text.insert('end', f"{email}\n\n", 'key')
            self.result_text.insert('end', "Check that the email is correct.", 'source')
        else:
            self.result_text.insert('end', f"Found {len(all_keys)} secret key(s) for:\n", 'success')
            self.result_text.insert('end', f"{email}\n", 'header')
            self.result_text.insert('end', "─" * 46 + "\n\n", 'divider')

            for i, (key, source) in enumerate(all_keys):
                self.result_text.insert('end', f"Key {i+1}:\n", 'header')
                self.result_text.insert('end', f"{key}\n", 'key')
                self.result_text.insert('end', f"Source: {source}\n\n", 'source')

        self.result_text.configure(state='disabled')

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    App().run()
