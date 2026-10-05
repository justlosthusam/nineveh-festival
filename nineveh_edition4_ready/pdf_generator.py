import os
import fitz # PyMuPDF
from io import BytesIO

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(PROJECT_DIR, "pdfs")
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

def create_booking_pdf(booking):
    ticket_id = booking.get("id", "NIFF2-000")
    pdf_filename = f"{ticket_id}.pdf"
    pdf_path = os.path.join(PDF_DIR, pdf_filename)

    doc = fitz.open()

    # PAGE 1: Master Summary & Overview Document
    page1 = doc.new_page(width=595, height=842)

    # 1. Header Banner
    page1.draw_rect(fitz.Rect(0, 0, 595, 120), color=(0.11, 0.02, 0.03), fill=(0.11, 0.02, 0.03))
    page1.draw_line(fitz.Point(0, 120), fitz.Point(595, 120), color=(0.77, 0.63, 0.35), width=3)

    emblem_path = os.path.join(PROJECT_DIR, "assets", "emblem.png")
    if os.path.exists(emblem_path):
        page1.insert_image(fitz.Rect(20, 15, 110, 105), filename=emblem_path)

    page1.insert_text(fitz.Point(135, 45), "NINEVEH INTERNATIONAL FILM FESTIVAL", fontsize=14, color=(0.77, 0.63, 0.35))
    page1.insert_text(fitz.Point(135, 68), "Mahragan Nineveh Al-Cinemai Al-Dawli - 2nd Edition", fontsize=11, color=(1, 1, 1))
    page1.insert_text(fitz.Point(135, 90), "MASTER REGISTRATION REPORT & SEATS APPROVAL DOCUMENT", fontsize=9, color=(0.8, 0.8, 0.8))

    page1.draw_rect(fitz.Rect(30, 140, 565, 185), color=(0.77, 0.63, 0.35), fill=(0.15, 0.04, 0.05))
    page1.insert_text(fitz.Point(45, 168), f"REGISTRATION ID: {ticket_id}  |  STATUS: PENDING ORGANIZER APPROVAL", fontsize=11, color=(1, 0.85, 0.4))

    y = 210
    page1.draw_rect(fitz.Rect(30, y, 565, y + 25), color=(0.77, 0.63, 0.35), fill=(0.77, 0.63, 0.35))
    page1.insert_text(fitz.Point(40, y + 17), "FIELD / PARAMETER", fontsize=10, color=(0, 0, 0))
    page1.insert_text(fitz.Point(220, y + 17), "DETAILS / VALUES", fontsize=10, color=(0, 0, 0))
    y += 25

    details = [
        ("Full Name (Primary)", booking.get("name", "")),
        ("Contact Phone", booking.get("phone", "")),
        ("Organizer", "Nineveh Film Festival Committee"),
        ("Category / Type", booking.get("category", "Festival Guest")),
        ("Organization / Media", booking.get("organization", "-") or "-"),
        ("Requested Seats Count", str(booking.get("personsCount", 1))),
        ("Assigned Seat Codes", ", ".join(booking.get("seatCodes", []))),
        ("Registration Timestamp", booking.get("createdAt", "")[:19].replace("T", " "))
    ]

    for label, val in details:
        page1.draw_rect(fitz.Rect(30, y, 200, y + 24), color=(0.3, 0.3, 0.3), fill=(0.95, 0.95, 0.95))
        page1.draw_rect(fitz.Rect(200, y, 565, y + 24), color=(0.3, 0.3, 0.3), fill=(1, 1, 1))
        page1.insert_text(fitz.Point(40, y + 16), label, fontsize=9, color=(0, 0, 0))
        page1.insert_text(fitz.Point(210, y + 16), str(val), fontsize=9, color=(0, 0, 0))
        y += 24

    attendees = booking.get("attendees", [])
    if not attendees:
        attendees = [{"name": booking.get("name"), "category": booking.get("category"), "seatCode": booking.get("seatCodes", ["-"])[0]}]

    # Table on Page 1
    y += 15
    page1.insert_text(fitz.Point(30, y), "ATTENDEES & SEAT MAPPING LIST:", fontsize=11, color=(0.11, 0.02, 0.03))
    y += 10
    page1.draw_rect(fitz.Rect(30, y, 565, y + 20), color=(0.2, 0.2, 0.2), fill=(0.2, 0.2, 0.2))
    page1.insert_text(fitz.Point(40, y + 14), "#", fontsize=9, color=(1, 1, 1))
    page1.insert_text(fitz.Point(70, y + 14), "Full Name", fontsize=9, color=(1, 1, 1))
    page1.insert_text(fitz.Point(320, y + 14), "Category", fontsize=9, color=(1, 1, 1))
    page1.insert_text(fitz.Point(470, y + 14), "Seat Code", fontsize=9, color=(1, 1, 1))
    y += 20

    for i, att in enumerate(attendees):
        page1.draw_rect(fitz.Rect(30, y, 565, y + 20), color=(0.8, 0.8, 0.8), fill=(0.97, 0.97, 0.97))
        page1.insert_text(fitz.Point(40, y + 14), str(i + 1), fontsize=9, color=(0, 0, 0))
        page1.insert_text(fitz.Point(70, y + 14), str(att.get("name", "")), fontsize=9, color=(0, 0, 0))
        page1.insert_text(fitz.Point(320, y + 14), str(att.get("category", "")), fontsize=9, color=(0, 0, 0))
        page1.insert_text(fitz.Point(470, y + 14), str(att.get("seatCode", "")), fontsize=9, color=(0.77, 0.63, 0.35))
        y += 20

    # Approval Action Box on Page 1
    y_qr = max(y + 20, 580)
    approve_url = f"http://localhost:8080/api/admin/approve-email?id={ticket_id}"
    page1.draw_rect(fitz.Rect(30, y_qr, 565, y_qr + 100), color=(0.77, 0.63, 0.35), fill=(0.98, 0.96, 0.90))
    page1.insert_text(fitz.Point(45, y_qr + 25), "ORGANIZER APPROVAL ACTION:", fontsize=11, color=(0.11, 0.02, 0.03))
    page1.insert_text(fitz.Point(45, y_qr + 45), "To approve this booking and permanently lock seats:", fontsize=9, color=(0.2, 0.2, 0.2))
    page1.insert_text(fitz.Point(45, y_qr + 65), approve_url, fontsize=9, color=(0.7, 0.1, 0.1))

    page1.draw_line(fitz.Point(30, 810), fitz.Point(565, 810), color=(0.77, 0.63, 0.35), width=1)
    page1.insert_text(fitz.Point(30, 825), "Nineveh International Film Festival 2nd Edition - Official System Document", fontsize=8, color=(0.5, 0.5, 0.5))

    # PAGES 2+: INDIVIDUAL TICKET CARDS FOR EVERY ATTENDEE SEPARATELY
    for idx, att in enumerate(attendees):
        page_att = doc.new_page(width=595, height=842)
        att_ticket_id = f"{ticket_id}-{idx+1}"
        
        # Header Banner
        page_att.draw_rect(fitz.Rect(0, 0, 595, 110), color=(0.11, 0.02, 0.03), fill=(0.11, 0.02, 0.03))
        page_att.draw_line(fitz.Point(0, 110), fitz.Point(595, 110), color=(0.77, 0.63, 0.35), width=3)
        
        if os.path.exists(emblem_path):
            page_att.insert_image(fitz.Rect(25, 15, 105, 95), filename=emblem_path)

        page_att.insert_text(fitz.Point(125, 45), "NINEVEH INTERNATIONAL FILM FESTIVAL", fontsize=13, color=(0.77, 0.63, 0.35))
        page_att.insert_text(fitz.Point(125, 65), "Mahragan Nineveh Al-Cinemai Al-Dawli - 2nd Edition", fontsize=10, color=(1, 1, 1))
        page_att.insert_text(fitz.Point(125, 85), f"INDIVIDUAL ATTENDEE TICKET #{idx+1} OF {len(attendees)}", fontsize=9, color=(0.8, 0.8, 0.8))

        # Ticket Body Box
        page_att.draw_rect(fitz.Rect(40, 140, 555, 650), color=(0.77, 0.63, 0.35), fill=(0.99, 0.99, 0.98))
        
        page_att.draw_rect(fitz.Rect(40, 140, 555, 180), color=(0.77, 0.63, 0.35), fill=(0.11, 0.02, 0.03))
        page_att.insert_text(fitz.Point(60, 165), f"TICKET ID: {att_ticket_id}", fontsize=12, color=(1, 0.85, 0.4))

        # Attendee Specific Data
        py = 210
        att_details = [
            ("Attendee Full Name", att.get("name", "")),
            ("Attendee Seat Code", att.get("seatCode", "")),
            ("Category", att.get("category", "Festival Guest")),
            ("Contact Phone", booking.get("phone", "")),
            ("Master Booking ID", ticket_id)
        ]

        for lbl, val in att_details:
            page_att.draw_rect(fitz.Rect(60, py, 210, py + 28), color=(0.8, 0.8, 0.8), fill=(0.92, 0.92, 0.92))
            page_att.draw_rect(fitz.Rect(210, py, 535, py + 28), color=(0.8, 0.8, 0.8), fill=(1, 1, 1))
            page_att.insert_text(fitz.Point(70, py + 18), lbl, fontsize=10, color=(0, 0, 0))
            page_att.insert_text(fitz.Point(220, py + 18), str(val), fontsize=10, color=(0, 0, 0))
            py += 28

        # Unique QR Code for this Attendee
        try:
            import qrcode
            qr_data = f"NIFF2|{att_ticket_id}|{att.get('name')}|{att.get('seatCode')}"
            qr_img = qrcode.make(qr_data)
            qr_stream = BytesIO()
            qr_img.save(qr_stream, format="PNG")
            page_att.insert_image(fitz.Rect(200, 390, 395, 585), stream=qr_stream.getvalue())
        except Exception:
            page_att.draw_rect(fitz.Rect(200, 390, 395, 585), color=(0.3, 0.3, 0.3), fill=(0.95, 0.95, 0.95))

        page_att.insert_text(fitz.Point(180, 610), "Scan QR / Barcode at Main Hall Gate for Entry", fontsize=9, color=(0.3, 0.3, 0.3))

        page_att.draw_line(fitz.Point(30, 810), fitz.Point(565, 810), color=(0.77, 0.63, 0.35), width=1)
        page_att.insert_text(fitz.Point(30, 825), "Nineveh International Film Festival 2nd Edition - Individual Pass", fontsize=8, color=(0.5, 0.5, 0.5))

    doc.save(pdf_path)
    doc.close()
    return pdf_path, pdf_filename
