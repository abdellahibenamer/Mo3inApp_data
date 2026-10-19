# -*- coding: utf-8 -*-
"""
ينسخ خطوط مصحف المدينة QCF4 من جهازك إلى fonts/qcf4/ ويتأكد من اكتمالها.

يبحث تلقائيًا في:  C:\\Windows\\Fonts  و  %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts
ويمكنك إضافة مجلدات أخرى:   python tools/collect_fonts.py --src "D:\\خطوط" --src "E:\\x"

المطلوب: QCF4_Hafs_01_W.ttf … QCF4_Hafs_47_W.ttf (47 ملفًا)،
واختياريًا QCF4_QBSML.ttf (خط عناوين السور؛ بدونه يُستعمل إطار نصي بديل).
⚠️ راجع شروط مجمّع الملك فهد قبل نشر هذه الخطوط علنًا. الأفضل أن يكون المستودع خاصًا (Private).
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "..", "fonts", "qcf4")
REQUIRED = [f"QCF4_Hafs_{i:02d}_W.ttf" for i in range(1, 48)]
OPTIONAL = ["QCF4_QBSML.ttf"]


def search_dirs():
    dirs = []
    for i, a in enumerate(sys.argv):
        if a == "--src" and i + 1 < len(sys.argv):
            dirs.append(sys.argv[i + 1])
    win = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\Windows"
    dirs.append(os.path.join(win, "Fonts"))
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(os.path.join(local, "Microsoft", "Windows", "Fonts"))
    return dirs


def looks_like_font(path):
    try:
        with open(path, "rb") as f:
            return f.read(4) in (b"\x00\x01\x00\x00", b"true", b"OTTO") and os.path.getsize(path) > 100_000
    except OSError:
        return False


def main():
    found = {}
    for d in search_dirs():
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            for want in REQUIRED + OPTIONAL:
                if name.lower() == want.lower() and want not in found:
                    found[want] = os.path.join(d, name)
    os.makedirs(DEST, exist_ok=True)
    copied, bad = 0, []
    lines = []
    for want in REQUIRED + OPTIONAL:
        src = found.get(want)
        if not src:
            continue
        if not looks_like_font(src):
            bad.append(want)
            continue
        dst = os.path.join(DEST, want)
        if not (os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src)):
            shutil.copy2(src, dst)
        copied += 1
        with open(dst, "rb") as f:
            lines.append(f"{hashlib.sha256(f.read()).hexdigest()}  {want}")
    with open(os.path.join(DEST, "SHA256.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    missing = [w for w in REQUIRED if w not in found]
    print(f"تم نسخ {copied} ملف إلى {os.path.abspath(DEST)}")
    if bad:
        print("⚠️ ملفات تالفة أو ليست خطوطًا:", ", ".join(bad))
    if missing:
        print(f"❌ ينقص {len(missing)} من 47 خطًا:", ", ".join(missing))
    else:
        print("✅ الخطوط الـ47 كلها موجودة.")
    if "QCF4_QBSML.ttf" not in found:
        print("ℹ️ خط عناوين السور QCF4_QBSML.ttf غير موجود (اختياري).")
    sys.exit(1 if missing or bad else 0)


if __name__ == "__main__":
    main()
