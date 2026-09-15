#!/data/data/com.termux/files/usr/bin/bash
# =====================================================================
#  FF-TurboNet v3.0 — مساعد أندرويد/تيرمكس
#  تثبيت تلقائي + فحص بينق + دعم روت اختياري (sysctl) — قانوني 100%
#  لا يلمس اللعبة إطلاقًا — فقط جهازك وشبكتك أنت
# =====================================================================
VERSION="3.0.0"
RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'; CYN='\033[0;36m'; RST='\033[0m'
ok(){ echo -e "  ${GRN}[✓]${RST} $1"; }
warn(){ echo -e "  ${YLW}[!]${RST} $1"; }
err(){ echo -e "  ${RED}[✗]${RST} $1"; }
info(){ echo -e "  ${CYN}[i]${RST} $1"; }

echo -e "${CYN}"
echo "  ███████╗███████╗ ██████╗    ████████╗██╗   ██╗██████╗ ███████╗██████╗"
echo "  ██╔════╝██╔════╝██╔════╝    ╚══██╔══╝██║   ██║██╔══██╗██╔════╝██╔══██╗"
echo "  ██████╗  ███████╗██║            ██║   ██║   ██║██████╔╝█████╗  ██████╔╝"
echo "  ██╔══╝  ╚════██║██║            ██║   ██║   ██║██╔══██╗██╔══╝  ██╔═══╝ "
echo "  ███████╗███████║╚██████╗       ██║   ╚██████╔╝██║  ██║███████╗██║     "
echo "  ╚══════╝╚══════╝ ╚═════╝       ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝     v$VERSION"
echo -e "${RST}"

# ------------------------- تثبيت تلقائي -------------------------
PKGS=""
command -v python >/dev/null 2>&1 || PKGS="$PKGS python"
command -v ping >/dev/null 2>&1 || PKGS="$PKGS iputils"
if [ -n "$PKGS" ]; then
    info "تثبيت المتطلبات تلقائيًا: $PKGS (اضغط y عند الطلب)"
    pkg install -y $PKGS || { err "فشل التثبيت — تأكد من: apt update && apt upgrade"; exit 1; }
fi
ok "المتطلبات جاهزة"

# ------------------------- كشف الروت -------------------------
ROOTED=0
if command -v su >/dev/null 2>&1; then
    su -c "id" >/dev/null 2>&1 && ROOTED=1 || true
fi
if [ $ROOTED -eq 1 ]; then
    ok "الجهاز مروّت (روت) — التحسينات الكاملة متاحة"
else
    warn "بدون روت: فحص البينق + نصائح يدوية فقط (التعديلات تحتاج روت)"
fi

# ------------------------- sysctl مع روت -------------------------
tune_rooted() {
    echo
    info "تطبيق تحسينات sysctl (مع روت)..."
    local applied=0 failed=0
    apply() {
        su -c "sysctl -w \"$1=$2\"" >/dev/null 2>&1 && { echo -e "  ${GRN}✓${RST} $1 = $2"; applied=$((applied+1)); } || { echo -e "  ${RED}✗${RST} $1 (غير مدعوم في هذه النواة)"; failed=$((failed+1)); }
    }
    apply "net.ipv4.tcp_fastopen" "3"
    apply "net.ipv4.tcp_mtu_probing" "1"
    apply "net.ipv4.tcp_no_metrics_save" "1"
    apply "net.ipv4.tcp_timestamps" "1"
    apply "net.ipv4.tcp_sack" "1"
    apply "net.ipv4.tcp_frto" "2"
    apply "net.ipv4.tcp_window_scaling" "1"
    apply "net.ipv4.tcp_keepalive_time" "60"
    apply "net.ipv4.tcp_keepalive_intvl" "10"
    apply "net.ipv4.tcp_keepalive_probes" "6"
    apply "net.core.rmem_max" "16777216"
    apply "net.core.wmem_max" "16777216"
    su -c "sysctl -w \"net.ipv4.udp_mem=8388608 12582912 16777216\"" >/dev/null 2>&1 && echo -e "  ${GRN}✓${RST} net.ipv4.udp_mem (حزم UDP — أهم حزم للعبة)"
    ok "تم تطبيق $applied تحسينًا" ; [ $failed -gt 0 ] && warn "$failed غير مدعومة في نواة هاتفك (طبيعي)"
}

# ------------------------- فحص البينق -------------------------
ping_test() {
    echo
    echo -e "  ${CYN}═══ فحص البينق لسيرفرات فري فاير ═══${RST}"
    ping -c 4 -W 2 ff.garena.com 2>/dev/null | tail -2 | sed 's/^/  /' || warn "ff.garena.com لا يستجيب"
    echo
    ping -c 4 -W 2 ff.garena.com.cdn.cloudflare.net 2>/dev/null | tail -2 | sed 's/^/  /' || warn "CDN الشرق الأوسط لا يستجيب"
    echo
    ping -c 4 -W 2 202.81.97.70 2>/dev/null | tail -2 | sed 's/^/  /' || warn "سيرفر بنغلاديش لا يستجيب"
    echo
    info "للفحص الاحترافي الكامل: python ff_turbonet.py ping"
}

# ------------------------- القائمة -------------------------
while true; do
    echo
    echo -e "  ${CYN}┌─────────────────────────────────────────────┐${RST}"
    echo -e "  ${CYN}│${RST}  FF-TurboNet Android — القائمة            ${CYN}│${RST}"
    echo -e "  ${CYN}└─────────────────────────────────────────────┘${RST}"
    echo "   [1] فحص البينق لسيرفرات فري فاير"
    echo "   [2] تحسينات الشبكة (يحتاج روت)"
    echo "   [3] تشغيل الأداة الكاملة (python ff_turbonet.py)"
    echo "   [4] نصائح يدوية بدون روت (مهم للجميع)"
    echo "   [0] خروج"
    read -r -p "   اختر [0-4]: " ch
    case "$ch" in
        1) ping_test ;;
        2) if [ $ROOTED -eq 1 ]; then tune_rooted; else warn "يتطلب روت — استخدم [4] للنصائح اليدوية"; fi ;;
        3) python "$(dirname "$0")/ff_turbonet.py" || python3 "$(dirname "$0")/ff_turbonet.py" ;;
        4)
            echo
            info "نصائح تيرمكس بدون روت (طبّقها من إعدادات الهاتف):"
            echo "   1. الإعدادات → الشبكة → Private DNS → اكتب: one.one.one.one"
            echo "      (Cloudflare DNS عبر TLS — يسرّع كل استعلامات جهازك)"
            echo "   2. الإعدادات → البطارية → تقييد الخلفية لـ: فيسبوك/ماسنجر/إنستغرام/واتساب"
            echo "   3. فعّل 'وضع اللعب/Game Mode' المدمج في هاتفك (Samsung/Xiaomi/Realme)"
            echo "   4. إعدادات المطور → 'Mobile data always active' = ON (تجميع ذكي للشبكتين)"
            echo "   5. قبل الماتش: أغلق كل التطبيقات من المهمات الحديثة"
            echo "   6. اللعب على واي فاي 5GHz أفضل من الجوال إذا كان الإشارة قوية"
            echo "   7. في اللعبة: الإعدادات → الشبكة → اختر الأقل بينق (High Ping Mark)"
            ;;
        0) echo -e "  ${YLW}مع السلامة! بينق منخفض وثابت 🎮${RST}"; exit 0 ;;
        *) err "اختيار غير صحيح" ;;
    esac
done
