"""
OBS Recorder Tray  v3  --  aec_demo_master
======================================================================
ARCHITECTURE

  Claude's only job:
    Write  tools/current_stage.json  ->  {"project": "...", "phase": "..."}
    That is it. Claude does NOT call any OBS MCP tools for recording.

  Tray app owns ALL recording:
    - Right-click  -> pick source  -> recording starts immediately
    - Each source is bound to a specific OBS instance (port)
    - Simultaneous recordings across DIFFERENT ports are fully supported
    - Clicking a source on the SAME port as an active recording:
        auto-stop that clip, start new one  (one clip per OBS instance)
    - Clicking a source on a DIFFERENT port: starts alongside existing clip
    - Health check (videoActive via GetSourceActive) before every clip
    - Filename: NNN-phase_app   e.g.  003-site_prep_rhino

CONFIG  (obs_recorder_config.json)
    connections:  {port_str: {host, password, scene}}
    items:        {key: {source, port, label}}
    capture_root: folder override (blank = auto from project)

STAGE FILE  (tools/current_stage.json)
    { "project": "cliff_house_01", "phase": "site_prep" }

TRAY ICON STATES
    Dark grey  = idle / all stopped
    Red        = one or more recordings active
    Amber dot  = warning (source not active -- open app first)
======================================================================
"""
import pystray
from PIL import Image, ImageDraw
import json, threading, time, os, re, websocket, hashlib, base64

TOOLS_DIR   = os.path.dirname(os.path.abspath(__file__))
AEC_BASE    = os.path.normpath(os.path.join(TOOLS_DIR, ".."))
STAGE_FILE  = os.path.join(TOOLS_DIR, "current_stage.json")
CONFIG_FILE = os.path.join(TOOLS_DIR, "obs_recorder_config.json")

RESOLUTIONS = [
    (3200, 2000, "3200 x 2000  (native)"),
    (2560, 1600, "2560 x 1600"),
    (1920, 1200, "1920 x 1200"),
    (1600, 1000, "1600 x 1000"),
    (1280,  800, "1280 x 800"),
    (1064,  666, "1064 x 666"),
]

# ---- CONFIG ---------------------------------------------------------------
_CFG_DEFAULTS = {
    "connections": {
        "4455": {"host": "localhost", "password": "bigfish", "scene": "Claude-rhino_capture"},
        "4456": {"host": "localhost", "password": "bigfish", "scene": "Claude-rhino_capture"},
    },
    "items": {
        "claude":  {"source": "claude_window",  "port": 4455, "label": "Record Claude"},
        "rhino":   {"source": "Rhino_window",   "port": 4455, "label": "Record Rhino"},
        "blender": {"source": "blender_window", "port": 4456, "label": "Record Blender"},
        "display": {"source": "Display Capture","port": 4456, "label": "Record Display"},
    },
    "capture_root": "",
}

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        cfg = {**_CFG_DEFAULTS, **data}
        if "connections" not in cfg:
            cfg["connections"] = _CFG_DEFAULTS["connections"]
        # Migrate old flat items format {key: "source_name"} -> new format
        for k, v in cfg["items"].items():
            if isinstance(v, str):
                cfg["items"][k] = {"source": v, "port": 4455, "label": f"Record {k.title()}"}
        return cfg
    except Exception:
        with open(CONFIG_FILE, "w") as f:
            json.dump(_CFG_DEFAULTS, f, indent=2)
        return dict(_CFG_DEFAULTS)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

CFG = load_config()

# ---- STAGE FILE -----------------------------------------------------------
def read_stage():
    try:
        with open(STAGE_FILE) as f:
            s = json.load(f)
        return {
            "project": (s.get("project") or "unknown").strip(),
            "phase":   (s.get("phase")   or "session").strip(),
        }
    except Exception:
        return {"project": "unknown", "phase": "session"}

def get_capture_dir(stage):
    override = (CFG.get("capture_root") or "").strip()
    if override and os.path.isdir(override):
        return override
    proj = stage["project"]
    if proj and proj != "unknown":
        path = os.path.join(AEC_BASE, "aa_demo_versions", proj, "demo_captures")
    else:
        path = os.path.join(AEC_BASE, "demo_captures")
    os.makedirs(path, exist_ok=True)
    return path

_prefix = {"value": ""}   # user-set name prefix, e.g. "pool_deck"

def build_filename(phase, app_name, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    nums = []
    for f in os.listdir(dest_dir):
        m = re.match(r'^(\d{3})-', f)
        if m and f.lower().endswith((".mp4", ".mkv", ".mov")):
            nums.append(int(m.group(1)))
    seq   = max(nums, default=0) + 1
    clean = re.sub(r'[^a-z0-9]+', '_', phase.lower()).strip('_') or "session"
    prefix = re.sub(r'[^a-z0-9-]+', '-', _prefix["value"].lower()).strip('-')
    prefix_part = f"{prefix}_" if prefix else ""
    return f"{seq:03d}-{prefix_part}{clean}_{app_name}"

# ---- OBS CLIENT -----------------------------------------------------------
class OBSClient:
    def __init__(self, host, port, password, scene):
        self.host     = host
        self.port     = int(port)
        self.password = password
        self.scene    = scene
        self.ws       = None
        self._id      = 0
        self.ok       = False
        self.lock     = threading.Lock()

    def connect(self):
        try:
            ws = websocket.WebSocket()
            ws.settimeout(5)
            ws.connect(f"ws://{self.host}:{self.port}")
            hello   = json.loads(ws.recv())
            payload = {"op": 1, "d": {"rpcVersion": 1}}
            ai = hello.get("d", {}).get("authentication")
            if ai and self.password:
                s = base64.b64encode(
                    hashlib.sha256((self.password + ai["salt"]).encode()).digest()).decode()
                a = base64.b64encode(
                    hashlib.sha256((s + ai["challenge"]).encode()).digest()).decode()
                payload["d"]["authentication"] = a
            ws.send(json.dumps(payload))
            ws.recv()
            self.ws = ws
            self.ok = True
            print(f"[OBS:{self.port}] Connected")
        except Exception as e:
            self.ok = False
            print(f"[OBS:{self.port}] Connect failed: {e}")

    def req(self, type_, data=None):
        with self.lock:
            if not self.ok:
                self.connect()
            if not self.ok:
                return None
            self._id += 1
            try:
                self.ws.send(json.dumps({"op": 6, "d": {
                    "requestType": type_,
                    "requestId":   str(self._id),
                    "requestData": data or {},
                }}))
                return json.loads(self.ws.recv()).get("d", {}).get("responseData")
            except Exception as e:
                self.ok = False
                print(f"[OBS:{self.port}] req {type_} failed: {e}")
                return None

    def get_scene_items(self):
        r = self.req("GetSceneItemList", {"sceneName": self.scene})
        return r.get("sceneItems", []) if r else []

    def show_only(self, source_name):
        """Show source_name, hide everything else in the scene.
        No hardwired port->source mapping -- any source can go to any port."""
        items = self.get_scene_items()
        if not items:
            print(f"[OBS:{self.port}] WARN: show_only('{source_name}') -- scene empty")
            return
        for item in items:
            name = item["sourceName"]
            iid  = item["sceneItemId"]
            want = (name == source_name)
            r = self.req("SetSceneItemEnabled", {
                "sceneName":        self.scene,
                "sceneItemId":      iid,
                "sceneItemEnabled": want,
            })
            print(f"[OBS:{self.port}] show_only: '{name}' -> {want}  ok={r is not None}")

    def source_active(self, source_name):
        r = self.req("GetSourceActive", {"sourceName": source_name})
        if r is None:
            return False  # connection dead - don't silently record nothing
        return bool(r.get("videoActive", True))

    def is_recording(self):
        r = self.req("GetRecordStatus")
        return r.get("outputActive", False) if r else False

    def set_record_dir(self, path):
        os.makedirs(path, exist_ok=True)
        self.req("SetRecordDirectory", {"recordDirectory": path})

    def set_filename(self, name):
        self.req("SetProfileParameter", {
            "parameterCategory": "Output",
            "parameterName":     "FilenameFormatting",
            "parameterValue":    name,
        })

    def get_output_resolution(self):
        r = self.req("GetVideoSettings")
        return (r.get("outputWidth", 0), r.get("outputHeight", 0)) if r else (0, 0)

    def set_output_resolution(self, w, h):
        self.req("SetVideoSettings", {"outputWidth": w, "outputHeight": h})

    def start(self): self.req("StartRecord")
    def stop(self):  self.req("StopRecord")

# ---- OBS POOL -------------------------------------------------------------
_obs_pool = {}

def get_obs(port):
    port = int(port)
    if port not in _obs_pool:
        conn   = CFG["connections"].get(str(port), {})
        client = OBSClient(
            host     = conn.get("host",     "localhost"),
            port     = port,
            password = conn.get("password", ""),
            scene    = conn.get("scene",    "Claude-rhino_capture"),
        )
        _obs_pool[port] = client
        threading.Thread(target=client.connect, daemon=True).start()
    return _obs_pool[port]

# ---- RECORDING STATE ------------------------------------------------------
_recording = {}   # {port_int: {"active": bool, "source": str|None, "fname": str|None}}

def _rec_state(port):
    return _recording.get(int(port), {"active": False, "source": None, "fname": None})

def _set_rec(port, active, source=None, fname=None):
    _recording[int(port)] = {"active": active, "source": source, "fname": fname}

def _any_recording():
    return any(v["active"] for v in _recording.values())

def refresh_icon():
    set_icon("red" if _any_recording() else "dark")

# ---- RECORDING ACTIONS ----------------------------------------------------
def do_record(app_name, source_name, port):
    port = int(port)
    obs  = get_obs(port)

    if obs.is_recording():
        obs.stop()
        time.sleep(1.5)

    obs.show_only(source_name)
    time.sleep(0.3)

    if not obs.source_active(source_name):
        # videoActive=False can fire if the window handle is stale but OBS still
        # has the last frame.  Warn via tooltip but proceed with recording anyway.
        icon.title = (f"WARNING [{port}]: '{source_name}' handle stale -- "
                      "fix: OBS Sources -> Properties -> reselect window")
        print(f"[OBS:{port}] WARN: {source_name} videoActive=False, recording anyway")

    stage = read_stage()
    dest  = get_capture_dir(stage)
    fname = build_filename(stage["phase"], app_name, dest)

    obs.set_record_dir(dest)
    obs.set_filename(fname)
    time.sleep(0.15)
    obs.start()
    time.sleep(0.6)

    if not obs.is_recording():
        _set_rec(port, False)
        refresh_icon()
        icon.title = 'ERROR: StartRecord failed port ' + str(port)
        print('[OBS:' + str(port) + '] ERROR: did not start')
        return

    _set_rec(port, True, source_name, fname)
    refresh_icon()
    icon.title = f"REC [{port}]: {fname}"
    print(f"[OBS:{port}] Recording -> {dest}\\{fname}")

def do_stop_all():
    for port, client in list(_obs_pool.items()):
        # Always send StopRecord -- don't rely on is_recording() which can
        # false-negative after a WebSocket reconnect. OBS ignores stop if idle.
        client.stop()
        time.sleep(0.4)
        default_src = next(
            (v["source"] for v in CFG["items"].values()
             if int(v.get("port", 0)) == port),
            None
        )
        if default_src:
            client.show_only(default_src)
        _set_rec(port, False)
    refresh_icon()
    icon.title = "OBS Recorder -- stopped"
    print("[OBS] All stopped")

def open_captures():
    stage = read_stage()
    path  = get_capture_dir(stage)
    os.startfile(path)

def run_bg(fn, *a):
    threading.Thread(target=fn, args=a, daemon=True).start()

# ---- PREFIX DIALOG --------------------------------------------------------
def set_prefix():
    import tkinter as tk
    root = tk.Tk()
    root.title("Set name prefix")
    root.resizable(False, False)
    root.configure(bg="#1e1e1e")
    root.attributes("-topmost", True)

    BG, FG = "#1e1e1e", "#e0e0e0"
    FONT   = ("Segoe UI", 10)
    BOLD   = ("Segoe UI", 10, "bold")

    tk.Label(root, text="Clip name prefix  (e.g. pool-deck, angle-wide — blank to clear)",
             bg=BG, fg="#888", font=FONT).pack(padx=16, pady=(14, 4), anchor="w")

    var = tk.StringVar(value=_prefix["value"])
    entry = tk.Entry(root, textvariable=var, width=32,
                     bg="#2d2d2d", fg=FG, insertbackground=FG,
                     relief="flat", font=FONT, bd=6)
    entry.pack(padx=16, pady=4)
    entry.focus_set()
    entry.select_range(0, tk.END)

    def on_ok(*_):
        _prefix["value"] = var.get().strip()
        p = _prefix["value"]
        icon.title = f"Prefix: {p}" if p else "OBS Recorder -- no prefix"
        root.destroy()

    entry.bind("<Return>", on_ok)
    tk.Button(root, text="OK", command=on_ok,
              bg="#0078d4", fg="#fff", relief="flat",
              font=BOLD, padx=16).pack(pady=(4, 14))
    root.mainloop()

# ---- SETTINGS DIALOG ------------------------------------------------------
def open_settings():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.title("OBS Recorder -- Settings")
    root.resizable(False, False)
    root.configure(bg="#1e1e1e")

    BG, FG   = "#1e1e1e", "#e0e0e0"
    CODE_BG  = "#151515"
    ENTRY_BG = "#2d2d2d"
    ACC      = "#0078d4"
    FONT     = ("Segoe UI", 10)
    BOLD     = ("Segoe UI", 10, "bold")
    MONO     = ("Consolas", 10)

    def section_label(text, r):
        tk.Label(root, text=text, bg=BG, fg="#888",
                 font=BOLD, anchor="w").grid(
                 row=r, column=0, columnspan=3,
                 padx=16, pady=(14, 2), sticky="w")

    def code_label(text, r):
        tk.Label(root, text=text, bg=CODE_BG, fg="#4ec94e",
                 font=MONO, anchor="w", padx=10, pady=6).grid(
                 row=r, column=0, columnspan=3,
                 padx=16, sticky="ew")

    row = 0

    section_label("Current stage  (written by Claude -- read-only here)", row); row += 1
    stage = read_stage()
    code_label(f'  project: {stage["project"]}     phase: {stage["phase"]}', row); row += 1

    section_label("Output resolution  (per OBS instance)", row); row += 1
    res_vars = {}
    for port_str in sorted(CFG["connections"]):
        client = get_obs(int(port_str))
        cur_w, cur_h = client.get_output_resolution()
        status = f"{cur_w} x {cur_h}" if cur_w else "not connected"
        pf = tk.Frame(root, bg=BG)
        pf.grid(row=row, column=0, columnspan=3, padx=16, pady=2, sticky="ew")
        tk.Label(pf, text=f":{port_str}", bg=CODE_BG, fg="#4ec94e",
                 font=MONO, width=6, anchor="w", padx=6, pady=3).pack(side="left")
        tk.Label(pf, text=f"  {status}", bg=BG, fg="#666", font=FONT).pack(side="left", padx=8)
        res_labels = [r[2] for r in RESOLUTIONS]
        rv = tk.StringVar(value=next(
            (r[2] for r in RESOLUTIONS if r[0] == cur_w and r[1] == cur_h), res_labels[0]))
        res_vars[port_str] = (rv, cur_w, cur_h)
        om = tk.OptionMenu(pf, rv, *res_labels)
        om.config(bg=ENTRY_BG, fg=FG, activebackground="#3a3a3a", activeforeground=FG,
                  relief="flat", highlightthickness=0, font=FONT, width=22)
        om["menu"].config(bg=ENTRY_BG, fg=FG, font=FONT)
        om.pack(side="left", padx=(8, 0))
        row += 1

    section_label("Capture folder  (blank = auto from project)", row); row += 1
    path_var = tk.StringVar(value=CFG.get("capture_root", ""))
    tk.Entry(root, textvariable=path_var, width=46,
             bg=ENTRY_BG, fg=FG, insertbackground=FG,
             relief="flat", font=FONT, bd=4).grid(
             row=row, column=0, columnspan=2, padx=(16, 4), pady=2, sticky="ew")

    def browse():
        d = filedialog.askdirectory(title="Capture folder",
                                    initialdir=path_var.get() or AEC_BASE)
        if d:
            path_var.set(d)
            update_preview()

    tk.Button(root, text="Browse...", command=browse,
              bg="#333", fg=FG, relief="flat", font=FONT,
              padx=10).grid(row=row, column=2, padx=(0, 16), pady=2)
    row += 1

    section_label("Next filename preview", row); row += 1
    preview_var = tk.StringVar()
    tk.Label(root, textvariable=preview_var, bg=CODE_BG, fg="#4ec94e",
             font=MONO, anchor="w", padx=10, pady=6).grid(
             row=row, column=0, columnspan=3, padx=16, sticky="ew")
    row += 1

    def update_preview(*_):
        dest  = path_var.get().strip() or get_capture_dir(read_stage())
        fname = build_filename(read_stage()["phase"], "rhino", dest)
        preview_var.set(f"  {fname}.mp4")

    update_preview()
    path_var.trace_add("write", update_preview)

    section_label("Sources", row); row += 1
    hdr = tk.Frame(root, bg=BG)
    hdr.grid(row=row, column=0, columnspan=3, padx=16, sticky="ew")
    for text, w in [("Key", 10), ("Port", 6), ("OBS Source Name", 20), ("Menu Label", 16)]:
        tk.Label(hdr, text=text, bg=BG, fg="#666", font=FONT,
                 width=w, anchor="w").pack(side="left", padx=(0 if text == "Key" else 4, 0))
    row += 1

    # ---- dynamic rows ----
    rows_frame = tk.Frame(root, bg=BG)
    rows_frame.grid(row=row, column=0, columnspan=3, padx=16, sticky="ew")
    row += 1

    item_rows = []   # list of dicts: {key_var, src_var, port_var, lbl_var, frame}

    def make_item_row(key="", src="", port="4446", lbl=""):
        rf = tk.Frame(rows_frame, bg=BG)
        rf.pack(fill="x", pady=2)
        key_var = tk.StringVar(value=key)
        src_var = tk.StringVar(value=src)
        port_var = tk.StringVar(value=str(port))
        lbl_var = tk.StringVar(value=lbl)
        tk.Entry(rf, textvariable=key_var, width=10,
                 bg=CODE_BG, fg="#4ec94e", insertbackground="#4ec94e",
                 relief="flat", font=MONO, bd=3).pack(side="left")
        tk.Entry(rf, textvariable=port_var, width=6,
                 bg=ENTRY_BG, fg=FG, insertbackground=FG,
                 relief="flat", font=MONO, bd=3).pack(side="left", padx=(4, 0))
        tk.Entry(rf, textvariable=src_var, width=20,
                 bg=ENTRY_BG, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT, bd=3).pack(side="left", padx=(4, 0))
        tk.Entry(rf, textvariable=lbl_var, width=16,
                 bg=ENTRY_BG, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT, bd=3).pack(side="left", padx=(4, 0))
        entry = {"key_var": key_var, "src_var": src_var,
                 "port_var": port_var, "lbl_var": lbl_var, "frame": rf}
        def remove_row(e=entry):
            e["frame"].destroy()
            item_rows.remove(e)
        tk.Button(rf, text="x", command=remove_row,
                  bg="#5a1a1a", fg="#ff8080", relief="flat",
                  font=FONT, padx=6).pack(side="left", padx=(4, 0))
        item_rows.append(entry)

    for key, item_cfg in CFG["items"].items():
        make_item_row(
            key=key,
            src=item_cfg.get("source", ""),
            port=str(item_cfg.get("port", 4446)),
            lbl=item_cfg.get("label", f"Record {key.title()}")
        )

    add_btn_frame = tk.Frame(root, bg=BG)
    add_btn_frame.grid(row=row, column=0, columnspan=3, padx=16, pady=(4,0), sticky="w")
    row += 1
    tk.Button(add_btn_frame, text="+ Add source", command=make_item_row,
              bg="#1a3a1a", fg="#4ec94e", relief="flat",
              font=FONT, padx=10).pack(side="left")
    source_vars = item_rows  # alias so on_save works

    def on_save():
        for port_str, (rv, cur_w, cur_h) in res_vars.items():
            sel = next((r for r in RESOLUTIONS if r[2] == rv.get()), None)
            if sel and (sel[0], sel[1]) != (cur_w, cur_h):
                get_obs(int(port_str)).set_output_resolution(sel[0], sel[1])
                print(f"[OBS:{port_str}] Resolution -> {sel[0]}x{sel[1]}")
        new_items = {}
        for entry in item_rows:
            k   = entry["key_var"].get().strip()
            src = entry["src_var"].get().strip()
            prt = entry["port_var"].get().strip()
            lbl = entry["lbl_var"].get().strip()
            if k and src:
                try: port_int = int(prt)
                except ValueError: port_int = 4446
                new_items[k] = {"source": src, "port": port_int,
                                 "label": lbl or f"Record {k.title()}"}
        CFG["items"] = new_items
        CFG["capture_root"] = path_var.get().strip()
        save_config(CFG)
        root.destroy()

    bf = tk.Frame(root, bg=BG)
    bf.grid(row=row, column=0, columnspan=3, padx=16, pady=(14, 16), sticky="e")
    tk.Button(bf, text="Cancel", command=root.destroy,
              bg="#333", fg=FG, relief="flat", font=FONT,
              padx=14).pack(side="right", padx=(6, 0))
    tk.Button(bf, text="Save", command=on_save,
              bg=ACC, fg="#fff", relief="flat", font=BOLD,
              padx=14).pack(side="right")

    root.columnconfigure(0, weight=1)
    root.mainloop()

# ---- TRAY ICON ------------------------------------------------------------
def make_icon(fill, dot_color=None):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.ellipse([2, 2, 62, 62],   fill=fill, outline="#ffffff", width=3)
    d.ellipse([22, 22, 42, 42], fill="#ffffff")
    if dot_color:
        d.ellipse([42, 4, 60, 22], fill=dot_color, outline="#1e1e1e", width=2)
    return img

ICONS = {
    "dark":  make_icon("#2c2c2c"),
    "red":   make_icon("#c0392b"),
    "amber": make_icon("#2c2c2c", dot_color="#e67e22"),
}

def set_icon(state):
    icon.icon = ICONS.get(state, ICONS["dark"])

def _record_cb(k, s, p):
    """Return a zero-arg callback for pystray (rejects callables with >2 params)."""
    return lambda: run_bg(do_record, k, s, p)

def build_menu():
    entries = []
    for key, item_cfg in CFG["items"].items():
        source_name = item_cfg["source"]
        port        = int(item_cfg["port"])
        label       = item_cfg.get("label", f"Record {key.title()}")
        state       = _rec_state(port)
        display = ("\u25cf  " + label) if (state["active"] and state["source"] == source_name) else label
        entries.append(pystray.MenuItem(
            display,
            _record_cb(key, source_name, port)
        ))
    entries += [
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Stop All",        lambda: run_bg(do_stop_all)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Set prefix...",   lambda: run_bg(set_prefix)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Folder",     lambda: run_bg(open_captures)),
        pystray.MenuItem("Settings...",     lambda: run_bg(open_settings)),
    ]
    return entries

def _startup_connect():
    for port_str in CFG["connections"]:
        get_obs(int(port_str))

icon = pystray.Icon("OBS Recorder", ICONS["dark"], "OBS Recorder", pystray.Menu(build_menu))
threading.Thread(target=_startup_connect, daemon=True).start()
icon.run()
