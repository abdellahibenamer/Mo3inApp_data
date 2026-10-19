import base64
import datetime
import hashlib
import http.server
import json
import os
import platform
import re
import shutil
import sys
import time
import secrets
import uuid
import webbrowser
from urllib.parse import quote
import random
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
import webview


# ==========================================
# 1. طبقة البايثون (PYTHON BACKEND ENGINE)
# ==========================================

# قائمة القرّاء: المصدر الوحيد للروابط.
# كل المجلدات أدناه مأخوذة من فهرس موقع everyayah.com نفسه.
# ملاحظة: لا يوجد "الحصري برواية ورش" على everyayah (آية بآية)،
# المتوفر لورش: الدوسري، ياسين الجزائري، عبد الباسط (ينقصه بعض الآيات).
EVERYAYAH = "https://everyayah.com/data/"
RECITERS = [
    # ---------- ورش عن نافع ----------
    {"id": "warsh_dosary", "group": "ورش عن نافع",
     "label": "إبراهيم الدوسري - ورش (128)",
     "url": EVERYAYAH + "warsh/warsh_ibrahim_aldosary_128kbps/"},
    {"id": "warsh_yassin", "group": "ورش عن نافع",
     "label": "ياسين الجزائري - ورش (64)",
     "url": EVERYAYAH + "warsh/warsh_yassin_al_jazaery_64kbps/"},
    {"id": "warsh_basit", "group": "ورش عن نافع",
     "label": "عبد الباسط - ورش (ينقصه بعض الآيات)",
     "url": EVERYAYAH + "warsh/warsh_Abdul_Basit_128kbps/"},
    # ---------- حفص عن عاصم ----------
    {"id": "husary_murattal", "group": "حفص عن عاصم",
     "label": "الحصري - مرتل",
     "url": EVERYAYAH + "Husary_128kbps/"},
    {"id": "husary_mujawwad", "group": "حفص عن عاصم",
     "label": "الحصري - مجوّد",
     "url": EVERYAYAH + "Husary_128kbps_Mujawwad/"},
    {"id": "husary_muallim", "group": "حفص عن عاصم",
     "label": "الحصري - المصحف المعلّم",
     "url": EVERYAYAH + "Husary_Muallim_128kbps/"},
    {"id": "minshawi", "group": "حفص عن عاصم",
     "label": "المنشاوي - مرتل",
     "url": EVERYAYAH + "Minshawy_Murattal_128kbps/"},
    {"id": "basit_hafs", "group": "حفص عن عاصم",
     "label": "عبد الباسط - مرتل",
     "url": EVERYAYAH + "Abdul_Basit_Murattal_192kbps/"},
    {"id": "alafasy", "group": "حفص عن عاصم",
     "label": "مشاري العفاسي",
     "url": EVERYAYAH + "Alafasy_128kbps/"},
    {"id": "shuraym", "group": "حفص عن عاصم",
     "label": "سعود الشريم",
     "url": EVERYAYAH + "Saood_ash-Shuraym_128kbps/"},
    {"id": "muaiqly", "group": "حفص عن عاصم",
     "label": "ماهر المعيقلي",
     "url": EVERYAYAH + "MaherAlMuaiqly128kbps/"},
]

# بيانات مصحف المدينة برسم QCF4 (رواية حفص): كل كلمة مع رمز الحرف (glyph) واسم خطها.
# ===== معلومات التطبيق (عدّلها بمعلوماتك لتظهر في القائمة الجانبية) =====
APP_INFO = {
    "name": "معين الحفَّاظ",
    "version": "1.0.2",
    "developer": "Et-Talib",     # اسمك أو اسم الفريق (اتركه فارغًا إن أردت إخفاء الهوية)
    "email": "abdellahibenamer@gmail.com",         # يفضّل بريد مخصص للتطبيق؛ Gmail/Outlook/Yahoo تفتح واجهة الكتابة مباشرة
    "telegram": "@Mo3in_Hoffad_bot",      # @username أو رابط https://t.me/... (قناة/مجموعة/بوت تُخفي هويتك)
    "whatsapp": "",      # رقم مع رمز الدولة، أو رابط https://wa.me/... أو https://chat.whatsapp.com/... أو رابط قناة
    "form": "",          # رابط نموذج اقتراحات (مثل Google Forms) — لا يكشف هوية صاحب التطبيق
    "website": "",       # مثال: https://example.com
}

# ===== سجل التغييرات: يظهر في القائمة الجانبية ← ✨ ما الجديد =====
# عند إصدار نسخة جديدة: ارفع APP_INFO["version"] وأضف عنصرًا جديدًا في أول القائمة.
# من فتح التطبيق بعد التحديث يرى نقطة تنبيه على زر ☰ وتُفتح له الميزات الجديدة تلقائيًا.
CHANGELOG = [
    {"version": "1.0.2", "date": "2026-10", "items": [
        "🧭 التنقل في المصحف بالأحزاب والأرباع (240 ربعًا) إلى جانب الأجزاء.",
        "🗂 كل بيانات التطبيق (السور والصفحات والتفاسير والخطوط) صارت من مستودع بياناتنا، وتُحفظ على جهازك فتعمل دون إنترنت.",
        "🔤 خطوط الواجهة تُحمَّل من مستودع البيانات بدل Google Fonts.",
    ]},
    {"version": "1.1.0", "date": "2026-10", "items": [
        "🎙 مشغّل المتون: حمّل ملفات صوتية من جهازك (ملفات أو مجلد) وتحكّم بسرعة التشغيل مع بقاء الصوت طبيعيًا.",
        "🔁 تكرار الملف أو مقطع A–B عددًا محددًا أو بلا توقف، مع فاصل صمت بين التكرارات للترديد والحفظ.",
        "🔖 احفظ المقاطع المهمة بأسماء (مثل «البيت 1–3») وارجع إليها بضغطة، ويتذكر التطبيق موضع توقفك في كل ملف.",
        "✨ قسم «ما الجديد» في القائمة الجانبية يعرض مزايا كل إصدار.",
    ]},
    {"version": "1.0.0", "date": "2026-10", "items": [
        "🎧 التلاوة آية بآية بعدة قرّاء وروايات، مع التكرار والسرعة والمقاطع، وعرض الآية المتلوة فقط.",
        "📖 المصحف برسم مصحف المدينة (QCF4) مع البحث بالأسماء والكلمات، والأجزاء، والعلامات، والورد اليومي، وتلاوة الصفحة بالتتابع.",
        "🧠 اختبار الحفظ بأربعة أنماط مع مراجعة متباعدة للآيات المتعثرة.",
        "📚 التفسير تحت الآيات، 📥 صوت دون إنترنت، 🌙 وضع ليلي، ⏱ مؤقّت نوم، 🗕 وضع مصغّر.",
        "🔒 إحصاء مجهول اختياري لعدد المستخدمين، بموافقتك فقط.",
    ]},
]

# عنوان عدّاد المستخدمين المجهول (نقطة /ping في Worker الخاص بك). اتركه فارغًا لتعطيل الميزة تمامًا.
# مثال: "https://quran-relay-bot.حسابك.workers.dev/ping"
ANALYTICS_URL = ""

# مستودع بيانات التطبيق الخاص بك (السور، الأجزاء، الأرباع، صفحات المصحف، التفاسير، الخطوط).
# يقرأ التطبيق منه مرة واحدة ويحفظ نسخة محلية، فيعمل بعدها دون إنترنت.
# وإن وُجد مجلد data بجوار التطبيق (نسخة من المستودع) فيُستعمل بدل الإنترنت (للبناء المضمَّن).
DATA_BASE = "https://raw.githubusercontent.com/abdellahibenamer-spec/Mo3inApp_data/main/"

# إصدارات التفسير (الملفات في tafsir/<المعرّف>.json داخل مستودع البيانات)
TAFSIR_EDITIONS = {
    "ar-tafsir-muyassar": "التفسير الميسر",
    "ar-tafseer-al-saddi": "تفسير السعدي",
    "ar-tafsir-al-jalalayn": "تفسير الجلالين",
    "ar-tafsir-al-mukhtasar": "المختصر في تفسير القرآن",
    "en-tafsir-al-mukhtasar": "Al-Mukhtasar (English)",
    "french-mokhtasar": "Al-Mukhtasar (Français)",
}

# فترات المراجعة المتباعدة (طريقة لايتنر): 10 دقائق، يوم، 3، 7، 14، 30، 60 يومًا
SRS_STEPS = [600, 86400, 3 * 86400, 7 * 86400, 14 * 86400, 30 * 86400, 60 * 86400]

UI_FONTS = {   # خطوط الواجهة (OFL) من fonts/ui في مستودع البيانات
    "AmiriQuran-Regular.ttf": ("Amiri Quran", "400"),
    "Amiri-Regular.ttf": ("Amiri", "400"),
    "Amiri-Bold.ttf": ("Amiri", "700"),
    "ScheherazadeNew-Regular.ttf": ("Scheherazade New", "400"),
    "ScheherazadeNew-Bold.ttf": ("Scheherazade New", "700"),
}


def _data_roots():
    """مجلدات بيانات مضمَّنة بجوار التطبيق (نسخة من المستودع)، إن وُجدت."""
    base = os.path.dirname(os.path.abspath(__file__))
    roots = [os.path.join(base, "data")]
    if getattr(sys, "frozen", False):
        roots.insert(0, os.path.join(os.path.dirname(sys.executable), "data"))
    return [r for r in roots if os.path.isdir(r)]



def _font_dirs():
    """
    أماكن البحث عن الخطوط بالترتيب:
    1) مجلد fonts بجوار الملف، 2) مجلد الملف نفسه،
    3) خطوط ويندوز (C:\\Windows\\Fonts)، 4) خطوط المستخدم الحالي المثبّتة لحسابه فقط.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    dirs = [os.path.join(base, "fonts"), base]
    if getattr(sys, "frozen", False):          # نسخة PyInstaller
        exe = os.path.dirname(sys.executable)
        dirs = [os.path.join(exe, "fonts"), exe] + dirs
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\Windows"
    dirs.append(os.path.join(windir, "Fonts"))
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(os.path.join(local, "Microsoft", "Windows", "Fonts"))
    return dirs


_FONT_INDEX = None


def _font_index():
    """فهرس {اسم الملف بحروف صغيرة: المسار الكامل}، يُبنى مرة واحدة (مجلد ويندوز كبير)."""
    global _FONT_INDEX
    if _FONT_INDEX is None:
        index = {}
        for d in _font_dirs():
            try:
                for name in os.listdir(d):
                    low = name.lower()
                    if low.startswith("qcf4_") and low not in index:
                        index[low] = os.path.join(d, name)
            except OSError:
                continue
        _FONT_INDEX = index
    return _FONT_INDEX


def _find_font_file(font_name):
    """يبحث عن QCF4_Hafs_07_W.ttf (أو بدون _W / بامتداد آخر) في الأماكن أعلاه."""
    index = _font_index()
    for suf in ("_W", ""):
        for ext in (".ttf", ".otf", ".woff2", ".woff"):
            path = index.get(f"{font_name}{suf}{ext}".lower())
            if path:
                return path
    return None


_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")


def _plain(text):
    """نص عربي بلا تشكيل (للمقارنة فقط)."""
    return _DIACRITICS.sub("", text or "")


_EXTRA_MARKS = re.compile(r"[\u0610-\u061A\u08D3-\u08FF]")


def _skeleton(text):
    """
    هيكل الكلمات للبحث: يتجاهل التشكيل وفروق الألف والهمزة والتاء المربوطة،
    فيجد «الصلاة» رغم أن رسمها في المصحف «الصلوٰة». يُطبَّق على النص والاستعلام معًا.
    """
    t = (text or "").replace("\u0670", "ا")
    t = _DIACRITICS.sub("", t)
    t = _EXTRA_MARKS.sub("", t)
    for a in "أإآٱ":
        t = t.replace(a, "ا")
    t = t.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    t = t.replace("وا", "ا")
    return re.sub(r"[\sاء]", "", t)


# صيغ الملفات الصوتية المحلية (مشغّل المتون)
AUDIO_MIME = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg", ".oga": "audio/ogg",
              ".m4a": "audio/mp4", ".aac": "audio/aac", ".flac": "audio/flac", ".opus": "audio/ogg",
              ".webm": "audio/webm"}


def _ver(v):
    """يحوّل '1.10.2' إلى (1, 10, 2) للمقارنة."""
    return tuple(int(x) for x in re.findall(r"\d+", str(v or "0"))) or (0,)


class _MediaHandler(http.server.BaseHTTPRequestHandler):
    """يخدم الملفات التي اختارها المستخدم فقط (برمز عشوائي لكل ملف) على 127.0.0.1، مع دعم Range للتقديم والتأخير."""
    server_version = "QuranMedia/1.0"

    def log_message(self, *a):
        pass

    def _serve(self, head_only):
        m = re.fullmatch(r"/a/([0-9a-f]{24})", self.path.split("?")[0])
        path = self.server.files.get(m.group(1)) if m else None
        if not path or not os.path.isfile(path):
            self.send_error(404)
            return
        size = os.path.getsize(path)
        start, end, status = 0, size - 1, 200
        rng = self.headers.get("Range")
        if rng and size:
            r = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip())
            if not r or (r.group(1) == "" and r.group(2) == ""):
                self.send_error(416)
                return
            if r.group(1) == "":
                start = max(0, size - int(r.group(2)))
            else:
                start = int(r.group(1))
                end = int(r.group(2)) if r.group(2) else size - 1
            if start >= size or start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            end = min(end, size - 1)
            status = 206
        ext = os.path.splitext(path)[1].lower()
        self.send_response(status)
        self.send_header("Content-Type", AUDIO_MIME.get(ext, "application/octet-stream"))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(max(0, end - start + 1)))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if head_only or not size:
            return
        try:
            with open(path, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(65536, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def do_GET(self):
        self._serve(False)

    def do_HEAD(self):
        self._serve(True)


class QuranBackendAPI:

    def __init__(self):
        self.cache_dir = os.path.join(tempfile.gettempdir(), "QuranAppCache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.settings_file = os.path.join(self.cache_dir, "settings.json")

        # بيانات المصحف الكاملة (للبحث والاختبار): تُبنى في خيط خلفي
        # مجلد الصوتيات المحمّلة (دائم، بعكس الكاش المؤقت)
        base = os.environ.get("LOCALAPPDATA") or os.path.join(
            os.path.expanduser("~"), ".local", "share")
        self.audio_dir = os.path.join(base, "QuranApp", "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
        self.data_dir = os.path.dirname(self.audio_dir)
        self.user_file = os.path.join(self.data_dir, "userdata.json")
        self._user_lock = threading.Lock()
        self._fresh_install = not os.path.exists(self.user_file)
        self._local_files = {}          # رمز عشوائي -> مسار (للملفات المحلية المسجّلة)
        self._tokens = {}               # معرّف الملف -> رمز
        self._media_srv = None
        self._media_lock = threading.Lock()
        self._off_lock = threading.Lock()
        self._data_lock = threading.RLock()
        self._data_mem = {}
        self._tafsir_idx = {}
        self._off_state = {"running": False, "cancel": False, "total": 0,
                           "done": 0, "failed": 0, "missing": 0, "bytes": 0,
                           "reciter": "", "error": None}

        self._corpus_lock = threading.Lock()
        self._corpus_state = {"ready": False, "running": False,
                              "done": 0, "total": 604, "error": None}
        self._verses = {}
        self._order = []
        self._first_idx = {}

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        }

    # ---------- أدوات مساعدة ----------
    def _read_json(self, path):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def _write_json(self, path, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"Cache write error: {e}", flush=True)

    # ---------- واجهة يستدعيها JavaScript ----------
    def log_audio_url(self, url, surah, ayah, riwaya_name):
        """طباعة فورية للرابط في Terminal"""
        print(
            f"\n{'=' * 65}\n"
            f"📖 التلاوة: سورة {surah} | الآية ﴿{ayah}﴾\n"
            f"🎙️ القارئ: {riwaya_name}\n"
            f"🔗 رابط MP3 المباشر:\n{url}\n"
            f"{'=' * 65}\n",
            flush=True,
        )
        return True

    def get_reciters(self):
        return RECITERS

    def check_reciters(self):
        """
        يتحقق من وجود أول آية عند كل قارئ.
        القيم: True = يعمل، False = 404 (الرابط خاطئ)، None = تعذر التحقق (شبكة).
        """
        def probe(r):
            url = r["url"] + "001001.mp3"
            try:
                res = requests.head(
                    url, headers=self.headers, timeout=8, allow_redirects=True
                )
                if res.status_code in (403, 405):
                    res = requests.get(
                        url, headers=self.headers, timeout=8, stream=True
                    )
                    res.close()
                if res.status_code == 200:
                    return r["id"], True
                if res.status_code == 404:
                    print(f"[404] {url}", flush=True)
                    return r["id"], False
                return r["id"], None
            except Exception:
                return r["id"], None

        with ThreadPoolExecutor(max_workers=6) as pool:
            return dict(pool.map(probe, RECITERS))

    # ---------- مصحف المدينة QCF4 ----------
    # ---------- طبقة البيانات: مضمَّن ← كاش محلي ← تنزيل من مستودعك ----------
    def _data_path(self, rel, download=True, timeout=180):
        """مسار ملف من مستودع البيانات. يُنزَّل مرة واحدة ويُحفظ في الكاش."""
        if not re.fullmatch(r"[A-Za-z0-9_\-./]+", rel or "") or ".." in rel:
            return None
        parts = rel.split("/")
        for root in _data_roots():
            p = os.path.join(root, *parts)
            if os.path.isfile(p):
                return p
        cache = os.path.join(self.cache_dir, "data", *parts)
        if os.path.isfile(cache) and os.path.getsize(cache) > 0:
            return cache
        if not download or not DATA_BASE:
            return None
        with self._data_lock:
            if os.path.isfile(cache) and os.path.getsize(cache) > 0:
                return cache
            tmp = cache + ".part"
            try:
                os.makedirs(os.path.dirname(cache), exist_ok=True)
                with requests.get(DATA_BASE + rel, headers=self.headers, timeout=timeout, stream=True) as r:
                    if r.status_code != 200:
                        print(f"data {rel}: HTTP {r.status_code}", flush=True)
                        return None
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_content(65536):
                            f.write(chunk)
                os.replace(tmp, cache)
                return cache
            except Exception as e:
                print(f"data {rel}: {e}", flush=True)
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                return None

    def _data_json(self, rel):
        with self._data_lock:
            if rel in self._data_mem:
                return self._data_mem[rel]
            path = self._data_path(rel)
            if not path:
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError):
                if path.startswith(self.cache_dir):        # ملف تالف في الكاش: نحذفه ليُعاد تنزيله
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                return None
            self._data_mem[rel] = data
            return data

    def get_ui_font(self, name):
        """خطوط الواجهة (Amiri...) من مستودعك، لتعمل دون Google Fonts."""
        if name not in UI_FONTS:
            return None
        path = self._data_path("fonts/ui/" + name)
        if not path:
            return None
        with open(path, "rb") as f:
            return {"family": UI_FONTS[name][0], "weight": UI_FONTS[name][1],
                    "mime": "font/ttf", "data": base64.b64encode(f.read()).decode("ascii")}

    def ui_fonts_list(self):
        return [{"name": k, "family": v[0], "weight": v[1]} for k, v in UI_FONTS.items()]

    # ---------- مصحف المدينة QCF4 ----------
    def _qcf_font_path(self, font_name, download=False):
        local = _find_font_file(font_name)             # خط مثبّت على الجهاز
        if local:
            return local
        return self._data_path(f"fonts/qcf4/{font_name}_W.ttf" if font_name != "QCF4_QBSML" else "fonts/qcf4/QCF4_QBSML.ttf",
                               download=download)

    def qcf_info(self):
        """هل خطوط QCF4 متاحة؟ (مثبّتة، أو مضمّنة/محفوظة، أو يمكن تنزيلها من مستودعك)"""
        have = self._qcf_font_path("QCF4_Hafs_01") is not None
        return {"available": have or bool(DATA_BASE),
                "qbsml": self._qcf_font_path("QCF4_QBSML") is not None or bool(DATA_BASE)}

    def get_qcf_font(self, font_name):
        """يعيد الخط مشفرًا base64 (يُحمَّل عند الحاجة فقط، وينزَّل من مستودعك أول مرة)."""
        if not re.fullmatch(r"QCF4_[A-Za-z0-9_]+", str(font_name)):
            return None
        path = self._qcf_font_path(font_name, download=True)
        if not path:
            return None
        ext = path.rsplit(".", 1)[-1].lower()
        mime = {"ttf": "font/ttf", "otf": "font/otf",
                "woff": "font/woff", "woff2": "font/woff2"}[ext]
        with open(path, "rb") as f:
            return {"mime": mime, "data": base64.b64encode(f.read()).decode("ascii")}

    def _pages_doc(self):
        doc = self._data_json("mushaf/qcf4_pages.json")
        if doc and doc.get("format") == "qcf4-pages/1" and len(doc.get("data", {})) == 604:
            return doc
        return None

    def _qcf_page(self, n):
        doc = self._pages_doc()
        return doc["data"].get(str(n)) if doc else None

    def _qcf_index(self):
        """فهرس السور بالشكل القديم {"chapters": [...]} مبنيًا على meta/chapters.json في مستودعك."""
        ch = self._data_json("meta/chapters.json")
        if not ch:
            return None
        return {"chapters": [{"id": c["id"], "name_arabic": c["name_plain"], "name": c["name_en"],
                              "verses_count": c["ayahs"], "pages": [c["page_start"], c["page_end"]]}
                             for c in ch]}

    def _qcf_chapter_pages(self, surah):
        idx = self._qcf_index()
        if not idx:
            return None
        for ch in idx.get("chapters", []):
            if ch.get("id") == surah:
                return ch.get("pages")
        return None

    def get_navigation(self):
        """الأجزاء والأرباع (من meta) لقوائم التنقل في المصحف."""
        juz = self._data_json("meta/juz.json")
        rub = self._data_json("meta/hizb_rub.json")
        if not juz or not rub:
            return None
        return {"juz": juz, "rub": rub}

    def data_version(self):
        m = self._data_json("manifest.json")
        return (m or {}).get("dataset_version", "")

    def _fetch_qcf(self, surah):
        """
        يبني آيات السورة برموز QCF4:
        {"ayahs": {"1": [{"c": رمز, "f": خط, "e": هل علامة نهاية}], ...},
         "bismillah": [{"c":..., "f":...}], "fonts": [...]}
        """
        if not self.qcf_info()["available"]:
            return None
        rng = self._qcf_chapter_pages(surah)
        if not rng:
            return None
        pages = list(range(rng[0], rng[1] + 1))
        with ThreadPoolExecutor(max_workers=8) as pool:
            data = list(pool.map(self._qcf_page, pages))
        if any(d is None for d in data):
            return None

        ayahs, bismillah, fonts = {}, [], []
        for page in data:
            for line in page.get("lines", []):
                for w in line.get("words", []):
                    t = w.get("type")
                    item = {"c": w["char"], "f": w["font"]}
                    if t == "bismillah" and w.get("sura") == surah:
                        bismillah.append(item)
                    elif t in ("word", "end"):
                        key = w.get("verse_key", "")
                        sura, _, ayah = key.partition(":")
                        if sura == str(surah):
                            item["e"] = (t == "end")
                            ayahs.setdefault(ayah, []).append(item)
                    else:
                        continue
                    if w["font"] not in fonts:
                        fonts.append(w["font"])
        return {"ayahs": ayahs, "bismillah": bismillah, "fonts": fonts}

    # ---------- معلومات التطبيق والتخزين ----------
    def _compose_url(self, subject="", body=""):
        """رابط كتابة رسالة جاهزة: Gmail/Outlook/Yahoo على الويب مباشرة، وغيرها عبر mailto."""
        em = (APP_INFO.get("email") or "").strip()
        if not em or "@" not in em:
            return None, None
        domain = em.rsplit("@", 1)[-1].lower()
        to, su, bd = quote(em, safe=""), quote(subject, safe=""), quote(body, safe="")
        if domain in ("gmail.com", "googlemail.com"):
            return ("https://mail.google.com/mail/?view=cm&fs=1"
                    f"&to={to}&su={su}&body={bd}"), "Gmail"
        if domain in ("outlook.com", "hotmail.com", "live.com", "msn.com"):
            return ("https://outlook.live.com/mail/0/deeplink/compose"
                    f"?to={to}&subject={su}&body={bd}"), "Outlook"
        if domain.startswith("yahoo."):
            return (f"https://compose.mail.yahoo.com/?to={to}&subject={su}&body={bd}"), "Yahoo"
        return f"mailto:{em}?subject={su}&body={bd}", "mailto"

    def compose_email(self, subject, body):
        """يفتح واجهة كتابة رسالة إلى بريد التطبيق وفيها نص المستخدم."""
        url, provider = self._compose_url(str(subject or "")[:200], str(body or "")[:3500])
        if not url:
            return {"ok": False, "provider": None}
        return {"ok": self.open_link(url), "provider": provider}

    def app_info(self):
        info = dict(APP_INFO)
        info["platform"] = f"{platform.system()} {platform.release()}"
        contacts = []
        em = (APP_INFO.get("email") or "").strip()
        if em:
            url, _ = self._compose_url("", "")
            if url:
                contacts.append({"id": "email", "label": "البريد الإلكتروني",
                                 "icon": "✉️", "text": em, "url": url})
        tg = (APP_INFO.get("telegram") or "").strip()
        if tg:
            url = tg if tg.startswith("http") else "https://t.me/" + tg.lstrip("@")
            contacts.append({"id": "telegram", "label": "تيليجرام",
                             "icon": "✈️", "text": "", "url": url})
        wa = (APP_INFO.get("whatsapp") or "").strip()
        if wa:
            if wa.startswith("http"):
                url = wa
            else:
                digits = re.sub(r"\D", "", wa)
                url = ("https://wa.me/" + digits) if digits else ""
            if url:
                contacts.append({"id": "whatsapp", "label": "واتساب", "icon": "💬",
                                 "text": "", "url": url})
        form = (APP_INFO.get("form") or "").strip()
        if form:
            contacts.append({"id": "form", "label": "نموذج الاقتراحات", "icon": "📝",
                             "text": "", "url": form if form.startswith("http") else "https://" + form})
        web = (APP_INFO.get("website") or "").strip()
        if web:
            url = web if web.startswith("http") else "https://" + web
            contacts.append({"id": "website", "label": "الموقع الإلكتروني",
                             "icon": "🌐", "text": "", "url": url})
        info["contacts"] = contacts
        # لا نرسل البريد/الأرقام للواجهة إلا عند الحاجة (زر الإرسال يمر عبر compose_email)
        info["has_email"] = bool(em)
        for k in ("email", "telegram", "whatsapp", "form", "website"):
            info.pop(k, None)
        return info

    def open_link(self, url):
        url = str(url or "")
        if not re.match(r"^(https?://|mailto:)", url):
            return False
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False

    def storage_info(self):
        def folder(path):
            n = b = 0
            for root, _, files in os.walk(path):
                for f in files:
                    try:
                        b += os.path.getsize(os.path.join(root, f))
                        n += 1
                    except OSError:
                        pass
            return n, b
        cf, cb = folder(self.cache_dir)
        af, ab = folder(self.audio_dir)
        return {"cache_files": cf, "cache_bytes": cb, "audio_files": af,
                "audio_bytes": ab, "cache_path": self.cache_dir,
                "audio_path": self.audio_dir}

    def clear_cache(self):
        """يمسح الكاش المؤقت (صفحات المصحف والسور) ويُبقي الإعدادات والصوتيات المحمّلة."""
        n = 0
        dd = os.path.join(self.cache_dir, "data")
        if os.path.isdir(dd):
            for _r, _d, files in os.walk(dd):
                n += len(files)
            shutil.rmtree(dd, ignore_errors=True)
        self._data_mem.clear()
        self._tafsir_idx.clear()
        for name in os.listdir(self.cache_dir):
            path = os.path.join(self.cache_dir, name)
            if name == "settings.json" or not os.path.isfile(path):
                continue
            try:
                os.remove(path)
                n += 1
            except OSError:
                pass
        return n

    def reset_settings(self):
        try:
            os.remove(self.settings_file)
        except OSError:
            pass
        return True

    # ---------- الصوت دون إنترنت ----------
    def _reciter_by_id(self, rid):
        return next((r for r in RECITERS if r["id"] == rid), None)

    def get_audio(self, rid, s, a):
        """يعيد ملف آية محمّلًا (base64) إن وُجد، وإلا None فيُستخدم الرابط على الإنترنت."""
        if not self._reciter_by_id(rid):
            return None
        try:
            path = os.path.join(self.audio_dir, rid, f"{int(s):03d}{int(a):03d}.mp3")
            if os.path.getsize(path) > 1000:
                with open(path, "rb") as f:
                    return {"mime": "audio/mpeg",
                            "data": base64.b64encode(f.read()).decode("ascii")}
        except (OSError, TypeError, ValueError):
            pass
        return None

    def offline_summary(self):
        out = {}
        for r in RECITERS:
            n = b = 0
            try:
                for e in os.scandir(os.path.join(self.audio_dir, r["id"])):
                    if e.name.endswith(".mp3"):
                        n += 1
                        b += e.stat().st_size
            except OSError:
                pass
            out[r["id"]] = {"files": n, "bytes": b}
        return out

    def offline_status(self):
        return dict(self._off_state)

    def offline_cancel(self):
        self._off_state["cancel"] = True
        return True

    def offline_delete(self, rid):
        if self._off_state["running"] or not self._reciter_by_id(rid):
            return False
        shutil.rmtree(os.path.join(self.audio_dir, rid), ignore_errors=True)
        return True

    def _off_bump(self, key, n=1):
        with self._off_lock:
            self._off_state[key] += n

    def offline_start(self, rid, s_from, s_to):
        r = self._reciter_by_id(rid)
        with self._off_lock:
            if self._off_state["running"]:
                return dict(self._off_state)
        if not r:
            return {"error": "قارئ غير معروف"}
        idx = self._qcf_index()
        if not idx:
            return {"error": "تعذر جلب فهرس السور (تحقق من الاتصال بالإنترنت)"}
        try:
            lo, hi = sorted((int(s_from), int(s_to)))
        except (TypeError, ValueError):
            return {"error": "مجال غير صحيح"}
        counts = {c["id"]: c.get("verses_count", 0) for c in idx.get("chapters", [])}
        tasks = [(s, a) for s in range(lo, hi + 1) for a in range(1, counts.get(s, 0) + 1)]
        with self._off_lock:
            self._off_state.update({"running": True, "cancel": False,
                                    "total": len(tasks), "done": 0, "failed": 0,
                                    "missing": 0, "bytes": 0, "reciter": rid,
                                    "error": None})
        threading.Thread(target=self._offline_worker, args=(r, tasks),
                         daemon=True).start()
        return dict(self._off_state)

    def _offline_worker(self, r, tasks):
        st = self._off_state
        folder = os.path.join(self.audio_dir, r["id"])
        os.makedirs(folder, exist_ok=True)

        def job(t):
            try:
                if st["cancel"]:
                    return
                name = f"{t[0]:03d}{t[1]:03d}.mp3"
                path = os.path.join(folder, name)
                if os.path.exists(path) and os.path.getsize(path) > 1000:
                    return
                for _ in range(3):
                    if st["cancel"]:
                        return
                    try:
                        res = requests.get(r["url"] + name, headers=self.headers,
                                           timeout=30)
                        if res.status_code == 404:
                            self._off_bump("missing")
                            return
                        body = res.content
                        if (res.status_code == 200 and len(body) > 1000
                                and body[:1] != b"<"):
                            tmp = path + ".part"
                            with open(tmp, "wb") as f:
                                f.write(body)
                            os.replace(tmp, path)
                            self._off_bump("bytes", len(body))
                            return
                    except Exception:
                        pass
                self._off_bump("failed")
            finally:
                self._off_bump("done")

        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(job, tasks))
        except Exception as e:
            st["error"] = str(e)
        finally:
            st["running"] = False

    # ---------- بيانات المستخدم: المراجعة المتباعدة، العلامات، الورد اليومي ----------
    def _user_load(self):
        d = self._read_json(self.user_file) or {}
        d.setdefault("srs", {})
        d.setdefault("bookmarks", [])
        d.setdefault("wird", {"target": 2, "log": {}})
        d.setdefault("analytics", {"consent": None, "id": None, "last_ping": 0})
        return d

    def _user_save(self, d):
        tmp = self.user_file + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False)
            os.replace(tmp, self.user_file)
        except OSError as e:
            print(f"userdata save error: {e}", flush=True)

    def srs_record(self, key, known):
        """يسجّل نتيجة آية في الاختبار ويحسب موعد مراجعتها القادمة."""
        key = str(key)
        now = time.time()
        with self._user_lock:
            d = self._user_load()
            e = d["srs"].get(key) or {"box": 0, "right": 0, "wrong": 0}
            if known:
                e["right"] += 1
                e["box"] = min(e["box"] + 1, len(SRS_STEPS) - 1)
            else:
                e["wrong"] += 1
                e["box"] = 0
            e["due"] = now + SRS_STEPS[e["box"]]
            e["last"] = now
            d["srs"][key] = e
            self._user_save(d)
        return self.srs_summary()

    def srs_summary(self):
        now = time.time()
        srs = self._user_load()["srs"]
        return {"seen": len(srs),
                "due": sum(1 for e in srs.values() if e.get("due", 0) <= now),
                "weak": sum(1 for e in srs.values() if e.get("box", 0) <= 1 and e.get("wrong", 0) > 0),
                "mastered": sum(1 for e in srs.values() if e.get("box", 0) >= 4)}

    def srs_pick_due(self, s_from, s_to, exclude=None):
        """آية مستحقة للمراجعة داخل المجال (الأقدم استحقاقًا أولًا)، أو None."""
        try:
            lo, hi = sorted((int(s_from), int(s_to)))
        except (TypeError, ValueError):
            lo, hi = 1, 114
        now = time.time()
        skip = set(exclude or [])
        due = []
        for k, e in self._user_load()["srs"].items():
            try:
                sura = int(k.split(":")[0])
            except ValueError:
                continue
            if lo <= sura <= hi and e.get("due", 0) <= now and k not in skip:
                due.append((e.get("due", 0), k))
        if not due:
            return None
        due.sort()
        return self.get_verse(random.choice(due[:5])[1])

    def srs_reset(self):
        with self._user_lock:
            d = self._user_load()
            d["srs"] = {}
            self._user_save(d)
        return self.srs_summary()

    def bookmarks_list(self):
        return sorted(self._user_load()["bookmarks"], key=lambda b: -b.get("t", 0))

    def bookmark_add(self, key, page):
        with self._user_lock:
            d = self._user_load()
            if not any(b["k"] == key for b in d["bookmarks"]):
                d["bookmarks"].append({"k": str(key), "page": int(page), "t": time.time()})
                self._user_save(d)
        return self.bookmarks_list()

    def bookmark_remove(self, key):
        with self._user_lock:
            d = self._user_load()
            d["bookmarks"] = [b for b in d["bookmarks"] if b["k"] != key]
            self._user_save(d)
        return self.bookmarks_list()

    def wird_get(self):
        w = self._user_load()["wird"]
        target = max(1, int(w.get("target", 2)))
        log = w.get("log", {})
        today = datetime.date.today()
        pages = log.get(today.isoformat(), [])
        day = today if len(pages) >= target else today - datetime.timedelta(days=1)
        streak = 0
        while len(log.get(day.isoformat(), [])) >= target:
            streak += 1
            day -= datetime.timedelta(days=1)
        return {"target": target, "today": sorted(pages), "done": len(pages),
                "streak": streak, "days": len(log)}

    def wird_set_target(self, n):
        try:
            n = max(1, min(604, int(n)))
        except (TypeError, ValueError):
            n = 2
        with self._user_lock:
            d = self._user_load()
            d["wird"]["target"] = n
            self._user_save(d)
        return self.wird_get()

    def wird_mark(self, page, done):
        today = datetime.date.today().isoformat()
        with self._user_lock:
            d = self._user_load()
            log = d["wird"].setdefault("log", {})
            pages = set(log.get(today, []))
            (pages.add if done else pages.discard)(int(page))
            log[today] = sorted(pages)
            self._user_save(d)
        return self.wird_get()

    # ---------- عدّاد المستخدمين المجهول (بموافقة المستخدم فقط) ----------
    def analytics_state(self):
        a = self._user_load()["analytics"]
        return {"enabled": bool(ANALYTICS_URL), "consent": a.get("consent"),
                "id": a.get("id") or ""}

    def analytics_set(self, consent):
        """يحفظ اختيار المستخدم. عند الموافقة يُنشأ معرّف عشوائي؛ وعند الرفض يُمسح."""
        with self._user_lock:
            d = self._user_load()
            a = d["analytics"]
            a["consent"] = bool(consent)
            if consent:
                if not a.get("id"):
                    a["id"] = uuid.uuid4().hex
            else:
                a["id"] = None
                a["last_ping"] = 0
            self._user_save(d)
        return self.analytics_state()

    def analytics_ping(self):
        """يرسل (مرة كل يوم على الأكثر) المعرّف العشوائي ورقم الإصدار واسم النظام فقط."""
        if not ANALYTICS_URL:
            return {"sent": False, "reason": "disabled"}
        d = self._user_load()
        a = d["analytics"]
        if a.get("consent") is not True or not a.get("id"):
            return {"sent": False, "reason": "no-consent"}
        now = time.time()
        if now - a.get("last_ping", 0) < 20 * 3600:
            return {"sent": False, "reason": "recent"}
        payload = {"id": a["id"], "v": str(APP_INFO.get("version", ""))[:20],
                   "os": platform.system()[:20]}
        try:
            r = requests.post(ANALYTICS_URL, json=payload, timeout=8)
            ok = 200 <= r.status_code < 300
        except Exception:
            ok = False
        if ok:
            with self._user_lock:
                d = self._user_load()
                d["analytics"]["last_ping"] = now
                self._user_save(d)
        return {"sent": ok, "payload": payload}

    # ---------- ما الجديد ----------
    def get_changelog(self):
        return CHANGELOG

    def whatsnew_state(self):
        cur = str(APP_INFO.get("version", "0"))
        with self._user_lock:
            d = self._user_load()
            last = d.get("last_seen_version")
            if last is None and self._fresh_install:      # تثبيت جديد: لا نزعجه بما هو «جديد»
                d["last_seen_version"] = last = cur
                self._user_save(d)
        return {"current": cur, "last_seen": last or "0.0.0",
                "has_new": _ver(last or "0.0.0") < _ver(cur)}

    def whatsnew_mark_seen(self):
        with self._user_lock:
            d = self._user_load()
            d["last_seen_version"] = str(APP_INFO.get("version", "0"))
            self._user_save(d)
        return True

    # ---------- مشغّل المتون: ملفات صوتية من جهازك ----------
    def _ensure_media_server(self):
        with self._media_lock:
            if self._media_srv is None:
                srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _MediaHandler)
                srv.files = self._local_files
                srv.daemon_threads = True
                threading.Thread(target=srv.serve_forever, daemon=True).start()
                self._media_srv = srv
            return self._media_srv.server_address[1]

    def _local_state(self, d):
        return d.setdefault("local_audio", {"files": [], "settings": {}})

    def _local_public(self, entry):
        port = self._ensure_media_server()
        exists = os.path.isfile(entry["path"])
        tok = self._tokens.get(entry["id"])
        if not tok:
            tok = secrets.token_hex(12)
            self._tokens[entry["id"]] = tok
        if exists:
            self._local_files[tok] = entry["path"]
        return {"id": entry["id"], "name": entry["name"], "exists": exists,
                "pos": entry.get("pos", 0), "segments": entry.get("segments", []),
                "url": f"http://127.0.0.1:{port}/a/{tok}"}

    def local_audio_list(self):
        d = self._user_load()
        return [self._local_public(e) for e in self._local_state(d)["files"]]

    def local_audio_add(self, paths):
        """يضيف ملفات صوتية إلى مكتبة المتون (يتجاهل غير المدعوم والمكرر)."""
        added = 0
        with self._user_lock:
            d = self._user_load()
            lib = self._local_state(d)["files"]
            known = {e["id"] for e in lib}
            for p in paths or []:
                p = os.path.abspath(str(p))
                ext = os.path.splitext(p)[1].lower()
                fid = hashlib.sha1(p.lower().encode("utf-8")).hexdigest()[:12]
                if ext in AUDIO_MIME and os.path.isfile(p) and fid not in known:
                    lib.append({"id": fid, "path": p,
                                "name": os.path.splitext(os.path.basename(p))[0],
                                "pos": 0, "segments": [], "added": time.time()})
                    known.add(fid)
                    added += 1
            lib.sort(key=lambda e: e["name"].lower())
            self._user_save(d)
        return {"added": added, "items": self.local_audio_list()}

    def _file_dialog(self, folder=False):
        try:
            win = webview.windows[0]
            if folder:
                kind = getattr(getattr(webview, "FileDialog", None), "FOLDER", None) or webview.FOLDER_DIALOG
                return list(win.create_file_dialog(kind) or []), None
            kind = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            res = win.create_file_dialog(
                kind, allow_multiple=True,
                file_types=("Audio files (*.mp3;*.wav;*.ogg;*.m4a;*.aac;*.flac;*.opus)", "All files (*.*)"))
            return list(res or []), None
        except Exception as e:
            return [], str(e)

    def local_audio_pick(self):
        paths, err = self._file_dialog(False)
        out = self.local_audio_add(paths)
        out["error"] = err
        return out

    def local_audio_pick_folder(self):
        folders, err = self._file_dialog(True)
        paths = []
        for f in folders:
            for root, _, files in os.walk(f):
                for name in files:
                    if os.path.splitext(name)[1].lower() in AUDIO_MIME:
                        paths.append(os.path.join(root, name))
                if len(paths) > 2000:
                    break
        out = self.local_audio_add(sorted(paths))
        out["error"] = err
        return out

    def local_audio_remove(self, fid):
        with self._user_lock:
            d = self._user_load()
            st = self._local_state(d)
            st["files"] = [e for e in st["files"] if e["id"] != fid]
            self._user_save(d)
        tok = self._tokens.pop(fid, None)
        if tok:
            self._local_files.pop(tok, None)
        return self.local_audio_list()

    def local_audio_update(self, fid, patch):
        """يحفظ موضع التوقف والمقاطع المسمّاة لملف (بعد التحقق من القيم)."""
        if not isinstance(patch, dict):
            return False
        with self._user_lock:
            d = self._user_load()
            for e in self._local_state(d)["files"]:
                if e["id"] != fid:
                    continue
                if "pos" in patch:
                    try:
                        e["pos"] = max(0.0, float(patch["pos"]))
                    except (TypeError, ValueError):
                        pass
                if "segments" in patch and isinstance(patch["segments"], list):
                    segs = []
                    for sg in patch["segments"][:100]:
                        try:
                            a, b = float(sg["a"]), float(sg["b"])
                            if 0 <= a < b:
                                segs.append({"name": str(sg.get("name", ""))[:60], "a": a, "b": b})
                        except (TypeError, ValueError, KeyError):
                            continue
                    e["segments"] = segs
                self._user_save(d)
                return True
        return False

    def local_audio_settings(self, new=None):
        allowed = {"speed": (0.25, 4.0), "repeat": (0, 99), "gap": (0, 60), "volume": (0, 1)}
        with self._user_lock:
            d = self._user_load()
            st = self._local_state(d)["settings"]
            if isinstance(new, dict):
                for k, (lo, hi) in allowed.items():
                    if k in new:
                        try:
                            st[k] = min(hi, max(lo, float(new[k])))
                        except (TypeError, ValueError):
                            pass
                for k in ("autoNext", "loopAll", "pitch"):
                    if k in new:
                        st[k] = bool(new[k])
                self._user_save(d)
            return dict(st)

    # ---------- التفسير ----------
    def tafsir_editions(self):
        return [{"id": k, "label": v} for k, v in TAFSIR_EDITIONS.items()]

    def get_tafsir(self, slug, surah):
        """نص التفسير لكل آية في السورة: {"1": "...", ...} أو None عند تعذر الجلب."""
        if slug not in TAFSIR_EDITIONS:
            return None
        try:
            surah = int(surah)
        except (TypeError, ValueError):
            return None
        with self._data_lock:
            idx = self._tafsir_idx.get(slug)
            if idx is None:
                doc = self._data_json(f"tafsir/{slug}.json")
                if not doc or "ayahs" not in doc:
                    return None
                idx = {}
                for k, text in doc["ayahs"].items():
                    sv, _, av = k.partition(":")
                    idx.setdefault(int(sv), {})[av] = text
                self._tafsir_idx[slug] = idx
        return idx.get(surah, {})

    # ---------- نافذة التطبيق ----------
    def set_window_mode(self, mini):
        """الوضع المصغّر: نافذة صغيرة فوق النوافذ الأخرى. يعود للتكبير عند الإيقاف."""
        try:
            win = webview.windows[0]
            if mini:
                try:
                    win.restore()
                except Exception:
                    pass
                win.resize(520, 300)
                try:
                    win.on_top = True
                except Exception:
                    pass
            else:
                try:
                    win.on_top = False
                except Exception:
                    pass
                win.maximize()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ---------- المصحف والبحث والاختبار ----------
    def get_chapters(self):
        idx = self._qcf_index()
        if not idx:
            return []
        return [{"id": c["id"], "name": c.get("name_arabic", ""),
                 "en": c.get("name", ""), "verses": c.get("verses_count", 0),
                 "pages": c.get("pages", [1, 1])}
                for c in idx.get("chapters", [])]

    def get_page(self, n):
        """صفحة من المصحف (1..604): أسطر وكلمات برموز الخط ونصها."""
        try:
            n = int(n)
        except (TypeError, ValueError):
            return None
        if not 1 <= n <= 604:
            return None
        page = self._qcf_page(n)
        if not page:
            return None
        fonts, lines = [], []
        for line in page.get("lines", []):
            words = []
            for w in line.get("words", []):
                words.append({"c": w.get("char", ""), "f": w.get("font", ""),
                              "t": w.get("type", ""), "x": w.get("text", ""),
                              "s": w.get("sura"), "k": w.get("verse_key")})
                if w.get("font") and w["font"] not in fonts:
                    fonts.append(w["font"])
            lines.append({"n": line.get("line"), "w": words})
        return {"page": n, "lines": lines, "fonts": fonts,
                "surahs": page.get("surahs", [])}

    # --- بيانات كل الآيات ---
    def start_corpus(self):
        """يبدأ (مرة واحدة) تحميل صفحات المصحف الـ604 وبناء فهرس الآيات."""
        with self._corpus_lock:
            st = self._corpus_state
            if st["ready"] or st["running"]:
                return dict(st)
            st.update({"running": True, "error": None, "done": 0})
        threading.Thread(target=self._build_corpus, daemon=True).start()
        return dict(self._corpus_state)

    def corpus_status(self):
        return dict(self._corpus_state)

    def _build_corpus(self):
        st = self._corpus_state
        try:
            if not self._qcf_index():
                raise RuntimeError("تعذر جلب فهرس المصحف (تحقق من الاتصال بالإنترنت)")

            def load(n):
                d = self._qcf_page(n)
                st["done"] += 1
                return d

            with ThreadPoolExecutor(max_workers=16) as pool:
                pages = list(pool.map(load, range(1, 605)))
            for n in range(1, 605):                     # إعادة محاولة الصفحات الفاشلة
                if pages[n - 1] is None:
                    pages[n - 1] = self._qcf_page(n)
            missing = [n for n, pg in enumerate(pages, 1) if pg is None]
            if missing:
                raise RuntimeError(f"تعذر تحميل {len(missing)} صفحة من المصحف")

            verses, order = {}, []
            for n, page in enumerate(pages, 1):
                for line in page.get("lines", []):
                    for w in line.get("words", []):
                        t = w.get("type")
                        key = w.get("verse_key")
                        if t not in ("word", "end") or not key:
                            continue
                        v = verses.get(key)
                        if v is None:
                            sura, _, ayah = key.partition(":")
                            v = {"k": key, "s": int(sura), "a": int(ayah),
                                 "page": n, "words": [], "parts": []}
                            verses[key] = v
                            order.append(key)
                        v["words"].append({"c": w["char"], "f": w["font"],
                                           "e": t == "end"})
                        if t == "word":
                            v["parts"].append(w.get("text", ""))
            first = {}
            for i, key in enumerate(order):
                v = verses[key]
                v["i"] = i
                v["text"] = " ".join(v.pop("parts"))
                v["norm"] = _skeleton(v["text"])
                first.setdefault(v["s"], i)
            first[115] = len(order)

            self._verses, self._order, self._first_idx = verses, order, first
            st["ready"] = True
        except Exception as e:
            st["error"] = str(e)
        finally:
            st["running"] = False

    def _verse_out(self, v, with_words=False):
        out = {"k": v["k"], "s": v["s"], "a": v["a"], "i": v["i"],
               "page": v["page"], "text": v["text"]}
        if with_words:
            out["words"] = v["words"]
        return out

    def search_verses(self, query, limit=60):
        if not self._corpus_state["ready"]:
            return {"ready": False}
        q = _skeleton(query)
        if len(q) < 2:
            return {"ready": True, "total": 0, "results": []}
        results, total = [], 0
        for key in self._order:
            v = self._verses[key]
            if q in v["norm"]:
                total += 1
                if len(results) < limit:
                    results.append(self._verse_out(v))
        return {"ready": True, "total": total, "results": results}

    def get_verse(self, key):
        v = self._verses.get(str(key))
        return self._verse_out(v, True) if v else None

    def get_verse_at(self, i):
        try:
            i = int(i)
        except (TypeError, ValueError):
            return None
        if 0 <= i < len(self._order):
            return self._verse_out(self._verses[self._order[i]], True)
        return None

    def random_verse(self, s_from, s_to, seen=None):
        """آية عشوائية من السور [s_from..s_to]، مع تجنّب ما سُئل مؤخرًا قدر الإمكان."""
        try:
            s_from, s_to = int(s_from), int(s_to)
        except (TypeError, ValueError):
            return None
        if s_from > s_to:
            s_from, s_to = s_to, s_from
        a = self._first_idx.get(s_from)
        b = self._first_idx.get(s_to + 1)
        if a is None or b is None or a >= b:
            return None
        seen_set = set(seen or [])
        i = random.randrange(a, b)
        if len(seen_set) < (b - a):
            for _ in range(500):
                if i not in seen_set:
                    break
                i = random.randrange(a, b)
        return self._verse_out(self._verses[self._order[i]], True)

    def load_settings(self):
        return self._read_json(self.settings_file) or {}

    def save_settings(self, data):
        if isinstance(data, dict):
            self._write_json(self.settings_file, data)
        return True

    def fetch_surahs(self):
        """قائمة السور من meta/chapters.json في مستودع بياناتك."""
        ch = self._data_json("meta/chapters.json")
        if not ch:
            return []
        return [{"number": c["id"], "name": c["name_ar"], "englishName": c["name_en"],
                 "numberOfAyahs": c["ayahs"]} for c in ch]

    def fetch_surah_verses(self, surah_number):
        """
        آيات السورة من بيانات صفحات المصحف نفسها (فلا يعتمد التطبيق على أي موقع آخر). يعيد:
        {"ayahs": [{"numberInSurah", "text"}], "bismillah": True/False, "qcf": ...}
        البسملة ليست جزءًا من نص الآية 1 في هذه البيانات، فتُعرض بطاقةً مستقلة (إلا الفاتحة والتوبة).
        """
        surah_number = int(surah_number)
        rng = self._qcf_chapter_pages(surah_number)
        if not rng:
            return None
        texts, prefix = {}, f"{surah_number}:"
        for n in range(rng[0], rng[1] + 1):
            page = self._qcf_page(n)
            if not page:
                return None
            for line in page.get("lines", []):
                for w in line.get("words", []):
                    k = w.get("verse_key")
                    if w.get("type") == "word" and k and k.startswith(prefix):
                        texts.setdefault(int(k.split(":")[1]), []).append(w.get("text", ""))
        if not texts:
            return None
        result = {"ayahs": [{"numberInSurah": a, "text": " ".join(ws)} for a, ws in sorted(texts.items())],
                  "bismillah": surah_number not in (1, 9)}
        try:
            result["qcf"] = self._fetch_qcf(surah_number)
        except Exception as e:
            print(f"QCF error: {e}", flush=True)
            result["qcf"] = None
        return result

    @staticmethod
    def _strip_bismillah(ayahs, surah_number):
        ayahs = [dict(a) for a in ayahs]  # نسخة، لا نعدّل الكاش
        # الفاتحة: البسملة آية حقيقية. التوبة: بلا بسملة.
        if surah_number in (1, 9) or not ayahs:
            return {"ayahs": ayahs, "bismillah": False}

        words = ayahs[0].get("text", "").split()
        if len(words) > 4 and _plain(words[0]).lstrip("\ufeff").startswith("بسم"):
            ayahs[0]["text"] = " ".join(words[4:])
            return {"ayahs": ayahs, "bismillah": True}
        return {"ayahs": ayahs, "bismillah": surah_number != 9}


# =========================================================
# 2. طبقة الواجهة (HTML5 / CSS3 / JAVASCRIPT FRONTEND LAYER)
# =========================================================
HTML_UI_CONTENT = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>مقرأة القرآن الكريم</title>

    <style>
        /*LOCAL_FONT_CSS*/
        :root { --ayah-font: "Amiri Quran", "Amiri", serif; --ayah-size: 28px; }
        * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }

        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background-color: #f4f7f6;
            color: #2d3436;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        #sidebar {
            width: 280px;
            background-color: #ffffff;
            border-left: 1px solid #e1e8ed;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }
        #sidebar h2 {
            padding: 16px;
            background-color: #1b4332;
            color: #fff;
            font-size: 18px;
            text-align: center;
        }
        #surah-search {
            margin: 10px;
            padding: 9px 12px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            font-size: 14px;
            user-select: text;
        }
        #surah-list { list-style: none; overflow-y: auto; flex-grow: 1; }
        #surah-list li {
            padding: 11px 18px;
            border-bottom: 1px solid #f1f2f6;
            cursor: pointer;
            transition: background 0.2s;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            gap: 8px;
        }
        #surah-list li small { color: #94a3b8; font-weight: 400; }
        #surah-list li:hover { background-color: #d8f3dc; }
        #surah-list li.active { background-color: #2d6a4f; color: #fff; }
        #surah-list li.active small { color: #d8f3dc; }

        #main-content {
            flex-grow: 1;
            min-width: 0;
            min-height: 0;
            display: flex;
            flex-direction: column;
            background-color: #fafbfc;
        }
        #ayah-container {
            flex-grow: 1;
            padding: 24px 30px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .placeholder {
            text-align: center; margin-top: 50px; color: #64748b; font-size: 18px;
        }
        .bismillah {
            text-align: center;
            font-family: var(--ayah-font);
            font-size: calc(var(--ayah-size) + 6px);
            color: #1b4332;
            padding: 6px 0 10px;
        }
        .ayah-card {
            background-color: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px 20px;
            font-family: var(--ayah-font);
            font-size: var(--ayah-size);
            line-height: 2.3;
            color: #1e293b;
            cursor: pointer;
            /* لا نستخدم transition: all حتى لا يتأخر تغيّر حجم الخط أثناء ملاءمة الآية للإطار */
            transition: border-color 0.25s ease, transform 0.25s ease, background-color 0.25s ease, box-shadow 0.25s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .ayah-card:hover { border-color: #52b788; transform: translateY(-1px); }
        .ayah-card.in-range { border-right: 5px solid #95d5b2; }
        .ayah-card.playing {
            background-color: #d8f3dc;
            border: 2px solid #2d6a4f;
            box-shadow: 0 4px 12px rgba(45, 106, 79, 0.15);
        }
        /* inline-block: يتيح للمتصفح نقل الكلمة إلى سطر جديد (لا توجد مسافات بين رموز QCF4) */
        .qw { display: inline-block; margin-inline: 0.1em; white-space: nowrap; }
        .ayah-card { overflow-wrap: break-word; min-width: 0; }

        /* وضع الآية الواحدة: تظهر الآية المتلوة فقط، كبيرة وفي الوسط */
        .focus-hint { display: none; text-align: center; margin: auto; color: #64748b; font-size: 18px; }
        #ayah-container.focus-mode .ayah-card:not(.playing),
        #ayah-container.focus-mode .bismillah { display: none; }
        #ayah-container.focus-mode.no-playing .focus-hint { display: block; }
        #ayah-container.focus-mode .ayah-card.playing {
            margin-block: auto;
            text-align: center;
            font-size: calc(var(--ayah-size) * 1.45);
            padding: 28px 30px;
        }
        #ayah-container.focus-mode .ayah-card.playing:hover { transform: none; }
        /* رموز QCF4 تقع في منطقة الاستخدام الخاص (PUA) وهي تُعامل كحروف LTR افتراضيًا،
           فنفرض الاتجاه من اليمين لليسار على النص كله */
        .ayah-card.qcf .ayah-text, .bismillah, .glyphs { direction: rtl; unicode-bidi: bidi-override; }
        .ayah-card.qcf { line-height: 2.1; }
        .ayah-number { display: inline-block; color: #2d6a4f; font-weight: bold; margin-inline-start: 10px; }

        /* وضع اختبار الحفظ: إخفاء النص حتى المرور بالمؤشر */
        #ayah-container.hide-text .ayah-text { filter: blur(9px); transition: filter 0.2s; }
        #ayah-container.hide-text .ayah-card:hover .ayah-text { filter: none; }

        #status-bar {
            background-color: #e8f5e9;
            border-top: 1px solid #c8e6c9;
            padding: 10px 20px;
            font-size: 13px;
            color: #1b5e20;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        #status-bar.error { background-color: #ffebee; border-color: #ffcdd2; color: #b71c1c; }
        .url-box { display: flex; gap: 8px; align-items: center; }
        .url-input {
            flex-grow: 1;
            font-family: monospace;
            font-size: 12px;
            padding: 6px 10px;
            border: 1px solid #a5d6a7;
            border-radius: 4px;
            direction: ltr;
            background: #fff;
            color: #333;
            user-select: all;
        }
        .btn-copy {
            background-color: #1b4332; color: #fff; border: none;
            padding: 6px 12px; border-radius: 4px; font-size: 12px;
            cursor: pointer; font-weight: bold;
        }
        .btn-copy:hover { background-color: #2d6a4f; }

        #progress { width: 100%; height: 6px; accent-color: #2d6a4f; cursor: pointer; }

        #controls-bar {
            background-color: #fff;
            border-top: 1px solid #e1e8ed;
            padding: 8px 16px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px 18px;
            flex-shrink: 0;
            max-height: 38vh;
            overflow-y: auto;
        }
        #status-bar { flex-shrink: 0; }
        .ctl { display: flex; align-items: center; gap: 6px; font-size: 14px; }
        .btn {
            background-color: #2d6a4f; color: #fff; border: none;
            padding: 9px 18px; border-radius: 8px; font-weight: bold;
            cursor: pointer; transition: background 0.2s;
        }
        .btn:hover { background-color: #1b4332; }
        select {
            padding: 7px 10px; border-radius: 6px;
            border: 1px solid #cbd5e1; font-size: 14px; background: #fff;
        }
        label.chk { cursor: pointer; display: flex; align-items: center; gap: 5px; }

        /* ===== التبويبات والعروض ===== */
        #topbar { display: flex; align-items: center; gap: 6px; padding: 6px 14px; background: #1b4332; flex-shrink: 0; }
        .tab { background: transparent; color: #d8f3dc; border: none; padding: 8px 20px; border-radius: 8px; font-size: 15px; font-weight: 700; cursor: pointer; }
        .tab:hover { background: #2d6a4f; }
        .tab.active { background: #fff; color: #1b4332; }
        #corpus-status { margin-inline-start: auto; color: #b7e4c7; font-size: 13px; display: flex; gap: 8px; align-items: center; }
        #corpus-status button { background: #fff; color: #1b4332; border: none; border-radius: 6px; padding: 3px 10px; cursor: pointer; font-weight: 700; }
        #views { flex: 1; min-height: 0; display: flex; }
        .view { display: none; flex: 1; min-width: 0; min-height: 0; }
        .view.active { display: flex; }
        .hidden { display: none !important; }
        .btn.sm { padding: 6px 12px; font-size: 13px; }
        .btn.alt { background: #fff; color: #1b4332; border: 1px solid #2d6a4f; }
        .btn.alt:hover { background: #d8f3dc; }
        .btn:disabled { opacity: .45; cursor: not-allowed; }

        /* ===== المصحف ===== */
        #mushaf-main { flex: 1; display: flex; flex-direction: column; min-width: 0; min-height: 0; background: #f1ebdd; }
        #mushaf-toolbar { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; padding: 8px 16px; background: #fff; border-bottom: 1px solid #e1e8ed; flex-shrink: 0; position: relative; z-index: 5; }
        .search-wrap { position: relative; flex: 1 1 320px; min-width: 240px; max-width: 520px; }
        #mushaf-search { width: 100%; padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; user-select: text; }
        #search-results { position: absolute; top: 100%; right: 0; left: 0; margin-top: 4px; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; max-height: 60vh; overflow-y: auto; box-shadow: 0 8px 24px rgba(0,0,0,.15); z-index: 20; }
        .res-head { padding: 6px 12px; background: #f1f5f9; color: #475569; font-size: 12px; font-weight: 700; }
        .res-item { padding: 9px 12px; border-bottom: 1px solid #f1f2f6; cursor: pointer; }
        .res-item:hover { background: #d8f3dc; }
        .res-item b { font-size: 13px; color: #1b4332; }
        .res-text { font-family: var(--ayah-font); font-size: 19px; line-height: 1.9; color: #1e293b; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .res-note { padding: 12px; color: #64748b; font-size: 13px; }
        #mushaf-page-input { width: 70px; padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; text-align: center; font-size: 14px; user-select: text; }
        #mushaf-scroll { flex: 1; min-height: 0; overflow: auto; padding: 16px; display: flex; justify-content: center; align-items: flex-start; }
        #mushaf-page { --ms: 30px; background: #fffdf7; border: 1px solid #e3d9bd; border-radius: 6px; padding: 18px 12px; box-shadow: 0 4px 18px rgba(0,0,0,.1); flex-shrink: 0; }
        .mline { display: flex; align-items: center; justify-content: center; gap: .25em; direction: rtl; white-space: nowrap; line-height: 1.95; min-height: calc(var(--ms) * 1.95); width: 100%; }
        .mline.justify { justify-content: space-between; gap: 0; }
        .mline.measure { width: max-content; justify-content: flex-start; }
        .mw { font-size: var(--ms); cursor: pointer; border-radius: 4px; padding: 0 1px; }
        .mw.u { font-family: var(--ayah-font); }
        .mw:hover { background: rgba(82,183,136,.18); }
        .mw.sel { background: #b7e4c7; }
        .mheader { padding: 6px 0; }
        .mhead-glyph { font-size: calc(var(--ms) * 1.25); }
        .mhead-fallback { border: 2px solid #b08d57; border-radius: 8px; padding: 2px 46px; background: #f6edd3; color: #5b4520; font-family: var(--ayah-font); font-size: calc(var(--ms) * 1.1); }
        .mbism { font-size: var(--ms); font-family: var(--ayah-font); }
        #mushaf-info { display: flex; align-items: center; gap: 12px; padding: 8px 16px; background: #e8f5e9; border-top: 1px solid #c8e6c9; color: #1b5e20; font-size: 14px; flex-shrink: 0; }

        /* ===== الاختبار ===== */
        #quiz-main { flex: 1; display: flex; flex-direction: column; min-width: 0; min-height: 0; background: #fafbfc; }
        #quiz-setup { margin: 40px auto; max-width: 680px; background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 28px; text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,.05); }
        #quiz-setup h2 { color: #1b4332; margin-bottom: 10px; }
        #quiz-setup p { color: #64748b; margin-bottom: 18px; line-height: 1.8; }
        #quiz-setup .ctl { justify-content: center; flex-wrap: wrap; gap: 10px 14px; }
        #quiz-msg { margin-top: 14px; color: #b45309; font-size: 14px; min-height: 20px; }
        #quiz-play { flex: 1; display: flex; flex-direction: column; min-height: 0; }
        #quiz-toolbar { display: flex; flex-wrap: wrap; gap: 8px 10px; align-items: center; padding: 10px 16px; background: #fff; border-bottom: 1px solid #e1e8ed; flex-shrink: 0; }
        #quiz-stats { margin-inline-start: auto; color: #475569; font-size: 14px; }
        #quiz-stage { flex: 1; min-height: 0; overflow-y: auto; padding: 20px 40px; display: flex; flex-direction: column; gap: 12px; }
        .quiz-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 22px; font-family: var(--ayah-font); font-size: calc(var(--ayah-size) * 1.15); line-height: 2.3; text-align: center; }
        .quiz-card.target { background: #d8f3dc; border: 2px solid #2d6a4f; font-size: calc(var(--ayah-size) * 1.35); box-shadow: 0 4px 12px rgba(45,106,79,.15); }
        .quiz-label { font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 13px; color: #2d6a4f; font-weight: 700; line-height: 1.6; margin-bottom: 4px; }
        .quiz-ph { border: 2px dashed #94a3b8; border-radius: 12px; padding: 24px; text-align: center; color: #64748b; background: repeating-linear-gradient(45deg, #eef2f6, #eef2f6 10px, #e2e8f0 10px, #e2e8f0 20px); cursor: pointer; font-size: 15px; }
        .quiz-ph:hover { border-color: #2d6a4f; color: #2d6a4f; }

        /* ===== القائمة الجانبية ===== */
        #drawer-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.42); z-index: 99; }
        #drawer { position: fixed; top: 0; bottom: 0; right: 0; width: 410px; max-width: 94vw; background: #fff; color: #2d3436; z-index: 100; display: flex; flex-direction: column; box-shadow: -6px 0 28px rgba(0,0,0,.3); }
        .dr-head { background: #1b4332; color: #fff; padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
        .dr-title { font-size: 19px; font-weight: 800; }
        .dr-ver { font-size: 12px; color: #b7e4c7; margin-top: 3px; }
        .dr-close { background: transparent; border: none; color: #fff; font-size: 22px; cursor: pointer; padding: 4px 10px; border-radius: 6px; }
        .dr-close:hover { background: rgba(255,255,255,.15); }
        .dr-body { overflow-y: auto; flex: 1; padding: 10px 12px 24px; }
        .dr-sec { border: 1px solid #e2e8f0; border-radius: 10px; margin-top: 10px; overflow: hidden; }
        .dr-sec > summary { cursor: pointer; padding: 12px 14px; font-weight: 700; background: #f1f5f9; list-style: none; }
        .dr-sec > summary::-webkit-details-marker { display: none; }
        .dr-sec[open] > summary { border-bottom: 1px solid #e2e8f0; }
        .dr-in { padding: 12px 14px; display: flex; flex-direction: column; gap: 10px; font-size: 14px; line-height: 1.8; }
        .dr-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .dr-muted { color: #64748b; font-size: 12.5px; line-height: 1.7; }
        .dr-in textarea { width: 100%; min-height: 90px; padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-family: inherit; font-size: 14px; resize: vertical; user-select: text; }
        .dr-in select { max-width: 100%; }
        .dr-kbd { display: flex; justify-content: space-between; gap: 8px; border-bottom: 1px dashed #e2e8f0; padding: 3px 0; }
        .dr-kbd kbd { background: #eef2f6; border: 1px solid #cbd5e1; border-radius: 5px; padding: 0 7px; font-family: monospace; font-size: 12px; }
        .off-item { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px dashed #e2e8f0; }
        #off-progress { width: 100%; height: 8px; accent-color: #2d6a4f; }
        #theme-btn { background: transparent; border: none; color: #fff; font-size: 18px; cursor: pointer; padding: 4px 10px; border-radius: 8px; }
        #theme-btn:hover { background: #2d6a4f; }
        #toast { position: fixed; bottom: 96px; left: 50%; transform: translateX(-50%); background: #b91c1c; color: #fff; padding: 10px 18px; border-radius: 10px; z-index: 120; font-size: 14px; box-shadow: 0 6px 20px rgba(0,0,0,.3); max-width: 80vw; }

        /* ===== الوضع الليلي ===== */
        body.dark { background: #121614; color: #e7ece9; color-scheme: dark; }
        body.dark #sidebar { background: #1a211e; border-left-color: #2a3530; }
        body.dark #surah-search, body.dark #mushaf-search, body.dark #mushaf-page-input,
        body.dark select, body.dark .url-input, body.dark .dr-in textarea { background: #222c28; color: #e7ece9; border-color: #34423c; }
        body.dark #surah-list li { border-bottom-color: #232d29; }
        body.dark #surah-list li:hover { background: #25382f; }
        body.dark #surah-list li small { color: #7f8f87; }
        body.dark #main-content, body.dark #quiz-main { background: #151a18; }
        body.dark .placeholder { color: #9aa8a1; }
        body.dark .ayah-card, body.dark .quiz-card { background: #1c2320; border-color: #2d3a35; color: #e7ece9; }
        body.dark .ayah-card.playing, body.dark .quiz-card.target { background: #1f3d2f; border-color: #52b788; }
        body.dark .ayah-number, body.dark .quiz-label, body.dark .bismillah { color: #74c69d; }
        body.dark #status-bar { background: #18241e; border-top-color: #25382f; color: #b7e4c7; }
        body.dark #status-bar.error { background: #3a1d1d; border-color: #5c2b2b; color: #fca5a5; }
        body.dark #controls-bar, body.dark #mushaf-toolbar, body.dark #quiz-toolbar { background: #1a211e; border-color: #2a3530; color: #e7ece9; }
        body.dark .btn.alt { background: #1a211e; color: #b7e4c7; border-color: #40916c; }
        body.dark .btn.alt:hover { background: #25382f; }
        body.dark #mushaf-main { background: #101412; }
        body.dark #mushaf-page { background: #1b1f1c; border-color: #2f3a34; color: #ece7da; box-shadow: 0 4px 18px rgba(0,0,0,.5); }
        body.dark .mw:hover { background: rgba(116,198,157,.18); }
        body.dark .mw.sel { background: #2d6a4f; }
        body.dark .mhead-fallback { background: #2a2519; border-color: #8a6d3b; color: #e6d3a3; }
        body.dark #mushaf-info { background: #18241e; border-color: #25382f; color: #b7e4c7; }
        body.dark #search-results { background: #1a211e; border-color: #34423c; }
        body.dark .res-head { background: #222c28; color: #9aa8a1; }
        body.dark .res-item { border-bottom-color: #232d29; }
        body.dark .res-item:hover { background: #25382f; }
        body.dark .res-item b { color: #74c69d; }
        body.dark .res-text, body.dark .res-note { color: #d6dcd8; }
        body.dark #quiz-setup { background: #1a211e; border-color: #2d3a35; }
        body.dark #quiz-setup h2 { color: #74c69d; }
        body.dark #quiz-setup p, body.dark #quiz-stats { color: #9aa8a1; }
        body.dark .quiz-ph { background: repeating-linear-gradient(45deg, #1d2522, #1d2522 10px, #232d29 10px, #232d29 20px); border-color: #475a52; color: #9aa8a1; }
        body.dark #drawer { background: #1a211e; color: #e7ece9; }
        body.dark .dr-sec { border-color: #2d3a35; }
        body.dark .dr-sec > summary { background: #222c28; }
        body.dark .dr-sec[open] > summary { border-bottom-color: #2d3a35; }
        body.dark .dr-muted { color: #9aa8a1; }
        body.dark .dr-kbd, body.dark .off-item { border-bottom-color: #2d3a35; }
        body.dark .dr-kbd kbd { background: #222c28; border-color: #34423c; color: #e7ece9; }

        /* ===== ميزات جديدة ===== */
        .tafsir-text { font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 15px; line-height: 1.9; color: #475569; margin-top: 10px; padding-top: 8px; border-top: 1px dashed #cbd5e1; text-align: start; white-space: pre-line; }
        #mushaf-tafsir { background: #fffdf4; border-top: 1px solid #e3d9bd; padding: 10px 18px; max-height: 26vh; overflow-y: auto; font-size: 15px; line-height: 1.9; color: #3b3b3b; white-space: pre-line; flex-shrink: 0; user-select: text; }
        .bm-wrap { position: relative; }
        #bm-panel { position: fixed; width: 330px; max-height: 50vh; overflow-y: auto; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.18); z-index: 25; margin-top: 4px; }
        .bm-item { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 8px 12px; border-bottom: 1px solid #f1f2f6; cursor: pointer; font-size: 14px; }
        .bm-item:hover { background: #d8f3dc; }
        .chip { background: #e8f5e9; color: #1b5e20; border-radius: 999px; padding: 4px 12px; font-size: 13px; font-weight: 700; }
        .btn.on { background: #b08d57; }
        #sleep-chip { background: #3b82f6; color: #fff; border: none; border-radius: 999px; padding: 4px 12px; font-size: 13px; font-weight: 700; cursor: pointer; margin-inline-start: 8px; }
        #quiz-guess { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        #qg-ayah { width: 80px; padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; user-select: text; }
        #qg-result { font-weight: 700; font-size: 14px; }
        #mini-bar { display: none; }
        body.mini #topbar, body.mini #sidebar, body.mini #status-bar, body.mini #controls-bar,
        body.mini .view:not(#view-recite) { display: none !important; }
        body.mini #mini-bar { display: flex; justify-content: center; align-items: center; gap: 8px; padding: 6px; background: #1b4332; flex-shrink: 0; }
        body.mini #mini-bar button { background: #2d6a4f; color: #fff; border: none; border-radius: 8px; padding: 6px 16px; font-size: 16px; cursor: pointer; }
        body.mini #mini-bar button:hover { background: #40916c; }
        body.mini #ayah-container { padding: 8px; }
        body.mini .tafsir-text { display: none; }
        body.dark .tafsir-text { color: #b6c2bc; border-top-color: #34423c; }
        body.dark #mushaf-tafsir { background: #18201c; border-top-color: #25382f; color: #d6dcd8; }
        body.dark #bm-panel { background: #1a211e; border-color: #34423c; }
        body.dark .bm-item { border-bottom-color: #232d29; }
        body.dark .bm-item:hover { background: #25382f; }
        body.dark .chip { background: #18241e; color: #b7e4c7; }
        #consent-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.55); z-index: 150; display: flex; align-items: center; justify-content: center; padding: 16px; }
        #consent-card { background: #fff; color: #2d3436; border-radius: 14px; max-width: 520px; width: 100%; padding: 22px 24px; box-shadow: 0 12px 40px rgba(0,0,0,.35); line-height: 1.85; font-size: 15px; }
        #consent-card h3 { color: #1b4332; margin-bottom: 8px; }
        #consent-card ul { padding-inline-start: 22px; margin: 6px 0 10px; }
        #consent-card .row { display: flex; gap: 10px; justify-content: flex-start; margin-top: 14px; flex-wrap: wrap; }
        body.dark #consent-card { background: #1a211e; color: #e7ece9; }
        body.dark #consent-card h3 { color: #74c69d; }

        /* ===== ما الجديد + مشغّل المتون ===== */
        #menu-dot { display: inline-block; width: 9px; height: 9px; background: #ef4444; border-radius: 50%; margin-inline-start: 6px; vertical-align: super; }
        .badge { background: #ef4444; color: #fff; border-radius: 999px; padding: 1px 8px; font-size: 11px; margin-inline-start: 8px; }
        .wn-ver { font-weight: 800; color: #1b4332; margin-top: 4px; }
        .wn-ver small { color: #64748b; font-weight: 400; margin-inline-start: 6px; }
        .wn-list { padding-inline-start: 20px; margin: 4px 0 6px; line-height: 1.9; }
        #view-matn { background: #fafbfc; }
        #matn-side { width: 300px; background: #fff; border-left: 1px solid #e1e8ed; display: flex; flex-direction: column; flex-shrink: 0; min-height: 0; }
        .matn-actions { display: flex; gap: 8px; padding: 10px; flex-wrap: wrap; }
        #matn-filter { margin: 0 10px 8px; padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; user-select: text; }
        #matn-list { list-style: none; overflow-y: auto; flex: 1; }
        #matn-list li { padding: 10px 14px; border-bottom: 1px solid #f1f2f6; cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 6px; font-size: 14px; }
        #matn-list li:hover { background: #d8f3dc; }
        #matn-list li.active { background: #2d6a4f; color: #fff; }
        #matn-list li.missing { color: #b91c1c; text-decoration: line-through; }
        #matn-list li button { background: transparent; border: none; cursor: pointer; color: inherit; font-size: 14px; opacity: .7; }
        #matn-main { flex: 1; min-width: 0; overflow-y: auto; padding: 22px 28px; display: flex; flex-direction: column; gap: 14px; }
        .matn-title { font-size: 20px; font-weight: 800; color: #1b4332; }
        .matn-seek { display: flex; align-items: center; gap: 10px; direction: ltr; }
        .matn-seek span { font-family: monospace; font-size: 13px; color: #475569; min-width: 44px; text-align: center; }
        .seek-wrap { position: relative; flex: 1; height: 28px; display: flex; align-items: center; }
        #matn-ab { position: absolute; top: 9px; height: 10px; background: rgba(176,141,87,.45); border-radius: 4px; pointer-events: none; }
        #matn-seek { position: relative; width: 100%; accent-color: #2d6a4f; cursor: pointer; }
        .matn-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .matn-row .btn { min-width: 44px; }
        .matn-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; }
        .matn-card h4 { color: #1b4332; font-size: 14px; }
        .matn-card input[type=number] { width: 64px; padding: 5px; border: 1px solid #cbd5e1; border-radius: 6px; user-select: text; }
        .matn-card input[type=text] { padding: 6px 8px; border: 1px solid #cbd5e1; border-radius: 6px; user-select: text; }
        .speed-val { font-family: monospace; font-weight: 700; min-width: 54px; }
        .seg-item { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 6px 4px; border-bottom: 1px dashed #e2e8f0; cursor: pointer; font-size: 14px; }
        .seg-item:hover { background: #d8f3dc; }
        body.dark #view-matn, body.dark #matn-main { background: #151a18; }
        body.dark #matn-side, body.dark .matn-card { background: #1a211e; border-color: #2d3a35; }
        body.dark #matn-filter, body.dark .matn-card input { background: #222c28; color: #e7ece9; border-color: #34423c; }
        body.dark #matn-list li { border-bottom-color: #232d29; }
        body.dark #matn-list li:hover { background: #25382f; }
        body.dark .matn-title, body.dark .matn-card h4, body.dark .wn-ver { color: #74c69d; }
        body.dark .seg-item { border-bottom-color: #2d3a35; }
        body.dark .seg-item:hover { background: #25382f; }
    </style>
</head>
<body>

    <div id="topbar">
        <button class="tab" id="menu-btn" title="القائمة">☰<span id="menu-dot" class="hidden"></span></button>
        <button class="tab active" data-view="recite">🎧 التلاوة</button>
        <button class="tab" data-view="mushaf">📖 المصحف</button>
        <button class="tab" data-view="quiz">🧠 اختبار</button>
        <button class="tab" data-view="matn">🎙 المتون</button>
        <span id="corpus-status"></span>
        <button id="sleep-chip" class="hidden" title="إلغاء مؤقّت النوم"></button>
        <button id="mini-btn" class="tab" title="الوضع المصغّر (نافذة صغيرة فوق النوافذ)">🗕</button>
        <button id="theme-btn" title="الوضع الليلي / النهاري">🌙</button>
    </div>

    <div id="mini-bar">
        <button id="mini-prev" title="السابقة">⏮</button>
        <button id="mini-play" title="تشغيل / إيقاف">▶</button>
        <button id="mini-next" title="التالية">⏭</button>
        <button id="mini-exit" title="العودة للنافذة الكاملة">⤢</button>
    </div>

    <div id="views">
    <div id="view-recite" class="view active">

    <div id="sidebar">
        <h2>فهرس السور</h2>
        <input id="surah-search" type="text" placeholder="🔍 ابحث عن سورة (اسم أو رقم)">
        <ul id="surah-list"></ul>
    </div>

    <div id="main-content">
        <div id="ayah-container">
            <div class="placeholder">اختر سورة من القائمة للبدء في الاستماع والتحفيظ</div>
        </div>

        <div id="status-bar">
            <div id="status-text">الجاهزية: قم باختيار سورة للبدء</div>
            <div class="url-box">
                <input type="text" id="url-input" class="url-input" readonly placeholder="رابط الصوت المباشر يظهر هنا..." />
                <button class="btn-copy" onclick="copyUrl()">نسخ 📋</button>
            </div>
            <input type="range" id="progress" min="0" max="1000" value="0">
        </div>

        <div id="controls-bar">
            <div class="ctl">
                <button class="btn" id="btn-prev">⏮ السابقة</button>
                <button class="btn" id="btn-play">تشغيل ▶</button>
                <button class="btn" id="btn-next">التالية ⏭</button>
            </div>

            <div class="ctl">
                <label>القارئ:</label>
                <select id="riwaya-select"></select>
            </div>

            <div class="ctl">
                <label>المقطع من آية</label>
                <select id="range-from"></select>
                <label>إلى</label>
                <select id="range-to"></select>
                <label class="chk"><input type="checkbox" id="loop-range"> إعادة المقطع</label>
            </div>

            <div class="ctl">
                <label>تكرار الآية:</label>
                <select id="repeat-select">
                    <option value="1">مرة واحدة</option>
                    <option value="2">مرتان</option>
                    <option value="3">3 مرات</option>
                    <option value="5">5 مرات</option>
                    <option value="10">10 مرات</option>
                    <option value="0">بلا توقف ∞</option>
                </select>
            </div>

            <div class="ctl">
                <label>السرعة:</label>
                <select id="speed-select">
                    <option value="0.75">0.75×</option>
                    <option value="1" selected>1×</option>
                    <option value="1.25">1.25×</option>
                    <option value="1.5">1.5×</option>
                </select>
            </div>

            <div class="ctl">
                <label>الخط:</label>
                <select id="font-select">
                    <option value="amiri-quran">الرسم العثماني (Amiri Quran)</option>
                    <option value="scheherazade">شهرزاد الجديد</option>
                    <option value="amiri">أميري</option>
                </select>
                <select id="size-select">
                    <option value="22">صغير</option>
                    <option value="28" selected>متوسط</option>
                    <option value="36">كبير</option>
                    <option value="44">كبير جدًا</option>
                </select>
            </div>

            <div class="ctl">
                <label class="chk"><input type="checkbox" id="show-status" checked> شريط المعلومات</label>
                <label class="chk"><input type="checkbox" id="focus-only"> عرض الآية المتلوة فقط</label>
                <label class="chk"><input type="checkbox" id="hide-text"> إخفاء النص (اختبار الحفظ)</label>
            </div>
        </div>
    </div>
    </div><!-- /view-recite -->

    <div id="view-mushaf" class="view">
        <div id="mushaf-main">
            <div id="mushaf-toolbar">
                <div class="search-wrap">
                    <input id="mushaf-search" type="text" autocomplete="off" placeholder="🔍 ابحث باسم سورة أو بكلمات من الآيات (أو 2:255)">
                    <div id="search-results" class="hidden"></div>
                </div>
                <select id="mushaf-surah"></select>
                <div class="ctl">
                    <button class="btn sm" id="mp-prev">▶ السابقة</button>
                    <input id="mushaf-page-input" type="number" min="1" max="604" value="1">
                    <span>/ 604</span>
                    <button class="btn sm" id="mp-next">التالية ◀</button>
                </div>
                <div class="ctl">
                    <label>عرض الصفحة:</label>
                    <select id="mushaf-width">
                        <option value="fit" selected>ملائم للشاشة</option>
                        <option value="560">ضيق</option>
                        <option value="720">متوسط</option>
                        <option value="900">عريض</option>
                        <option value="1100">واسع</option>
                    </select>
                </div>
                <div class="ctl">
                    <select id="mushaf-juz"></select>
                    <select id="mushaf-rub" title="الأحزاب والأرباع"></select>
                    <div class="bm-wrap">
                        <button class="btn sm alt" id="bm-add" title="حفظ علامة على الآية المحددة (أو أول آية في الصفحة)">☆ علامة</button>
                        <button class="btn sm alt" id="bm-list">🔖 العلامات (<span id="bm-count">0</span>)</button>
                        <div id="bm-panel" class="hidden"></div>
                    </div>
                </div>
                <div class="ctl">
                    <button class="btn sm" id="mp-play">▶ تلاوة الصفحة</button>
                    <label class="chk"><input type="checkbox" id="mp-auto" checked> متابعة للصفحة التالية</label>
                </div>
                <div class="ctl">
                    <span class="chip" id="wird-chip">📅 الورد: —</span>
                    <button class="btn sm alt" id="wird-btn">✓ قرأتُ هذه الصفحة</button>
                </div>
            </div>
            <div id="mushaf-scroll"><div id="mushaf-page"><div class="placeholder">⌛ جاري التحميل...</div></div></div>
            <div id="mushaf-tafsir" class="hidden"></div>
            <div id="mushaf-info" class="hidden">
                <span id="mushaf-info-text"></span>
                <button class="btn sm" id="mushaf-listen">▶ استماع</button>
                <button class="btn sm alt" id="mushaf-copy">نسخ النص 📋</button>
            </div>
        </div>
    </div>

    <div id="view-quiz" class="view">
        <div id="quiz-main">
            <div id="quiz-setup">
                <h2>🧠 اختبار الحفظ</h2>
                <p>اختر مجال السور. ستظهر لك آية عشوائية منها، وعليك أن تعرف اسم السورة والآية التي قبلها والتي بعدها،
                   ثم تتحقق بأزرار الإظهار.</p>
                <div class="ctl" style="margin-bottom:12px">
                    <label>نمط الاختبار:</label>
                    <select id="quiz-mode">
                        <option value="context">السورة والآيات المجاورة</option>
                        <option value="complete">إكمال الآية من أولها</option>
                        <option value="number">تحديد السورة ورقم الآية</option>
                        <option value="audio">اختبار صوتي (بلا نص)</option>
                    </select>
                    <label class="chk"><input type="checkbox" id="quiz-review"> ركّز على الآيات المستحقة للمراجعة</label>
                </div>
                <div class="ctl">
                    <label>من سورة</label><select id="quiz-from"></select>
                    <label>إلى سورة</label><select id="quiz-to"></select>
                    <button class="btn" id="quiz-start">ابدأ الاختبار</button>
                </div>
                <div class="dr-muted" id="quiz-srs" style="margin-top:12px"></div>
                <div id="quiz-msg"></div>
            </div>
            <div id="quiz-play" class="hidden">
                <div id="quiz-toolbar">
                    <button class="btn sm" id="qz-name">🏷 إظهار اسم السورة</button>
                    <button class="btn sm hidden" id="qz-word">➕ كلمة</button>
                    <button class="btn sm hidden" id="qz-rest">إظهار بقية الآية</button>
                    <button class="btn sm hidden" id="qz-reveal">👁 إظهار الآية</button>
                    <button class="btn sm" id="qz-prev">⬆ إظهار الآية السابقة</button>
                    <button class="btn sm" id="qz-next">⬇ إظهار الآية التالية</button>
                    <button class="btn sm alt" id="qz-listen">🔊 استماع</button>
                    <button class="btn sm" id="qz-yes">✅ عرفتها</button>
                    <button class="btn sm" id="qz-no">❌ لم أعرفها</button>
                    <button class="btn sm alt" id="qz-skip">⏭ آية أخرى</button>
                    <span id="quiz-guess" class="hidden">
                        <label>السورة</label><select id="qg-surah"></select>
                        <label>الآية</label><input id="qg-ayah" type="number" min="1" max="286">
                        <button class="btn sm" id="qz-check">تحقق</button>
                        <span id="qg-result"></span>
                    </span>
                    <button class="btn sm alt" id="qz-setup">⚙ تغيير المجال</button>
                    <span id="quiz-stats"></span>
                </div>
                <div id="quiz-stage"></div>
            </div>
        </div>
    </div>


    <div id="view-matn" class="view">
        <div id="matn-side">
            <div class="matn-actions">
                <button class="btn sm" id="matn-add">➕ ملفات</button>
                <button class="btn sm alt" id="matn-folder">📁 مجلد</button>
            </div>
            <input id="matn-filter" type="text" placeholder="🔍 بحث في المكتبة">
            <ul id="matn-list"></ul>
        </div>
        <div id="matn-main">
            <div class="matn-title" id="matn-title">اختر ملفًا صوتيًا من المكتبة (أو أضف ملفات من جهازك)</div>

            <div class="matn-seek">
                <span id="matn-cur">0:00</span>
                <div class="seek-wrap"><div id="matn-ab" class="hidden"></div><input id="matn-seek" type="range" min="0" max="1000" value="0"></div>
                <span id="matn-dur">0:00</span>
            </div>

            <div class="matn-row">
                <button class="btn" id="matn-prev" title="الملف السابق">⏮</button>
                <button class="btn" id="matn-back" title="رجوع 5 ثوانٍ">⏪ 5</button>
                <button class="btn" id="matn-play" title="تشغيل / إيقاف (Space)">▶</button>
                <button class="btn" id="matn-fwd" title="تقديم 5 ثوانٍ">5 ⏩</button>
                <button class="btn" id="matn-next" title="الملف التالي">⏭</button>
                <label>الصوت 🔈</label><input id="matn-vol" type="range" min="0" max="100" value="100" style="width:110px">
            </div>

            <div class="matn-card">
                <h4>⚡ السرعة</h4>
                <div class="matn-row">
                    <input id="matn-speed" type="range" min="0.5" max="2" step="0.05" value="1" style="width:220px">
                    <span class="speed-val" id="matn-speed-val">×1.00</span>
                    <button class="btn sm alt" data-speed="0.5">0.5</button>
                    <button class="btn sm alt" data-speed="0.75">0.75</button>
                    <button class="btn sm alt" data-speed="1">1</button>
                    <button class="btn sm alt" data-speed="1.25">1.25</button>
                    <button class="btn sm alt" data-speed="1.5">1.5</button>
                    <button class="btn sm alt" data-speed="2">2</button>
                    <label class="chk"><input type="checkbox" id="matn-pitch" checked> إبقاء نبرة الصوت طبيعية</label>
                </div>
            </div>

            <div class="matn-card">
                <h4>🔁 التكرار (للحفظ والترديد)</h4>
                <div class="matn-row">
                    <label>كرّر</label><input id="matn-repeat" type="number" min="0" max="99" value="1">
                    <span class="dr-muted">مرة (0 = بلا توقف)</span>
                    <label>فاصل بين التكرارات</label><input id="matn-gap" type="number" min="0" max="60" step="0.5" value="0">
                    <span class="dr-muted">ثانية</span>
                    <span class="chip" id="matn-loop-label">—</span>
                </div>
                <div class="matn-row">
                    <button class="btn sm" id="matn-setA">[ نقطة A</button>
                    <button class="btn sm" id="matn-setB">نقطة B ]</button>
                    <label class="chk"><input type="checkbox" id="matn-abon"> تكرار المقطع A–B فقط</label>
                    <button class="btn sm alt" id="matn-clearab">مسح A–B</button>
                    <span class="dr-muted" id="matn-ab-label"></span>
                </div>
                <div class="matn-row">
                    <label class="chk"><input type="checkbox" id="matn-autonext" checked> الانتقال للملف التالي بعد انتهاء التكرار</label>
                    <label class="chk"><input type="checkbox" id="matn-loopall"> إعادة قائمة التشغيل</label>
                </div>
            </div>

            <div class="matn-card">
                <h4>🔖 المقاطع المحفوظة لهذا الملف</h4>
                <div class="matn-row">
                    <input id="matn-segname" type="text" placeholder="اسم المقطع (مثل: الأبيات 1–3)" style="min-width:220px">
                    <button class="btn sm" id="matn-segsave">حفظ المقطع الحالي (A–B)</button>
                </div>
                <div id="matn-segs"></div>
                <div class="dr-muted">اختصارات: Space تشغيل/إيقاف · ← → تقديم/رجوع 5 ثوانٍ · [ و ] لنقطتي A وB · L لتفعيل تكرار المقطع · - و + للسرعة</div>
            </div>
        </div>
    </div>

    </div>

    <div id="drawer-overlay" class="hidden"></div>
    <aside id="drawer" class="hidden">
        <div class="dr-head">
            <div>
                <div class="dr-title" id="dr-title">مقرأة القرآن الكريم</div>
                <div class="dr-ver" id="dr-ver"></div>
            </div>
            <button class="dr-close" id="dr-close" title="إغلاق">✕</button>
        </div>
        <div class="dr-body">

            <details class="dr-sec" id="wn-sec">
                <summary>✨ ما الجديد <span class="badge hidden" id="wn-badge">جديد</span></summary>
                <div class="dr-in" id="wn-body"></div>
            </details>

            <details class="dr-sec" open>
                <summary>⚙️ الإعدادات</summary>
                <div class="dr-in">
                    <label class="chk"><input type="checkbox" id="set-dark"> 🌙 الوضع الليلي</label>
                    <label class="chk"><input type="checkbox" id="set-status" checked> إظهار شريط المعلومات (الرابط وتقدّم التشغيل)</label>
                </div>
            </details>

            <details class="dr-sec">
                <summary>📚 التفسير</summary>
                <div class="dr-in">
                    <div class="dr-muted">يظهر تحت كل آية في التلاوة، وعند تحديد آية في المصحف.</div>
                    <select id="tafsir-select"></select>
                </div>
            </details>

            <details class="dr-sec">
                <summary>📈 الحفظ والورد اليومي</summary>
                <div class="dr-in">
                    <div class="dr-muted" id="srs-text"></div>
                    <div class="dr-row"><label>هدف الورد اليومي (صفحات):</label><input id="wird-target" type="number" min="1" max="604" style="width:70px;padding:5px;border:1px solid #cbd5e1;border-radius:6px"><button class="btn sm" id="wird-save">حفظ</button></div>
                    <div class="dr-muted" id="wird-text"></div>
                    <button class="btn sm alt" id="srs-reset">تصفير سجل المراجعة</button>
                </div>
            </details>

            <details class="dr-sec">
                <summary>⏱ مؤقّت النوم والوضع المصغّر</summary>
                <div class="dr-in">
                    <div class="dr-row"><label>إيقاف الصوت بعد:</label>
                        <select id="sleep-select">
                            <option value="0">بلا مؤقّت</option><option value="10">10 دقائق</option><option value="15">15 دقيقة</option>
                            <option value="30">30 دقيقة</option><option value="45">45 دقيقة</option><option value="60">ساعة</option><option value="90">ساعة ونصف</option>
                        </select></div>
                    <div class="dr-muted">يخفت الصوت تدريجيًا في آخر ثوانٍ ثم يتوقف.</div>
                    <button class="btn sm alt" id="mini-btn2">🗕 الوضع المصغّر (نافذة صغيرة فوق النوافذ)</button>
                </div>
            </details>

            <details class="dr-sec">
                <summary>📥 الصوت دون إنترنت</summary>
                <div class="dr-in">
                    <div class="dr-muted">حمّل تلاوة القارئ على جهازك ليعمل التطبيق بلا إنترنت. تُستخدم الملفات المحمّلة تلقائيًا عند التشغيل.</div>
                    <div class="dr-row"><label>القارئ:</label><select id="off-reciter"></select></div>
                    <div class="dr-row"><label>من سورة</label><select id="off-from"></select><label>إلى</label><select id="off-to"></select></div>
                    <div class="dr-muted" id="off-estimate"></div>
                    <div class="dr-row">
                        <button class="btn sm" id="off-start">⬇ تحميل</button>
                        <button class="btn sm alt hidden" id="off-cancel">إيقاف</button>
                    </div>
                    <progress id="off-progress" value="0" max="1" class="hidden"></progress>
                    <div class="dr-muted" id="off-text"></div>
                    <div id="off-list"></div>
                </div>
            </details>

            <details class="dr-sec">
                <summary>💬 تواصل واقتراحات</summary>
                <div class="dr-in">
                    <div class="dr-muted">يسعدنا سماع اقتراحاتك وملاحظاتك.</div>
                    <div class="dr-row" id="contact-links"></div>
                    <select id="sug-type">
                        <option>اقتراح</option>
                        <option>بلاغ عن خطأ</option>
                        <option>سؤال</option>
                    </select>
                    <textarea id="sug-text" placeholder="اكتب رسالتك هنا..."></textarea>
                    <button class="btn sm" id="sug-send">✉️ إرسال عبر البريد</button>
                    <div class="dr-muted" id="sug-msg"></div>
                </div>
            </details>

            <details class="dr-sec">
                <summary>⌨️ اختصارات لوحة المفاتيح</summary>
                <div class="dr-in">
                    <div class="dr-kbd"><span>تشغيل / إيقاف (التلاوة)</span><kbd>Space</kbd></div>
                    <div class="dr-kbd"><span>الآية التالية / الصفحة التالية</span><kbd>←</kbd></div>
                    <div class="dr-kbd"><span>الآية السابقة / الصفحة السابقة</span><kbd>→</kbd></div>
                    <div class="dr-kbd"><span>إغلاق هذه القائمة</span><kbd>Esc</kbd></div>
                    <div class="dr-kbd"><span>المتون: تقديم / رجوع 5 ثوانٍ</span><kbd>← →</kbd></div>
                    <div class="dr-kbd"><span>المتون: نقطة A / نقطة B</span><kbd>[ ]</kbd></div>
                </div>
            </details>

            <details class="dr-sec">
                <summary>💾 التخزين</summary>
                <div class="dr-in">
                    <div class="dr-muted" id="storage-text"></div>
                    <div class="dr-row">
                        <button class="btn sm alt" id="clear-cache">مسح الذاكرة المؤقتة</button>
                        <button class="btn sm alt" id="reset-settings">إعادة ضبط الإعدادات</button>
                    </div>
                    <div class="dr-muted" id="storage-msg"></div>
                </div>
            </details>

            <details class="dr-sec" id="privacy-sec">
                <summary>🔒 الخصوصية</summary>
                <div class="dr-in">
                    <label class="chk"><input type="checkbox" id="set-analytics"> السماح بإرسال إحصاء مجهول لعدد المستخدمين</label>
                    <div class="dr-muted">عند السماح يُرسل مرة كل يوم: معرّف عشوائي + رقم الإصدار + اسم النظام. لا يُرسل أي شيء عن قراءتك أو بحثك أو تلاوتك، ولا نحفظ عنوان الشبكة. الاختيار لك وتغييره متاح دائمًا.</div>
                    <div class="dr-muted" id="analytics-id"></div>
                </div>
            </details>

            <details class="dr-sec">
                <summary>ℹ️ حول التطبيق</summary>
                <div class="dr-in">
                    <div id="about-name" style="font-weight:800;font-size:16px"></div>
                    <div>تطبيق لتلاوة القرآن الكريم وحفظه: تلاوة آية بآية بعدة قرّاء وروايات، ومصحف المدينة برسم QCF4 مع البحث، واختبار للحفظ.</div>
                    <div id="about-dev" class="dr-muted"></div>
                    <div class="dr-muted">
                        <b>المصادر والشكر:</b><br>
                        • خطوط مصحف المدينة QCF4: مجمّع الملك فهد لطباعة المصحف الشريف.<br>
                        • بيانات صفحات المصحف: مشروع quran-qcf4.<br>
                        • الصوتيات: موقع EveryAyah.com.<br>
                        • نصوص السور والصفحات: مستودع بيانات التطبيق (مبني على بيانات مجمّع الملك فهد وquran-meta).
                    </div>
                    <div class="dr-muted" id="about-sys"></div>
                </div>
            </details>

        </div>
    </aside>
    <div id="consent-overlay" class="hidden">
        <div id="consent-card">
            <h3>🤝 ساعدنا بإحصاء مجهول لعدد المستخدمين</h3>
            <div>نودّ معرفة عدد من يستعمل التطبيق لنطوّره. إن وافقتَ فسيرسل التطبيق مرة كل يوم على الأكثر:</div>
            <ul>
                <li>معرّفًا <b>عشوائيًا</b> لا يرتبط باسمك ولا بجهازك،</li>
                <li>رقم إصدار التطبيق،</li>
                <li>اسم نظام التشغيل فقط (مثل Windows).</li>
            </ul>
            <div><b>لا يُرسل أبدًا:</b> اسمك أو موقعك أو ما تقرؤه أو تبحث عنه أو تسمعه. ولا نحفظ عنوان الشبكة (IP).
                يمكنك تغيير اختيارك في أي وقت من القائمة ☰ ← 🔒 الخصوصية.</div>
            <div class="row">
                <button class="btn" id="consent-yes">موافق</button>
                <button class="btn alt" id="consent-no">لا، شكرًا</button>
            </div>
        </div>
    </div>
    <div id="toast" class="hidden"></div>

    <audio id="audio-player" preload="auto"></audio>

    <script>
        // ---------- الحالة ----------
        let reciters = [];
        let settings = {};
        let surahs = [];
        let currentSurah = 1;
        let ayahsData = [];
        let currentAyahIndex = 0;
        let currentRepeatIndex = 0;
        let consecutiveErrors = 0;
        let skipTimer = null;
        let rangeTimer = null;
        let isSeeking = false;
        let lastRes = null;
        let qcfAvailable = false;
        const loadedQcfFonts = new Set();

        const $ = (id) => document.getElementById(id);
        const audioPlayer = $('audio-player');
        const ayahContainer = $('ayah-container');
        const btnPlay = $('btn-play');
        const riwayaSelect = $('riwaya-select');
        const repeatSelect = $('repeat-select');
        const speedSelect = $('speed-select');
        const rangeFrom = $('range-from');
        const rangeTo = $('range-to');
        const loopRange = $('loop-range');
        const hideText = $('hide-text');
        const focusOnly = $('focus-only');
        const fontSelect = $('font-select');
        const sizeSelect = $('size-select');
        const HAS_LOCAL_FONT = /*HAS_LOCAL_FONT*/false;
        const FONT_STACKS = {
            'amiri-quran': '"Amiri Quran", "Amiri", serif',
            'scheherazade': '"Scheherazade New", "Amiri", serif',
            'amiri': '"Amiri", serif',
            'kfgqpc': '"KFGQPC Uthmani", "Amiri Quran", serif',
        };

        const isQcf = () => fontSelect.value === 'qcf4' && qcfAvailable && lastRes && lastRes.qcf;

        async function ensureQcfFonts(names) {
            for (const name of names) {
                if (loadedQcfFonts.has(name)) continue;
                const f = await api().get_qcf_font(name);
                if (!f) continue;
                const face = new FontFace(name, `url(data:${f.mime};base64,${f.data})`);
                await face.load();
                document.fonts.add(face);
                loadedQcfFonts.add(name);
            }
        }

        // في وضع الآية الواحدة: صغّر الخط تدريجيًا حتى تظهر الآية كاملة داخل الإطار
        function fitFocus() {
            document.querySelectorAll('.ayah-card').forEach(c => { c.style.fontSize = ''; });
            if (!(focusOnly.checked || document.body.classList.contains('mini'))) return;
            const card = ayahContainer.querySelector('.ayah-card.playing');
            if (!card) return;
            const maxH = ayahContainer.clientHeight - 48;
            let size = parseFloat(sizeSelect.value) * 1.45;
            card.style.fontSize = size + 'px';
            while (card.offsetHeight > maxH && size > 14) {
                size -= 2;
                card.style.fontSize = size + 'px';
            }
        }
        window.addEventListener('resize', () => fitFocus());

        function syncFocus() {
            ayahContainer.classList.toggle('focus-mode', focusOnly.checked || document.body.classList.contains('mini'));
            ayahContainer.classList.toggle('no-playing', !ayahContainer.querySelector('.ayah-card.playing'));
            fitFocus();
        }

        function rerender() {
            if (!lastRes) return;
            renderAyahs(lastRes.bismillah);
            markRange();
            if (hasSrc()) {
                const card = $(`ayah-${currentAyahIndex}`);
                if (card) card.classList.add('playing');
            }
            syncFocus();
        }

        function applyFont() {
            const root = document.documentElement.style;
            root.setProperty('--ayah-font', FONT_STACKS[fontSelect.value] || FONT_STACKS['amiri-quran']);
            root.setProperty('--ayah-size', sizeSelect.value + 'px');
        }
        const progress = $('progress');
        const statusBar = $('status-bar');
        const statusText = $('status-text');
        const urlInput = $('url-input');

        const api = () => window.pywebview.api;

        window.addEventListener('pywebviewready', init);

        // ---------- أدوات ----------
        function normalizeAr(s) {
            return (s || '')
                .replace(/[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g, '')
                .replace(/[أإآٱ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي');
        }

        function copyUrl() {
            if (!urlInput.value) return;
            const done = () => {
                const btn = document.querySelector('.btn-copy');
                btn.textContent = 'تم النسخ! ✓';
                setTimeout(() => { btn.textContent = 'نسخ 📋'; }, 2000);
            };
            urlInput.select();
            if (navigator.clipboard) {
                navigator.clipboard.writeText(urlInput.value).then(done).catch(() => {
                    document.execCommand('copy'); done();
                });
            } else { document.execCommand('copy'); done(); }
        }

        function updateStatus(msg, url, isError) {
            statusText.textContent = msg;
            if (url !== undefined) urlInput.value = url;
            statusBar.classList.toggle('error', !!isError);
            if (isError && !statusBarOn) showToast(msg);   // الشريط مخفي: أظهر الخطأ مؤقتًا
        }

        function persist() {
            settings = {
                riwaya: riwayaSelect.value,
                repeat: repeatSelect.value,
                speed: speedSelect.value,
                loop: loopRange.checked,
                hide: hideText.checked,
                focus: focusOnly.checked,
                font: fontSelect.value,
                size: sizeSelect.value,
                surah: currentSurah,
                page: typeof mushafPage === 'number' ? mushafPage : 1,
                mwidth: $('mushaf-width').value,
                quizFrom: $('quiz-from').value || settings.quizFrom,
                quizTo: $('quiz-to').value || settings.quizTo,
                dark: darkMode,
                statusbar: statusBarOn,
                quizMode: $('quiz-mode').value,
                quizReview: $('quiz-review').checked,
                tafsir: typeof tafsirId === 'string' ? tafsirId : (settings.tafsir || ''),
            };
            if (window.pywebview) api().save_settings(settings);
        }

        function currentReciter() {
            return reciters.find(r => r.id === riwayaSelect.value) || reciters[0];
        }

        function hasSrc() { return !!audioPlayer.getAttribute('src'); }

        function getRange() {
            const n = ayahsData.length;
            let a = parseInt(rangeFrom.value) - 1;
            let b = parseInt(rangeTo.value) - 1;
            if (isNaN(a)) a = 0;
            if (isNaN(b)) b = n - 1;
            return [Math.min(a, b), Math.max(a, b)];
        }

        function markRange() {
            const [a, b] = getRange();
            document.querySelectorAll('.ayah-card').forEach((c, i) => {
                c.classList.toggle('in-range', i >= a && i <= b);
            });
        }

        // عند تغيير المقطع أثناء التشغيل: ابدأ من أول المقطع الجديد
        // (مهلة قصيرة حتى لا يُعاد التشغيل مرتين عند تغيير "من" ثم "إلى")
        function onRangeChanged() {
            markRange();
            clearTimeout(rangeTimer);
            if (!hasSrc() || audioPlayer.paused) return;
            rangeTimer = setTimeout(() => {
                currentRepeatIndex = 0;
                playAyah(getRange()[0]);
            }, 700);
        }

        function stopAudio() {
            playToken++;
            clearTimeout(rangeTimer);
            clearTimeout(skipTimer);
            audioPlayer.pause();
            audioPlayer.removeAttribute('src');
            audioPlayer.load();
            progress.value = 0;
            btnPlay.textContent = 'تشغيل ▶';
        }

        // ---------- التهيئة ----------
        async function init() {
            reciters = await api().get_reciters();
            settings = (await api().load_settings()) || {};
            applyPrefs();

            buildReciterSelect();
            if (settings.riwaya && reciters.some(r => r.id === settings.riwaya)) riwayaSelect.value = settings.riwaya;
            if (settings.repeat) repeatSelect.value = settings.repeat;
            if (settings.speed) speedSelect.value = settings.speed;
            loopRange.checked = !!settings.loop;
            hideText.checked = !!settings.hide;
            focusOnly.checked = !!settings.focus;
            ayahContainer.classList.toggle('hide-text', hideText.checked);

            qcfAvailable = (await api().qcf_info()).available;
            if (qcfAvailable) {
                const q = document.createElement('option');
                q.value = 'qcf4';
                q.textContent = 'مصحف المدينة (QCF4)';
                fontSelect.insertBefore(q, fontSelect.firstChild);
                fontSelect.value = 'qcf4';
            }
            if (HAS_LOCAL_FONT) {
                const o = document.createElement('option');
                o.value = 'kfgqpc';
                o.textContent = 'مصحف المدينة (KFGQPC)';
                fontSelect.insertBefore(o, fontSelect.firstChild);
                fontSelect.value = 'kfgqpc';
            }
            if (settings.font && [...fontSelect.options].some(o => o.value === settings.font)) fontSelect.value = settings.font;
            if (settings.size) sizeSelect.value = settings.size;
            applyFont();

            setupAudioMonitor();
            setupEventListeners();
            await loadSurahList();
            initExtras();

            // تحقق خلفي من الروابط حتى لا يبقى رابط ميت دون أن تعلم
            api().check_reciters().then(applyAvailability);
        }

        function buildReciterSelect() {
            riwayaSelect.innerHTML = '';
            const groups = {};
            reciters.forEach(r => {
                if (!groups[r.group]) {
                    const og = document.createElement('optgroup');
                    og.label = r.group;
                    groups[r.group] = og;
                    riwayaSelect.appendChild(og);
                }
                const opt = document.createElement('option');
                opt.value = r.id;
                opt.textContent = r.label;
                opt.dataset.label = r.label;
                groups[r.group].appendChild(opt);
            });
        }

        function applyAvailability(map) {
            let unknown = 0, bad = 0;
            [...riwayaSelect.options].forEach(opt => {
                const st = map[opt.value];
                if (st === false) {
                    opt.disabled = true;
                    opt.textContent = opt.dataset.label + ' ⚠ غير متاح';
                    bad++;
                } else if (st === null) { unknown++; }
            });
            if (riwayaSelect.selectedOptions[0] && riwayaSelect.selectedOptions[0].disabled) {
                const first = [...riwayaSelect.options].find(o => !o.disabled);
                if (first) riwayaSelect.value = first.value;
            }
            if (unknown === riwayaSelect.options.length) {
                updateStatus('⚠️ تعذر التحقق من روابط الصوت (تحقق من الاتصال بالإنترنت).');
            } else if (bad > 0 && !hasSrc()) {
                updateStatus(`ℹ️ تم تعطيل ${bad} قارئ لأن ملفاتهم غير متاحة حاليًا.`);
            }
        }

        // ---------- الصوت ----------
        function setupAudioMonitor() {
            audioPlayer.onplaying = () => {
                consecutiveErrors = 0;
                const a = ayahsData[currentAyahIndex];
                if (!a) return;
                const max = parseInt(repeatSelect.value);
                const rep = max === 0 ? `(تكرار ${currentRepeatIndex + 1})`
                    : (max > 1 ? `(تكرار ${currentRepeatIndex + 1}/${max})` : '');
                updateStatus(`▶ جاري التلاوة: [الآية ${a.numberInSurah}] ${rep} - ${currentReciter().label}${currentAudio.offline ? ' 📁 (دون إنترنت)' : ''}`, currentAudio.remote, false);
                btnPlay.textContent = 'إيقاف مؤقت ⏸';
            };
            audioPlayer.onpause = () => {
                if (hasSrc() && !audioPlayer.ended) btnPlay.textContent = 'تشغيل ▶';
            };
            audioPlayer.ontimeupdate = () => {
                if (!isSeeking && audioPlayer.duration) {
                    progress.value = Math.round(audioPlayer.currentTime / audioPlayer.duration * 1000);
                }
            };
            audioPlayer.onerror = () => {
                if (!hasSrc()) return;              // تفريغ المصدر عمدًا ليس خطأ
                const src = audioPlayer.src;
                consecutiveErrors++;
                const a = ayahsData[currentAyahIndex];
                const [, last] = getRange();
                const canSkip = consecutiveErrors <= 3 && currentAyahIndex < last;
                updateStatus(
                    `❌ تعذر تحميل صوت الآية ${a ? a.numberInSurah : ''} (ملف غير موجود أو لا اتصال)` +
                    (canSkip ? ' — سيتم الانتقال للتالية...' : ''),
                    src, true);
                if (canSkip) {
                    clearTimeout(skipTimer);
                    skipTimer = setTimeout(() => { currentRepeatIndex = 0; playAyah(currentAyahIndex + 1); }, 1500);
                } else {
                    btnPlay.textContent = 'تشغيل ▶';
                }
            };
            audioPlayer.onended = () => {
                const max = parseInt(repeatSelect.value);
                currentRepeatIndex++;
                if (max === 0 || currentRepeatIndex < max) {
                    audioPlayer.currentTime = 0;
                    audioPlayer.play().catch(() => {});
                    return;
                }
                currentRepeatIndex = 0;
                const [first, last] = getRange();
                if (currentAyahIndex < first || currentAyahIndex > last) {
                    playAyah(first);                    // خرجنا من المقطع المحدد: ارجع لبدايته
                } else if (currentAyahIndex < last) {
                    playAyah(currentAyahIndex + 1);
                } else if (loopRange.checked) {
                    playAyah(first);
                } else {
                    btnPlay.textContent = 'تشغيل ▶';
                    updateStatus('✅ اكتمل المقطع المحدد بحمد الله.');
                }
            };
        }

        async function playAyah(index) {
            if (index < 0 || index >= ayahsData.length) return;
            clearTimeout(skipTimer);

            currentAyahIndex = index;
            const ayah = ayahsData[index];
            const surahStr = String(currentSurah).padStart(3, '0');
            const ayahStr = String(ayah.numberInSurah).padStart(3, '0');
            const audioUrl = `${currentReciter().url}${surahStr}${ayahStr}.mp3`;

            api().log_audio_url(audioUrl, currentSurah, ayah.numberInSurah, currentReciter().label);

            document.querySelectorAll('.ayah-card').forEach(c => c.classList.remove('playing'));
            const card = $(`ayah-${index}`);
            if (card) {
                card.classList.add('playing');
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            syncFocus();

            updateStatus('⌛ جاري تحميل الصوت...', audioUrl, false);
            const myToken = ++playToken;
            const res = await resolveAudio(currentReciter(), `${currentSurah}:${ayah.numberInSurah}`, audioUrl);
            if (myToken !== playToken) return;               // طُلبت آية أخرى أثناء التحضير
            currentAudio = { remote: audioUrl, offline: res.offline };
            setSrc(audioPlayer, res);
            const rate = parseFloat(speedSelect.value) || 1;
            audioPlayer.defaultPlaybackRate = rate;
            audioPlayer.playbackRate = rate;
            audioPlayer.play().catch(err => {
                if (err && err.name === 'AbortError') return;   // تم استبدال المصدر
                updateStatus(`❌ رفض المشغل البدء: ${err.message}`, audioUrl, true);
            });
            btnPlay.textContent = 'إيقاف مؤقت ⏸';
        }

        // ---------- الأحداث ----------
        function setupEventListeners() {
            riwayaSelect.onchange = () => {
                currentRepeatIndex = 0;
                consecutiveErrors = 0;
                persist();
                updateStatus(`🔄 تم تغيير القارئ إلى: ${currentReciter().label}`);
                if (ayahsData.length > 0 && hasSrc()) playAyah(currentAyahIndex);
            };
            repeatSelect.onchange = () => { currentRepeatIndex = 0; persist(); };
            speedSelect.onchange = () => {
                const r = parseFloat(speedSelect.value) || 1;
                audioPlayer.defaultPlaybackRate = r;
                audioPlayer.playbackRate = r;
                persist();
            };
            loopRange.onchange = persist;
            fontSelect.onchange = async () => {
                applyFont(); persist();
                if (isQcf()) await ensureQcfFonts(lastRes.qcf.fonts);
                rerender();
            };
            sizeSelect.onchange = () => { applyFont(); persist(); fitFocus(); };
            focusOnly.onchange = () => { syncFocus(); persist(); };
            hideText.onchange = () => {
                ayahContainer.classList.toggle('hide-text', hideText.checked);
                persist();
            };

            rangeFrom.onchange = () => {
                if (parseInt(rangeFrom.value) > parseInt(rangeTo.value)) rangeTo.value = rangeFrom.value;
                onRangeChanged();
            };
            rangeTo.onchange = () => {
                if (parseInt(rangeTo.value) < parseInt(rangeFrom.value)) rangeFrom.value = rangeTo.value;
                onRangeChanged();
            };

            btnPlay.onclick = () => {
                if (!ayahsData.length) return;
                if (!hasSrc()) { playAyah(getRange()[0]); return; }
                if (audioPlayer.paused) {
                    const [first, last] = getRange();
                    if (currentAyahIndex < first || currentAyahIndex > last) { currentRepeatIndex = 0; playAyah(first); return; }
                    audioPlayer.play(); btnPlay.textContent = 'إيقاف مؤقت ⏸';
                }
                else { audioPlayer.pause(); btnPlay.textContent = 'تشغيل ▶'; }
            };
            $('btn-next').onclick = () => { currentRepeatIndex = 0; playAyah(currentAyahIndex + 1); };
            $('btn-prev').onclick = () => { currentRepeatIndex = 0; playAyah(currentAyahIndex - 1); };

            progress.onmousedown = () => { isSeeking = true; };
            progress.onchange = () => {
                if (audioPlayer.duration) audioPlayer.currentTime = progress.value / 1000 * audioPlayer.duration;
                isSeeking = false;
            };

            $('surah-search').oninput = (e) => {
                const q = normalizeAr(e.target.value.trim());
                document.querySelectorAll('#surah-list li').forEach(li => {
                    li.style.display = (!q || li.dataset.search.includes(q)) ? '' : 'none';
                });
            };

            document.addEventListener('keydown', (e) => {
                const t = e.target.tagName;
                // لا نعترض الكتابة في حقول الإدخال، ولا نفعّل اختصارات التطبيق والقائمة الجانبية مفتوحة
                if (!$('drawer').classList.contains('hidden')) return;
                if (t === 'TEXTAREA' || t === 'SELECT' || e.target.isContentEditable) return;
                if (t === 'INPUT' && !['checkbox', 'radio', 'button', 'range'].includes(e.target.type)) return;
                if (currentView === 'matn') { matnKey(e); return; }
                if (currentView === 'mushaf') {
                    if (t === 'INPUT' || t === 'SELECT') return;
                    if (e.code === 'ArrowLeft') showMushafPage(mushafPage + 1);
                    else if (e.code === 'ArrowRight') showMushafPage(mushafPage - 1);
                    return;
                }
                if (currentView !== 'recite') return;
                if (t === 'INPUT' && e.target.type === 'text') return;
                if (t === 'SELECT') return;
                if (e.code === 'Space') { e.preventDefault(); btnPlay.click(); }
                else if (e.code === 'ArrowLeft') { $('btn-next').click(); }
                else if (e.code === 'ArrowRight') { $('btn-prev').click(); }
            });
        }

        // ---------- السور والآيات ----------
        async function loadSurahList() {
            surahs = await api().fetch_surahs();
            const listEl = $('surah-list');
            listEl.innerHTML = '';

            if (!surahs || surahs.length === 0) {
                const li = document.createElement('li');
                li.style.cssText = 'color:red; justify-content:center;';
                li.textContent = 'تعذر جلب الفهرس. تحقق من الاتصال.';
                listEl.appendChild(li);
                return;
            }

            surahs.forEach(s => {
                const plain = normalizeAr(s.name);
                const title = plain.startsWith('سوره') ? s.name : `سورة ${s.name}`;
                const li = document.createElement('li');
                li.dataset.num = s.number;
                li.dataset.search = `${s.number} ${plain} ${(s.englishName || '').toLowerCase()}`;
                li.innerHTML = '<span></span><small></small>';
                li.firstChild.textContent = `${s.number}. ${title}`;
                li.lastChild.textContent = `${s.numberOfAyahs} آية`;
                li.onclick = () => loadSurahVerses(s.number, true);
                listEl.appendChild(li);
            });

            // استرجاع آخر سورة دون تشغيل تلقائي
            const last = parseInt(settings.surah);
            if (last >= 1 && last <= 114) loadSurahVerses(last, false);
        }

        async function loadSurahVerses(surahNum, autoplay) {
            stopAudio();
            currentSurah = surahNum;
            currentAyahIndex = 0;
            currentRepeatIndex = 0;
            consecutiveErrors = 0;

            document.querySelectorAll('#surah-list li').forEach(li =>
                li.classList.toggle('active', li.dataset.num == surahNum));
            const activeLi = document.querySelector('#surah-list li.active');
            if (activeLi) activeLi.scrollIntoView({ block: 'nearest' });

            updateStatus(`⌛ جاري جلب نص السورة رقم (${surahNum})...`, '');
            ayahContainer.innerHTML = '<div class="placeholder" style="color:#2d6a4f">⌛ جاري تحميل الآيات...</div>';

            const res = await api().fetch_surah_verses(surahNum);

            if (!res) {
                updateStatus('❌ تعذر الاتصال بالشبكة لجلب آيات السورة', '', true);
                ayahContainer.innerHTML = '';
                const box = document.createElement('div');
                box.style.cssText = 'text-align:center; padding:30px; color:red;';
                box.innerHTML = '<h3>⚠️ تعذر جلب آيات السورة</h3>';
                const b = document.createElement('button');
                b.className = 'btn';
                b.style.marginTop = '10px';
                b.textContent = '🔄 إعادة المحاولة';
                b.onclick = () => loadSurahVerses(surahNum, autoplay);
                box.appendChild(b);
                ayahContainer.appendChild(box);
                return;
            }

            lastRes = res;
            ayahsData = res.ayahs;
            if (fontSelect.value === 'qcf4' && qcfAvailable && !res.qcf) {
                updateStatus('⚠️ تعذر جلب بيانات مصحف المدينة (QCF4)، سيُعرض النص بخط عادي. تحقق من الاتصال.', '', true);
            }
            if (isQcf()) {
                updateStatus('⌛ جاري تحميل خط المصحف...', '');
                try { await ensureQcfFonts(res.qcf.fonts); await getBismillah(); }
                catch (e) { updateStatus('⚠️ تعذر تحميل خطوط QCF4: ' + e, '', true); }
            }
            renderAyahs(res.bismillah);
            fillRangeSelects();
            persist();
            updateStatus(`📖 تم تحميل السورة (${ayahsData.length} آية). ${autoplay ? '' : 'اضغط تشغيل للبدء.'}`, '');
            if (autoplay) playAyah(0);
        }

        function fillRangeSelects() {
            [rangeFrom, rangeTo].forEach(sel => {
                sel.innerHTML = '';
                ayahsData.forEach(a => {
                    const o = document.createElement('option');
                    o.value = a.numberInSurah;
                    o.textContent = a.numberInSurah;
                    sel.appendChild(o);
                });
            });
            rangeFrom.value = ayahsData[0].numberInSurah;
            rangeTo.value = ayahsData[ayahsData.length - 1].numberInSurah;
            markRange();
        }

        function renderAyahs(showBismillah) {
            ayahContainer.innerHTML = '';
            const hint = document.createElement('div');
            hint.className = 'focus-hint';
            hint.textContent = 'اضغط «تشغيل ▶» لتظهر الآية المتلوة هنا';
            ayahContainer.appendChild(hint);
            const qcf = isQcf() ? lastRes.qcf : null;
            if (showBismillah) {
                const b = document.createElement('div');
                b.className = 'bismillah';
                if (qcf && bismillahWords) {
                    bismillahWords.forEach(w => {
                        const sp = document.createElement('span');
                        sp.className = 'qw';
                        sp.style.fontFamily = `"${w.f}"`;
                        sp.textContent = w.c;
                        b.appendChild(sp);
                    });
                } else if (qcf && qcf.bismillah.length) {
                    qcf.bismillah.forEach(w => {
                        const sp = document.createElement('span');
                        sp.style.fontFamily = `"${w.f}"`;
                        sp.textContent = w.c;
                        b.appendChild(sp);
                    });
                } else {
                    b.textContent = 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ';
                }
                ayahContainer.appendChild(b);
            }
            ayahsData.forEach((ayah, index) => {
                const card = document.createElement('div');
                card.className = 'ayah-card';
                card.id = `ayah-${index}`;

                const words = qcf && qcf.ayahs[String(ayah.numberInSurah)];
                if (words && words.length) {
                    // رسم مصحف المدينة: علامة نهاية الآية ورقمها جزء من الخط نفسه
                    card.classList.add('qcf');
                    const txt = document.createElement('span');
                    txt.className = 'ayah-text';
                    words.forEach(w => {
                        const sp = document.createElement('span');
                        sp.className = 'qw';
                        sp.style.fontFamily = `"${w.f}"`;
                        sp.textContent = w.c;
                        txt.appendChild(sp);
                    });
                    card.appendChild(txt);
                } else {
                    const txt = document.createElement('span');
                    txt.className = 'ayah-text';
                    txt.textContent = ayah.text;

                    const num = document.createElement('span');
                    num.className = 'ayah-number';
                    num.textContent = `﴿${toAr(ayah.numberInSurah)}﴾`;

                    card.appendChild(txt);          // الرقم بعد النص، كما في المصحف
                    card.appendChild(num);
                }
                card.onclick = () => {
                    const [a, b] = getRange();
                    if (index < a || index > b) {          // خارج المقطع: ابدأ من هنا حتى نهاية السورة
                        rangeFrom.value = ayah.numberInSurah;
                        rangeTo.value = ayahsData[ayahsData.length - 1].numberInSurah;
                        markRange();
                    }
                    currentRepeatIndex = 0;
                    playAyah(index);
                };
                ayahContainer.appendChild(card);
            });
            syncFocus();
            fillTafsirCards();
        }

        // =====================================================
        //  عام: التبويبات، فهرس السور، حالة بيانات المصحف
        // =====================================================
        let chapters = [];
        let corpusReady = false;
        let currentView = 'recite';
        let mushafPage = 1;
        let mushafLoaded = false;
        let mushafData = null;
        let mushafSel = null;
        let searchTimer = null;
        const miscAudio = new Audio();
        let bismillahWords = null;       // كلمات البسملة (من الآية 1:1) بخط QCF4 العادي
        let bismillahPromise = null;

        // البسملة تُرسم من كلمات الآية الأولى في الفاتحة، فهي رموز عادية الحجم؛
        // أمّا رمز البسملة الواحد العريض فقد ظهر مشطوبًا ببعض الأحجام في ويندوز.
        function getBismillah() {
            if (!bismillahPromise) {
                bismillahPromise = (async () => {
                    if (!qcfAvailable) return null;
                    try {
                        const pg = await api().get_page(1);
                        const words = pg.lines.flatMap(l => l.w).filter(w => w.k === '1:1' && w.t === 'word');
                        await ensureQcfFonts([...new Set(words.map(w => w.f))]);
                        if (words.length && words.every(w => loadedQcfFonts.has(w.f))) bismillahWords = words;
                    } catch (e) { /* نستخدم الرمز العريض أو النص العادي */ }
                    return bismillahWords;
                })();
            }
            return bismillahPromise;
        }

        function chapName(id) {
            const c = chapters.find(x => x.id === Number(id));
            return c ? c.name : String(id);
        }

        function verseUrl(key) {
            const [s, a] = key.split(':').map(Number);
            return `${currentReciter().url}${String(s).padStart(3, '0')}${String(a).padStart(3, '0')}.mp3`;
        }

        async function playMisc(key) {
            audioPlayer.pause();
            const url = verseUrl(key);
            api().log_audio_url(url, chapName(key.split(':')[0]), key.split(':')[1], currentReciter().label);
            const res = await resolveAudio(currentReciter(), key, url);
            setSrc(miscAudio, res);
            miscAudio.play().catch(() => {});
        }

        function stopAllAudio() {
            playToken++;
            mushafPlayStop();
            localPauseSave();
            clearTimeout(skipTimer);
            clearTimeout(rangeTimer);
            audioPlayer.pause();
            miscAudio.pause();
            btnPlay.textContent = 'تشغيل ▶';
        }

        function switchView(name) {
            if (name !== currentView) stopAllAudio();     // يتوقف الصوت عند الانتقال بين التبويبات
            currentView = name;
            document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.view === name));
            document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === 'view-' + name));
            if (name === 'mushaf') {
                if (!mushafLoaded) showMushafPage(settings.page || 1); else fitMushaf();
            }
            if (name === 'recite') fitFocus();
        }

        async function initExtras() {
            document.querySelectorAll('.tab').forEach(t => { t.onclick = () => switchView(t.dataset.view); });
            try { chapters = await api().get_chapters(); } catch (e) { chapters = []; }
            fillChapterSelects();
            setupDrawer();
            getBismillah();
            setupMushafEvents();
            setupQuizEvents();
            setupExtras();
            api().start_corpus();
            pollCorpus();
        }

        function fillChapterSelects() {
            ['mushaf-surah', 'quiz-from', 'quiz-to', 'off-from', 'off-to', 'qg-surah'].forEach(id => {
                const sel = $(id);
                sel.innerHTML = '';
                chapters.forEach(c => {
                    const o = document.createElement('option');
                    o.value = c.id;
                    o.textContent = `${c.id}. ${c.name}`;
                    sel.appendChild(o);
                });
            });
            if (chapters.length) {
                $('off-from').value = 1;
                $('off-to').value = chapters.length;
                $('quiz-from').value = settings.quizFrom || 1;
                $('quiz-to').value = settings.quizTo || chapters.length;
                if (settings.quizMode) $('quiz-mode').value = settings.quizMode;
                $('quiz-review').checked = !!settings.quizReview;
            }
            if (settings.mwidth) $('mushaf-width').value = settings.mwidth;
        }

        async function pollCorpus() {
            const el = $('corpus-status');
            let st;
            try { st = await api().corpus_status(); } catch (e) { return; }
            if (st.ready) {
                corpusReady = true;
                el.textContent = '✓ بيانات المصحف جاهزة (البحث والاختبار)';
                setTimeout(() => { if (corpusReady) el.textContent = ''; }, 4000);
                return;
            }
            if (st.error) {
                el.textContent = '⚠️ ' + st.error + ' ';
                const b = document.createElement('button');
                b.textContent = 'إعادة المحاولة';
                b.onclick = async () => { await api().start_corpus(); pollCorpus(); };
                el.appendChild(b);
                return;
            }
            el.textContent = `⌛ تجهيز بيانات المصحف ${st.done}/${st.total}`;
            setTimeout(pollCorpus, 1000);
        }

        // رسم كلمة/آية بخط QCF4 إن توفر، وإلا بنصها العادي
        async function prepFonts(verses) {
            if (!qcfAvailable) return;
            const names = new Set();
            verses.forEach(v => (v.words || []).forEach(w => names.add(w.f)));
            try { await ensureQcfFonts([...names]); } catch (e) { /* نكمل بالنص العادي */ }
        }

        function fillVerse(el, v, showEnd = true) {
            el.innerHTML = '';
            const useGlyph = qcfAvailable && v.words && v.words.length && v.words.every(w => loadedQcfFonts.has(w.f));
            const txt = document.createElement('span');
            txt.className = 'ayah-text' + (useGlyph ? ' glyphs' : '');
            if (useGlyph) {
                v.words.forEach(w => {
                    if (w.e && (!showEnd || v.partial)) return;
                    const sp = document.createElement('span');
                    sp.className = 'qw';
                    sp.style.fontFamily = `"${w.f}"`;
                    sp.textContent = w.c;
                    txt.appendChild(sp);
                });
            } else {
                txt.textContent = (showEnd && !v.partial) ? `${v.text} ﴿${toAr(v.a)}﴾` : v.text;
            }
            if (v.partial) txt.appendChild(document.createTextNode(' …'));
            el.appendChild(txt);
        }

        // =====================================================
        //  المصحف
        // =====================================================
        function setupMushafEvents() {
            $('mp-prev').onclick = () => showMushafPage(mushafPage - 1);
            $('mp-next').onclick = () => showMushafPage(mushafPage + 1);
            $('mushaf-page-input').onchange = (e) => showMushafPage(e.target.value);
            $('mushaf-surah').onchange = (e) => {
                const c = chapters.find(x => x.id === Number(e.target.value));
                if (c) showMushafPage(c.pages[0]);
            };
            $('mushaf-width').onchange = () => { fitMushaf(); persist(); };
            $('mushaf-search').oninput = () => { clearTimeout(searchTimer); searchTimer = setTimeout(runSearch, 250); };
            $('mushaf-search').onfocus = () => { if ($('search-results').children.length) $('search-results').classList.remove('hidden'); };
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.search-wrap')) $('search-results').classList.add('hidden');
            });
            $('mushaf-listen').onclick = () => { if (mushafSel) playMisc(mushafSel); };
            $('mushaf-copy').onclick = copySelectedVerse;
            window.addEventListener('resize', () => fitMushaf());
        }

        async function showMushafPage(n, hlKey, keepPlay) {
            if (!keepPlay) mushafPlayStop();
            n = Math.max(1, Math.min(604, parseInt(n) || 1));
            mushafPage = n;
            mushafLoaded = true;
            $('mushaf-page-input').value = n;
            const box = $('mushaf-page');
            box.innerHTML = '<div class="placeholder">⌛ جاري تحميل الصفحة...</div>';
            const data = await api().get_page(n);
            if (n !== mushafPage) return;                       // طُلبت صفحة أخرى أثناء التحميل
            if (!data) {
                box.innerHTML = '<div class="placeholder" style="color:#b91c1c">تعذر تحميل الصفحة. تحقق من الاتصال بالإنترنت.</div>';
                return;
            }
            mushafData = data;
            if (qcfAvailable) { try { await ensureQcfFonts(data.fonts); await getBismillah(); } catch (e) { /* نص عادي */ } }
            if (n !== mushafPage) return;
            renderMushaf(data);
            if (data.surahs && data.surahs.length) $('mushaf-surah').value = data.surahs[0].id;
            if (hlKey) selectVerse(hlKey, true); else clearVerseSel();
            syncMushafExtras();
            persist();
        }

        function glyphSpan(w, cls) {
            const sp = document.createElement('span');
            sp.className = cls;
            sp.style.fontFamily = `"${w.f}"`;
            sp.textContent = w.c;
            return sp;
        }

        function renderMushaf(data) {
            const box = $('mushaf-page');
            box.innerHTML = '';
            data.lines.forEach(line => {
                const row = document.createElement('div');
                row.className = 'mline';
                const first = line.w[0];
                if (!first) { box.appendChild(row); return; }
                if (first.t === 'surah_header') {
                    row.classList.add('mheader');
                    if (loadedQcfFonts.has(first.f)) row.appendChild(glyphSpan(first, 'mhead-glyph'));
                    else {
                        const b = document.createElement('div');
                        b.className = 'mhead-fallback';
                        b.textContent = `سورة ${chapName(first.s)}`;
                        row.appendChild(b);
                    }
                } else if (first.t === 'bismillah') {
                    row.classList.add('mbism');
                    if (bismillahWords) bismillahWords.forEach(w => row.appendChild(glyphSpan(w, 'mw')));
                    else if (loadedQcfFonts.has(first.f)) row.appendChild(glyphSpan(first, 'mw'));
                    else row.textContent = 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ';
                } else {
                    row.classList.add('mtext');
                    line.w.forEach(w => {
                        const sp = document.createElement('span');
                        sp.className = 'mw';
                        if (w.k) { sp.dataset.k = w.k; sp.onclick = () => selectVerse(w.k, false); }
                        if (loadedQcfFonts.has(w.f)) {
                            sp.style.fontFamily = `"${w.f}"`;
                            sp.textContent = w.c;
                        } else {
                            sp.classList.add('u');
                            sp.textContent = w.t === 'end' ? `﴿${toAr((w.k || '').split(':')[1] || '')}﴾` : (w.x || '');
                        }
                        row.appendChild(sp);
                    });
                }
                box.appendChild(row);
            });
            fitMushaf();
        }

        // يضبط حجم الخط: إمّا ليملأ العرض المختار، وإمّا (ملائم للشاشة) لتظهر الصفحة كاملة بلا تمرير
        function fitMushaf() {
            const box = $('mushaf-page');
            if (!box || !mushafData || !$('view-mushaf').classList.contains('active')) return;
            const scroll = $('mushaf-scroll');
            const availW = scroll.clientWidth - 32;
            const availH = scroll.clientHeight - 32;
            const PAD = 26;                                   // حشوة الصفحة الأفقية + الحدود
            const rows = [...box.querySelectorAll('.mline.mtext')];
            if (!rows.length) { box.style.setProperty('--ms', '30px'); return; }

            const S0 = 30;
            box.style.width = 'max-content';
            box.style.setProperty('--ms', S0 + 'px');
            rows.forEach(r => { r.classList.remove('justify'); r.classList.add('measure'); });
            const nat = rows.map(r => r.getBoundingClientRect().width);
            rows.forEach(r => r.classList.remove('measure'));
            const maxW = Math.max(...nat, 1);

            const mode = $('mushaf-width').value;
            let S, inner;
            if (mode === 'fit') {
                const sW = S0 * (Math.min(availW, 1100) - PAD) / maxW;
                const lines = Math.max(mushafData.lines.length, 8);
                const sH = (availH - 44) / (lines * 1.95 + 0.6);   // ارتفاع الأسطر + الحشوة
                S = Math.max(14, Math.min(sW, sH, 64));
                inner = maxW * S / S0;
            } else {
                const W = Math.max(320, Math.min(parseInt(mode) || 720, availW));
                inner = W - PAD;
                S = Math.min(S0 * inner / maxW, 64);
            }
            box.style.width = (inner + PAD) + 'px';
            box.style.setProperty('--ms', S + 'px');
            const centerAll = mushafData.page <= 2;
            rows.forEach((r, i) => {
                const w = nat[i] * S / S0;
                r.classList.toggle('justify', !centerAll && w >= 0.88 * inner);
            });
        }

        function clearVerseSel() {
            mushafSel = null;
            document.querySelectorAll('.mw.sel').forEach(e => e.classList.remove('sel'));
            $('mushaf-info').classList.add('hidden');
        }

        function selectVerse(key, scroll) {
            mushafSel = key;
            document.querySelectorAll('.mw.sel').forEach(e => e.classList.remove('sel'));
            const els = document.querySelectorAll(`.mw[data-k="${key}"]`);
            els.forEach(e => e.classList.add('sel'));
            const [s, a] = key.split(':').map(Number);
            $('mushaf-info-text').textContent = `سورة ${chapName(s)} · الآية ${a} · صفحة ${mushafPage}`;
            $('mushaf-info').classList.remove('hidden');
            showVerseTafsir(key);
            updateBmStar();
            if (scroll && els[0]) els[0].scrollIntoView({ block: 'center', behavior: 'smooth' });
        }

        async function copySelectedVerse() {
            if (!mushafSel) return;
            let text = '';
            const v = corpusReady ? await api().get_verse(mushafSel) : null;
            if (v) text = v.text;
            else if (mushafData) {
                text = mushafData.lines.flatMap(l => l.w).filter(w => w.k === mushafSel && w.t === 'word').map(w => w.x).join(' ');
            }
            const [s, a] = mushafSel.split(':').map(Number);
            const out = `${text} ﴿${a}﴾ [سورة ${chapName(s)}]`;
            const done = () => { $('mushaf-info-text').textContent += ' — تم النسخ ✓'; };
            if (navigator.clipboard) navigator.clipboard.writeText(out).then(done).catch(() => {});
            else {
                const ta = document.createElement('textarea');
                ta.value = out; document.body.appendChild(ta); ta.select();
                document.execCommand('copy'); ta.remove(); done();
            }
        }

        // ----- البحث: أسماء السور + كلمات الآيات + «2:255» أو «البقرة 255» -----
        async function runSearch() {
            const q = $('mushaf-search').value.trim();
            const box = $('search-results');
            if (!q) { box.classList.add('hidden'); box.innerHTML = ''; return; }
            const nq = normalizeAr(q);
            box.innerHTML = '';
            box.classList.remove('hidden');

            const addHead = (t) => { const h = document.createElement('div'); h.className = 'res-head'; h.textContent = t; box.appendChild(h); };
            const addNote = (t) => { const n = document.createElement('div'); n.className = 'res-note'; n.textContent = t; box.appendChild(n); };
            const goTo = (page, key) => { box.classList.add('hidden'); showMushafPage(page, key); };

            // 1) رقم السورة:الآية
            let ref = null;
            let m = q.match(/^(\d{1,3})\s*[:\-\/ ]\s*(\d{1,3})$/);
            if (m) ref = [Number(m[1]), Number(m[2])];
            else {
                m = nq.match(/^(.+?)\s+(\d{1,3})$/);
                if (m) {
                    const c = chapters.find(x => normalizeAr(x.name).includes(m[1]) || x.en.toLowerCase().includes(m[1].toLowerCase()));
                    if (c) ref = [c.id, Number(m[2])];
                }
            }
            if (ref) {
                if (!corpusReady) addNote('⌛ جاري تجهيز بيانات المصحف، أعد المحاولة بعد قليل...');
                else {
                    const v = await api().get_verse(`${ref[0]}:${ref[1]}`);
                    if (v) {
                        addHead('الانتقال إلى الآية');
                        box.appendChild(resultItem(v, goTo));
                    } else addNote('لا توجد آية بهذا الرقم.');
                }
            }

            // 2) أسماء السور
            const sm = chapters.filter(c =>
                String(c.id) === nq || (nq.length >= 2 && (normalizeAr(c.name).includes(nq) || c.en.toLowerCase().includes(nq.toLowerCase()))));
            if (sm.length) {
                addHead(`السور (${sm.length})`);
                sm.slice(0, 12).forEach(c => {
                    const it = document.createElement('div');
                    it.className = 'res-item';
                    const b = document.createElement('b');
                    b.textContent = `📖 سورة ${c.name} — ${c.verses} آية — صفحة ${c.pages[0]}`;
                    it.appendChild(b);
                    it.onclick = () => goTo(c.pages[0]);
                    box.appendChild(it);
                });
            }

            // 3) كلمات من الآيات
            if (!ref) {
                if (!corpusReady) addNote('⌛ جاري تجهيز بيانات المصحف للبحث في الآيات (أول مرة فقط)...');
                else if (nq.replace(/\s/g, '').length >= 2) {
                    const r = await api().search_verses(q, 60);
                    if ($('mushaf-search').value.trim() !== q) return;      // تغيّر النص أثناء البحث
                    if (r.total) {
                        addHead(`الآيات (${r.total})${r.total > r.results.length ? ' — تُعرض أول ' + r.results.length : ''}`);
                        r.results.forEach(v => box.appendChild(resultItem(v, goTo)));
                    } else if (!sm.length) addNote('لا نتائج.');
                } else if (!sm.length) addNote('اكتب حرفين على الأقل.');
            }
        }

        function resultItem(v, goTo) {
            const it = document.createElement('div');
            it.className = 'res-item';
            const b = document.createElement('b');
            b.textContent = `﴿سورة ${chapName(v.s)} : ${v.a}﴾ — صفحة ${v.page}`;
            const t = document.createElement('div');
            t.className = 'res-text';
            t.textContent = v.text;
            it.appendChild(b);
            it.appendChild(t);
            it.onclick = () => goTo(v.page, v.k);
            return it;
        }

        // =====================================================
        //  الاختبار
        // =====================================================
        const TOTAL_VERSES = 6236;
        const quiz = { mode: 'context', review: false, target: null, prev: [], next: [], seen: [],
                       asked: 0, known: 0, nameShown: false, textShown: true, words: 1, checked: false, busy: false };

        function setupQuizEvents() {
            $('quiz-start').onclick = quizStart;
            $('qz-setup').onclick = () => {
                miscAudio.pause();
                $('quiz-play').classList.add('hidden');
                $('quiz-setup').classList.remove('hidden');
                refreshSrsInfo();
            };
            $('qz-name').onclick = () => { quiz.nameShown = true; quizRender(false); };
            $('qz-prev').onclick = () => quizReveal('prev');
            $('qz-next').onclick = () => quizReveal('next');
            $('qz-listen').onclick = () => { if (quiz.target) playMisc(quiz.target.k); };
            $('qz-yes').onclick = () => quizMark(true);
            $('qz-no').onclick = () => quizMark(false);
            $('qz-skip').onclick = () => quizNew();
            $('qz-word').onclick = () => { quiz.words++; quizRender(false); };
            $('qz-rest').onclick = () => { quiz.words = 9999; quizRender(false); };
            $('qz-reveal').onclick = () => { quiz.textShown = true; quizRender(false); };
            $('qz-check').onclick = quizCheckGuess;
            $('quiz-mode').onchange = persist;
            $('quiz-review').onchange = persist;
            refreshSrsInfo();
        }

        async function refreshSrsInfo() {
            try {
                const x = await api().srs_summary();
                $('quiz-srs').textContent = `سجل المراجعة: ${x.seen} آية مسجّلة · مستحقة للمراجعة الآن: ${x.due} · متعثرة: ${x.weak} · متقنة: ${x.mastered}`;
                const t = $('srs-text');
                if (t) t.textContent = `آيات مسجّلة: ${x.seen} · مستحقة الآن: ${x.due} · متعثرة: ${x.weak} · متقنة: ${x.mastered}`;
            } catch (e) { /* تجاهل */ }
        }

        async function quizStart() {
            const msg = $('quiz-msg');
            msg.textContent = '';
            const st = await api().corpus_status();
            if (!st.ready) {
                msg.textContent = st.error
                    ? '⚠️ ' + st.error
                    : `⌛ جاري تجهيز بيانات المصحف (${st.done}/${st.total}) — أعد المحاولة بعد قليل.`;
                return;
            }
            corpusReady = true;
            quiz.mode = $('quiz-mode').value;
            quiz.review = $('quiz-review').checked;
            quiz.seen = []; quiz.asked = 0; quiz.known = 0;
            $('quiz-setup').classList.add('hidden');
            $('quiz-play').classList.remove('hidden');
            persist();
            await quizNew();
        }

        async function quizNew() {
            if (quiz.busy) return;
            quiz.busy = true;
            try {
                miscAudio.pause();
                const from = $('quiz-from').value, to = $('quiz-to').value;
                let v = null, note = '';
                if (quiz.review) {
                    v = await api().srs_pick_due(from, to, quiz.seen.map(i => i));
                    if (!v) note = 'لا آيات مستحقة للمراجعة الآن في هذا المجال؛ اختيرت آية عشوائية.';
                }
                if (!v) v = await api().random_verse(from, to, quiz.seen);
                if (!v) { $('qz-setup').click(); $('quiz-msg').textContent = 'تعذر اختيار آية من هذا المجال.'; return; }
                quiz.seen.push(v.i);
                if (quiz.seen.length > 400) quiz.seen.shift();
                quiz.target = v; quiz.prev = []; quiz.next = []; quiz.nameShown = false;
                quiz.checked = false;
                quiz.textShown = quiz.mode !== 'audio';
                const n = v.words.filter(w => !w.e).length;
                quiz.words = n <= 1 ? 1 : Math.min(n - 1, Math.max(2, Math.round(n * 0.3)));
                $('qg-ayah').value = '';
                $('qg-result').textContent = note;
                $('qz-check').disabled = false;
                await prepFonts([v]);
                quizRender(true);
                if (quiz.mode === 'audio') playMisc(v.k);
            } finally { quiz.busy = false; }
        }

        function quizMark(known) {
            if (!quiz.target) return;
            quiz.asked++;
            if (known) quiz.known++;
            api().srs_record(quiz.target.k, known).then(refreshSrsInfo);
            quizNew();
        }

        function quizCheckGuess() {
            const t = quiz.target;
            if (!t || quiz.checked) return;
            const s = Number($('qg-surah').value), a = Number($('qg-ayah').value);
            const okS = s === t.s, okA = a === t.a;
            const correct = okS && okA;
            quiz.checked = true;
            quiz.nameShown = true;
            quiz.asked++;
            if (correct) quiz.known++;
            api().srs_record(t.k, correct).then(refreshSrsInfo);
            $('qg-result').textContent = correct
                ? '✅ صحيح!'
                : `❌ الصواب: سورة ${chapName(t.s)} · الآية ${t.a}${okS ? ' (السورة صحيحة)' : ''}`;
            $('qz-check').disabled = true;
            quizRender(false);
        }

        async function quizReveal(dir) {
            if (quiz.busy || !quiz.target) return;
            const t = quiz.target;
            const idx = dir === 'prev' ? t.i - quiz.prev.length - 1 : t.i + quiz.next.length + 1;
            if (idx < 0 || idx >= TOTAL_VERSES) return;
            quiz.busy = true;
            try {
                const v = await api().get_verse_at(idx);
                if (!v) return;
                await prepFonts([v]);
                (dir === 'prev' ? quiz.prev : quiz.next).push(v);
                quizRender(false, v.i);
            } finally { quiz.busy = false; }
        }

        function quizCard(v, kind, showEnd) {
            const d = document.createElement('div');
            d.className = 'quiz-card ' + kind;
            d.dataset.i = v.i;
            if (quiz.nameShown) {
                const l = document.createElement('div');
                l.className = 'quiz-label';
                l.textContent = `سورة ${chapName(v.s)} · الآية ${v.a} · صفحة ${v.page}`;
                d.appendChild(l);
            }
            const body = document.createElement('div');
            fillVerse(body, v, showEnd === undefined ? quiz.nameShown : showEnd);   // رقم الآية يظهر مع اسم السورة فقط
            d.appendChild(body);
            return d;
        }

        function quizTargetCard() {
            const t = quiz.target;
            if (quiz.mode === 'audio' && !quiz.textShown) {
                const d = document.createElement('div');
                d.className = 'quiz-ph target';
                d.textContent = '🎧 استمع إلى الآية ثم خمّن السورة والآيات المجاورة — اضغط هنا لإظهار نص الآية';
                d.onclick = () => { quiz.textShown = true; quizRender(false); };
                return d;
            }
            let v = t;
            if (quiz.mode === 'complete') {
                const ws = t.words.filter(w => !w.e);
                if (quiz.words < ws.length) {
                    v = Object.assign({}, t, { words: ws.slice(0, quiz.words), text: t.text.split(' ').slice(0, quiz.words).join(' '), partial: true });
                }
            }
            return quizCard(v, 'target');
        }

        function quizPlaceholder(dir) {
            const d = document.createElement('div');
            d.className = 'quiz-ph';
            d.textContent = dir === 'prev'
                ? '⬆ الآية السابقة (مظلّلة) — اضغط لإظهارها'
                : '⬇ الآية التالية (مظلّلة) — اضغط لإظهارها';
            d.onclick = () => quizReveal(dir);
            return d;
        }

        function quizToolbar() {
            const m = quiz.mode, t = quiz.target;
            const nWords = t ? t.words.filter(w => !w.e).length : 0;
            $('qz-name').classList.toggle('hidden', m === 'number');
            $('qz-prev').classList.toggle('hidden', m === 'number');
            $('qz-next').classList.toggle('hidden', m === 'number');
            $('qz-yes').classList.toggle('hidden', m === 'number');
            $('qz-no').classList.toggle('hidden', m === 'number');
            $('qz-word').classList.toggle('hidden', !(m === 'complete' && quiz.words < nWords));
            $('qz-rest').classList.toggle('hidden', !(m === 'complete' && quiz.words < nWords));
            $('qz-reveal').classList.toggle('hidden', !(m === 'audio' && !quiz.textShown));
            $('quiz-guess').classList.toggle('hidden', m !== 'number');
            $('qz-skip').textContent = m === 'number' ? '⏭ التالي' : '⏭ آية أخرى';
        }

        function quizRender(scrollTarget, focusIdx) {
            const stage = $('quiz-stage');
            const t = quiz.target;
            if (!t) return;
            const keep = stage.scrollTop;
            stage.innerHTML = '';
            const ctx = quiz.mode !== 'number';
            const canPrev = ctx && t.i - quiz.prev.length - 1 >= 0;
            const canNext = ctx && t.i + quiz.next.length + 1 < TOTAL_VERSES;
            if (canPrev) stage.appendChild(quizPlaceholder('prev'));
            [...quiz.prev].reverse().forEach(v => stage.appendChild(quizCard(v, 'ctx')));
            const tc = quizTargetCard();
            tc.id = 'quiz-target';
            stage.appendChild(tc);
            quiz.next.forEach(v => stage.appendChild(quizCard(v, 'ctx')));
            if (canNext) stage.appendChild(quizPlaceholder('next'));

            $('qz-prev').disabled = !canPrev;
            $('qz-next').disabled = !canNext;
            $('qz-name').disabled = quiz.nameShown;
            $('quiz-stats').textContent = `الأسئلة: ${quiz.asked} · عرفتها: ${quiz.known}`;
            quizToolbar();

            if (scrollTarget) tc.scrollIntoView({ block: 'center' });
            else if (focusIdx !== undefined) {
                const el = stage.querySelector(`.quiz-card[data-i="${focusIdx}"]`);
                if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else stage.scrollTop = keep;
        }

        // =====================================================
        //  المظهر، شريط المعلومات، القائمة الجانبية، الصوت دون إنترنت
        // =====================================================
        let darkMode = false;
        let statusBarOn = true;
        let offlineHas = {};
        let playToken = 0;
        let currentAudio = { remote: '', offline: false };
        let toastTimer = null;
        const toAr = (n) => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
        const fmtBytes = (b) => b >= 1073741824 ? (b / 1073741824).toFixed(2) + ' غيغابايت'
            : b >= 1048576 ? (b / 1048576).toFixed(1) + ' ميغابايت' : Math.round(b / 1024) + ' كيلوبايت';

        function applyPrefs() {
            const sysDark = !!(window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
            setDark(settings.dark !== undefined ? !!settings.dark : sysDark, false);
            setStatusBar(settings.statusbar !== false, false);
        }

        function setDark(v, save = true) {
            darkMode = v;
            document.body.classList.toggle('dark', v);
            $('theme-btn').textContent = v ? '☀️' : '🌙';
            $('set-dark').checked = v;
            if (save) persist();
        }

        function setStatusBar(v, save = true) {
            statusBarOn = v;
            statusBar.classList.toggle('hidden', !v);
            $('show-status').checked = v;
            $('set-status').checked = v;
            if (save) persist();
            if (v) fitFocus(); else setTimeout(fitFocus, 0);
        }

        function showToast(msg, info) {
            const t = $('toast');
            t.style.background = info ? '#166534' : '#b91c1c';
            t.textContent = msg;
            t.classList.remove('hidden');
            clearTimeout(toastTimer);
            toastTimer = setTimeout(() => t.classList.add('hidden'), 5000);
        }

        // ---- تشغيل الصوت: الملف المحمّل إن وُجد، وإلا الرابط على الإنترنت ----
        async function resolveAudio(rec, key, remote) {
            if (offlineHas[rec.id]) {
                try {
                    const [s, a] = key.split(':').map(Number);
                    const f = await api().get_audio(rec.id, s, a);
                    if (f) {
                        const bin = atob(f.data);
                        const bytes = new Uint8Array(bin.length);
                        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
                        return { url: URL.createObjectURL(new Blob([bytes], { type: f.mime })), offline: true };
                    }
                } catch (e) { /* نكمل بالرابط على الإنترنت */ }
            }
            return { url: remote, offline: false };
        }

        function setSrc(el, res) {
            if (el._blob) { URL.revokeObjectURL(el._blob); el._blob = null; }
            if (res.offline) el._blob = res.url;
            el.src = res.url;
        }

        // ---- القائمة الجانبية ----
        function openDrawer() {
            $('drawer-overlay').classList.remove('hidden');
            $('drawer').classList.remove('hidden');
            onDrawerOpened();
            refreshOffline();
            refreshStorage();
        }
        function closeDrawer() {
            $('drawer-overlay').classList.add('hidden');
            $('drawer').classList.add('hidden');
        }

        async function setupDrawer() {
            $('menu-btn').onclick = openDrawer;
            $('dr-close').onclick = closeDrawer;
            $('drawer-overlay').onclick = closeDrawer;
            document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });
            $('theme-btn').onclick = () => setDark(!darkMode);
            $('set-dark').onchange = (e) => setDark(e.target.checked);
            $('set-status').onchange = (e) => setStatusBar(e.target.checked);
            $('show-status').onchange = (e) => setStatusBar(e.target.checked);

            // حول التطبيق + وسائل التواصل
            let info = { name: 'مقرأة القرآن الكريم', version: '', contacts: [], developer: '', email: '', platform: '' };
            try { info = await api().app_info(); } catch (e) { /* افتراضي */ }
            $('dr-title').textContent = info.name;
            $('dr-ver').textContent = info.version ? 'الإصدار ' + info.version : '';
            $('about-name').textContent = `${info.name} ${info.version}`;
            $('about-dev').textContent = info.developer ? 'تطوير: ' + info.developer : '';
            $('about-sys').textContent = info.platform ? 'النظام: ' + info.platform : '';
            const box = $('contact-links');
            box.innerHTML = '';
            if (!info.contacts.length) {
                const n = document.createElement('div');
                n.className = 'dr-muted';
                n.textContent = 'لم تُضبط وسائل التواصل بعد.';
                box.appendChild(n);
            }
            info.contacts.forEach(c => {
                const b = document.createElement('button');
                b.className = 'btn sm alt';
                b.textContent = `${c.icon} ${c.label}`;
                b.onclick = () => api().open_link(c.url);
                box.appendChild(b);
            });
            $('sug-send').onclick = () => {
                const text = $('sug-text').value.trim();
                const msg = $('sug-msg');
                if (!text) { msg.textContent = 'اكتب رسالتك أولًا.'; return; }
                const body = `${text}\n\n---\nالإصدار: ${info.version}\nالنظام: ${info.platform}`;
                if (!info.has_email) {
                    msg.textContent = 'لم يُضبط بريد التواصل في التطبيق.';
                    return;
                }
                const sub = `[${info.name}] ${$('sug-type').value}`;
                api().compose_email(sub, body).then(r => {
                    if (!r.ok) { msg.textContent = 'تعذر فتح واجهة البريد.'; return; }
                    msg.textContent = r.provider === 'mailto'
                        ? 'تم فتح برنامج البريد على جهازك، اضغط «إرسال» هناك.'
                        : `تم فتح واجهة ${r.provider} وفيها رسالتك جاهزة، اضغط «إرسال» هناك.`;
                });
            };

            // الصوت دون إنترنت
            const sel = $('off-reciter');
            sel.innerHTML = '';
            reciters.forEach(r => {
                const o = document.createElement('option');
                o.value = r.id;
                o.textContent = r.label;
                sel.appendChild(o);
            });
            sel.value = riwayaSelect.value;
            $('off-from').onchange = updateOffEstimate;
            $('off-to').onchange = updateOffEstimate;
            $('off-start').onclick = startOffline;
            $('off-cancel').onclick = () => api().offline_cancel();
            updateOffEstimate();
            refreshOffline();
            pollOffline(true);

            // التخزين
            $('clear-cache').onclick = async () => {
                const n = await api().clear_cache();
                $('storage-msg').textContent = `تم مسح ${n} ملف. ستُعاد بيانات المصحف عند الحاجة.`;
                refreshStorage();
            };
            $('reset-settings').onclick = async () => {
                await api().reset_settings();
                $('storage-msg').textContent = 'أُعيد ضبط الإعدادات. أعد تشغيل التطبيق لتطبيقها.';
            };
        }

        function updateOffEstimate() {
            const a = Number($('off-from').value), b = Number($('off-to').value);
            const lo = Math.min(a, b), hi = Math.max(a, b);
            const n = chapters.filter(c => c.id >= lo && c.id <= hi).reduce((x, c) => x + c.verses, 0);
            $('off-estimate').textContent = `عدد الملفات الصوتية (ملف لكل آية): ${n}. قد يستغرق تحميل المصحف كاملًا وقتًا ومساحة كبيرة.`;
        }

        async function refreshOffline() {
            let sum = {};
            try { sum = await api().offline_summary(); } catch (e) { return; }
            offlineHas = {};
            const list = $('off-list');
            list.innerHTML = '';
            reciters.forEach(r => {
                const x = sum[r.id];
                offlineHas[r.id] = !!(x && x.files > 0);
                if (!offlineHas[r.id]) return;
                const row = document.createElement('div');
                row.className = 'off-item';
                const t = document.createElement('span');
                t.textContent = `${r.label} — ${x.files} ملف — ${fmtBytes(x.bytes)}`;
                const d = document.createElement('button');
                d.className = 'btn sm alt';
                d.textContent = 'حذف';
                d.onclick = async () => {
                    if (!(await api().offline_delete(r.id))) { $('off-text').textContent = 'تعذر الحذف أثناء التحميل.'; return; }
                    refreshOffline();
                };
                row.appendChild(t);
                row.appendChild(d);
                list.appendChild(row);
            });
        }

        async function startOffline() {
            const st = await api().offline_start($('off-reciter').value, $('off-from').value, $('off-to').value);
            if (st.error) { $('off-text').textContent = '⚠️ ' + st.error; return; }
            pollOffline(false);
        }

        async function pollOffline(silent) {
            let st;
            try { st = await api().offline_status(); } catch (e) { return; }
            const bar = $('off-progress');
            if (st.running) {
                bar.classList.remove('hidden');
                bar.max = Math.max(st.total, 1);
                bar.value = st.done;
                $('off-start').disabled = true;
                $('off-cancel').classList.remove('hidden');
                $('off-text').textContent = `${st.done}/${st.total} — تم تنزيل ${fmtBytes(st.bytes)} — فشل ${st.failed} — غير متوفر ${st.missing}`;
                setTimeout(() => pollOffline(false), 700);
                return;
            }
            $('off-start').disabled = false;
            $('off-cancel').classList.add('hidden');
            if (!silent && st.total) {
                bar.value = st.done;
                $('off-text').textContent = `انتهى: ${st.done}/${st.total} — فشل ${st.failed} — غير متوفر ${st.missing} — تم تنزيل ${fmtBytes(st.bytes)}`
                    + (st.failed ? ' (أعد التحميل لإكمال الفاشل)' : ' ✓');
                refreshOffline();
            } else bar.classList.add('hidden');
        }

        async function refreshStorage() {
            try {
                const x = await api().storage_info();
                $('storage-text').textContent =
                    `الذاكرة المؤقتة: ${fmtBytes(x.cache_bytes)} (${x.cache_files} ملف)\n` +
                    `الصوتيات المحمّلة: ${fmtBytes(x.audio_bytes)} (${x.audio_files} ملف)\n` +
                    `مجلد الصوتيات: ${x.audio_path}`;
                $('storage-text').style.whiteSpace = 'pre-line';
                $('storage-text').style.userSelect = 'text';
            } catch (e) { /* تجاهل */ }
        }

        // =====================================================
        //  تفسير، علامات، ورد، تلاوة المصحف، مؤقّت النوم، الوضع المصغّر
        // =====================================================
        const JUZ_PAGES = [1, 22, 42, 62, 82, 102, 121, 142, 162, 182, 201, 222, 242, 262, 282,
                           302, 322, 342, 362, 382, 402, 422, 442, 462, 482, 502, 522, 542, 562, 582];
        let tafsirId = '';
        const tafsirCache = {};
        let bookmarks = [];
        let wirdState = null;
        const mplay = { active: false, keys: [], i: 0, last: null, errors: 0 };
        let sleepEnd = 0, sleepTimer = null, miniSync = null;

        async function setupExtras() {
            // التفسير
            const sel = $('tafsir-select');
            sel.innerHTML = '<option value="">بلا تفسير</option>';
            try {
                (await api().tafsir_editions()).forEach(e => {
                    const o = document.createElement('option');
                    o.value = e.id; o.textContent = e.label; sel.appendChild(o);
                });
            } catch (e) { /* تجاهل */ }
            tafsirId = settings.tafsir || '';
            sel.value = tafsirId;
            sel.onchange = () => { tafsirId = sel.value; persist(); fillTafsirCards(); if (mushafSel) showVerseTafsir(mushafSel); else { $('mushaf-tafsir').classList.add('hidden'); fitMushaf(); } };

            // الجزء
            const juz = $('mushaf-juz');
            juz.innerHTML = '';
            let nav = null;
            try { nav = await api().get_navigation(); } catch (e) { nav = null; }
            if (nav && nav.juz.length === 30) nav.juz.forEach((j, i) => { JUZ_PAGES[i] = j.page; });
            buildRubSelect(nav);
            JUZ_PAGES.forEach((p, i) => {
                const o = document.createElement('option');
                o.value = p; o.textContent = `الجزء ${i + 1} (ص ${p})`;
                juz.appendChild(o);
            });
            juz.onchange = () => showMushafPage(juz.value);

            // العلامات والورد
            $('bm-add').onclick = toggleBookmark;
            $('bm-list').onclick = () => {
                const panel = $('bm-panel');
                panel.classList.toggle('hidden');
                if (!panel.classList.contains('hidden')) {          // نضعها داخل حدود الشاشة مهما كان موضع الزر
                    const r = $('bm-list').getBoundingClientRect();
                    panel.style.top = (r.bottom + 4) + 'px';
                    panel.style.left = Math.max(8, Math.min(r.right - 330, window.innerWidth - 338)) + 'px';
                }
            };
            document.addEventListener('click', (e) => { if (!e.target.closest('.bm-wrap')) $('bm-panel').classList.add('hidden'); });
            $('wird-btn').onclick = toggleWirdPage;
            $('wird-save').onclick = async () => { wirdState = await api().wird_set_target($('wird-target').value); updateWirdUi(); };
            $('srs-reset').onclick = async () => { await api().srs_reset(); refreshSrsInfo(); };
            refreshBookmarks();
            refreshWird();
            refreshSrsInfo();

            // تلاوة المصحف المتتابعة
            $('mp-play').onclick = () => { if (mplay.active) mushafPlayStop(); else mushafPlayStart(); };
            miscAudio.onended = () => { if (mplay.active) { mplay.i++; mplay.errors = 0; mushafPlayNext(); } };
            miscAudio.onerror = () => {
                if (!mplay.active || !miscAudio.getAttribute('src')) return;
                mplay.errors++;
                if (mplay.errors <= 3) { mplay.i++; setTimeout(mushafPlayNext, 800); } else mushafPlayStop();
            };

            // مؤقّت النوم والوضع المصغّر
            $('sleep-select').onchange = () => startSleep(Number($('sleep-select').value));
            $('sleep-chip').onclick = cancelSleep;
            $('mini-btn').onclick = () => toggleMini(true);
            $('mini-btn2').onclick = () => { closeDrawer(); toggleMini(true); };
            $('mini-exit').onclick = () => toggleMini(false);
            $('mini-prev').onclick = () => $('btn-prev').click();
            $('mini-next').onclick = () => $('btn-next').click();
            $('mini-play').onclick = () => btnPlay.click();
            initAnalytics();
            loadUiFonts();
            setupMatn();
            initWhatsNew();
        }

        // ---- عدّاد المستخدمين المجهول (بموافقة صريحة فقط) ----
        async function initAnalytics() {
            let st;
            try { st = await api().analytics_state(); } catch (e) { return; }
            if (!st.enabled) { $('privacy-sec').classList.add('hidden'); return; }      // الميزة معطّلة في هذه النسخة
            showAnalyticsState(st);
            $('set-analytics').onchange = async (e) => {
                showAnalyticsState(await api().analytics_set(e.target.checked));
                if (e.target.checked) api().analytics_ping();
            };
            $('consent-yes').onclick = async () => {
                showAnalyticsState(await api().analytics_set(true));
                $('consent-overlay').classList.add('hidden');
                api().analytics_ping();
            };
            $('consent-no').onclick = async () => {
                showAnalyticsState(await api().analytics_set(false));
                $('consent-overlay').classList.add('hidden');
            };
            if (st.consent === null) $('consent-overlay').classList.remove('hidden');   // أول تشغيل: نسأل
            else if (st.consent === true) api().analytics_ping();
        }
        function showAnalyticsState(st) {
            $('set-analytics').checked = st.consent === true;
            $('analytics-id').textContent = st.consent === true && st.id ? 'معرّفك العشوائي: ' + st.id : '';
        }

        // ---- خطوط الواجهة من مستودع البيانات (بدل Google Fonts) ----
        async function loadUiFonts() {
            let list = [];
            try { list = await api().ui_fonts_list(); } catch (e) { return; }
            for (const f of list) {
                try {
                    const d = await api().get_ui_font(f.name);
                    if (!d) continue;
                    const face = new FontFace(d.family, `url(data:${d.mime};base64,${d.data})`, { weight: d.weight });
                    await face.load();
                    document.fonts.add(face);
                } catch (e) { /* نكمل بالخطوط البديلة */ }
            }
            if (typeof fitFocus === 'function') fitFocus();
        }

        // ---- التفسير ----
        async function getTafsir(id, surah) {
            const k = id + ':' + surah;
            if (!(k in tafsirCache)) tafsirCache[k] = await api().get_tafsir(id, surah);
            return tafsirCache[k];
        }
        function tafsirFor(map, n) {
            if (map[String(n)]) return map[String(n)];
            for (let i = n - 1; i >= 1; i--) if (map[String(i)]) return '↑ ' + map[String(i)];
            return '';
        }
        async function fillTafsirCards() {
            document.querySelectorAll('.tafsir-text').forEach(e => e.remove());
            if (!tafsirId || !ayahsData.length) return;
            const surah = currentSurah;
            const map = await getTafsir(tafsirId, surah);
            if (!map) { showToast('تعذر جلب التفسير (تحقق من الاتصال بالإنترنت).'); return; }
            if (surah !== currentSurah) return;
            ayahsData.forEach((a, i) => {
                const card = $('ayah-' + i);
                if (!card) return;
                const d = document.createElement('div');
                d.className = 'tafsir-text';
                d.dir = 'auto';
                d.textContent = tafsirFor(map, a.numberInSurah);
                card.appendChild(d);
            });
            fitFocus();
        }
        async function showVerseTafsir(key) {
            const box = $('mushaf-tafsir');
            if (!tafsirId) { box.classList.add('hidden'); fitMushaf(); return; }
            const [s, a] = key.split(':').map(Number);
            const map = await getTafsir(tafsirId, s);
            if (mushafSel !== key) return;
            if (!map) { box.textContent = 'تعذر جلب التفسير (تحقق من الاتصال بالإنترنت).'; box.classList.remove('hidden'); return; }
            box.dir = 'auto';
            box.textContent = tafsirFor(map, a);
            box.classList.remove('hidden');
            fitMushaf();
        }

        // ---- العلامات المرجعية ----
        function currentBookmarkKey() {
            if (mushafSel) return mushafSel;
            if (!mushafData) return null;
            const w = mushafData.lines.flatMap(l => l.w).find(x => x.k);
            return w ? w.k : null;
        }
        async function refreshBookmarks() {
            try { bookmarks = await api().bookmarks_list(); } catch (e) { bookmarks = []; }
            $('bm-count').textContent = bookmarks.length;
            const panel = $('bm-panel');
            panel.innerHTML = '';
            if (!bookmarks.length) {
                const n = document.createElement('div');
                n.className = 'res-note';
                n.textContent = 'لا علامات بعد. حدّد آية ثم اضغط «☆ علامة».';
                panel.appendChild(n);
            }
            bookmarks.forEach(b => {
                const [s, a] = b.k.split(':').map(Number);
                const row = document.createElement('div');
                row.className = 'bm-item';
                const t = document.createElement('span');
                t.textContent = `⭐ سورة ${chapName(s)} : ${a} — ص ${b.page}`;
                const d = document.createElement('button');
                d.className = 'btn sm alt';
                d.textContent = '✕';
                d.onclick = async (e) => { e.stopPropagation(); await api().bookmark_remove(b.k); refreshBookmarks(); };
                row.onclick = () => { $('bm-panel').classList.add('hidden'); showMushafPage(b.page, b.k); };
                row.appendChild(t); row.appendChild(d);
                panel.appendChild(row);
            });
            updateBmStar();
        }
        function updateBmStar() {
            const k = currentBookmarkKey();
            $('bm-add').textContent = (k && bookmarks.some(b => b.k === k)) ? '★ علامة' : '☆ علامة';
        }
        async function toggleBookmark() {
            const k = currentBookmarkKey();
            if (!k) return;
            if (bookmarks.some(b => b.k === k)) await api().bookmark_remove(k);
            else await api().bookmark_add(k, mushafPage);
            refreshBookmarks();
        }

        // ---- الورد اليومي ----
        async function refreshWird() {
            try { wirdState = await api().wird_get(); } catch (e) { return; }
            updateWirdUi();
        }
        function updateWirdUi() {
            if (!wirdState) return;
            const w = wirdState;
            $('wird-chip').textContent = `📅 الورد: ${w.done}/${w.target} صفحة · 🔥 ${w.streak} يوم`;
            const read = w.today.includes(mushafPage);
            $('wird-btn').textContent = read ? '✓ مقروءة اليوم' : '✓ قرأتُ هذه الصفحة';
            $('wird-btn').classList.toggle('on', read);
            if ($('wird-target') !== document.activeElement) $('wird-target').value = w.target;
            $('wird-text').textContent = `أيام مسجّلة: ${w.days} · تسلسل الأيام المنجزة: ${w.streak}`;
        }
        async function toggleWirdPage() {
            const read = wirdState && wirdState.today.includes(mushafPage);
            wirdState = await api().wird_mark(mushafPage, !read);
            updateWirdUi();
        }
        let RUBS = [];
        function buildRubSelect(nav) {
            const sel = $('mushaf-rub');
            sel.innerHTML = '';
            if (!nav || nav.rub.length !== 240) { sel.classList.add('hidden'); return; }
            RUBS = nav.rub;
            const ph = document.createElement('option');
            ph.value = ''; ph.textContent = 'الحزب / الربع';
            sel.appendChild(ph);
            const quarters = ['', 'الأول', 'الثاني', 'الثالث', 'الرابع'];
            let group = null, lastJuz = 0;
            RUBS.forEach((r, i) => {
                if (r.juz !== lastJuz) {
                    group = document.createElement('optgroup');
                    group.label = `الجزء ${r.juz}`;
                    sel.appendChild(group);
                    lastJuz = r.juz;
                }
                const o = document.createElement('option');
                o.value = i;
                o.textContent = `الحزب ${r.hizb} — الربع ${quarters[r.quarter]} (ص ${r.page})`;
                group.appendChild(o);
            });
            sel.onchange = () => {
                if (sel.value === '') return;
                const r = RUBS[Number(sel.value)];
                showMushafPage(r.page, `${r.surah}:${r.ayah}`);
            };
        }

        function syncMushafExtras() {
            const juz = $('mushaf-juz');
            if (RUBS.length) {
                let cur = 0;
                RUBS.forEach((r, i) => { if (r.page <= mushafPage) cur = i; });
                $('mushaf-rub').value = String(cur);
            }
            let idx = 0;
            JUZ_PAGES.forEach((p, i) => { if (p <= mushafPage) idx = i; });
            juz.value = JUZ_PAGES[idx];
            updateWirdUi();
            updateBmStar();
        }

        // ---- تلاوة صفحة المصحف بالتتابع ----
        function pageVerseKeys() {
            const seen = new Set(), keys = [];
            mushafData.lines.forEach(l => l.w.forEach(w => { if (w.k && !seen.has(w.k)) { seen.add(w.k); keys.push(w.k); } }));
            return keys;
        }
        async function mushafPlayStart() {
            if (!mushafData) return;
            audioPlayer.pause();
            mplay.active = true;
            mplay.errors = 0;
            const keys = pageVerseKeys();
            let start = mushafSel ? keys.indexOf(mushafSel) : 0;
            if (start < 0) start = 0;
            mplay.keys = keys;
            mplay.i = start;
            $('mp-play').textContent = '⏹ إيقاف التلاوة';
            await mushafPlayNext();
        }
        async function mushafPlayNext() {
            if (!mplay.active) return;
            if (mplay.i >= mplay.keys.length) {
                if ($('mp-auto').checked && mushafPage < 604) {
                    await showMushafPage(mushafPage + 1, null, true);
                    if (!mplay.active) return;
                    const keys = pageVerseKeys();
                    if (keys.length && keys[0] === mplay.last) keys.shift();    // آية مكتملة من الصفحة السابقة
                    mplay.keys = keys;
                    mplay.i = 0;
                    return mushafPlayNext();
                }
                mushafPlayStop();
                return;
            }
            const key = mplay.keys[mplay.i];
            mplay.last = key;
            selectVerse(key, true);
            const res = await resolveAudio(currentReciter(), key, verseUrl(key));
            if (!mplay.active) return;
            setSrc(miscAudio, res);
            miscAudio.play().catch(() => {});
        }
        function mushafPlayStop() {
            if (!mplay.active) return;
            mplay.active = false;
            miscAudio.pause();
            $('mp-play').textContent = '▶ تلاوة الصفحة';
        }

        // ---- مؤقّت النوم ----
        function startSleep(min) {
            cancelSleep(true);
            if (!min) return;
            sleepEnd = Date.now() + min * 60000;
            sleepTimer = setInterval(tickSleep, 1000);
            tickSleep();
            showToast(`سيتوقف الصوت بعد ${min} دقيقة.`, true);
        }
        function tickSleep() {
            const left = sleepEnd - Date.now();
            const chip = $('sleep-chip');
            if (left <= 0) {
                stopAllAudio();
                cancelSleep(false);
                showToast('انتهى مؤقّت النوم. تقبّل الله منكم.', true);
                return;
            }
            const m = Math.floor(left / 60000), sec = Math.floor(left / 1000) % 60;
            chip.classList.remove('hidden');
            chip.textContent = `💤 ${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
            if (left <= 8000) { const v = Math.max(0, left / 8000); audioPlayer.volume = v; miscAudio.volume = v; localAudio.volume = mt.settings.volume * v; }
        }
        function cancelSleep(silent) {
            clearInterval(sleepTimer);
            sleepTimer = null;
            $('sleep-chip').classList.add('hidden');
            audioPlayer.volume = 1;
            miscAudio.volume = 1;
            localAudio.volume = mt.settings.volume;
            $('sleep-select').value = '0';
        }

        // ---- الوضع المصغّر ----
        async function toggleMini(on) {
            if (on) { switchView('recite'); document.body.classList.add('mini'); }
            else document.body.classList.remove('mini');
            clearInterval(miniSync);
            if (on) miniSync = setInterval(() => { $('mini-play').textContent = btnPlay.textContent.includes('إيقاف') ? '⏸' : '▶'; }, 400);
            syncFocus();
            let r = { ok: true };
            try { r = await api().set_window_mode(on); } catch (e) { r = { ok: false }; }
            if (!r.ok && on) showToast('تعذّر تصغير النافذة تلقائيًا؛ صغّرها يدويًا (الواجهة المصغّرة مفعّلة).');
            setTimeout(syncFocus, 350);
        }

        // =====================================================
        //  ما الجديد
        // =====================================================
        let wnState = { has_new: false, current: '' };

        async function initWhatsNew() {
            let log = [];
            try { log = await api().get_changelog(); wnState = await api().whatsnew_state(); } catch (e) { return; }
            const box = $('wn-body');
            box.innerHTML = '';
            log.forEach((rel, i) => {
                const wrap = document.createElement(i === 0 ? 'div' : 'details');
                if (i > 0) {
                    const sm = document.createElement('summary');
                    sm.textContent = `الإصدار \u2066${rel.version}\u2069${rel.date ? ' — \u2066' + rel.date + '\u2069' : ''}`;
                    wrap.appendChild(sm);
                } else {
                    const h = document.createElement('div');
                    h.className = 'wn-ver';
                    h.textContent = `الإصدار \u2066${rel.version}\u2069`;
                    const sm = document.createElement('small');
                    sm.textContent = rel.date ? '\u2066' + rel.date + '\u2069' : '';
                    h.appendChild(sm);
                    wrap.appendChild(h);
                }
                const ul = document.createElement('ul');
                ul.className = 'wn-list';
                rel.items.forEach(t => { const li = document.createElement('li'); li.textContent = t; ul.appendChild(li); });
                wrap.appendChild(ul);
                box.appendChild(wrap);
            });
            refreshWnDot();
            if (wnState.has_new) showToast(`✨ جديد في الإصدار ${wnState.current} — افتح القائمة ☰ لتعرف المزايا الجديدة.`, true);
        }

        function refreshWnDot() {
            $('menu-dot').classList.toggle('hidden', !wnState.has_new);
            $('wn-badge').classList.toggle('hidden', !wnState.has_new);
        }

        async function onDrawerOpened() {
            if (!wnState.has_new) return;
            $('wn-sec').open = true;                                  // نعرض الجديد أول ما يفتح القائمة بعد التحديث
            try { await api().whatsnew_mark_seen(); } catch (e) { /* تجاهل */ }
            wnState.has_new = false;
            $('menu-dot').classList.add('hidden');                    // نُبقي شارة «جديد» حتى يغلق القائمة
        }

        // =====================================================
        //  مشغّل المتون: ملفات صوتية من جهازك
        // =====================================================
        const localAudio = new Audio();
        localAudio.preload = 'metadata';
        const mt = {
            files: [], idx: -1, a: null, b: null, abOn: false, loops: 0, pendingPos: 0,
            gapTimer: null, watch: null, saveTimer: null,
            settings: { speed: 1, repeat: 1, gap: 0, autoNext: true, loopAll: false, volume: 1, pitch: true },
        };

        const fmtTime = (t) => {
            t = Math.max(0, Math.floor(t || 0));
            const h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60), s = t % 60;
            return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(s).padStart(2, '0');
        };
        const curFile = () => mt.files[mt.idx] || null;

        async function setupMatn() {
            try { Object.assign(mt.settings, await api().local_audio_settings(null) || {}); } catch (e) { /* افتراضي */ }
            const S = mt.settings;
            $('matn-speed').value = S.speed; $('matn-repeat').value = S.repeat; $('matn-gap').value = S.gap;
            $('matn-autonext').checked = !!S.autoNext; $('matn-loopall').checked = !!S.loopAll;
            $('matn-pitch').checked = S.pitch !== false; $('matn-vol').value = Math.round(S.volume * 100);
            localAudio.volume = S.volume;
            applySpeed(S.speed, false);

            $('matn-add').onclick = async () => { const r = await api().local_audio_pick(); matnAfterAdd(r); };
            $('matn-folder').onclick = async () => { const r = await api().local_audio_pick_folder(); matnAfterAdd(r); };
            $('matn-filter').oninput = renderMatnList;
            $('matn-play').onclick = matnPlayPause;
            $('matn-prev').onclick = () => nextMatn(false, -1);
            $('matn-next').onclick = () => nextMatn(false, 1);
            $('matn-back').onclick = () => matnSeekBy(-5);
            $('matn-fwd').onclick = () => matnSeekBy(5);
            $('matn-seek').oninput = () => { if (localAudio.duration) localAudio.currentTime = $('matn-seek').value / 1000 * localAudio.duration; };
            $('matn-vol').oninput = () => { mt.settings.volume = $('matn-vol').value / 100; localAudio.volume = mt.settings.volume; saveMatnSettings(); };
            $('matn-speed').oninput = () => applySpeed(Number($('matn-speed').value), true);
            document.querySelectorAll('[data-speed]').forEach(b => { b.onclick = () => applySpeed(Number(b.dataset.speed), true); });
            $('matn-pitch').onchange = () => { mt.settings.pitch = $('matn-pitch').checked; applySpeed(mt.settings.speed, true); };
            $('matn-repeat').onchange = () => { mt.settings.repeat = Number($('matn-repeat').value) || 0; mt.loops = 0; updateLoopLabel(); saveMatnSettings(); };
            $('matn-gap').onchange = () => { mt.settings.gap = Number($('matn-gap').value) || 0; saveMatnSettings(); };
            $('matn-autonext').onchange = () => { mt.settings.autoNext = $('matn-autonext').checked; saveMatnSettings(); };
            $('matn-loopall').onchange = () => { mt.settings.loopAll = $('matn-loopall').checked; saveMatnSettings(); };
            $('matn-setA').onclick = () => setAB('a');
            $('matn-setB').onclick = () => setAB('b');
            $('matn-clearab').onclick = clearAB;
            $('matn-abon').onchange = () => { mt.abOn = $('matn-abon').checked; mt.loops = 0; updateLoopLabel(); };
            $('matn-segsave').onclick = saveSegment;

            localAudio.onloadedmetadata = () => {
                if (mt.pendingPos && mt.pendingPos < localAudio.duration - 1) localAudio.currentTime = mt.pendingPos;
                mt.pendingPos = 0;
                updateMatnTime(); renderAB();
            };
            localAudio.ontimeupdate = updateMatnTime;
            localAudio.onplay = () => { $('matn-play').textContent = '⏸'; startWatch(); };
            localAudio.onpause = () => { $('matn-play').textContent = '▶'; stopWatch(); savePosSoon(); };
            localAudio.onended = () => handleUnitEnd(true);
            localAudio.onerror = () => { if (localAudio.getAttribute('src')) showToast('تعذّر تشغيل هذا الملف (صيغة غير مدعومة أو الملف مفقود).'); };
            await refreshMatnList();
        }

        async function refreshMatnList() {
            try { mt.files = await api().local_audio_list(); } catch (e) { mt.files = []; }
            renderMatnList();
        }

        function matnAfterAdd(r) {
            if (r.error) showToast('تعذّر فتح نافذة اختيار الملفات: ' + r.error);
            mt.files = r.items || mt.files;
            const id = curFile() && curFile().id;
            mt.idx = id ? mt.files.findIndex(f => f.id === id) : -1;
            renderMatnList();
            if (r.added) showToast(`تمت إضافة ${r.added} ملف(ات).`, true);
        }

        function renderMatnList() {
            const q = ($('matn-filter').value || '').trim().toLowerCase();
            const ul = $('matn-list');
            ul.innerHTML = '';
            if (!mt.files.length) {
                const li = document.createElement('li');
                li.style.cssText = 'cursor:default;color:#64748b';
                li.textContent = 'لا ملفات بعد. اضغط «➕ ملفات» أو «📁 مجلد».';
                ul.appendChild(li);
                return;
            }
            mt.files.forEach((f, i) => {
                if (q && !f.name.toLowerCase().includes(q)) return;
                const li = document.createElement('li');
                li.className = (i === mt.idx ? 'active ' : '') + (f.exists ? '' : 'missing');
                const nm = document.createElement('span');
                nm.textContent = f.name;
                const del = document.createElement('button');
                del.textContent = '✕';
                del.title = 'إزالة من المكتبة (لا يُحذف الملف من جهازك)';
                del.onclick = async (e) => {
                    e.stopPropagation();
                    const cur = curFile();
                    mt.files = await api().local_audio_remove(f.id);
                    mt.idx = cur ? mt.files.findIndex(x => x.id === cur.id) : -1;
                    if (mt.idx < 0 && cur && cur.id === f.id) { localAudio.pause(); localAudio.removeAttribute('src'); $('matn-title').textContent = 'اختر ملفًا صوتيًا'; }
                    renderMatnList(); renderSegments();
                };
                li.appendChild(nm); li.appendChild(del);
                li.onclick = () => { if (f.exists) selectMatn(i, true); else showToast('هذا الملف لم يعد موجودًا في مكانه.'); };
                ul.appendChild(li);
            });
        }

        function selectMatn(i, play) {
            if (i < 0 || i >= mt.files.length) return;
            savePosNow();
            audioPlayer.pause(); miscAudio.pause(); mushafPlayStop();
            clearTimeout(mt.gapTimer); mt.gapTimer = null;
            mt.idx = i; mt.loops = 0; mt.a = mt.b = null; mt.abOn = false; $('matn-abon').checked = false;
            const f = mt.files[i];
            mt.pendingPos = f.pos || 0;
            localAudio.src = f.url;
            applySpeed(mt.settings.speed, false);
            $('matn-title').textContent = f.name;
            renderMatnList(); renderAB(); renderSegments(); updateLoopLabel();
            if (play) localAudio.play().catch(() => {});
        }

        function nextMatn(auto, dir = 1) {
            if (!mt.files.length) return;
            let i = mt.idx + dir;
            if (i >= mt.files.length) { if (auto && !mt.settings.loopAll) { localAudio.pause(); return; } i = 0; }
            if (i < 0) i = mt.files.length - 1;
            if (!mt.files[i].exists) { mt.idx = i; return nextMatn(auto, dir); }
            selectMatn(i, true);
        }

        function matnPlayPause() {
            if (mt.idx < 0) { const i = mt.files.findIndex(f => f.exists); if (i >= 0) selectMatn(i, true); return; }
            if (mt.gapTimer) {                                           // ضغط أثناء الفاصل: ابدأ التكرار الآن
                clearTimeout(mt.gapTimer); mt.gapTimer = null;
                localAudio.currentTime = segMode() ? mt.a : 0; localAudio.play().catch(() => {}); return;
            }
            if (localAudio.paused) { audioPlayer.pause(); miscAudio.pause(); localAudio.play().catch(() => {}); } else localAudio.pause();
        }

        function matnSeekBy(sec) {
            if (!localAudio.duration) return;
            localAudio.currentTime = Math.min(localAudio.duration, Math.max(0, localAudio.currentTime + sec));
        }

        function applySpeed(v, save) {
            v = Math.min(2, Math.max(0.5, Math.round(v * 20) / 20));
            mt.settings.speed = v;
            localAudio.defaultPlaybackRate = v;
            localAudio.playbackRate = v;
            const keep = mt.settings.pitch !== false;
            localAudio.preservesPitch = keep; localAudio.webkitPreservesPitch = keep; localAudio.mozPreservesPitch = keep;
            $('matn-speed').value = v;
            $('matn-speed-val').textContent = '×' + v.toFixed(2);
            if (save) saveMatnSettings();
        }

        function updateMatnTime() {
            const d = localAudio.duration || 0;
            $('matn-cur').textContent = fmtTime(localAudio.currentTime);
            $('matn-dur').textContent = fmtTime(d);
            if (d && document.activeElement !== $('matn-seek')) $('matn-seek').value = Math.round(localAudio.currentTime / d * 1000);
        }

        // ---- نقطتا A وB وتكرار المقطع ----
        const segMode = () => mt.abOn && mt.a !== null && mt.b !== null && mt.b > mt.a;

        function setAB(which) {
            if (!localAudio.src) return;
            mt[which] = Math.round(localAudio.currentTime * 100) / 100;
            if (mt.a !== null && mt.b !== null && mt.b <= mt.a) { showToast('نقطة B يجب أن تكون بعد نقطة A.'); mt[which === 'a' ? 'b' : 'a'] = null; }
            if (mt.a !== null && mt.b !== null) { mt.abOn = true; $('matn-abon').checked = true; }
            mt.loops = 0; updateLoopLabel(); renderAB();
        }
        function clearAB() { mt.a = mt.b = null; mt.abOn = false; $('matn-abon').checked = false; mt.loops = 0; updateLoopLabel(); renderAB(); }

        function renderAB() {
            const bar = $('matn-ab'), d = localAudio.duration || 0;
            $('matn-ab-label').textContent = (mt.a !== null ? 'A = ' + fmtTime(mt.a) : '') + (mt.b !== null ? '   B = ' + fmtTime(mt.b) : '');
            if (!d || mt.a === null) { bar.classList.add('hidden'); return; }
            const b = mt.b !== null ? mt.b : d;
            bar.classList.remove('hidden');
            bar.style.left = (mt.a / d * 100) + '%';
            bar.style.width = (Math.max(0, b - mt.a) / d * 100) + '%';
        }

        function updateLoopLabel() {
            const rep = Number(mt.settings.repeat);
            $('matn-loop-label').textContent = rep === 1 && !mt.loops ? '—' : `${mt.loops + (localAudio.paused && !mt.loops ? 0 : 1)}/${rep === 0 ? '∞' : rep}`;
        }

        function startWatch() { if (!mt.watch) mt.watch = setInterval(watchTick, 40); }
        function stopWatch() { clearInterval(mt.watch); mt.watch = null; }
        function watchTick() {
            if (segMode() && !localAudio.paused && localAudio.currentTime >= mt.b - 0.03) handleUnitEnd(false);
        }

        // انتهى «المقطع» (A–B أو الملف كله): كرّر بعد الفاصل، أو انتقل، أو توقف
        function handleUnitEnd(fromEnded) {
            if (mt.gapTimer) return;
            const seg = segMode();
            if (!seg && !fromEnded) return;
            mt.loops++;
            const rep = Number(mt.settings.repeat);
            if (rep === 0 || mt.loops < rep) {
                updateLoopLabel();
                localAudio.pause();
                const gap = Math.max(0, Number(mt.settings.gap)) * 1000;
                mt.gapTimer = setTimeout(() => {
                    mt.gapTimer = null;
                    localAudio.currentTime = seg ? mt.a : 0;
                    localAudio.play().catch(() => {});
                }, gap);
                return;
            }
            mt.loops = 0;
            updateLoopLabel();
            if (seg) { localAudio.pause(); return; }
            if (mt.settings.autoNext) nextMatn(true, 1); else localAudio.pause();
        }

        // ---- المقاطع المحفوظة ----
        function renderSegments() {
            const box = $('matn-segs');
            box.innerHTML = '';
            const f = curFile();
            if (!f || !f.segments.length) { const d = document.createElement('div'); d.className = 'dr-muted'; d.textContent = 'لا مقاطع محفوظة لهذا الملف.'; box.appendChild(d); return; }
            f.segments.forEach((sg, i) => {
                const row = document.createElement('div');
                row.className = 'seg-item';
                const t = document.createElement('span');
                t.textContent = `${sg.name || 'مقطع ' + (i + 1)}  (${fmtTime(sg.a)} → ${fmtTime(sg.b)})`;
                const del = document.createElement('button');
                del.className = 'btn sm alt'; del.textContent = '✕';
                del.onclick = async (e) => { e.stopPropagation(); f.segments.splice(i, 1); await api().local_audio_update(f.id, { segments: f.segments }); renderSegments(); };
                row.onclick = () => {
                    mt.a = sg.a; mt.b = sg.b; mt.abOn = true; $('matn-abon').checked = true; mt.loops = 0;
                    localAudio.currentTime = sg.a; renderAB(); updateLoopLabel();
                    localAudio.play().catch(() => {});
                };
                row.appendChild(t); row.appendChild(del);
                box.appendChild(row);
            });
        }
        async function saveSegment() {
            const f = curFile();
            if (!f) return;
            if (mt.a === null || mt.b === null || mt.b <= mt.a) { showToast('حدّد نقطتي A وB أولًا.'); return; }
            f.segments.push({ name: $('matn-segname').value.trim() || `مقطع ${f.segments.length + 1}`, a: mt.a, b: mt.b });
            await api().local_audio_update(f.id, { segments: f.segments });
            $('matn-segname').value = '';
            renderSegments();
        }

        // ---- حفظ الموضع والإعدادات ----
        function savePosNow() {
            const f = curFile();
            if (f && localAudio.src && localAudio.currentTime > 0) { f.pos = localAudio.currentTime; api().local_audio_update(f.id, { pos: f.pos }); }
        }
        function savePosSoon() { clearTimeout(mt.saveTimer); mt.saveTimer = setTimeout(savePosNow, 300); }
        function saveMatnSettings() { api().local_audio_settings(mt.settings); }
        function localPauseSave() {
            clearTimeout(mt.gapTimer); mt.gapTimer = null;
            if (!localAudio.paused) localAudio.pause();
            savePosNow();
        }
        setInterval(() => { if (!localAudio.paused) savePosNow(); }, 5000);

        function matnKey(e) {
            const k = e.key;
            if (e.code === 'Space') { e.preventDefault(); matnPlayPause(); }
            else if (e.code === 'ArrowLeft') matnSeekBy(5);
            else if (e.code === 'ArrowRight') matnSeekBy(-5);
            else if (k === '[') setAB('a');
            else if (k === ']') setAB('b');
            else if (k === 'l' || k === 'L') { $('matn-abon').checked = !$('matn-abon').checked; $('matn-abon').onchange(); }
            else if (k === '-') applySpeed(mt.settings.speed - 0.05, true);
            else if (k === '+' || k === '=') applySpeed(mt.settings.speed + 0.05, true);
        }
    </script>
</body>
</html>
"""

# ==========================================
# 3. الخط المحلي الاختياري (مصحف المدينة KFGQPC)
# ==========================================
def build_html():
    """
    إن وُجد ملف خط عثماني (مثل UthmanicHafs*.ttf) داخل مجلد fonts بجانب هذا الملف
    يُضمَّن في الصفحة ويصبح الخيار الافتراضي. وإلا يُستخدم Amiri Quran من الإنترنت.
    """
    import base64

    html = HTML_UI_CONTENT
    base = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__)))
    font_dir = os.path.join(base, "fonts")
    try:
        for name in sorted(os.listdir(font_dir)):
            low = name.lower()
            if low.startswith("qcf"):
                continue
            if low.endswith((".ttf", ".otf", ".woff", ".woff2")) and (
                "uthman" in low or "hafs" in low or "kfgqpc" in low
            ):
                with open(os.path.join(font_dir, name), "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                fmt = {"ttf": "truetype", "otf": "opentype",
                       "woff": "woff", "woff2": "woff2"}[low.rsplit(".", 1)[1]]
                css = (
                    '@font-face { font-family: "KFGQPC Uthmani"; '
                    f'src: url(data:font/{fmt};base64,{b64}) format("{fmt}"); }}'
                )
                html = html.replace("/*LOCAL_FONT_CSS*/", css)
                html = html.replace("/*HAS_LOCAL_FONT*/false", "true")
                print(f"✔ تم تحميل الخط المحلي: {name}", flush=True)
                break
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Font load error: {e}", flush=True)
    return html


# ==========================================
# 4. تشغيل التطبيق
# ==========================================
if __name__ == "__main__":
    backend_api = QuranBackendAPI()

    window_args = dict(
        title="مقرأة القرآن الكريم 📖",
        html=build_html(),
        js_api=backend_api,
        width=1280,
        height=800,
        min_size=(900, 600),
        resizable=True,
    )
    try:
        # تفتح النافذة مكبّرة لتظهر الواجهة كاملة دون تكبير يدوي
        window = webview.create_window(**window_args, maximized=True)
    except TypeError:               # إصدار قديم من pywebview لا يدعم maximized
        window = webview.create_window(**window_args)

    webview.start(debug=False)
