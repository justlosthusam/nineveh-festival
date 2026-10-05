import os
import sys
import json
import http.server
import socketserver
import urllib.parse
from datetime import datetime
import threading, queue, time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import pdf_generator

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PORT = int(os.environ.get("PORT", "8080"))
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/") or f"http://localhost:{PORT}"
import secrets, hmac
_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_key.txt")
def _load_admin_key():
    k = os.environ.get("ADMIN_KEY", "").strip()
    if k:
        return k
    if os.path.exists(_KEY_FILE):
        return open(_KEY_FILE, encoding="utf-8").read().strip()
    k = secrets.token_urlsafe(12)
    with open(_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(k)
    return k
ADMIN_KEY = _load_admin_key()
def key_ok(k):
    return bool(k) and hmac.compare_digest(str(k), ADMIN_KEY)
STATIC_ALLOWED = ("/index.html", "/css/", "/js/", "/assets/", "/pdfs/", "/favicon.ico")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(PROJECT_DIR, "db.json")
ORGANIZER_EMAIL = "husamalsiayd@gmail.com"

# ===== تكوين البلوكات حسب الخريطة الرسمية =====
# القطاع A محجوز بالكامل (غير موجود). B و C: الصفوف 1-9 فقط (10-14 محذوفة).
THEATER_BLOCKS = [
    {"id": "B", "rows": [{"row": 1, "count": 10}, {"row": 2, "count": 11}, {"row": 3, "count": 11}, {"row": 4, "count": 12}, {"row": 5, "count": 12}, {"row": 6, "count": 13}, {"row": 7, "count": 13}, {"row": 8, "count": 14}, {"row": 9, "count": 14}]},
    {"id": "C", "rows": [{"row": 1, "count": 10}, {"row": 2, "count": 10}, {"row": 3, "count": 11}, {"row": 4, "count": 12}, {"row": 5, "count": 12}, {"row": 6, "count": 13}, {"row": 7, "count": 13}, {"row": 8, "count": 14}, {"row": 9, "count": 15}]},
    {"id": "D", "rows": [{"row": 1, "count": 13}, {"row": 2, "count": 13}, {"row": 3, "count": 13}, {"row": 4, "count": 13}, {"row": 5, "count": 13}, {"row": 6, "count": 13}, {"row": 7, "count": 13}, {"row": 8, "count": 13}, {"row": 9, "count": 13}]},
    {"id": "E", "rows": [{"row": 1, "count": 20}, {"row": 2, "count": 19}, {"row": 3, "count": 19}, {"row": 4, "count": 19}, {"row": 5, "count": 18}, {"row": 6, "count": 18}, {"row": 7, "count": 17}, {"row": 8, "count": 17}, {"row": 9, "count": 16}, {"row": 10, "count": 16}]},
    {"id": "F", "rows": [{"row": 1, "count": 13}, {"row": 2, "count": 13}, {"row": 3, "count": 13}, {"row": 4, "count": 13}, {"row": 5, "count": 13}, {"row": 6, "count": 13}, {"row": 7, "count": 13}, {"row": 8, "count": 13}, {"row": 9, "count": 13}]}
]
OUTDOOR_TOTAL = 4000  # 50 صف x 80 مقعد

# ===== بث مباشر للأدمن (SSE) =====
_subs = []
_subs_lock = threading.Lock()
def broadcast(event, payload=None):
    msg = json.dumps({"event": event, "data": payload or {}}, ensure_ascii=False)
    with _subs_lock:
        for q in list(_subs):
            try: q.put_nowait(msg)
            except Exception: pass

def apply_approve(db, ticket_id):
    bk = next((b for b in db["bookings"] if b["id"].upper() == ticket_id.upper()), None)
    if not bk: return None
    bk["status"] = "approved"
    for s_ in db["seats"]:
        if s_["code"] in bk.get("seatCodes", []):
            s_["status"] = "reserved"; s_["bookingId"] = bk["id"]
    return bk

def apply_reject(db, ticket_id):
    bk = next((b for b in db["bookings"] if b["id"].upper() == ticket_id.upper()), None)
    if not bk: return None
    bk["status"] = "rejected"
    for s_ in db["seats"]:
        if s_.get("bookingId") == bk["id"]:
            s_["status"] = "available"; s_["bookingId"] = None
    return bk

def init_db():
    if not os.path.exists(DB_FILE):
        seats = []
        seat_id_counter = 1
        for b in THEATER_BLOCKS:
            for r in b["rows"]:
                for s in range(1, r["count"] + 1):
                    seats.append({
                        "id": seat_id_counter,
                        "code": f"{b['id']}-{r['row']}-{s}",
                        "block": b["id"],
                        "row": r["row"],
                        "number": s,
                        "type": "theater",
                        "status": "available",
                        "bookingId": None
                    })
                    seat_id_counter += 1
        for i in range(1, OUTDOOR_TOTAL + 1):
            seats.append({
                "id": seat_id_counter,
                "code": f"\u0635\u064a\u0641\u064a-{i}",
                "block": "\u0635\u064a\u0641\u064a",
                "row": (i - 1) // 80 + 1,
                "number": i,
                "type": "outdoor",
                "status": "available",
                "bookingId": None
            })
            seat_id_counter += 1
        data = {
            "seats": seats,
            "bookings": [],
            "config": {
                "organizerEmail": ORGANIZER_EMAIL,
                "festivalName": "\u0645\u0647\u0631\u062c\u0627\u0646 \u0646\u064a\u0646\u0648\u0649 \u0627\u0644\u0633\u064a\u0646\u0645\u0627\u0626\u064a \u0627\u0644\u062f\u0648\u0644\u064a - \u0627\u0644\u062f\u0648\u0631\u0629 \u0627\u0644\u062b\u0627\u0646\u064a\u0629",
                "blockTotals": {"B": 110, "C": 110, "D": 117, "E": 179, "F": 117},
                "outdoorTotal": OUTDOOR_TOTAL
            }
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def load_db():
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Send Email Notification with PDF Attachment
def send_email_with_pdf(booking, pdf_path):
    try:
        ticket_id = booking.get("id", "NIFF2-000")
        name = booking.get("name", "")
        phone = booking.get("phone", "")
        seat_codes = ", ".join(booking.get("seatCodes", []))
        approve_url = f"{BASE_URL}/api/admin/approve-email?id={ticket_id}&key={urllib.parse.quote(ADMIN_KEY)}"
        pdf_url = f"{BASE_URL}/pdfs/{ticket_id}.pdf"

        subject = f"طلب موافقة حجز جديد [{ticket_id}] - {name} ({seat_codes})"
        
        body_html = f"""
        <div style="direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #120304; color: #ffffff; padding: 25px; border-radius: 16px;">
          <h2 style="color: #c5a059; margin-bottom: 5px;">مهرجان نينوى السينمائي الدولي - الدورة الثانية</h2>
          <p style="color: #e6d3a7; font-size: 14px;">طلب حجز جديد بانتظار إقرار موافقتك</p>
          <hr style="border-color: #c5a059; opacity: 0.3; margin: 15px 0;">
          
          <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(197,160,89,0.3);">
            <p><strong>رقم الحجز:</strong> <span style="color: #ffd700;">{ticket_id}</span></p>
            <p><strong>اسم طالب الحجز:</strong> {name}</p>
            <p><strong>رقم الهاتف:</strong> {phone}</p>
            <p><strong>الصفة / الجهة:</strong> {booking.get('category', 'مواطن')} ({booking.get('organization', '-') or '-'})</p>
            <p><strong>المقاعد المطلوبة:</strong> <strong style="color: #c5a059;">{seat_codes}</strong></p>
          </div>

          <p style="margin-top: 20px; font-size: 13px;">تم إرفاق ملف الـ PDF كاملاً ببيانات الحجز مع هذه الرسالة.</p>
          
          <div style="margin-top: 25px; text-align: center;">
            <a href="{approve_url}" style="background-color: #c5a059; color: #120304; padding: 12px 28px; font-weight: bold; text-decoration: none; border-radius: 10px; font-size: 14px; display: inline-block;">موافقة وإقرار تثبيت الحجز والمقاعد (Approve)</a>
          </div>
          <div style="margin-top: 15px; text-align: center;">
            <a href="{pdf_url}" target="_blank" style="color: #e6d3a7; font-size: 12px; text-decoration: underline;">تحميل وتنزيل ملف PDF الحجز</a>
          </div>
        </div>
        """

        msg = MIMEMultipart()
        msg['From'] = "niff-system@localhost"
        msg['To'] = ORGANIZER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=f"{ticket_id}.pdf")
                part['Content-Disposition'] = f'attachment; filename="{ticket_id}.pdf"'
                msg.attach(part)

        # Connect to local or standard SMTP server if configured
        try:
            with smtplib.SMTP('localhost', 25, timeout=2) as server:
                server.send_message(msg)
                print(f"[EMAIL] Successfully sent email with PDF to {ORGANIZER_EMAIL}")
        except Exception:
            print(f"[EMAIL SUMMARY] Email payload generated for {ORGANIZER_EMAIL} with PDF attached: {pdf_path}")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        path = parsed.path
        if path == "/":
            path = "/index.html"
        if not path.startswith(STATIC_ALLOWED):
            return os.path.join(PROJECT_DIR, "__blocked__")
        full = os.path.normpath(os.path.join(PROJECT_DIR, path.lstrip("/")))
        if not full.startswith(PROJECT_DIR):
            return os.path.join(PROJECT_DIR, "__blocked__")
        return full

    def _send_json(self, response_data, status=200):
        body = json.dumps(response_data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_content, status=200):
        body = html_content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/seats":
            db = load_db()
            self._send_json({"seats": db["seats"], "total": len(db["seats"])})
            return

        elif path == "/api/bookings":
            if not key_ok(query_params.get("key", [""])[0]):
                self._send_json({"error": "unauthorized"}, status=401)
                return
            db = load_db()
            self._send_json({"bookings": db.get("bookings", []), "total": len(db.get("bookings", []))})
            return

        elif path.startswith("/api/verify/"):
            ticket_id = path.replace("/api/verify/", "").strip()
            db = load_db()
            booking = next((b for b in db["bookings"] if b["id"].upper() == ticket_id.upper() or b["id"].upper() in ticket_id.upper()), None)
            
            if booking:
                is_approved = (booking.get("status") == "approved")
                self._send_json({
                    "valid": True,
                    "approved": is_approved,
                    "booking": booking
                })
            else:
                self._send_json({"valid": False, "message": "تذكرة غير صالحة أو غير موجودة في النظام"}, status=404)
            return

        # Serve generated PDF files directly
        elif path.startswith("/pdfs/"):
            pdf_name = os.path.basename(path)
            full_pdf_path = os.path.join(PROJECT_DIR, "pdfs", pdf_name)
            if os.path.exists(full_pdf_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'inline; filename="{pdf_name}"')
                with open(full_pdf_path, "rb") as f:
                    content = f.read()
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                return
            else:
                self._send_html("<h2>لم يتم العثور على ملف الـ PDF المطلوب</h2>", status=404)
                return

        elif path == "/api/admin/stream":
            if not key_ok(query_params.get("key", [""])[0]):
                self._send_json({"error": "unauthorized"}, status=401); return
            q = queue.Queue()
            with _subs_lock: _subs.append(q)
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache, no-transform")
                self.send_header("X-Accel-Buffering", "no")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                self.wfile.write(b"retry: 2000\n\n"); self.wfile.flush()
                while True:
                    try:
                        m = q.get(timeout=15)
                        self.wfile.write(("data: " + m + "\n\n").encode("utf-8"))
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
            except Exception:
                pass
            finally:
                with _subs_lock:
                    if q in _subs: _subs.remove(q)
            return

        elif path == "/admin":
            if not key_ok(query_params.get("key", [""])[0]):
                self._send_html(LOGIN_HTML, status=401); return
            with open(os.path.join(PROJECT_DIR, "admin.html"), "r", encoding="utf-8") as f:
                self._send_html(f.read()); return

        # (legacy server-rendered dashboard kept for old links)
        elif path == "/api/admin/dashboard":
            akey = query_params.get("key", [""])[0]
            if not key_ok(akey):
                self._send_html("""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>دخول الأدمن</title></head><body style="background:#120304;color:#fff;font-family:Tahoma,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0"><form method="get" action="/admin" style="background:#1e080a;border:1px solid #c5a059;border-radius:16px;padding:28px;width:300px;text-align:center"><h3 style="color:#c5a059;margin-top:0">لوحة الأدمن</h3><input name="key" type="password" placeholder="كلمة السر" style="width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:1px solid #c5a059;background:#000;color:#fff;margin-bottom:12px"><button style="width:100%;padding:10px;border:0;border-radius:8px;background:#c5a059;font-weight:bold">دخول</button></form></body></html>""", status=401)
                return
            kq = urllib.parse.quote(ADMIN_KEY)
            db = load_db()
            bookings = db.get("bookings", [])
            pending_count = len([b for b in bookings if b.get("status") == "pending_approval"])
            approved_count = len([b for b in bookings if b.get("status") == "approved"])

            rows_html = ""
            for b in reversed(bookings):
                status_badge = '<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-green-500/20 text-green-300 border border-green-500/40"> معتمد ومحجوز</span>' if b.get("status") == "approved" else '<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">⏳ بانتظار موافقتك</span>' if b.get("status") == "pending_approval" else '<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-red-500/20 text-red-300 border border-red-500/40">مرفوض</span>'
                
                approve_btn = f'<a href="/api/admin/approve-email?id={b["id"]}&key={kq}" class="px-3 py-1.5 bg-gold-matte text-black font-extrabold text-xs rounded-lg inline-block">موافقة</a> <a href="/api/admin/reject?id={b["id"]}&key={kq}" onclick="return confirm(&quot;رفض الطلب وتحرير المقاعد؟&quot;)" class="px-3 py-1.5 bg-red-700/40 text-red-200 border border-red-500/40 font-bold text-xs rounded-lg inline-block">رفض</a>' if b.get("status") == "pending_approval" else ('<span class="text-xs text-gray-400">تمت الموافقة</span>' if b.get("status") == "approved" else '<span class="text-xs text-red-300">مرفوض</span>')
                
                pdf_link = f'<a href="/pdfs/{b["id"]}.pdf" target="_blank" class="px-3 py-1.5 bg-red-600/30 text-red-300 border border-red-500/40 font-bold text-xs rounded-lg flex items-center gap-1"> ملف PDF الحجز</a>'
                
                rows_html += f"""
                <tr class="border-b border-yellow-700/20 hover:bg-white/5 text-xs">
                  <td class="p-3 font-mono font-bold text-yellow-300">{b['id']}</td>
                  <td class="p-3 font-bold text-white">{b['name']}</td>
                  <td class="p-3">{b['phone']}</td>
                  <td class="p-3">{b.get('category', 'مواطن')}</td>
                  <td class="p-3 font-bold text-gold-matte">{', '.join(b.get('seatCodes', []))}</td>
                  <td class="p-3">{status_badge}</td>
                  <td class="p-3 flex gap-2 justify-end">{pdf_link} {approve_btn}</td>
                </tr>
                """

            html_dash = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <meta http-equiv="refresh" content="20">
              <title>لوحة إدارة وموافقات PDF الإيميل | مهرجان نينوى السينمائي الدولي</title>
              <script src="https://cdn.tailwindcss.com"></script>
              <link rel="stylesheet" href="/css/style.css">
            </head>
            <body class="bg-black text-white p-4 md:p-8 min-h-screen">
              <div class="max-w-6xl mx-auto space-y-6">
                
                <div class="flex items-center justify-between border-b border-yellow-700/30 pb-4">
                  <div>
                    <h1 class="text-2xl font-bold text-gold-matte">لوحة إدارة وموافقات الحجوزات وملفات الـ PDF</h1>
                    <p class="text-xs text-gray-300">مهرجان نينوى السينمائي الدولي - الدورة الثانية (الإيميل المستهدف: husamalsiayd@gmail.com)</p>
                  </div>
                  <a href="/index.html" class="px-4 py-2 bg-white/10 text-xs rounded-xl font-bold hover:bg-white/20">← العودة للموقع</a>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                  <div class="glass-panel p-4 rounded-2xl border border-yellow-700/30">
                    <p class="text-xs text-gray-400">إجمالي طلبات الحجز</p>
                    <p class="text-2xl font-bold text-gold-matte">{len(bookings)}</p>
                  </div>
                  <div class="glass-panel p-4 rounded-2xl border border-amber-500/30">
                    <p class="text-xs text-amber-300">طلبات بانتظار موافقتك</p>
                    <p class="text-2xl font-bold text-amber-400">{pending_count}</p>
                  </div>
                  <div class="glass-panel p-4 rounded-2xl border border-green-500/30">
                    <p class="text-xs text-green-300">مقاعد معتمدة ومحجوزة</p>
                    <p class="text-2xl font-bold text-green-400">{approved_count}</p>
                  </div>
                </div>

                <div class="glass-panel rounded-2xl overflow-x-auto border border-yellow-700/30">
                  <table class="w-full text-right min-w-[700px]">
                    <thead>
                      <tr class="bg-black/60 text-yellow-300 border-b border-yellow-700/30 text-xs">
                        <th class="p-3">رقم الحجز</th>
                        <th class="p-3">اسم الطالب</th>
                        <th class="p-3">الهاتف</th>
                        <th class="p-3">الصفة</th>
                        <th class="p-3">المقاعد</th>
                        <th class="p-3">الحالة</th>
                        <th class="p-3 text-left">تقرير الـ PDF والإجراء</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows_html if rows_html else '<tr><td colspan="7" class="p-8 text-center text-gray-500">لا توجد طلبات حجز حالياً</td></tr>'}
                    </tbody>
                  </table>
                </div>

              </div>
            </body>
            </html>
            """
            self._send_html(html_dash)
            return

        # Instant Email/PDF Organizer Approval Endpoint
        elif path == "/api/admin/reject":
            if not key_ok(query_params.get("key", [""])[0]):
                self._send_html("<h2>غير مصرّح</h2>", status=401)
                return
            tid = query_params.get("id", [""])[0].strip()
            db = load_db()
            bk = next((b for b in db["bookings"] if b["id"].upper() == tid.upper()), None)
            if bk and bk.get("status") == "pending_approval":
                bk["status"] = "rejected"
                for s in db["seats"]:
                    if s.get("bookingId") == bk["id"]:
                        s["status"] = "available"
                        s["bookingId"] = None
                save_db(db)
                broadcast("update", {"id": bk["id"], "status": "rejected"})
            self.send_response(302)
            self.send_header("Location", "/admin?key=" + urllib.parse.quote(ADMIN_KEY))
            self.end_headers()
            return

        elif path == "/api/admin/approve-email":
            if not key_ok(query_params.get("key", [""])[0]):
                self._send_html("<h2>غير مصرّح</h2>", status=401)
                return
            ticket_id = query_params.get("id", [""])[0].strip()
            db = load_db()
            booking = next((b for b in db["bookings"] if b["id"].upper() == ticket_id.upper()), None)
            
            if booking:
                booking["status"] = "approved"
                for s in db["seats"]:
                    if s["code"] in booking.get("seatCodes", []):
                        s["status"] = "reserved"
                        s["bookingId"] = ticket_id

                save_db(db)
                broadcast("update", {"id": ticket_id, "status": "approved"})

                clean_phone = "".join(filter(str.isdigit, booking.get("phone", "")))
                if clean_phone.startswith("0"):
                    formatted_phone = "964" + clean_phone[1:]
                elif clean_phone.startswith("964"):
                    formatted_phone = clean_phone
                else:
                    formatted_phone = "964" + clean_phone

                host = self.headers.get("Host", "sociology-mutual-skirt-invitation.trycloudflare.com")
                scheme = "https" if ("trycloudflare.com" in host or "workers.dev" in host or "pages.dev" in host) else "http"
                server_origin = f"{scheme}://{host}"

                main_seat = (booking.get("seatCodes") or ["R1-S01"])[0]
                pdf_public_url = f"{server_origin}/pdfs/{booking['id']}.pdf"
                ticket_public_url = f"{server_origin}/?ticket={booking['id']}&name={urllib.parse.quote(booking['name'])}&seat={urllib.parse.quote(main_seat)}"
                wa_msg = f"أهلاً وسهلاً بك في مهرجان نينوى السينمائي الدولي (الدورة الثانية)! \nتمت موافقة وإقرار حجزكم وتأكيد المقاعد رسمياً \n\n رقم التذكرة: {booking['id']}\n اسم المسجل: {booking['name']}\n المقعد المخصص: {', '.join(booking.get('seatCodes', []))}\n\n رابط تنزيل ملف الـ PDF الرسمي بالتذكرة والباركود:\n{pdf_public_url}\n\n أو اضغط هنا لعرض التذكرة والباركود المعتمد:\n{ticket_public_url}"
                wa_send_url = f"https://api.whatsapp.com/send?phone={formatted_phone}&text={urllib.parse.quote(wa_msg)}"

                html_resp = f"""
                <!DOCTYPE html>
                <html lang="ar" dir="rtl">
                <head>
                  <meta charset="UTF-8">
                  <title>تمت الموافقة والإقرار | مهرجان نينوى السينمائي الدولي</title>
                  <script src="https://cdn.tailwindcss.com"></script>
                  <link rel="stylesheet" href="/css/style.css">
                </head>
                <body class="bg-black text-white flex items-center justify-center min-h-screen p-4 text-center">
                  <div class="glass-panel p-8 rounded-3xl border-2 border-yellow-500 max-w-md w-full space-y-4 shadow-2xl">
                    <div class="w-16 h-16 bg-yellow-500 text-black rounded-full flex items-center justify-center text-3xl font-black mx-auto"></div>
                    <h2 class="text-2xl font-bold text-gold-matte">تم إقرار الموافقة وتأكيد حجز المقاعد رسمياً</h2>
                    <p class="text-xs text-gray-300">تم تثبيت المقاعد رسمياً في النظام وتفعيل التذكرة والباركود للمسجل</p>
                    <div class="bg-white/5 p-4 rounded-xl text-right text-xs space-y-2 border border-yellow-500/20">
                      <p><span class="text-gray-400">رقم الحجز:</span> <strong class="text-yellow-300 font-mono">{booking['id']}</strong></p>
                      <p><span class="text-gray-400">اسم الطالب:</span> <strong class="text-white">{booking['name']}</strong></p>
                      <p><span class="text-gray-400">رقم الهاتف:</span> <strong class="text-white font-mono">{booking['phone']}</strong></p>
                      <p><span class="text-gray-400">المقاعد المعتمدة:</span> <strong class="text-yellow-300">{', '.join(booking['seatCodes'])}</strong></p>
                    </div>
                    <div class="pt-2 space-y-2">
                      <a href="{wa_send_url}" target="_blank" class="w-full py-3 bg-green-600 text-white font-extrabold text-xs rounded-xl flex items-center justify-center gap-2 shadow-lg hover:bg-green-500 transition-all">
                        <span> إرسال تذكرة والباركود فوراً إلى واتساب المسجل ({booking['phone']})</span>
                      </a>
                      <div class="flex justify-center gap-2">
                        <a href="/admin?key={urllib.parse.quote(ADMIN_KEY)}" class="w-1/2 py-2.5 bg-yellow-600/30 text-yellow-200 border border-yellow-500/40 font-bold rounded-xl text-xs">لوحة الحجوزات والـ PDF</a>
                        <a href="/pdfs/{booking['id']}.pdf" target="_blank" class="w-1/2 py-2.5 bg-red-600/30 text-red-300 border border-red-500/40 font-bold rounded-xl text-xs">عرض ملف الـ PDF</a>
                      </div>
                    </div>
                  </div>
                </body>
                </html>
                """
                self._send_html(html_resp)
            else:
                self._send_html("<h2>لم يتم العثور على الحجز</h2>", status=404)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        req_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(req_body)
        except Exception:
            data = {}

        if path == "/api/register":
            db = load_db()
            seat_codes = data.get("seatCodes", [])
            name = data.get("name", "").strip()
            phone = data.get("phone", "").strip()
            category = data.get("category", "مواطن").strip()
            org = data.get("organization", "").strip()
            persons_count = int(data.get("personsCount", len(seat_codes) or 1))
            attendees = data.get("attendees", [])

            if not name or not phone:
                self._send_json({"error": "يرجى كتابة الاسم الكامل ورقم الهاتف"}, status=400)
                return
            if not seat_codes:
                self._send_json({"error": "يرجى اختيار المقاعد من الخارطة"}, status=400)
                return

            target_seats = [s for s in db["seats"] if s["code"] in seat_codes]
            if len(target_seats) != len(set(seat_codes)):
                self._send_json({"error": "بعض المقاعد المختارة غير موجودة في الخريطة"}, status=400)
                return
            unavailable = [s["code"] for s in target_seats if s["status"] in ("reserved", "pending")]
            if unavailable:
                self._send_json({"error": f"المقاعد التالية محجوزة أو قيد المراجعة: {', '.join(unavailable)}"}, status=400)
                return

            ticket_id = f"NIFF2-{int(datetime.now().timestamp() * 1000):X}"
            booking = {
                "id": ticket_id,
                "name": name,
                "phone": phone,
                "category": category,
                "organization": org,
                "personsCount": persons_count,
                "seatCodes": seat_codes,
                "attendees": attendees,
                "status": "pending_approval",
                "createdAt": datetime.now().isoformat(),
                "qrCodeData": f"NIFF2|{ticket_id}|{name}|{category}|{','.join(seat_codes)}"
            }

            for s in db["seats"]:
                if s["code"] in seat_codes:
                    s["status"] = "pending"
                    s["bookingId"] = ticket_id

            db["bookings"].append(booking)
            save_db(db)

            broadcast("new_booking", {"id": ticket_id, "name": name, "phone": phone, "seats": seat_codes})

            # Generate PDF Registration Document
            pdf_path, pdf_filename = pdf_generator.create_booking_pdf(booking)

            # Dispatch Email to husamalsiayd@gmail.com
            send_email_with_pdf(booking, pdf_path)

            self._send_json({
                "success": True,
                "ticket": booking,
                "pdfUrl": f"/pdfs/{pdf_filename}",
                "message": f"تم تسجيل طلب الحجز بنجاح وتوليد ملف الـ PDF. إشعار الموافقة موجه إلى {ORGANIZER_EMAIL}"
            })
            return

        if path in ("/api/admin/approve", "/api/admin/reject"):
            if not key_ok(data.get("key", "")):
                self._send_json({"error": "unauthorized"}, status=401); return
            db = load_db()
            tid = str(data.get("id", "")).strip()
            bk = apply_approve(db, tid) if path.endswith("approve") else apply_reject(db, tid)
            if not bk:
                self._send_json({"error": "not found"}, status=404); return
            save_db(db)
            broadcast("update", {"id": bk["id"], "status": bk["status"]})
            self._send_json({"success": True, "booking": bk}); return

        self._send_json({"error": "Not Found"}, status=404)

LOGIN_HTML = """<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>دخول الأدمن</title></head><body style="background:#120304;color:#fff;font-family:Tahoma,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0"><form method="get" action="/admin" style="background:#1e080a;border:1px solid #c5a059;border-radius:16px;padding:28px;width:300px;text-align:center"><h3 style="color:#c5a059;margin-top:0">لوحة الأدمن</h3><input name="key" type="password" placeholder="كلمة السر" style="width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:1px solid #c5a059;background:#000;color:#fff;margin-bottom:12px"><button style="width:100%;padding:10px;border:0;border-radius:8px;background:#c5a059;font-weight:bold">دخول</button></form></body></html>"""

if __name__ == "__main__":
    init_db()
    os.chdir(PROJECT_DIR)
    print(f"[Nineveh Film Festival 2nd Edition] Server running at http://localhost:{PORT}")
    print(f"[ADMIN] http://localhost:{PORT}/admin?key={ADMIN_KEY}")
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    server = socketserver.ThreadingTCPServer(("0.0.0.0", PORT), CustomHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
