# -*- coding: utf-8 -*-
"""
يجلب التفاسير من مشروع spa5k/tafsir_api (رخصة المستودع MIT) ويكتب لكل تفسير ملفًا واحدًا:
    tafsir/<slug>.json   =  {"edition":..., "label":..., "lang":..., "source":..., "ayahs": {"2:255": "نص", ...}}

التشغيل:  python tools/build_tafsir.py            (يتطلب: pip install requests)
          python tools/build_tafsir.py --only ar-tafsir-muyassar
ملاحظة: حقوق نصوص التفاسير نفسها تعود لأصحابها؛ راجع LICENSES.md.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = "https://raw.githubusercontent.com/spa5k/tafsir_api/main/tafsir/"
EDITIONS = {
    "ar-tafsir-muyassar": ("التفسير الميسر", "ar"),
    "ar-tafseer-al-saddi": ("تفسير السعدي", "ar"),
    "ar-tafsir-al-jalalayn": ("تفسير الجلالين", "ar"),
    "ar-tafsir-al-mukhtasar": ("المختصر في تفسير القرآن الكريم", "ar"),
    "en-tafsir-al-mukhtasar": ("Al-Mukhtasar fi Tafsir al-Quran (English)", "en"),
    "french-mokhtasar": ("Al-Mukhtasar (Français)", "fr"),
}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tafsir")


def fetch(slug, surah):
    for _ in range(3):
        try:
            r = requests.get(f"{BASE}{slug}/{surah}.json", timeout=40)
            if r.status_code == 200:
                return surah, r.json()
        except Exception:
            pass
    return surah, None


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    os.makedirs(OUT, exist_ok=True)
    for slug, (label, lang) in EDITIONS.items():
        if only and slug != only:
            continue
        with ThreadPoolExecutor(16) as pool:
            results = list(pool.map(lambda s: fetch(slug, s), range(1, 115)))
        bad = [s for s, d in results if d is None]
        if bad:
            sys.exit(f"فشل جلب السور {bad} من {slug}. أعد المحاولة.")
        ayahs = {}
        for s, data in results:
            for item in data:
                ayahs[f"{item.get('surah', s)}:{item['ayah']}"] = item.get("text", "")
        doc = {"edition": slug, "label": label, "lang": lang,
               "source": "https://github.com/spa5k/tafsir_api", "ayahs": ayahs}
        path = os.path.join(OUT, slug + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
        print(f"{slug}: {len(ayahs)} entries, {os.path.getsize(path) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
