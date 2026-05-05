import csv
import os
import sys
import tkinter as tk
from tkinter import messagebox

VERSION = "1.0"

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
    except FileNotFoundError:
        pass
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
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error reading recover CSV: {e}")
    return results

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Secret Key Lookup v{VERSION}")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(False, False)

        w, h = 520, 460
        sx = (self.root.winfo_screenwidth() - w) // 2
        sy = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f'{w}x{h}+{sx}+{sy}')

        base = get_base_dir()
        self.auth_data = {}
        self.recover_data = {}

        auth_path = None
        recover_path = None
        for f in os.listdir(base):
            fl = f.lower()
            if 'authenticator' in fl and fl.endswith('.csv'):
                auth_path = os.path.join(base, f)
            elif ('recover' in fl or 'merged' in fl) and fl.endswith('.csv'):
                recover_path = os.path.join(base, f)

        status_parts = []
        if auth_path:
            self.auth_data = load_authenticator_csv(auth_path)
            status_parts.append(f"Authenticator: {sum(len(v) for v in self.auth_data.values())} keys")
        else:
            status_parts.append("Authenticator CSV: NOT FOUND")

        if recover_path:
            self.recover_data = load_recover_csv(recover_path)
            status_parts.append(f"Recover: {sum(len(v) for v in self.recover_data.values())} keys")
        else:
            status_parts.append("Recover CSV: NOT FOUND")

        title = tk.Label(self.root, text="Secret Key Lookup", font=('Segoe UI', 16, 'bold'),
                         bg='#1a1a2e', fg='white')
        title.pack(pady=(16, 4))

        status = tk.Label(self.root, text=" | ".join(status_parts), font=('Segoe UI', 9),
                          bg='#1a1a2e', fg='#6b7280')
        status.pack(pady=(0, 12))

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

        hint = tk.Label(self.root, text="Place both CSV files in the same folder as this EXE",
                        font=('Segoe UI', 8), bg='#1a1a2e', fg='#4b5563')
        hint.pack(pady=(4, 8))

        self.email_entry.focus_set()

    def do_search(self):
        email = self.email_var.get().strip().lower()
        if not email:
            return

        self.result_text.configure(state='normal')
        self.result_text.delete('1.0', 'end')

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
            self.result_text.insert('end', "Make sure the email is correct and the CSV files\nare in the same folder as this EXE.", 'source')
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
