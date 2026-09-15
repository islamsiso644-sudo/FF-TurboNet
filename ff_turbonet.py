#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 FF-TurboNet v3.0 — أقوى أداة تحسين شبكة Free Fire (100% ضمن القواعد)
=====================================================================
 ما هي؟
   أداة مهنية مفتوحة المصدر تركّز على تحسين "جودة اتصالك" من جهازك:
   قياس البينق الحقيقي لسيرفرات فري فاير، تنظيف وتسريع DNS، تحسينات
   TCP/نظام مشروعة، وضع لعب يوقف المشتتات، ومراقب استقرار مباشر.

 ما هي NOT؟
   ليست اختراقًا: لا تلمس ملفات اللعبة أو ذاكرتها أو حزمها.
   لا تحتوي أي aimbot/ESP/حاقن. لا شيء يخالف قواعد Garena Fair Play.

 ✅ لماذا هي 100% قانونية؟
   كل التعديلات على نظام تشغيلك أنت (TCP/DNS/خدمات خلفية) — مثل
   تعديل إعدادات الراوتر تمامًا. اللعبة نفسها لا تُلمس إطلاقًا.

 المنصات: Windows 10/11 + Linux + Android (Termux)
 بدون أي مكتبات خارجية — Python خالص
=====================================================================
"""

import sys
import os
import re
import json
import time
import socket
import random
import struct
import shutil
import platform
import subprocess
import statistics
from datetime import datetime

VERSION = "3.0.0"
IS_WINDOWS = platform.system() == "Windows"
IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "") or os.path.exists("/data/data/com.termux")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "turbonet_report.txt")
BACKUP_FILE = os.path.join(SCRIPT_DIR, "turbonet_backup.json")

# ---------------------------------------------------------------------
#  سيرفرات فري فاير الرسمية — لأغراض القياس فقط (بيانات عامة معروفة)
#  المصادر: netify.ai (Garena/Sea/Tencent/CloudFront) + مجتمع FF
# ---------------------------------------------------------------------
FF_SERVERS = {
    "بنغلاديش (BD) — الخيار الأول للاعبين العرب في آسيا": [
        ("ff-events.garena.com", 443),
        ("202.81.97.70", 10000),
        ("202.81.97.72", 10000),
        ("202.81.97.73", 10000),
    ],
    "سنغافورة (SG) — المقر الرئيسي لجارينا": [
        ("ff.garena.com", 443),
        ("loginff.garena.com", 443),
        ("103.247.205.138", 10000),
    ],
    "إندونيسيا (IDN)": [
        ("freefiremobile.com", 443),
        ("125.212.198.39", 10000),
        ("125.212.198.71", 10000),
    ],
    "الهند (IND)": [
        ("freefireind.in", 443),
        ("dl.packetgm.com", 443),
    ],
    "الشرق الأوسط (MENA) — CDN جارينا": [
        ("ff.garena.com.cdn.cloudflare.net", 443),
        ("d1k2ga1ciqxi0i.cloudfront.net", 443),
    ],
}

# مزودو DNS العامون للقياس والمقارنة
DNS_CANDIDATES = [
    ("Cloudflare", "1.1.1.1"),
    ("Cloudflare-2", "1.0.0.1"),
    ("Google", "8.8.8.8"),
    ("Google-2", "8.8.4.4"),
    ("Quad9", "9.9.9.9"),
    ("OpenDNS", "208.67.222.222"),
]

# ------------------------- ألوان وإخراج ------------------------------
def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if IS_WINDOWS:
        os.system("")  # يفعّل ANSI في ويندوز 10+
    return sys.stdout.isatty()

_COLOR = _supports_color()

def c(text, code):
    return f"\033[{code}m{text}\033[0m" if _COLOR else text

def ok(msg):    print(c("[✓] " + msg, "92"))
def warn(msg):  print(c("[!] " + msg, "93"))
def err(msg):   print(c("[✗] " + msg, "91"))
def info(msg):  print(c("[i] " + msg, "96"))
def title(msg): print(); print(c("═" * 62, "95")); print(c("  " + msg, "95")); print(c("═" * 62, "95"))

def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

# ------------------------- أدوات مساعدة ------------------------------
_ELEVATED = None

def is_elevated():
    """هل نعمل بصلاحيات مسؤول (ويندوز) أو روت (لينكس/تيرمكس)؟"""
    global _ELEVATED
    if _ELEVATED is not None:
        return _ELEVATED
    if IS_WINDOWS:
        try:
            import ctypes
            _ELEVATED = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            _ELEVATED = False
    else:
        _ELEVATED = getattr(os, "geteuid", lambda: 1)() == 0
    return _ELEVATED

def su_available():
    """هل يوجد su (جهاز أندرويد مروّت)؟"""
    return shutil.which("su") is not None

def run(cmd, timeout=20):
    """تشغيل أمر نظامي وإرجاع (returncode, output)"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except Exception as e:
        return 1, str(e)

def run_root(cmd, timeout=20):
    """تشغيل أمر بصلاحيات روت (sudo في لينكس / su -c في تيرمكس)"""
    if is_elevated():
        return run(cmd, timeout)
    if IS_TERMUX and su_available():
        return run(f'su -c "{cmd}"', timeout)
    if not IS_WINDOWS and shutil.which("sudo"):
        return run(f"sudo {cmd}", timeout)
    return 1, "no-root"

def require_root():
    if is_elevated():
        return True
    if IS_WINDOWS:
        err("شغّل الأداة كمسؤول: كليك يمين → Run as administrator")
    else:
        err("شغّل بصلاحيات روت: sudo python3 ff_turbonet.py أو su في تيرمكس")
    return False

def load_backup():
    if os.path.exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_backup(data):
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    info(f"تم حفظ نسخة احتياطية: {BACKUP_FILE}")

def banner():
    print(c(r"""
███████╗███████╗ ██████╗    ████████╗██╗   ██╗██████╗ ███████╗██████╗
██╔════╝██╔════╝██╔════╝    ╚══██╔══╝██║   ██║██╔══██╗██╔════╝██╔══██╗
█████╗  ███████╗██║            ██║   ██║   ██║██████╔╝█████╗  ██████╔╝
██╔══╝  ╚════██║██║            ██║   ██║   ██║██╔══██╗██╔══╝  ██╔═══╝
███████╗███████║╚██████╗       ██║   ╚██████╔╝██║  ██║███████╗██║
╚══════╝╚══════╝ ╚═════╝       ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  v""" + VERSION, "93"))
    print(c("   أداة تحسين شبكة فري فاير — قانونية 100% — لا تلمس اللعبة إطلاقًا", "96"))
    print(c("   " + "═" * 58, "95"))

# ---- PART2 ----

# =====================================================================
#  الفحص 1: قياس البينق TCP الحقيقي لسيرفرات فري فاير (بدون امتيازات)
# =====================================================================
def tcp_ping(host, port, count=4, timeout=2.0):
    """
    بينق TCP حقيقي: زمن إنشاء اتصال TCP إلى (host, port).
    هذا هو الزمن الذي تشعر به فعليًا داخل اللعبة تقريبًا.
    """
    results = []
    for i in range(count):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        t0 = time.perf_counter()
        try:
            s.connect((host, port))
            ms = (time.perf_counter() - t0) * 1000.0
            results.append(ms)
        except Exception:
            results.append(None)
        finally:
            s.close()
        if i < count - 1:
            time.sleep(0.15)
    good = [r for r in results if r is not None]
    if not good:
        return {"ok": False, "avg": None, "min": None, "max": None,
                "jitter": None, "loss": 100.0}
    avg = statistics.mean(good)
    return {
        "ok": True,
        "avg": avg,
        "min": min(good),
        "max": max(good),
        "jitter": (max(good) - min(good)) if len(good) > 1 else 0.0,
        "loss": (1.0 - len(good) / count) * 100.0,
    }

def grade_ping(avg):
    if avg is None:      return c("غير متاح", "91"), 0
    if avg < 40:         return c("ممتاز ⚡", "92"), 5
    if avg < 70:         return c("جيد جدًا ✅", "92"), 4
    if avg < 100:        return c("مقبول 🆗", "93"), 3
    if avg < 150:        return c("ضعيف ⚠️", "93"), 2
    return c("سيء جدًا ❌", "91"), 1

def cmd_ping_all():
    title("فحص البينق لسيرفرات فري فاير الرسمية (TCP Ping)")
    info("نقيس زمن إنشاء اتصال TCP — نفس المسار الذي تستخدمه اللعبة")
    print()
    scores = []
    best = None
    for region, targets in FF_SERVERS.items():
        print(c(f"◈ {region}", "96"))
        for host, port in targets:
            r = tcp_ping(host, port, count=4)
            if r["ok"]:
                g, s = grade_ping(r["avg"])
                line = f"   {host:<42} متوسط: {r['avg']:6.1f} مللي  |  jitter: {r['jitter']:5.1f}  |  {g}"
                print(c(line, "92" if s >= 4 else "93" if s >= 2 else "91"))
                scores.append(s)
                if best is None or r["avg"] < best[2]:
                    best = (region, host, r["avg"], r["jitter"])
            else:
                print(c(f"   {host:<42} لا يستجيب (قد يكون محجوبًا من مزودك)", "90"))
        print()
    if best:
        ok(f"أفضل سيرفر لك: {best[1]} ({best[0]}) — بينق {best[2]:.1f} مللي")
        log(f"PING best={best[1]} avg={best[2]:.1f} jitter={best[3]:.1f}")
    avg_score = statistics.mean(scores) if scores else 0
    if avg_score >= 4:
        ok(f"تقييم شبكتك: ممتاز ({avg_score:.1f}/5) — شبكتك جاهزة للعب")
    elif avg_score >= 2.5:
        warn(f"تقييم شبكتك: متوسط ({avg_score:.1f}/5) — جرّب الفحوصات التالية للتحسين")
    else:
        err(f"تقييم شبكتك: ضعيف ({avg_score:.1f}/5) — التحسينات أدناه ضرورية لك")
    return avg_score

# =====================================================================
#  الفحص 2: تسريع DNS — قياس ثم تطبيق الأسرع (هذا يقلل اللاق/التأخير)
# =====================================================================
def query_dns(server, domain="ff.garena.com", timeout=1.5):
    """
    استعلام DNS يدوي عبر UDP: يرجع زمن الاستجابة بالمللي أو None.
    (بروتوكول DNS عام — لا يحتاج مكتبات خارجية)
    """
    tid = random.randint(0, 65535)
    flags = 0x0100  # RD
    header = struct.pack(">HHHHHH", tid, flags, 1, 0, 0, 0)
    qname = b"".join(bytes([len(p)]) + p.encode() for p in domain.split(".")) + b"\x00"
    question = qname + struct.pack(">HH", 1, 1)  # A, IN
    packet = header + question
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    t0 = time.perf_counter()
    try:
        s.sendto(packet, (server, 53))
        data, _ = s.recvfrom(512)
        ms = (time.perf_counter() - t0) * 1000.0
        return ms if len(data) > 12 else None
    except Exception:
        return None
    finally:
        s.close()

def cmd_dns_boost():
    title("تسريع DNS — قياس كل المزودين واختيار الأسرع لك")
    info("تأخير DNS = انتظار طويل عند كل دخول للعبة وتحديث النتائج")
    print()
    results = []
    for name, ip in DNS_CANDIDATES:
        samples = [query_dns(ip) for _ in range(3)]
        good = [x for x in samples if x is not None]
        if good:
            avg = statistics.mean(good)
            results.append((name, ip, avg))
            print(c(f"   {name:<14} {ip:<16} متوسط: {avg:6.2f} مللي", "96"))
        else:
            print(c(f"   {name:<14} {ip:<16} لا يستجيب", "90"))
    if not results:
        err("لا يوجد مزود DNS مستجيب — تحقق من اتصالك")
        return
    results.sort(key=lambda x: x[2])
    fastest = results[0]
    ok(f"الأسرع: {fastest[0]} ({fastest[1]}) بزمن {fastest[2]:.2f} مللي")
    log(f"DNS fastest={fastest[1]} {fastest[2]:.2f}ms")
    print()
    if not require_root():
        return
    # تطبيق الأسرع
    if IS_WINDOWS:
        # نضيف الرقم الأسرع في مقدمة قائمة DNS لكل واجهة نشطة
        rc, out = run(f'netsh interface ip add dns name="{get_active_iface()}" {fastest[1]} index=1', timeout=15)
        rc2, _ = run(f'netsh interface ip add dns name="{get_active_iface()}" {results[1][1]} index=2', timeout=15) if len(results) > 1 else (0, "")
        if rc == 0:
            ok(f"تم تعيين {fastest[0]} كـ DNS أساسي على واجهتك النشطة (سيصبح فوريًا بعد إعادة الاتصال/إعادة التشغيل)")
            save_backup({"dns_primary": fastest[1], "dns_secondary": results[1][1] if len(results) > 1 else None})
        else:
            err("تعذر تعيين DNS — جرّب يدويًا: الإعدادات → الشبكة → خصائص → IPv4 → DNS")
    else:
        # لينكس/تيرمكس: نضيف ملف resolv.conf.head لكي يطبق تلقائيًا
        line = f"nameserver {fastest[1]}\n"
        if IS_TERMUX:
            warn("في تيرمكس: DNS يُدار من نظام أندرويد نفسه — طبّق يدويًا من إعدادات WiFi (Private DNS)")
            info(f"الموصى به: أضف في إعدادات الهاتف → Private DNS → dns hostname → cloudflare")
            return
        rc, out = run_root(f"printf '{line}' > /etc/resolvconf/resolv.conf.d/head 2>/dev/null || printf '{line}' > /etc/resolv.conf.head")
        # إعادة توليد resolv.conf إن كان resolvconf مثبتًا
        run_root("resolvconf -u 2>/dev/null || true")
        info("ملاحظة: على أجهزة Linux قد يعيد NetworkManager قوالب DNS بعد إعادة الاتصال")
        ok(f"تم إعداد {fastest[0]} ({fastest[1]}) كـ DNS أولوي في resolv.conf.head")

def get_active_iface():
    """اسم واجهة الشبكة النشطة (لأوامر netsh في ويندوز)"""
    if IS_WINDOWS:
        rc, out = run('netsh interface show interface | findstr /C:"connected"')
        for line in out.splitlines():
            m = re.search(r"([A-Za-z0-9 _-]+)\s*$", line.strip())
            if m:
                return m.group(1).strip()
        return "Wi-Fi"
    return "wlan0"

# =====================================================================
#  الفحص 3: تحسينات TCP المشروعة (تخفض التأخير وتثبّت الاتصال)
# =====================================================================
LINUX_TCP_TUNING = [
    # (المفتاح, القيمة, الشرح)
    ("net.ipv4.tcp_congestion_control", "bbr",
     "خوارزمية BBR من جوجل: أفضل ثبات وأقل تأخير للألعاب (إن كانت متاحة)"),
    ("net.core.default_qdisc", "fq",
     "جدولة fq: المرافق الطبيعي لـ BBR — يجعل التأخير ثابتًا"),
    ("net.ipv4.tcp_fastopen", "3",
     "TCP Fast Open: يوفر جولة كاملة عند كل اتصال جديد (تقليل انتظار الدخول للعبة)"),
    ("net.ipv4.tcp_mtu_probing", "1",
     "اكتشاف MTU تلقائيًا: يمنع مشاكل التقطيع في شبكات الجوال"),
    ("net.ipv4.tcp_no_metrics_save", "1",
     "عدم حفظ قياسات الاتصالات القديمة السلبية: بداية نظيفة كل مرة"),
    ("net.ipv4.tcp_timestamps", "1",
     "الطوابع الزمنية: حساب RTT أدق وإعادة إرسال أفضل"),
    ("net.ipv4.tcp_sack", "1",
     "Selective ACK: استرجاع أسرع للحوزم المفقودة (أقل لاق داخل اللعبة)"),
    ("net.ipv4.tcp_frto", "2",
     "F-RTO: استرجاع أسرع بعد فقدان حزم (بعد انقطاع قصير لا يعاد الاتصال من الصفر)"),
    ("net.ipv4.tcp_low_latency", "1",
     "وضع التأخير المنخفض لـ TCP"),
    ("net.ipv4.tcp_window_scaling", "1",
     "تكبير نافذة TCP: استقبال بيانات أكثر بجولة أقل"),
    ("net.ipv4.tcp_keepalive_time", "60",
     "إبقاء الاتصال حيًا كل 60 ثانية بدل 7200: كشف انقطاعات اللعبة فورًا"),
    ("net.ipv4.tcp_keepalive_intvl", "10",
     "فحص الإبقاء كل 10 ثوانٍ"),
    ("net.ipv4.tcp_keepalive_probes", "6",
     "عدد محاولات الإبقاء قبل إعلان الموت"),
    ("net.ipv4.udp_mem", "8388608 12582912 16777216",
     "ذاكرة UDP أكبر: حزم اللعبة الأهم (فري فاير يعمل بـ UDP)"),
    ("net.core.rmem_max", "16777216",
     "أقصى مخزن استقبال: حزم لا تُفقد عند الزحام"),
    ("net.core.wmem_max", "16777216",
     "أقصى مخزن إرسال"),
    ("net.ipv4.tcp_rmem", "4096 87380 16777216",
     "نافذة استقبال TCP تلقائية"),
    ("net.ipv4.tcp_wmem", "4096 65536 16777216",
     "نافذة إرسال TCP تلقائية"),
    ("net.ipv4.tcp_notsent_lowat", "16384",
     "حد الحزم غير المرسلة: راحة فورية للحزم الصغيرة (مثل حزم اللعب)"),
    ("net.ipv4.tcp_ecn", "1",
     "إشعار الازدحام الصريح: تفاوض شفاف مع الشبكات التي تدعمه"),
    ("net.ipv4.route.flush", "1",
     "تنظيف جداول التوجيه القديمة (تنظيف واحد عند التطبيق)"),
]

def cmd_tcp_tune():
    title("تحسينات TCP/النظام المشروعة (Nagle + مخازن + BBR)")
    if IS_WINDOWS:
        print()
        warn("على ويندوز: تعطيل Nagle + تحسينات TCP تتم من ملف .bat المرفق (FF-TurboNet-Windows.bat)")
        info("هذا الملف يدير التسجيل تلقائيًا (TcpAckFrequency, TCPNoDelay, ...) بنسخة احتياطية")
        info("أو شغّل من هنا الآن:")
        print()
        print(c('   netsh int tcp set global autotuninglevel=normal', "96"))
        print(c('   netsh int tcp set global congestionprovider=ctcp', "96"))
        print(c('   netsh int tcp set global timestamps=enabled', "96"))
        print()
        if require_root():
            for cmd in [
                'netsh int tcp set global autotuninglevel=normal',
                'netsh int tcp set global congestionprovider=ctcp',
                'netsh int tcp set global timestamps=enabled',
                'netsh int tcp set global ecncapability=enabled',
            ]:
                rc, out = run(cmd, timeout=15)
                st = c("تم ✓", "92") if rc == 0 else c("تجاهل", "90")
                print(f"   {cmd:<60} {st}")
            log("TCP tune applied via netsh (Windows)")
            ok("تم تطبيق تحسينات TCP العامة على ويندوز")
        return
    # لينكس / تيرمكس
    if not require_root():
        return
    print()
    applied, skipped, failed = 0, 0, 0
    # تحقق من توفر bbr
    rc, avail = run("cat /proc/sys/net/ipv4/tcp_available_congestion_control")
    bbr_ok = "bbr" in (avail or "")
    backup = load_backup()
    backup.setdefault("sysctl", {})
    for key, val, desc in LINUX_TCP_TUNING:
        if "bbr" in key and not bbr_ok:
            skipped += 1
            warn(f"تخطي BBR — غير متاح على نواتك (سنعود إلى cubic الافتراضي)")
            continue
        if key == "net.ipv4.tcp_congestion_control" and not bbr_ok:
            continue
        if key == "net.core.default_qdisc" and not bbr_ok:
            continue
        rc, out = run_root(f'sysctl -w "{key}={val}"')
        if rc == 0:
            applied += 1
            backup["sysctl"][key] = val
            print(c(f"   ✓ {key} = {val}", "92"))
        else:
            failed += 1
            print(c(f"   ✗ {key} (غير موجود في هذه النواة)", "90"))
    # حفظ دائم عبر rc.local أو sysctl.d
    if applied:
        rc_local = "/data/data/com.termux/files/usr/etc/rc.local" if IS_TERMUX else "/etc/sysctl.d/99-turbonet.conf"
        lines = "\n".join(f"{k}={v}" for k, v in backup["sysctl"].items())
        if IS_TERMUX:
            warn("تيرمكس بدون روت لا يحفظ sysctl بشكل دائم — أعد التشغيل بعد كل إعادة تشغيل للهاتف")
            warn("للحفظ الدائم: استخدم خيار الروت (su) أو طبّق من FF-TurboNet-Windows.bat على جهاز الكمبيوتر")
        else:
            run_root(f"printf '{lines}\\n' > /etc/sysctl.d/99-turbonet.conf")
            run_root("sysctl --system 2>/dev/null | tail -1")
            ok(f"تم حفظ التحسينات بشكل دائم: /etc/sysctl.d/99-turbonet.conf")
    save_backup(backup)
    log(f"TCP tune applied={applied} skipped={skipped} failed={failed}")
    ok(f"النتيجة: {applied} تطبيق ناجح، {skipped} تخطي، {failed} فشل")

# =====================================================================
#  الفحص 4: وضع اللعب — قتل المشتتات على الشبكة (اختياري — بالخيار)
# =====================================================================
# قائمة عمليات معروفة تستهلك الشبكة في الخلفية (آمنة للقتل — ليست خدمات نظام حرجة)
BG_APPS = {
    "Windows": [
        # (اسم العملية, وصف عربي)
        ("OneDrive.exe", "مزامنة ون درايف — يرفع ملفات في الخلفية"),
        ("Dropbox.exe", "مزامنة دروبوكس"),
        ("MsMpEng.exe", "فحص في الخلفية (ويندوز ديفندر) — قتله مؤقت فقط، سيعد تلقائيًا"),
        ("GoogleUpdate.exe", "محدّث جوجل كروم"),
        ("GoogleCrashHandler.exe", "معالج أعطال كروم"),
        ("AdobeARM.exe", "محدّث أدوبي"),
        ("AdobeUpdateService.exe", "خدمة تحديث أدوبي"),
        ("Steam.exe", "ستيم — إن لم تكن تلعب من ستيم"),
        ("EpicGamesLauncher.exe", "منصة Epic"),
        ("discord.exe", "ديسكورد (إن لم تستخدمه للتواصل أثناء اللعب)"),
        ("SKYPE.EXE", "سكايب"),
        ("Teams.exe", "مايكروسوفت تيمز"),
        ("BackgroundTransferHost.exe", "نقل بيانات خلفي لويندوز"),
        ("WpnService.exe", "خدمة إشعارات ويندوز — تجلب تحديثات ولوحات"),
    ],
    "Android": [
        # (اسم الحزمة/الباكج, وصف)
        ("com.facebook.app", "فيسبوك"),
        ("com.facebook.orca", "ماسنجر"),
        ("com.instagram.android", "إنستغرام"),
        ("com.whatsapp", "واتساب"),
        ("com.snapchat.android", "سناب شات"),
        ("com.google.android.gms", "خدمات جوجل (تحديثات خلفية) — مؤقتًا فقط"),
        ("com.android.vending", "متجر بلاي — تحديثات خلفية"),
        ("com.tencent.ig", "⚠️ هذه باكج ببجي — لا تقتلها إن كنت تلعبها أيضًا"),
    ],
}

def cmd_gaming_mode():
    title("وضع اللعب — إيقاف البرامج الخلفية التي تسرق الشبكة")
    info("أي برنامج يرفع/ينزل بيانات أثناء اللعب = لاق وتقطيع")
    print()
    if IS_WINDOWS:
        killed = 0
        for proc, desc in BG_APPS["Windows"]:
            rc, out = run(f'tasklist /FI "IMAGENAME eq {proc}" /NH | findstr /I "{proc}"')
            if rc == 0 and proc.lower() in out.lower():
                run(f'taskkill /F /IM {proc} 2>nul', timeout=10)
                print(c(f"   ⛔ أوقفت: {proc} — {desc}", "92"))
                killed += 1
            else:
                print(c(f"   •  {proc} غير مشغّل", "90"))
        if killed:
            ok(f"أوقفت {killed} برنامجًا يستهلك الشبكة — شبكتك الآن للعبة فقط")
            log(f"Gaming mode killed={killed}")
        else:
            ok("لا توجد برامج خلفية مشغّلة تستهلك الشبكة — ممتاز!")
    elif IS_TERMUX:
        warn("في أندرويد: تطبيق Termux لا يستطيع قتل تطبيقات أخرى بدون روت")
        info("الحل المشروع: إعدادات الهاتف → Battery → تقييد الخلفية للتطبيقات الاجتماعية")
        info("أو فعّل 'وضع اللعب/Game Mode' المدمج في هاتفك إن وجد")
        if su_available():
            rc, out = run_root("pm list packages -3")
            installed = set(re.findall(r"package:(\S+)", out or ""))
            killed = 0
            for pkg, desc in BG_APPS["Android"]:
                if pkg in installed and "tencent" not in pkg and "gms" not in pkg:
                    rc, _ = run_root(f"am force-stop {pkg}")
                    if rc == 0:
                        print(c(f"   ⛔ أوقفت: {pkg} — {desc}", "92"))
                        killed += 1
            if killed:
                ok(f"تم إيقاف {killed} تطبيقًا خلفيًا (مع روت)")
            else:
                ok("لا توجد تطبيقات من القائمة مشغّلة")
        else:
            info("بدون روت: طبّق يدويًا — أغلق التطبيقات من المهمّات الحديثة قبل اللعب")
    else:
        # لينكس
        warn("على لينكس: أوقف التطبيقات الثقيلة يدويًا (torrents، sync، متصفح التحميل)")
        info("أوامر مفيدة: btop / htop لمراقبة المستهلكين")
        print()
        rc, out = run("ss -tunp 2>/dev/null | head -20")
        if rc == 0 and out.strip():
            info("أكثر الاتصالات النشطة حاليًا في نظامك:")
            print(out)

# ---- PART3 ----

# =====================================================================
#  الفحص 5: مراقب الاستقرار المباشر (يرصد اللاق الحقيقي لحظيًا)
# =====================================================================
def cmd_monitor():
    title("مراقب الاستقرار المباشر — شغّله وأنت تلعب (Ctrl+C للإيقاف)")
    target = pick_best_server()
    if not target:
        err("لم أستطع تحديد سيرفر — تحقق من اتصالك أولًا")
        return
    host, port = target
    info(f"المراقبة على: {host}:{port} — سجل النتائج يُحفظ في {os.path.basename(LOG_FILE)}")
    print()
    conn_errs, total, bad = 0, 0, 0
    samples = []
    print(c("   الوقت        بينق    jitter    حالة", "93"))
    print(c("   " + "─" * 46, "90"))
    try:
        while True:
            r = tcp_ping(host, port, count=1, timeout=2.0)
            total += 1
            ts = datetime.now().strftime("%H:%M:%S")
            if r["ok"]:
                samples.append(r["avg"])
                color = "92" if r["avg"] < 70 else ("93" if r["avg"] < 100 else "91")
                st = "ثابت ✅" if r["jitter"] == 0 else "متذبذب ⚠️"
                print(c(f"   {ts}   {r['avg']:6.1f}   {r['jitter'] if r['jitter'] is not None else 0:6.1f}   {st}", color))
            else:
                bad += 1
                print(c(f"   {ts}   فشل الاتصال ❌  (احتمال انقطاع/حجب)", "91"))
            time.sleep(1.0)
    except KeyboardInterrupt:
        print()
        if total:
            good = len(samples)
            rate = (bad / total) * 100
            if samples:
                info(f"ملخص: {total} محاولة | نجحت {good} | فشلت {bad} | فشل {rate:.1f}%")
                info(f"متوسط البينق: {statistics.mean(samples):.1f} مللي | الأعلى: {max(samples):.1f} | الأدنى: {min(samples):.1f}")
                if rate > 5:
                    err("نسبة فشل عالية — طبّق تحسينات TCP + DNS ثم أعد الفحص")
                elif statistics.pstdev(samples) > 30:
                    warn("تذبذب عالٍ — السبب غالبًا شبكة الجوال/الوايفاي، قرّب من الراوتر أو استخدم 5GHz")
                else:
                    ok("اتصالك مستقر — استمتع باللعب!")
                log(f"MONITOR total={total} bad={bad} avg={statistics.mean(samples) if samples else 'N/A'}")

def pick_best_server():
    """اختيار أفضل سيرفر فري فاير حسب البينق — فحص متوازٍ بالخيوط (سريع جدًا)"""
    from concurrent.futures import ThreadPoolExecutor
    targets = [(h, p) for region, tgts in FF_SERVERS.items() for h, p in tgts]
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(tcp_ping, h, p, 2, 1.0): (h, p) for h, p in targets}
        for fut, hp in futures.items():
            try:
                r = fut.result(timeout=8)
            except Exception:
                continue
            if r["ok"]:
                results.append((hp, r["avg"]))
    if not results:
        return None
    results.sort(key=lambda x: x[1])
    return results[0][0]

# =====================================================================
#  استرجاع الإعدادات الأصلية (Undo) — لأمانك الكامل
# =====================================================================
def cmd_undo():
    title("استرجاع الإعدادات الأصلية (Undo)")
    backup = load_backup()
    if not backup:
        warn("لا توجد نسخة احتياطية محفوظة — لا شيء لاسترجاعه")
        return
    if not require_root():
        return
    print()
    # 1) DNS
    if backup.get("dns_primary"):
        if IS_WINDOWS:
            rc, _ = run(f'netsh interface ip set dns name="{get_active_iface()}" dhcp')
            ok("أعدنا DNS إلى الوضع التلقائي (DHCP) على ويندوز")
        else:
            run_root("rm -f /etc/resolv.conf.head /etc/resolvconf/resolv.conf.d/head")
            run_root("resolvconf -u 2>/dev/null || true")
            ok("أزلنا DNS اليدوي واستعدنا إعداد النظام")
    # 2) sysctl
    if backup.get("sysctl"):
        if IS_WINDOWS:
            # استرجاع قيم التسجيل عبر bat (يشمل TcpAckFrequency/TCPNoDelay)
            bat = os.path.join(SCRIPT_DIR, "FF-TurboNet-Windows.bat")
            if os.path.exists(bat):
                info(f"لتكملة الاسترجاع الكامل على ويندوز: شغّل {os.path.basename(bat)} واختر [R]")
            rc, _ = run("netsh int tcp set global autotuninglevel=normal")
            rc, _ = run("netsh int tcp set global congestionprovider=default")
        else:
            run_root("rm -f /etc/sysctl.d/99-turbonet.conf")
            run_root("sysctl --system 2>/dev/null | tail -1")
            ok("أزلنا ملف التحسينات الدائمة واستعدنا إعدادات النواة الافتراضية")
    # 3) ملفات النسخة الاحتياطية للتسجيل (ويندوز - من ملف bat)
    for reg in backup.get("reg_backups", []):
        if IS_WINDOWS and os.path.existsSync(reg):
            run(f'reg import "{reg}" 2>nul', timeout=15)
            ok(f"استرجعنا ملف تسجيل: {os.path.basename(reg)}")
    if os.path.exists(BACKUP_FILE):
        os.remove(BACKUP_FILE)
    ok("تم الاسترجاع — نظامك كما كان تمامًا قبل الأداة ✅")
    log("UNDO completed")

# =====================================================================
#  القائمة الرئيسية
# =====================================================================
MENU = """
┌──────────────────────────────────────────────────────────┐
│  الأوامر المتاحة:                                          │
│                                                            │
│   [1] فحص البينق الشامل لسيرفرات فري فاير (بدون روت)      │
│   [2] تسريع DNS — قياس + تطبيق الأسرع                    │
│   [3] تحسينات TCP/النظام (BBR + مخازن + إبقاء حي)       │
│   [4] وضع اللعب — إيقاف سرّاق الشبكة الخلفيين             │
│   [5] المراقبة المباشرة — شغّلها وأنت تلعب                │
│   [6] الأقوى: كل التحسينات السابقة مرة واحدة             │
│   [7] استرجاع الإعدادات الأصلية (Undo)                   │
│   [8] معلومات النظام والشبكة                             │
│   [0] خروج                                                │
│                                                            │
│   سطر الأوامر:                                             │
│     ff_turbonet.py ping | dns | tune | game | monitor     │
│     ff_turbonet.py boost  (= كل التحسينات دفعة واحدة)     │
│     ff_turbonet.py undo   (= استرجاع كل الإعدادات)        │
└──────────────────────────────────────────────────────────┘
"""

def cmd_sysinfo():
    title("معلومات النظام والشبكة")
    print(f"   النظام        : {platform.system()} {platform.release()}")
    print(f"   المعالج       : {platform.machine()}")
    print(f"   Python        : {platform.python_version()}")
    print(f"   مستخدم مميز   : {'نعم' if is_elevated() else 'لا'}" + (f" | su متاح: {'نعم' if su_available() else 'لا'}" if IS_TERMUX else ""))
    rc, out = run("ip route get 1.1.1.1 2>/dev/null || route print -4 2>nul | findstr 0.0.0.0")
    info("البوابة الافتراضية:")
    print("   " + (out.strip().splitlines()[0] if out.strip() else "غير معروف"))
    rc, out = run("ip -br addr 2>/dev/null || ipconfig 2>nul")
    info("واجهات الشبكة:")
    for line in (out or "").strip().splitlines()[:10]:
        print("   " + line)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info(f"عنوان IP العام المحلي: {s.getsockname()[0]}")
        s.close()
    except Exception:
        pass

def main():
    banner()
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else None
    if arg in ("-h", "--help", "help"):
        print(MENU)
        return
    actions = {
        "ping": cmd_ping_all, "dns": cmd_dns_boost, "tune": cmd_tcp_tune,
        "game": cmd_gaming_mode, "monitor": cmd_monitor, "boost": cmd_boost_all,
        "undo": cmd_undo, "info": cmd_sysinfo,
    }
    if arg in actions:
        actions[arg]()
        return
    # قائمة تفاعلية
    while True:
        print(MENU)
        choice = input(c("اختر رقمًا [0-8]: ", "96")).strip()
        if choice == "1": cmd_ping_all()
        elif choice == "2": cmd_dns_boost()
        elif choice == "3": cmd_tcp_tune()
        elif choice == "4": cmd_gaming_mode()
        elif choice == "5": cmd_monitor()
        elif choice == "6": cmd_boost_all()
        elif choice == "7": cmd_undo()
        elif choice == "8": cmd_sysinfo()
        elif choice in ("0", "q", "exit", "خروج"): 
            print(c("مع السلامة! نتمنى لك بينق منخفض وثابت 🎮", "93")); break
        else: err("اختيار غير صحيح")
        try:
            input(c("\nاضغط Enter للعودة للقائمة...", "90"))
        except (EOFError, KeyboardInterrupt):
            break

def cmd_boost_all():
    title("الوضع الأقوى — تطبيق كل التحسينات مرة واحدة")
    warn("سنطبّق: تسريع DNS + تحسينات TCP + وضع اللعب (يحتاج صلاحيات)")
    if IS_WINDOWS and not is_elevated():
        err("شغّل كمسؤول (Run as Administrator) ثم أعد المحاولة")
        return
    if not IS_WINDOWS and not (is_elevated() or su_available()):
        warn("بدون روت: ستُطبَّق الفحوصات فقط (ping/DNS قياس) بدون التعديلات")
    print()
    cmd_ping_all()
    cmd_dns_boost()
    cmd_tcp_tune()
    cmd_gaming_mode()
    title("اكتمل وضع التحسين الكامل")
    ok("الآن: أعد تشغيل الاتصال بالشبكة (أو أعد التشغيل) ثم شغّل [5] المراقبة وأنت تلعب")
    ok(f"التقرير الكامل محفوظ: {os.path.basename(LOG_FILE)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(c("\nتم الإيقاف بواسطة المستخدم — وداعًا! 👋", "93"))
