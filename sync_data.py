# -*- coding: utf-8 -*-
"""
ينسخ مستودع البيانات (Mo3inApp_data) إلى مجلد data/ بجوار التطبيق ليصير جزءًا من النسخة الموزّعة.
عندها يقرأ التطبيق منه مباشرة دون إنترنت (يُفضَّل المضمَّن على التنزيل).

التشغيل (من مجلد مشروع التطبيق):
    python packaging/sync_data.py "D:\\maqraa\\Mo3inApp_data"
    python packaging/sync_data.py "D:\\maqraa\\Mo3inApp_data" --no-qcf-fonts     (بدون خطوط QCF4 ~ 97 ميغابايت)

⚠️ إن ضممتَ خطوط QCF4 وبيانات الصفحات فراجع شروط مجمّع الملك فهد (انظر LICENSES.md في مستودع البيانات).
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "..", "data")
FOLDERS = ["meta", "tafsir", "mushaf", os.path.join("fonts", "ui"), os.path.join("fonts", "qcf4")]
REQUIRED = ["manifest.json", "meta/chapters.json", "meta/juz.json", "meta/hizb_rub.json",
            "mushaf/qcf4_pages.json", "tafsir/ar-tafsir-muyassar.json", "fonts/ui/AmiriQuran-Regular.ttf"]


def main():
    if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
        sys.exit(__doc__)
    src = sys.argv[1]
    skip_qcf = "--no-qcf-fonts" in sys.argv
    missing = [r for r in REQUIRED if not os.path.isfile(os.path.join(src, *r.split("/")))]
    if missing:
        sys.exit("ملفات ناقصة في مستودع البيانات: " + ", ".join(missing))
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    total = 0
    for folder in FOLDERS:
        if skip_qcf and folder.endswith("qcf4"):
            continue
        s = os.path.join(src, folder)
        if not os.path.isdir(s):
            continue
        d = os.path.join(DEST, folder)
        os.makedirs(d, exist_ok=True)
        for name in os.listdir(s):
            sp = os.path.join(s, name)
            if os.path.isfile(sp) and not name.lower().startswith("readme"):
                shutil.copy2(sp, os.path.join(d, name))
                total += os.path.getsize(sp)
    shutil.copy2(os.path.join(src, "manifest.json"), os.path.join(DEST, "manifest.json"))
    print(f"تم نسخ البيانات إلى {os.path.abspath(DEST)}  ({total / 1e6:.1f} ميغابايت)")
    if skip_qcf:
        print("ℹ️ بدون خطوط QCF4: سيقرؤها التطبيق من جهاز المستخدم أو ينزّلها من DATA_BASE عند الحاجة.")


if __name__ == "__main__":
    main()
