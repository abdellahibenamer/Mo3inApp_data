# -*- coding: utf-8 -*-
"""
يضبط أرقام الصفحات في ملفات meta/* على ترقيم المصحف الذي يعرضه التطبيق فعلًا (QCF4، مصحف المدينة 1441هـ).

لماذا؟ حزمة quran-meta تتبع طبعة أخرى، فتختلف عن QCF4 في نحو 56 آية على 25 صفحة (مثل 5:77/5:78 في ص 121).
المقسّمات المنطقية (الأجزاء/الأرباع/السجدات/أسماء السور) تبقى من quran-meta، وأرقام الصفحات تُؤخذ من بيانات QCF4.

التشغيل (بعد python tools/build_pages.py أو بمجلد صفحات خام):
    python tools/apply_pagination.py --pages-file mushaf/qcf4_pages.json
    python tools/apply_pagination.py --pages-dir مجلد_الصفحات_الخام
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
META = os.path.join(ROOT, "meta")


def load_pages():
    if "--pages-file" in sys.argv:
        with open(sys.argv[sys.argv.index("--pages-file") + 1], encoding="utf-8") as f:
            data = json.load(f)["data"]
        return {int(n): [w for l in p["lines"] for w in l["words"]] for n, p in data.items()}
    if "--pages-dir" in sys.argv:
        d = sys.argv[sys.argv.index("--pages-dir") + 1]
        out = {}
        for n in range(1, 605):
            for fn in (f"qcf_page_{n:03d}.json", f"{n:03d}.json"):
                fp = os.path.join(d, fn)
                if os.path.exists(fp):
                    with open(fp, encoding="utf-8") as f:
                        out[n] = [w for l in json.load(f)["lines"] for w in l["words"]]
                    break
            else:
                sys.exit(f"ملف الصفحة {n} غير موجود في {d}")
        return out
    sys.exit(__doc__)


def rd(name):
    with open(os.path.join(META, name), encoding="utf-8") as f:
        return json.load(f)


def wr(name, data):
    with open(os.path.join(META, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main():
    words_by_page = load_pages()
    first, last, first_word = {}, {}, {}
    for n in sorted(words_by_page):
        for i, w in enumerate(words_by_page[n]):
            k = w.get("verse_key")
            if k and w["type"] in ("word", "end"):
                first.setdefault(k, n)
                last[k] = n
                first_word.setdefault(n, k)
    juz, rub, saj, ch = rd("juz.json"), rd("hizb_rub.json"), rd("sajdas.json"), rd("chapters.json")
    pg = lambda s, a: first[f"{s}:{a}"]

    for x in juz + rub + saj:
        x["page"] = pg(x["surah"], x["ayah"])
    for c in ch:
        c["page_start"] = first[f"{c['id']}:1"]
        c["page_end"] = last[f"{c['id']}:{c['ayahs']}"]

    # الجزء الذي تنتمي إليه آية = آخر جزء بدأ قبلها (أو عندها)
    juz_starts = [(j["surah"], j["ayah"]) for j in juz]

    def juz_of(s, a):
        n = 0
        for i, st in enumerate(juz_starts):
            if st <= (s, a):
                n = i + 1
        return n

    starts_on = {}
    for k, n in first.items():
        s, a = map(int, k.split(":"))
        if n not in starts_on or (s, a) < starts_on[n]:
            starts_on[n] = (s, a)
    pages = []
    for n in range(1, 605):
        if n in starts_on:
            s, a = starts_on[n]
            cont = first_word[n] != f"{s}:{a}"          # أول كلمات الصفحة تتمة آية بدأت في صفحة سابقة
        else:                                           # آية طويلة تغطي الصفحة كلها
            s, a = map(int, first_word[n].split(":"))
            cont = True
        pages.append({"page": n, "surah": s, "ayah": a, "juz": juz_of(s, a), "continues_prev": cont})
    wr("juz.json", juz); wr("hizb_rub.json", rub); wr("sajdas.json", saj); wr("chapters.json", ch); wr("pages.json", pages)
    info = rd("info.json")
    info["pagination"] = "qcf4-1441 (طبعة مصحف المدينة 1441هـ كما في خطوط QCF4)"
    wr("info.json", info)
    print("تم ضبط الصفحات على ترقيم QCF4:", len(pages), "صفحة،", sum(p["continues_prev"] for p in pages), "صفحة تبدأ بتتمة آية")


if __name__ == "__main__":
    main()
