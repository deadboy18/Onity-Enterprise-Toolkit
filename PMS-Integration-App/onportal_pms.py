import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from datetime import datetime, timedelta
import json
import os

# --- MODERN TOOLTIP CLASS ---
class ToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(400, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#1e293b", foreground="#ffffff", relief=tk.FLAT,
                         font=("Segoe UI", "9", "normal"), padx=10, pady=5)
        label.pack()

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# --- ONITY PROTOCOL ENGINE ---
class OnityPMSClient:
    def __init__(self, host, port=6669, timeout=15): 
        self.host = host
        self.port = port
        self.timeout = timeout
        self.STX, self.ETX, self.ENQ, self.ACK, self.NAK = '\x02', '\x03', '\x05', '\x06', '\x15'
        self.SEP = chr(179) 

    def _calculate_lrc(self, data):
        lrc = 0
        for char in data: lrc ^= ord(char)
        return chr(lrc)

    def test_connection(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3) # Short timeout for pings
                s.connect((self.host, self.port))
                s.sendall(self.ENQ.encode('latin-1')) 
                response = s.recv(1024).decode('latin-1', errors='ignore')
                if response == self.ACK: return "<ENQ>", "<ACK> (Success! Server is ready)"
                elif response == self.NAK: return "<ENQ>", "<NAK> (Server replied busy)"
                else: return "<ENQ>", f"Unexpected Response: {repr(response)}"
        except Exception as e:
            return "<ENQ>", f"Connection Error: {str(e)}"

    def _send_command(self, cmd_body):
        msg_to_lrc = f"{self.SEP}{cmd_body}{self.SEP}{self.ETX}"
        lrc = self._calculate_lrc(msg_to_lrc)
        packet = f"{self.STX}{msg_to_lrc}{lrc}"
        
        # FIX: Safely format readable request without mangling inner bytes
        packet_no_lrc = packet[:-1] 
        readable_req = packet_no_lrc.replace(self.SEP, '|').replace(self.STX, '<STX>').replace(self.ETX, '<ETX>') + '<LRC>'
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))
                s.sendall(packet.encode('latin-1')) 
                first_reply = s.recv(1024).decode('latin-1', errors='ignore')
                
                if self.NAK in first_reply: return readable_req, "<NAK> Server rejected command format"
                if self.ACK in first_reply:
                    if self.STX in first_reply:
                        res_clean = first_reply.replace(self.ACK, '<ACK> ').replace(self.SEP, '|').replace(self.STX, '<STX>').replace(self.ETX, '<ETX>')
                        return readable_req, res_clean
                    final_reply = s.recv(2048).decode('latin-1', errors='ignore')
                    res_clean = final_reply.replace(self.SEP, '|').replace(self.STX, '<STX>').replace(self.ETX, '<ETX>')
                    return readable_req, f"<ACK> received... then -> {res_clean}"
                return readable_req, f"Unknown reply: {repr(first_reply)}"
        except socket.timeout:
            return readable_req, "⏳ TIMEOUT: Server accepted it, but didn't read a card in time."
        except Exception as e:
            return f"Error", f"Connection Error: {str(e)}"

    def check_in(self, encoder_id, room, operator, nights, auths=""):
        now = datetime.now()
        start_date = now.strftime("%H%d%m%y") 
        checkout_date = now + timedelta(days=nights)
        end_date = f"12{checkout_date.strftime('%d%m%y')}" 
        parts = ["CN1", str(encoder_id), "E", room, "", "", "", auths, "", start_date, end_date, operator, "", "", ""]
        return self._send_command(self.SEP.join(parts))

    def check_out(self, room): return self._send_command(f"CO{self.SEP}0{self.SEP}{room}")
    def read_card(self, encoder_id): return self._send_command(f"LT{self.SEP}{encoder_id}{self.SEP}E")
    def reset_encoder(self, encoder_id): return self._send_command(f"EX{self.SEP}{encoder_id}{self.SEP}E")

# --- UI APPLICATION ---
class OnityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Onity OnPortal PMS Integration Tool")
        self.geometry("1200x800")
        
        self.bg_color = "#f0f2f5" 
        self.card_bg = "#ffffff"  
        self.configure(bg=self.bg_color)
        
        self.style = ttk.Style(self)
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
            
        self._configure_styles()
        
        self.profile = {
            "hotel_name": "Unconfigured Hotel",
            "host": "127.0.0.1",
            "port": 6669,
            "encoders": ["1 - Default"],
            "rooms": ["101"],
            "authorizations": {}
        }
        
        self._build_ui()
        self._apply_profile()
        
        # Start the background status ping
        self._start_status_ping()

    def _configure_styles(self):
        accent_blue = "#0056b3"
        accent_blue_hover = "#004494"
        text_color = "#212529"

        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('Card.TFrame', background=self.card_bg)
        self.style.configure('TLabel', background=self.card_bg, font=('Segoe UI', 10), foreground=text_color)
        self.style.configure('Header.TLabel', background=self.card_bg, font=('Segoe UI', 11, 'bold'), foreground=accent_blue)
        
        self.style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'), background=accent_blue, foreground='white')
        self.style.map('Action.TButton', background=[('active', accent_blue_hover)])

    def _build_ui(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hotel Profile", menu=file_menu)
        file_menu.add_command(label="Load Profile (JSON)", command=self.load_profile)
        file_menu.add_command(label="Save Current Profile", command=self.save_profile)
        
        # --- TOP BRANDING & STATUS PING ---
        header_frame = tk.Frame(self, bg="#ffffff", height=60)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="Onity OnPortal PMS Tool", bg="#ffffff", fg="#0056b3", font=("Segoe UI", 16, "bold")).pack(side="left", padx=20, pady=15)
        
        # The Server Status Indicator
        self.status_canvas = tk.Canvas(header_frame, width=16, height=16, bg="#ffffff", highlightthickness=0)
        self.status_canvas.pack(side="right", padx=(5, 20), pady=22)
        self.status_dot = self.status_canvas.create_oval(2, 2, 14, 14, fill="#9ca3af", outline="") # Default gray
        
        self.status_label = tk.Label(header_frame, text="Server: Checking...", bg="#ffffff", fg="#6c757d", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="right", pady=20)
        
        self.hotel_label = tk.Label(header_frame, text="Operating as: Unconfigured Hotel", bg="#ffffff", fg="#6c757d", font=("Segoe UI", 10))
        self.hotel_label.pack(side="right", padx=20, pady=20)
        
        # Spacer
        tk.Frame(self, bg=self.bg_color, height=15).pack(fill="x")

        # --- MAIN CONTENT GRID ---
        content_frame = tk.Frame(self, bg=self.bg_color)
        content_frame.pack(fill="both", expand=True, padx=20)
        
        # Left Panel (Settings)
        left_panel = ttk.Frame(content_frame, style='Card.TFrame')
        left_panel.pack(side="left", fill="y", ipadx=10, ipady=10)
        
        ttk.Label(left_panel, text="1. SYSTEM SETTINGS", style='Header.TLabel').grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))
        
        ttk.Label(left_panel, text="Host/IP:").grid(row=1, column=0, sticky="e", padx=(15, 5), pady=8)
        self.host_var = tk.StringVar()
        host_entry = ttk.Entry(left_panel, textvariable=self.host_var, width=18, font=("Segoe UI", 10))
        host_entry.grid(row=1, column=1, sticky="w", padx=5, pady=8)
        ToolTip(host_entry, "Hostname or IP of the Onity Main Server.")
        
        ttk.Label(left_panel, text="Port:").grid(row=2, column=0, sticky="e", padx=(15, 5), pady=8)
        self.port_var = tk.IntVar()
        port_entry = ttk.Entry(left_panel, textvariable=self.port_var, width=8, font=("Segoe UI", 10))
        port_entry.grid(row=2, column=1, sticky="w", padx=5, pady=8)
        ToolTip(port_entry, "PMS Listener Port. Usually 6669.")

        ttk.Label(left_panel, text="2. CARD PARAMETERS", style='Header.TLabel').grid(row=3, column=0, columnspan=2, sticky="w", padx=15, pady=(20, 10))
        
        ttk.Label(left_panel, text="Encoder:").grid(row=4, column=0, sticky="e", padx=(15, 5), pady=8)
        self.enc_var = tk.StringVar()
        self.enc_combo = ttk.Combobox(left_panel, textvariable=self.enc_var, state="readonly", width=17, font=("Segoe UI", 10))
        self.enc_combo.grid(row=4, column=1, sticky="w", padx=5, pady=8)
        ToolTip(self.enc_combo, "Select the physical USB encoder station.")
        
        ttk.Label(left_panel, text="Room:").grid(row=5, column=0, sticky="e", padx=(15, 5), pady=8)
        self.room_var = tk.StringVar()
        self.room_combo = ttk.Combobox(left_panel, textvariable=self.room_var, width=10, font=("Segoe UI", 10))
        self.room_combo.grid(row=5, column=1, sticky="w", padx=5, pady=8)
        ToolTip(self.room_combo, "Select the guest room to encode.")
        
        ttk.Label(left_panel, text="Nights:").grid(row=6, column=0, sticky="e", padx=(15, 5), pady=8)
        self.nights_var = tk.StringVar(value="1")
        nights_entry = ttk.Entry(left_panel, textvariable=self.nights_var, width=5, font=("Segoe UI", 10))
        nights_entry.grid(row=6, column=1, sticky="w", padx=5, pady=8)
        ToolTip(nights_entry, "Number of nights. Sets checkout for 12:00 PM.")
        
        ttk.Label(left_panel, text="Operator:").grid(row=7, column=0, sticky="e", padx=(15, 5), pady=8)
        self.op_var = tk.StringVar(value="FrontDesk")
        ttk.Entry(left_panel, textvariable=self.op_var, width=18, font=("Segoe UI", 10)).grid(row=7, column=1, sticky="w", padx=5, pady=8)
        
        ttk.Label(left_panel, text="Authorizations:").grid(row=8, column=0, sticky="ne", padx=(15, 5), pady=8)
        self.auth_listbox = tk.Listbox(left_panel, selectmode=tk.MULTIPLE, height=4, width=20, font=("Segoe UI", 9), relief=tk.SOLID, borderwidth=1, bg="#f8f9fa")
        self.auth_listbox.grid(row=8, column=1, sticky="w", padx=5, pady=8)
        ToolTip(self.auth_listbox, "Hold CTRL on your keyboard to select multiple special access areas.")

        # Right Panel (Actions & Logs)
        right_panel = ttk.Frame(content_frame, style='TFrame')
        right_panel.pack(side="left", fill="both", expand=True, padx=(20, 0))

        btn_frame = ttk.Frame(right_panel, style='Card.TFrame')
        btn_frame.pack(fill="x", pady=(0, 15), ipadx=10, ipady=15)
        
        ttk.Label(btn_frame, text="3. ACTIONS", style='Header.TLabel').pack(anchor="w", padx=15, pady=(5, 10))
        
        b_frame = ttk.Frame(btn_frame, style='Card.TFrame')
        b_frame.pack(fill="x", padx=15)
        ttk.Button(b_frame, text="📖 READ CARD (LT)", style='Action.TButton', command=self.do_read).pack(side="left", padx=(0, 10), expand=True, fill="x", ipady=8)
        ttk.Button(b_frame, text="✍️ CHECK-IN (CN1)", style='Action.TButton', command=self.do_checkin).pack(side="left", padx=10, expand=True, fill="x", ipady=8)
        ttk.Button(b_frame, text="🗑️ CHECK-OUT (CO)", style='Action.TButton', command=self.do_checkout).pack(side="left", padx=10, expand=True, fill="x", ipady=8)
        ttk.Button(b_frame, text="🔄 RESET READER", style='Action.TButton', command=self.do_reset).pack(side="left", padx=(10, 0), expand=True, fill="x", ipady=8)

        # Split Logs
        log_frame = ttk.Frame(right_panel, style='TFrame')
        log_frame.pack(fill="both", expand=True)
        log_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(1, weight=1)

        raw_card = ttk.Frame(log_frame, style='Card.TFrame')
        raw_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ttk.Label(raw_card, text="RAW NETWORK DATA", style='Header.TLabel').pack(anchor="w", padx=15, pady=(15, 5))
        self.raw_log = scrolledtext.ScrolledText(raw_card, wrap=tk.WORD, font=("Consolas", 9), bg="#1e293b", fg="#10b981", insertbackground="white", relief=tk.FLAT, padx=10, pady=10)
        self.raw_log.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        clean_card = ttk.Frame(log_frame, style='Card.TFrame')
        clean_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ttk.Label(clean_card, text="LIVE DASHBOARD", style='Header.TLabel').pack(anchor="w", padx=15, pady=(15, 5))
        self.clean_log = scrolledtext.ScrolledText(clean_card, wrap=tk.WORD, font=("Segoe UI", 10), bg="#ffffff", relief=tk.SOLID, borderwidth=1, padx=10, pady=10)
        self.clean_log.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.clean_log.tag_config('success', foreground='#15803d', font=("Segoe UI", 10, "bold")) 
        self.clean_log.tag_config('error', foreground='#b91c1c', font=("Segoe UI", 10, "bold"))   
        self.clean_log.tag_config('warning', foreground='#c2410c', font=("Segoe UI", 10, "bold")) 
        self.clean_log.tag_config('info', foreground='#0369a1', font=("Segoe UI", 10, "italic"))  

    # --- BACKGROUND PING THREAD ---
    def _start_status_ping(self):
        def ping_task():
            host = self.host_var.get()
            port = self.port_var.get()
            if not host or not port:
                self.update_status_ui("#9ca3af", "Not Configured")
                return
                
            client = OnityPMSClient(host, int(port), timeout=2)
            req, res = client.test_connection()
            
            if "<ACK>" in res:
                self.update_status_ui("#10b981", "Online") # Green
            else:
                self.update_status_ui("#ef4444", "Offline") # Red
                
        # Run the ping in a separate thread so it doesn't freeze the GUI
        threading.Thread(target=ping_task, daemon=True).start()
        
        # Schedule the next ping in 10 seconds
        self.after(10000, self._start_status_ping)

    def update_status_ui(self, color, text):
        self.status_canvas.itemconfig(self.status_dot, fill=color)
        self.status_label.config(text=f"Server: {text}")
        if color == "#ef4444":
            self.status_label.config(fg="#ef4444")
        else:
            self.status_label.config(fg="#6c757d")

    def load_profile(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Profiles", "*.json")])
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    self.profile = json.load(f)
                self._apply_profile()
                self._print_clean("📂 Hotel Profile Loaded Successfully!", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load profile:\n{e}")

    def save_profile(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Profiles", "*.json")])
        if filepath:
            self.profile["host"] = self.host_var.get()
            self.profile["port"] = self.port_var.get()
            try:
                with open(filepath, 'w') as f:
                    json.dump(self.profile, f, indent=4)
                self._print_clean(f"💾 Profile Saved to {os.path.basename(filepath)}", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save profile:\n{e}")

    def _apply_profile(self):
        hotel_name = self.profile.get('hotel_name', 'Untitled')
        self.hotel_label.config(text=f"Operating as: {hotel_name}")
        self.host_var.set(self.profile.get("host", "127.0.0.1"))
        self.port_var.set(self.profile.get("port", 6669))
        
        encoders = self.profile.get("encoders", [])
        self.enc_combo['values'] = encoders
        if encoders: self.enc_combo.current(0)
        
        rooms = self.profile.get("rooms", [])
        self.room_combo['values'] = rooms
        if rooms: self.room_combo.current(0)
        
        self.auth_listbox.delete(0, tk.END)
        self.auth_map = {} 
        auths = self.profile.get("authorizations", {})
        for idx, (code, name) in enumerate(auths.items()):
            self.auth_listbox.insert(tk.END, f"{name} ({code})")
            self.auth_map[idx] = code
            
        # Trigger an immediate ping when a profile is loaded
        self.update_status_ui("#9ca3af", "Checking...")
        threading.Thread(target=self._start_status_ping, daemon=True).start()

    def log_raw(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.raw_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.raw_log.see(tk.END)
        self.update()

    def _print_clean(self, message, tag=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if tag:
            self.clean_log.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        else:
            self.clean_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.clean_log.see(tk.END)
        self.update()

    def parse_response(self, res):
        clean_res = res.replace('<ACK> received... then -> ', '').replace('<STX>', '').replace('<ETX>', '').strip()
        parts = clean_res.split('|')
        
        if len(parts) < 2:
            if "<NAK>" in res: self._print_clean("❌ ERROR: Server Rejected Command Format (NAK)", "error")
            elif "TIMEOUT" in res: self._print_clean("⏳ TIMEOUT: Card was not tapped on the reader in time.", "warning")
            return

        cmd = parts[1]
        if cmd == 'LT':
            if len(parts) >= 12:
                room = parts[3]
                status_code = parts[7]
                copy_num = parts[8]
                auths = parts[9] if parts[9] else "None"
                
                status_map = {'CI': 'Checked In', 'CO': 'Checked Out', 'VD': 'Voided', 'OP': 'Staff/Operator'}
                full_status = f"{status_code} ({status_map.get(status_code, 'Unknown')})"
                
                parsed = "🏨 CARD READ SUCCESS\n"
                parsed += f"   ▶ Room:       {room}\n"
                parsed += f"   ▶ Status:     {full_status}\n"
                parsed += f"   ▶ Copy #:     {copy_num}\n"
                parsed += f"   ▶ Auth Codes: {auths}\n"
                self._print_clean(parsed, "success")
            elif len(parts) >= 4 and parts[3] in ['LD', 'LC']:
                self._print_clean(f"⚠️ CARD READ: Blank, Staff, or Cancelled Card ({parts[3]}).", "warning")
            else:
                self._print_clean("⚠️ DATA INCOMPLETE", "warning")
        elif cmd == 'CN1': self._print_clean("✅ CARD ENCODED SUCCESSFULLY", "success")
        elif cmd == 'CO': self._print_clean("✅ CHECK-OUT SUCCESSFUL (Database updated)", "success")
        elif cmd == 'ED': self._print_clean("❌ ERROR (ED): Card not inserted. Place card on reader!", "error")
        elif cmd == 'ES': self._print_clean("❌ ERROR (ES): Syntax Error.", "error")
        elif cmd == 'TD': self._print_clean("❌ ERROR (TD): Unknown Room.", "error")
        
        self._print_clean("-" * 45)

    def get_selected_encoder_id(self):
        return self.enc_var.get().split(" - ")[0]

    def execute_command(self, func, prompt_clean, prompt_raw, *args):
        client = OnityPMSClient(self.host_var.get(), int(self.port_var.get()))
        self.log_raw(prompt_raw)
        self._print_clean(prompt_clean, "info")
        
        req, res = func(client, *args)
        
        self.log_raw(f"SENT: {req}")
        self.log_raw(f"RECV: {res}")
        self.log_raw("-" * 60)
        self.parse_response(res)

    def do_read(self):
        self.execute_command(OnityPMSClient.read_card, "🔔 LISTEN FOR BEEP! Tap card on reader now...", "Awaiting hardware read event...", self.get_selected_encoder_id())

    def do_checkin(self):
        selected_indices = self.auth_listbox.curselection()
        auth_str = "".join([self.auth_map[i] for i in selected_indices])
        
        room = self.room_var.get()
        if room not in self.profile.get("rooms", []):
            if not messagebox.askyesno("Warning", f"Room '{room}' is not in the profile's room list.\n\nSend anyway?"):
                return
                
        try: nights = int(self.nights_var.get())
        except ValueError: nights = 1
            
        self.execute_command(OnityPMSClient.check_in, "🔔 LISTEN FOR BEEP! Tap card on reader to encode...", "Awaiting hardware write event...", self.get_selected_encoder_id(), room, self.op_var.get(), nights, auth_str)

    def do_checkout(self):
        self.execute_command(OnityPMSClient.check_out, "🌐 Processing database checkout... (No card needed)", "Sending network checkout command...", self.room_var.get())

    def do_reset(self):
        self.execute_command(OnityPMSClient.reset_encoder, "🌐 Resetting encoder... (No card needed)", "Sending network reset command...", self.get_selected_encoder_id())

if __name__ == "__main__":
    app = OnityApp()
    app.mainloop()