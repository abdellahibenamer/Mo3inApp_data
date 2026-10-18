# -*- coding: utf-8 -*-
"""
يحوّل تفاسير موجودة على جهازك إلى ملف واحد لكل تفسير بالصيغة التي يقرؤها التطبيق:
    tafsir/<اسم_المجلد>.json  =  {"edition", "label", "lang", "source", "ayahs": {"2:255": "نص", ...}}

المدخلات المقبولة (أحد الترتيبين داخل مجلد التفسير):
  أ) ملف لكل سورة:  1.json … 114.json   (وهو الأفضل ويكفي)
  ب) مجلد لكل سورة يحوي ملفًا لكل آية:   1/1.json, 1/2.json …  (يُستعمل لسورة لا يوجد لها ملف أ)

التشغيل:
    python tools/build_tafsir_local.py --src "D:\\تفاسير\\ar-tafsir-muyassar" --label "التفسير الميسر" --lang ar
    python tools/build_tafsir_local.py --src "D:\\تفاسير\\ar-tafseer-al-saddi" --src "D:\\تفاسير\\ar-tafsir-al-jalalayn"
    (--label و--lang لتفسير واحد فقط؛ وإلا تُؤخذ الأسماء من الجدول المعروف أو من اسم المجلد)

ثم:  python tools/validate.py   و   python tools/make_manifest.py --version ...
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "tafsir")
KNOWN = {
    "ar-tafsir-muyassar": ("التفسير الميسر", "ar"),
    "ar-tafseer-al-saddi": ("تفسير السعدي", "ar"),
    "ar-tafsir-al-jalalayn": ("تفسير الجلالين", "ar"),
    "ar-tafsir-al-mukhtasar": ("المختصر في تفسير القرآن الكريم", "ar"),
    "en-tafsir-al-mukhtasar": ("Al-Mukhtasar fi Tafsir al-Quran (English)", "en"),
    "french-mokhtasar": ("Al-Mukhtasar (Français)", "fr"),
}
AYAH_KEYS = ("ayah", "aya", "verse", "verse_number", "ayah_number", "number", "id")
TEXT_KEYS = ("text", "tafsir", "tafseer", "content", "body")
AYAHS = {1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75, 9: 129, 10: 109, 11: 123, 12: 111, 13: 43, 14: 52,
         15: 99, 16: 128, 17: 111, 18: 110, 19: 98, 20: 135, 21: 112, 22: 78, 23: 118, 24: 64, 25: 77, 26: 227, 27: 93,
         28: 88, 29: 69, 30: 60, 31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83, 37: 182, 38: 88, 39: 75, 40: 85, 41: 54,
         42: 53, 43: 89, 44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45, 51: 60, 52: 49, 53: 62, 54: 55, 55: 78,
         56: 96, 57: 29, 58: 22, 59: 24, 60: 13, 61: 14, 62: 11, 63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52,
         70: 44, 71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40, 79: 46, 80: 42, 81: 29, 82: 19, 83: 36,
         84: 25, 85: 22, 86: 17, 87: 19, 88: 26, 89: 30, 90: 20, 91: 15, 92: 21, 93: 11, 94: 8, 95: 8, 96: 19, 97: 5,
         98: 8, 99: 8, 100: 11, 101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4, 107: 7, 108: 3, 109: 6, 110: 3, 111: 5,
         112: 4, 113: 5, 114: 6}


def pick(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def entries(obj):
    """يستخلص قائمة (رقم_الآية، النص) من أي شكل شائع لملف السورة."""
    if isinstance(obj, dict):
        for k in ("ayahs", "verses", "tafsir", "data", "result", "items"):
            if isinstance(obj.get(k), list):
                return entries(obj[k])
        a, t = pick(obj, AYAH_KEYS), pick(obj, TEXT_KEYS)
        return [(int(a), str(t))] if a is not None and isinstance(t, str) else []
    out = []
    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict):
                a, t = pick(it, AYAH_KEYS), pick(it, TEXT_KEYS)
                if a is not None and isinstance(t, str):
                    out.append((int(a), t))
    return out


def read_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def build(src, label=None, lang=None):
    slug = os.path.basename(os.path.normpath(src))
    known = KNOWN.get(slug, (slug, "ar"))
    label, lang = label or known[0], lang or known[1]
    ayahs, problems = {}, []
    for s in range(1, 115):
        got = []
        f = os.path.join(src, f"{s}.json")
        if os.path.isfile(f):
            got = entries(read_json(f))
        if not got and os.path.isdir(os.path.join(src, str(s))):
            for name in sorted(os.listdir(os.path.join(src, str(s)))):
                if name.endswith(".json"):
                    try:
                        num = int(os.path.splitext(name)[0])
                        t = pick(read_json(os.path.join(src, str(s), name)), TEXT_KEYS) if isinstance(read_json(os.path.join(src, str(s), name)), dict) else None
                        if isinstance(t, str):
                            got.append((num, t))
                    except (ValueError, OSError):
                        pass
        if not got:
            problems.append(f"السورة {s}: لا ملف ولا آيات")
        for a, t in got:
            if 1 <= a <= AYAHS[s]:
                ayahs[f"{s}:{a}"] = t
            else:
                problems.append(f"{s}:{a} خارج عدد آيات السورة (تجاهلتُه)")
    os.makedirs(OUT, exist_ok=True)
    doc = {"edition": slug, "label": label, "lang": lang, "source": "local", "ayahs": ayahs}
    path = os.path.join(OUT, slug + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    covered = {int(k.split(":")[0]) for k in ayahs}
    print(f"{slug}: {len(ayahs)} مدخلًا، {len(covered)}/114 سورة، {os.path.getsize(path) / 1e6:.1f} MB")
    for p in problems[:15]:
        print("   ⚠️", p)
    return len(covered) == 114


def main():
    srcs = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--src" and i + 1 < len(sys.argv)]
    if not srcs:
        sys.exit(__doc__)
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else None
    lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else None
    ok = all([build(s, label if len(srcs) == 1 else None, lang if len(srcs) == 1 else None) for s in srcs])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
