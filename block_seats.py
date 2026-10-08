#!/usr/bin/env python3
"""يحجز كل المقاعد الداخلية الفارغة + عدداً محدداً من المقاعد الخارجية باسم إدارة المهرجان.
المقاعد التي لها حجز فعلي (معلّق أو معتمد) لا تُمَس.
python block_seats.py [db.json] [--outdoor 200]"""
import json, sys, argparse
from datetime import datetime
ap = argparse.ArgumentParser(); ap.add_argument("db", nargs="?", default="db.json")
ap.add_argument("--outdoor", type=int, default=200); a = ap.parse_args()

d = json.load(open(a.db, encoding="utf-8"))
now = datetime.now().isoformat(timespec="seconds")
def block(bid, seats, label):
    if not seats: return 0
    for s in seats: s["status"] = "reserved"; s["bookingId"] = bid
    codes = [s["code"] for s in seats]
    d["bookings"] = [b for b in d["bookings"] if b["id"] != bid]
    d["bookings"].append({"id": bid, "name": "حجز إدارة المهرجان - " + label, "phone": "-",
        "category": "إدارة المهرجان", "organization": "إدارة المهرجان", "personsCount": len(codes),
        "seatCodes": codes, "attendees": [], "status": "approved", "createdAt": now,
        "qrCodeData": f"NIFF2|{bid}|إدارة المهرجان|{','.join(codes)}", "adminBlock": True})
    return len(codes)

free = lambda t: [s for s in d["seats"] if s["type"] == t and s["status"] == "available" and not s["bookingId"]]
n_in = block("NIFF2-ADMIN-INDOOR", free("theater"), "الصالة الداخلية")
out = sorted(free("outdoor"), key=lambda s: s["number"])[:a.outdoor]
n_out = block("NIFF2-ADMIN-OUTDOOR", out, "الصالة الصيفية")
json.dump(d, open(a.db, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"داخلي محجوز للإدارة: {n_in} | صيفي محجوز للإدارة: {n_out} ({out[0]['code']} … {out[-1]['code']})")
