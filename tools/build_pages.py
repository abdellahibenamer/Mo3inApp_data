# -*- coding: utf-8 -*-
"""
يبني ملف صفحات المصحف برموز خطوط QCF4 (رواية حفص، مصحف المدينة) في ملف واحد:
    mushaf/qcf4_pages.json

المصدر: مستودع MohamadHajjRabee/quran-qcf4 (بيانات مبنية على خطوط مجمّع الملك فهد QCF4).
⚠️ هذا المستودع بلا ملف ترخيص، ويطلب احترام شروط مجمّع الملك فهد. راجع شروط المجمّع
   (qurancomplex.gov.sa) قبل توزيع هذا الملف أو نشره علنًا. لذلك لا يأتي هذا الملف جاهزًا
   في المستودع؛ شغّل الأداة بنفسك بعد أن تقرّر.

التشغيل:  python tools/build_pages.py [--out مسار.json]      (يتطلب: pip install requests)
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = "https://raw.githubusercontent.com/MohamadHajjRabee/quran-qcf4/main/"
HERE = os.path.dirname(os.path.abspath(__file__))


def fetch(n):
    for _ in range(3):
        try:
            r = requests.get(f"{BASE}pages/{n:03d}.json", timeout=40)
            if r.status_code == 200:
                return n, r.json()
        except Exception:
            pass
    return n, None


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(HERE, "..", "mushaf", "qcf4_pages.json")
    with ThreadPoolExecutor(16) as pool:
        results = list(pool.map(fetch, range(1, 605)))
    bad = [n for n, d in results if d is None]
    if bad:
        sys.exit(f"فشل جلب {len(bad)} صفحة: {bad[:10]}... أعد المحاولة.")
    pages = {}
    for n, d in results:
        lines = []
        for line in d.get("lines", []):
            words = [{k: w[k] for k in ("char", "font", "type", "text", "sura", "verse_key") if k in w}
                     for w in line.get("words", [])]
            lines.append({"line": line.get("line"), "words": words})
        pages[str(n)] = {"lines": lines, "surahs": d.get("surahs", [])}
    doc = {"format": "qcf4-pages/1", "pages": 604,
           "source": "https://github.com/MohamadHajjRabee/quran-qcf4", "data": pages}
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"تم: {len(pages)} صفحة، {os.path.getsize(out) / 1e6:.1f} MB ← {out}")


if __name__ == "__main__":
    main()
