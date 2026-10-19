# -*- coding: utf-8 -*-
"""
يتحقق من سلامة ملفات البيانات ويطابقها ببعضها وبمصادر مستقلة.

التشغيل:
    python tools/validate.py
    python tools/validate.py --pages-file mushaf/qcf4_pages.json   (أو --pages-dir مجلد_الصفحات_الخام)
                                    ← مطابقة إضافية مع علامات الأرباع وعناوين السور وترقيم الصفحات
    python tools/validate.py --manifest                       (مطابقة البصمات مع manifest.json)
"""
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FAILS = 0
# بدايات الأجزاء الثلاثين حسب مصحف المدينة (الجزءان 7 و11 يبدآن في منتصف الصفحتين 121 و201)
JUZ_PAGES = [1, 22, 42, 62, 82, 102, 121, 142, 162, 182, 201, 222, 242, 262, 282, 302, 322, 342, 362, 382,
             402, 422, 442, 462, 482, 502, 522, 542, 562, 582]


def load(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return json.load(f)


def check(label, cond, detail=""):
    global FAILS
    print(("✔ " if cond else "✘ ") + label + (f" | {detail}" if detail else ""))
    if not cond:
        FAILS += 1


def main():
    ch = load("meta", "chapters.json")
    juz = load("meta", "juz.json")
    rub = load("meta", "hizb_rub.json")
    pages = load("meta", "pages.json")
    saj = load("meta", "sajdas.json")

    check("السور: 114 وأرقامها متسلسلة", [c["id"] for c in ch] == list(range(1, 115)))
    check("مجموع الآيات 6236", sum(c["ayahs"] for c in ch) == 6236, sum(c["ayahs"] for c in ch))
    check("كل اسم سورة غير فارغ (عربي/إنجليزي/فرنسي)", all(c["name_ar"] and c["name_plain"] and c["name_en"] and c["name_fr"] for c in ch))
    check("بداية كل سورة بعد/عند بداية سابقتها، والصفحات 1..604",
          ch[0]["page_start"] == 1 and ch[-1]["page_end"] == 604 and
          all(ch[i]["page_start"] >= ch[i - 1]["page_start"] and ch[i]["page_start"] >= ch[i - 1]["page_end"] for i in range(1, 114)))
    check("الأجزاء: 30 وبداياتها تطابق قائمة مصحف المدينة", [j["page"] for j in juz] == JUZ_PAGES, [j["page"] for j in juz][:12])
    check("الأرباع: 240 ومرتّبة", len(rub) == 240 and all((rub[i]["surah"], rub[i]["ayah"]) > (rub[i - 1]["surah"], rub[i - 1]["ayah"]) for i in range(1, 240)))
    check("الحزب/الربع/الجزء مشتقّة صحيحة", all(r["hizb"] == (r["rub"] - 1) // 4 + 1 and r["quarter"] == (r["rub"] - 1) % 4 + 1 and r["juz"] == (r["rub"] - 1) // 8 + 1 for r in rub))
    check("بداية كل جزء = الربع رقم 8k+1", all((juz[i]["surah"], juz[i]["ayah"]) == (rub[i * 8]["surah"], rub[i * 8]["ayah"]) for i in range(30)))
    check("الصفحات: 604 وأول آية فيها غير متناقصة", len(pages) == 604 and pages[0]["surah"] == 1 and
          all((pages[i]["surah"], pages[i]["ayah"]) > (pages[i - 1]["surah"], pages[i - 1]["ayah"]) for i in range(1, 604)))
    check("السجدات: 15", len(saj) == 15)
    ayahs = {c["id"]: c["ayahs"] for c in ch}
    check("كل آية في الأرباع والسجدات موجودة فعلًا", all(1 <= r["ayah"] <= ayahs[r["surah"]] for r in rub) and all(1 <= s["ayah"] <= ayahs[s["surah"]] for s in saj))

    # التفاسير
    tdir = os.path.join(ROOT, "tafsir")
    for name in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else []:
        if not name.endswith(".json"):
            continue
        d = load("tafsir", name)
        keys = d["ayahs"]
        valid = all(1 <= int(k.split(":")[0]) <= 114 and 1 <= int(k.split(":")[1]) <= ayahs[int(k.split(":")[0])] for k in keys)
        covered = {int(k.split(":")[0]) for k in keys}
        check(f"تفسير {d['edition']}: {len(keys)} مدخلًا، يغطي {len(covered)}/114 سورة، والمفاتيح صحيحة", valid and len(covered) == 114)

    # مطابقة مع بيانات صفحات QCF4 (اختياري)
    if "--pages-dir" in sys.argv or "--pages-file" in sys.argv:
        pdir = sys.argv[sys.argv.index("--pages-dir") + 1] if "--pages-dir" in sys.argv else None
        combined = None
        if "--pages-file" in sys.argv:
            with open(sys.argv[sys.argv.index("--pages-file") + 1], encoding="utf-8") as f:
                combined = json.load(f)["data"]

        def get_page(n):
            if combined is not None:
                return combined[str(n)]
            for fn in (f"qcf_page_{n:03d}.json", f"{n:03d}.json"):
                fp = os.path.join(pdir, fn)
                if os.path.exists(fp):
                    with open(fp, encoding="utf-8") as f:
                        return json.load(f)
            return None

        markers, headers = [], {}
        for n in range(1, 605):
            pg = get_page(n)
            if pg is None:
                check(f"ملف الصفحة {n} موجود", False)
                return finish()
            for line in pg["lines"]:
                for w in line["words"]:
                    if w["type"] == "quarter":
                        markers.append((n, w["verse_key"]))
                    elif w["type"] == "surah_header":
                        headers[w["sura"]] = n
        # علامة الربع تقع عند بداية الربع: إمّا في سطر الآية الأولى أو بعد آخر آية في الربع السابق مباشرة
        rubset = {(f"{r['surah']}:{r['ayah']}", r["page"]) for r in rub}
        prev_of = {}
        for r in rub:
            s, a = r["surah"], r["ayah"]
            prev = f"{s}:{a - 1}" if a > 1 else (f"{s - 1}:{ayahs[s - 1]}" if s > 1 else None)
            if prev:
                prev_of[prev] = r["page"]
        okm = [m for m in markers if m[::-1] in rubset or prev_of.get(m[1]) == m[0]]
        check(f"علامات الأرباع في المصحف ({len(markers)}) كلها تطابق بدايات الأرباع", len(okm) == len(markers), f"{len(okm)}/{len(markers)}")
        # ترقيم الصفحات في meta يطابق QCF4
        first = {}
        for n in range(1, 605):
            for line in get_page(n)["lines"]:
                for w in line["words"]:
                    if w.get("verse_key") and w["type"] in ("word", "end"):
                        first.setdefault(w["verse_key"], n)
        pg_ok = all(first[f"{x['surah']}:{x['ayah']}"] == x["page"] for x in juz + rub + saj)
        check("صفحات الأجزاء والأرباع والسجدات تطابق ترقيم QCF4", pg_ok)
        check("بداية كل سورة وصفحاتها 1..604 تطابق QCF4", all(first[f"{c['id']}:1"] == c["page_start"] for c in ch))
        check("عناوين السور في المصحف تطابق page_start لكل السور الـ114", all(headers.get(c["id"]) == c["page_start"] for c in ch), f"{sum(1 for c in ch if headers.get(c['id']) == c['page_start'])}/114")

    if "--manifest" in sys.argv:
        m = load("manifest.json")
        ok = True
        for fi in m["files"]:
            p = os.path.join(ROOT, fi["path"])
            if not os.path.exists(p):
                ok = False
                print("   مفقود:", fi["path"])
                continue
            with open(p, "rb") as f:
                if hashlib.sha256(f.read()).hexdigest() != fi["sha256"]:
                    ok = False
                    print("   بصمة مختلفة:", fi["path"])
        check(f"manifest: كل الملفات ({len(m['files'])}) سليمة", ok)
    finish()


def finish():
    print("\nالنتيجة:", "كل الفحوص نجحت ✅" if FAILS == 0 else f"{FAILS} فحصًا فشل ❌")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
