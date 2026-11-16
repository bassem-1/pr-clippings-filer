#!/usr/bin/env python3
"""PR Clippings Filer. Run: python3 clippings_filer.py  ->  opens http://localhost:8000
Naming tokens: {date} {client} {note} {n}   (e.g. {date}_{client}_{note}_{n})
No installs needed (Python 3 standard library only)."""

import re, sys, glob, threading, shutil, tempfile, datetime, subprocess, webbrowser
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8000
DEFAULT_DEST = str(Path.home() / "Downloads")
DEFAULT_PATTERN = "{date}_{client}_{note}_{n}"
EMAIL_RE = re.compile(r"^[^@\s\"']+@[^@\s\"']+\.[A-Za-z]{2,}$")

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>PR Clippings Filer</title>
<style>
:root{--pink:#ff6fa5;--pink-dark:#e85690;--pink-bg:#ffe3ee;--ink:#3a2a33;--muted:#8a7680;--border:#f3c9dc}
*{box-sizing:border-box}
body{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;
  background:linear-gradient(160deg,#ffd9ea 0%,#ffeef5 55%,#fff5f9 100%);
  color:var(--ink);min-height:100vh;margin:0;padding:40px 16px;display:flex;justify-content:center}
.card{max-width:560px;width:100%;background:#fff;border-radius:18px;padding:32px 36px 36px;
  box-shadow:0 10px 30px rgba(216,90,140,.18),0 1px 3px rgba(216,90,140,.12)}
h2{margin:0 0 4px;font-size:24px;font-weight:700;color:var(--pink-dark);letter-spacing:.2px}
.sub{margin:0 0 22px;color:var(--muted);font-size:13.5px}
label{display:block;margin-top:16px;font-weight:600;font-size:13.5px;color:var(--ink)}
label.chk{font-weight:400;display:flex;align-items:center;gap:8px;margin-top:18px;font-size:14px}
label.chk input{width:16px;height:16px;accent-color:var(--pink)}
input[type=text]{width:100%;padding:10px 12px;margin-top:6px;border:1.5px solid var(--border);
  border-radius:10px;font-size:14px;background:#fffafc;transition:border-color .15s,box-shadow .15s}
input[type=text]:focus{outline:none;border-color:var(--pink);box-shadow:0 0 0 3px rgba(255,111,165,.18)}
input[type=file]{width:100%;margin-top:6px;padding:9px;border:1.5px dashed var(--border);
  border-radius:10px;font-size:13.5px;background:#fffafc}
.row{display:flex;gap:8px}.row input{flex:1}
small{display:block;margin-top:6px;color:var(--muted);font-size:12.5px}
#pv{color:var(--pink-dark);font-weight:600}
button{margin-top:6px;padding:9px 16px;border:1.5px solid var(--border);border-radius:10px;
  background:#fff;color:var(--ink);font-size:13.5px;font-weight:600;cursor:pointer;transition:all .15s}
button:hover{border-color:var(--pink);color:var(--pink-dark);background:#fff5f9}
#go{margin-top:26px;width:100%;padding:12px;font-size:15.5px;color:#fff;background:linear-gradient(135deg,var(--pink),var(--pink-dark));
  border:none;box-shadow:0 4px 12px rgba(232,86,144,.35)}
#go:hover{filter:brightness(1.06);box-shadow:0 6px 16px rgba(232,86,144,.45)}
#mail{margin-top:10px;width:100%;padding:11px;font-size:14.5px}
#quit{display:block;margin:18px auto 0;font-size:12.5px;font-weight:500;color:var(--muted)}
#out{margin-top:22px;white-space:pre-wrap;font-size:13px;color:var(--ink);background:#fff5f9;
  border:1px solid var(--border);border-radius:10px;padding:12px 14px;min-height:0}
#out:empty{display:none}
</style></head>
<body><div class="card">
<h2>📰 PR Clippings Filer</h2>
<p class="sub">Drop in your press &amp; social media clippings, name them consistently, file them by client, and send them on.</p>
<form id="f">
<label>Client *</label><input type="text" name="client" required>
<label>Note (optional)</label><input type="text" name="note" placeholder="e.g. Instagram, Press">
<label>Naming convention</label><input type="text" name="pattern" id="pattern">
<small>Tokens: {date} {client} {note} {n} &middot; preview: <span id="pv"></span></small>
<label>Destination folder</label>
<div class="row"><input type="text" name="dest" id="dest"><button type="button" id="browse">Browse…</button><button type="button" id="reset">Default</button></div>
<label class="chk"><input type="checkbox" name="subfolder" id="sub" checked> Create a subfolder named after the client</label>
<label>Clippings (screenshots, images or PDFs) *</label><input type="file" name="files" multiple required accept="image/*,application/pdf">
<button id="go">Rename &amp; save</button></form>
<label>Email the zipped folder to</label><input type="text" id="to" placeholder="name@example.com">
<button type="button" id="mail">✉️ Zip &amp; email folder</button>
<button type="button" id="quit">Quit PR Clippings Filer</button>
<div id="out"></div>
</div>
<script>
const D={pattern:"__PATTERN__",dest:"__DEST__"},$=id=>document.getElementById(id),f=$('f');
const get=k=>{try{return localStorage.getItem(k)}catch(e){return null}},set=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
$('pattern').value=get('pattern')||D.pattern;$('to').value=get('to')||'';$('to').oninput=()=>set('to',$('to').value.trim());$('dest').value=get('dest')||D.dest;$('sub').checked=get('sub')!=='0';
const pv=()=>{$('pv').textContent=$('pattern').value.replace('{date}',new Date().toISOString().slice(0,10)).replace('{client}',f.client.value||'Client')
 .replace('{note}',f.note.value||'').replace('{n}','01').replace(/[_\\- ]{2,}/g,'_').replace(/^[_\\- ]+|[_\\- ]+$/g,'')+'.png'};
['pattern','dest'].forEach(k=>$(k).oninput=()=>{set(k,$(k).value);pv()});f.client.oninput=f.note.oninput=pv;
$('sub').onchange=()=>set('sub',$('sub').checked?'1':'0');pv();
$('reset').onclick=()=>{$('dest').value=D.dest;set('dest',D.dest)};
$('browse').onclick=async()=>{const r=await fetch('/browse');const p=(await r.text()).trim();if(p){$('dest').value=p;set('dest',p)}};
f.onsubmit=async e=>{e.preventDefault();const fd=new FormData(f);
 for(const x of f.files.files) fd.append('dates',new Date(x.lastModified).toISOString().slice(0,10));
 $('out').textContent='Working...';const r=await fetch('/upload',{method:'POST',body:fd});
 $('out').textContent=await r.text();if(r.ok)f.files.value='';};
const target=()=>{let d=$('dest').value.replace(/\\/+$/,'');const c=f.client.value.trim();
 if($('sub').checked&&c)d+='/'+c.replace(/[^\\w\\- ]/g,'').trim().replace(/ /g,'-');return d};
$('quit').onclick=async()=>{await fetch('/quit',{method:'POST'}).catch(()=>{});
 document.querySelector('.card').innerHTML='<h2>PR Clippings Filer has quit</h2><p class="sub">You can close this tab. Double-click the app to open it again.</p>'};
$('mail').onclick=async()=>{const d=target(),to=$('to').value.trim();
 if(!/^[^@\\s]+@[^@\\s]+\\.[A-Za-z]{2,}$/.test(to)){$('out').textContent='Enter a valid email address to send to.';return}
 if(!confirm('Zip this folder and email it to '+to+'?\\n\\n'+d))return;
 const fd=new FormData();fd.append('folder',d);fd.append('to',to);$('out').textContent='Zipping & sending...';
 const r=await fetch('/email',{method:'POST',body:fd});$('out').textContent=await r.text();};
</script></body></html>"""

MAIL_SCRIPT = """on run argv
    set f to POSIX file (item 1 of argv) as alias
    tell application "Mail"
        set m to make new outgoing message with properties {subject:item 3 of argv, content:(item 4 of argv) & return & return, visible:false}
        tell m
            make new to recipient at end of to recipients with properties {address:item 2 of argv}
            tell content to make new attachment with properties {file name:f} at after last paragraph
        end tell
        delay 2
        send m
    end tell
end run"""

def clean(s):
    return re.sub(r"[^\w\- ]", "", s).strip().replace(" ", "-")

def pick_folder():
    try:
        if sys.platform == "darwin":
            r = subprocess.run(["osascript", "-e", 'POSIX path of (choose folder with prompt "Destination folder")'],
                               capture_output=True, text=True)
            return r.stdout.strip().rstrip("/")
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        p = filedialog.askdirectory(); root.destroy(); return p or ""
    except Exception:
        return ""

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        b = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path == "/browse":
            return self._send(200, pick_folder())
        page = PAGE.replace("__PATTERN__", DEFAULT_PATTERN).replace("__DEST__", DEFAULT_DEST.replace("\\", "/"))
        self._send(200, page, "text/html; charset=utf-8")

    def do_POST(self):
        if self.path == "/quit":
            self._send(200, "bye")
            return threading.Thread(target=self.server.shutdown, daemon=True).start()
        if self.path == "/email":
            return self.send_email()
        n = int(self.headers.get("Content-Length", 0))
        msg = BytesParser(policy=default).parsebytes(
            b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + self.rfile.read(n))
        fields, files, dates = {}, [], []
        for part in msg.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if part.get_filename():
                files.append((part.get_filename(), part.get_payload(decode=True)))
            elif name == "dates":
                dates.append(part.get_content().strip())
            else:
                fields[name] = part.get_content().strip()

        client = clean(fields.get("client", ""))
        if not client or not files:
            return self._send(400, "Need a client name and at least one file.")
        note = clean(fields.get("note", ""))
        pattern = fields.get("pattern") or DEFAULT_PATTERN
        if "{n}" not in pattern:
            pattern += "_{n}"
        folder = Path(fields.get("dest") or DEFAULT_DEST).expanduser()
        if "subfolder" in fields:
            folder = folder / client
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return self._send(400, f"Can't use folder {folder}: {e}")

        today = datetime.date.today().isoformat()
        done = []
        for i, (orig, data) in enumerate(files):
            date = dates[i] if i < len(dates) else today
            ext = Path(orig).suffix.lower() or ".png"
            k = 1
            while True:
                name = pattern.replace("{date}", date).replace("{client}", client) \
                              .replace("{note}", note).replace("{n}", f"{k:02d}")
                name = re.sub(r'[\\/:*?"<>|]', "", name)
                name = re.sub(r"[_\- ]{2,}", "_", name).strip("_- ")
                if not any(folder.glob(glob.escape(name) + ".*")):   # number across all file types
                    break
                k += 1
            (folder / f"{name}{ext}").write_bytes(data)
            done.append(f"{orig}  ->  {name}{ext}")
        self._send(200, f"Saved {len(done)} file(s) to {folder}\n\n" + "\n".join(done))

    def send_email(self):
        n = int(self.headers.get("Content-Length", 0))
        msg = BytesParser(policy=default).parsebytes(
            b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + self.rfile.read(n))
        fields = {p.get_param("name", header="content-disposition"): p.get_content().strip() for p in msg.iter_parts()}
        to = fields.get("to", "")
        if not EMAIL_RE.match(to):
            return self._send(400, "Enter a valid email address to send to.")
        folder = Path(fields.get("folder", "")).expanduser()
        if not fields.get("folder") or not folder.is_dir():
            return self._send(400, f"Folder not found: {folder}")
        if folder in (Path.home(), Path.home() / "Downloads", Path.home() / "Desktop"):
            return self._send(400, f"Refusing to zip all of {folder}. Tick the client subfolder option and enter a client.")
        if sys.platform != "darwin":
            return self._send(400, "Sending email needs macOS Mail.app.")
        out_dir = Path(tempfile.gettempdir()) / "pr_clippings_zips"
        out_dir.mkdir(exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        zip_path = Path(shutil.make_archive(str(out_dir / f"{folder.name}_{stamp}"), "zip", folder.parent, folder.name))
        size_mb = zip_path.stat().st_size / 1e6
        subject = f"Clippings - {folder.name}"
        body = f"Hello,\n\nPlease find attached the clippings for {folder.name}.\n\nBest regards"
        r = subprocess.run(["osascript", "-e", MAIL_SCRIPT, str(zip_path), to, subject, body],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return self._send(500, f"Mail.app couldn't send it: {r.stderr.strip()}\nZip is at {zip_path}")
        self._send(200, f"Sent {zip_path.name} ({size_mb:.1f} MB) to {to} via Mail.app.")

    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"Open http://localhost:{PORT}  (Ctrl+C to stop)")
    webbrowser.open(f"http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
