#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
استخراج ملفات meta/ الخمسة من ملف hafsData_v2-0.html

الاستخدام:
    python extract_meta.py "D:\\hafsData_v2-0.html" -o meta
    python extract_meta.py "D:\\hafsData_v2-0.html" --inspect     # لمعاينة بنية الملف فقط

المخرجات (في المجلد -o):
    chapters.json, juz.json, hizb_rub.json, pages.json, sajdas.json

ما يُستخرج من الملف نفسه : السور، الآيات، الصفحات، الأجزاء، علامات الأرباع (۞)، علامات السجدة (۩)، أسماء السور العربية.
ما لا يوجد في الملف    : الأسماء اللاتينية/الفرنسية، المعاني، الركوعات، ترتيب النزول، مكي/مدني
                          ← هذه مضمَّنة في الجداول أسفل الملف (يمكنك تعديلها).
"""
import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

RUB_MARK = "\u06DE"     # ۞ بداية ربع الحزب
SAJDA_MARK = "\u06E9"   # ۩ سجدة التلاوة
TOTAL_AYAHS = 6236

# ----------------------------------------------------------------------------
# بيانات مساعدة غير موجودة في ملف hafsData
# ----------------------------------------------------------------------------
# (name_en, meaning_en, name_fr, meaning_fr)  — بترتيب السور 1..114
NAMES = [
    ("Al-Faatiha", "The Opening", "Al Fâtiha", "L'ouverture"),
    ("Al-Baqara", "The Cow", "Al Baqarah", "La vache"),
    ("Aal-i-Imraan", "The Family of Imraan", "Âl Imrân", "La famille d'Imran"),
    ("An-Nisaa", "The Women", "An Nisâ'", "Les femmes"),
    ("Al-Maaida", "The Table", "Al Mâ'idah", "La table servie"),
    ("Al-An'aam", "The Cattle", "Al An'âm", "Les bestiaux"),
    ("Al-A'raaf", "The Heights", "Al A'râf", "Al A'raf"),
    ("Al-Anfaal", "The Spoils of War", "Al Anfâl", "Le butin"),
    ("At-Tawba", "The Repentance", "At Tawbah", "Le repentir"),
    ("Yunus", "Jonas", "Yûnus", "Jonas"),
    ("Hud", "Hud", "Hûd", "Hud"),
    ("Yusuf", "Joseph", "Yûsuf", "Joseph"),
    ("Ar-Ra'd", "The Thunder", "Ar Ra'd", "Le tonnerre"),
    ("Ibrahim", "Abraham", "Ibrâhîm", "Abraham"),
    ("Al-Hijr", "The Rock", "Al Hijr", "Al Hijr"),
    ("An-Nahl", "The Bee", "An Nahl", "Les abeilles"),
    ("Al-Israa", "The Night Journey", "Al Isrâ'", "Le voyage nocturne"),
    ("Al-Kahf", "The Cave", "Al Kahf", "La caverne"),
    ("Maryam", "Mary", "Maryam", "Marie"),
    ("Taa-Haa", "Taa-Haa", "Tâ-Hâ", "Ta-Ha"),
    ("Al-Anbiyaa", "The Prophets", "Al Anbiyâ'", "Les prophètes"),
    ("Al-Hajj", "The Pilgrimage", "Al Hajj", "Le pèlerinage"),
    ("Al-Muminoon", "The Believers", "Al Mu'minûn", "Les croyants"),
    ("An-Noor", "The Light", "An Nûr", "La lumière"),
    ("Al-Furqaan", "The Criterion", "Al Furqân", "Le discernement"),
    ("Ash-Shu'araa", "The Poets", "Ash Shu'arâ'", "Les poètes"),
    ("An-Naml", "The Ant", "An Naml", "Les fourmis"),
    ("Al-Qasas", "The Stories", "Al Qasas", "Le récit"),
    ("Al-Ankaboot", "The Spider", "Al Ankabût", "L'araignée"),
    ("Ar-Room", "The Romans", "Ar Rûm", "Les romains"),
    ("Luqman", "Luqman", "Luqmân", "Luqman"),
    ("As-Sajda", "The Prostration", "As Sajdah", "La prosternation"),
    ("Al-Ahzaab", "The Clans", "Al Ahzâb", "Les coalisés"),
    ("Saba", "Sheba", "Saba'", "Saba"),
    ("Faatir", "The Originator", "Fâtir", "Le Créateur"),
    ("Yaseen", "Yaseen", "Yâ-Sîn", "Ya-Sin"),
    ("As-Saaffaat", "Those drawn up in Ranks", "As Sâffât", "Les rangées"),
    ("Saad", "The letter Saad", "Sâd", "Sad"),
    ("Az-Zumar", "The Groups", "Az Zumar", "Les groupes"),
    ("Ghafir", "The Forgiver", "Ghâfir", "Le Pardonneur"),
    ("Fussilat", "Explained in Detail", "Fussilat", "Les versets détaillés"),
    ("Ash-Shura", "Consultation", "Ash Shûrâ", "La consultation"),
    ("Az-Zukhruf", "Ornaments of gold", "Az Zukhruf", "L'ornement"),
    ("Ad-Dukhaan", "The Smoke", "Ad Dukhân", "La fumée"),
    ("Al-Jaathiya", "Crouching", "Al Jâthiyah", "L'agenouillée"),
    ("Al-Ahqaf", "The Wind-Curved Sandhills", "Al Ahqâf", "Al Ahqaf"),
    ("Muhammad", "Muhammad", "Muhammad", "Muhammad"),
    ("Al-Fath", "The Victory", "Al Fath", "La victoire éclatante"),
    ("Al-Hujuraat", "The Inner Apartments", "Al Hujurât", "Les appartements"),
    ("Qaaf", "The letter Qaaf", "Qâf", "Qaf"),
    ("Adh-Dhaariyat", "The Winnowing Winds", "Adh Dhâriyât", "Les vents qui éparpillent"),
    ("At-Tur", "The Mount", "At Tûr", "Le mont"),
    ("An-Najm", "The Star", "An Najm", "L'étoile"),
    ("Al-Qamar", "The Moon", "Al Qamar", "La lune"),
    ("Ar-Rahmaan", "The Beneficent", "Ar Rahmân", "Le Tout Miséricordieux"),
    ("Al-Waaqia", "The Inevitable", "Al Wâqi'ah", "L'événement"),
    ("Al-Hadid", "The Iron", "Al Hadîd", "Le fer"),
    ("Al-Mujaadila", "The Pleading Woman", "Al Mujâdilah", "La discussion"),
    ("Al-Hashr", "The Exile", "Al Hashr", "Le rassemblement"),
    ("Al-Mumtahana", "She that is to be examined", "Al Mumtahanah", "L'éprouvée"),
    ("As-Saff", "The Ranks", "As Saff", "Le rang"),
    ("Al-Jumu'a", "Friday", "Al Jumu'ah", "Le vendredi"),
    ("Al-Munaafiqoon", "The Hypocrites", "Al Munâfiqûn", "Les hypocrites"),
    ("At-Taghaabun", "Mutual Disillusion", "At Taghâbun", "La grande perte"),
    ("At-Talaaq", "Divorce", "At Talâq", "Le divorce"),
    ("At-Tahrim", "The Prohibition", "At Tahrîm", "L'interdiction"),
    ("Al-Mulk", "The Sovereignty", "Al Mulk", "La royauté"),
    ("Al-Qalam", "The Pen", "Al Qalam", "La plume"),
    ("Al-Haaqqa", "The Reality", "Al Hâqqah", "Celle qui montre la vérité"),
    ("Al-Ma'aarij", "The Ascending Stairways", "Al Ma'ârij", "Les voies d'ascension"),
    ("Nooh", "Noah", "Nûh", "Noé"),
    ("Al-Jinn", "The Jinn", "Al Jinn", "Les djinns"),
    ("Al-Muzzammil", "The Enshrouded One", "Al Muzzammil", "L'enveloppé"),
    ("Al-Muddaththir", "The Cloaked One", "Al Muddaththir", "Le revêtu d'un manteau"),
    ("Al-Qiyaama", "The Resurrection", "Al Qiyâmah", "La résurrection"),
    ("Al-Insaan", "Man", "Al Insân", "L'homme"),
    ("Al-Mursalaat", "The Emissaries", "Al Mursalât", "Les envoyées"),
    ("An-Naba", "The Tidings", "An Naba'", "La nouvelle"),
    ("An-Naazi'aat", "Those who drag forth", "An Nâzi'ât", "Les anges qui arrachent les âmes"),
    ("Abasa", "He frowned", "Abasa", "Il s'est renfrogné"),
    ("At-Takwir", "The Overthrowing", "At Takwîr", "L'obscurcissement"),
    ("Al-Infitaar", "The Cleaving", "Al Infitâr", "La rupture"),
    ("Al-Mutaffifin", "Defrauding", "Al Mutaffifîn", "Les fraudeurs"),
    ("Al-Inshiqaaq", "The Splitting Open", "Al Inshiqâq", "La déchirure"),
    ("Al-Burooj", "The Constellations", "Al Burûj", "Les constellations"),
    ("At-Taariq", "The Morning Star", "At Târiq", "L'astre nocturne"),
    ("Al-A'laa", "The Most High", "Al A'lâ", "Le Très-Haut"),
    ("Al-Ghaashiya", "The Overwhelming", "Al Ghâshiyah", "L'enveloppante"),
    ("Al-Fajr", "The Dawn", "Al Fajr", "L'aube"),
    ("Al-Balad", "The City", "Al Balad", "La cité"),
    ("Ash-Shams", "The Sun", "Ash Shams", "Le soleil"),
    ("Al-Lail", "The Night", "Al Layl", "La nuit"),
    ("Ad-Dhuhaa", "The Morning Hours", "Ad Duhâ", "Le jour montant"),
    ("Ash-Sharh", "The Consolation", "Ash Sharh", "L'ouverture"),
    ("At-Tin", "The Fig", "At Tîn", "Le figuier"),
    ("Al-Alaq", "The Clot", "Al Alaq", "L'adhérence"),
    ("Al-Qadr", "The Power, Fate", "Al Qadr", "La destinée"),
    ("Al-Bayyina", "The Evidence", "Al Bayyinah", "La preuve"),
    ("Az-Zalzala", "The Earthquake", "Az Zalzalah", "La secousse"),
    ("Al-Aadiyaat", "The Chargers", "Al Âdiyât", "Les coursiers"),
    ("Al-Qaari'a", "The Calamity", "Al Qâri'ah", "Le fracas"),
    ("At-Takaathur", "Competition", "At Takâthur", "La rivalité"),
    ("Al-Asr", "The Declining Day, Epoch", "Al Asr", "Le temps"),
    ("Al-Humaza", "The Traducer", "Al Humazah", "Le calomniateur"),
    ("Al-Fil", "The Elephant", "Al Fîl", "L'éléphant"),
    ("Quraish", "Quraysh", "Quraysh", "Quraysh"),
    ("Al-Maa'un", "Almsgiving", "Al Mâ'ûn", "L'ustensile"),
    ("Al-Kawthar", "Abundance", "Al Kawthar", "L'abondance"),
    ("Al-Kaafiroon", "The Disbelievers", "Al Kâfirûn", "Les infidèles"),
    ("An-Nasr", "Divine Support", "An Nasr", "Le secours"),
    ("Al-Masad", "The Palm Fibre", "Al Masad", "Les fibres"),
    ("Al-Ikhlaas", "Sincerity", "Al Ikhlâs", "Le monostichisme"),
    ("Al-Falaq", "The Dawn", "Al Falaq", "L'aube naissante"),
    ("An-Naas", "Mankind", "An Nâs", "Les hommes"),
]

# عدد الركوعات لكل سورة (المجموع 558)
RUKU = [
    1, 40, 20, 24, 16, 20, 24, 10, 16, 11, 10, 12, 6, 7, 6, 16, 12, 12, 6, 8,
    7, 10, 6, 9, 6, 11, 7, 9, 7, 6, 4, 3, 9, 6, 5, 5, 5, 5, 8, 9,
    6, 5, 7, 3, 4, 4, 4, 4, 2, 3, 3, 2, 3, 3, 3, 3, 4, 3, 3, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
] + [1] * 35

# السور المدنية (على طريقة Tanzil)
MADANI = {2, 3, 4, 5, 8, 9, 13, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60, 61, 62,
          63, 64, 65, 66, 76, 98, 99, 110}

# أرقام السور مرتبةً حسب ترتيب النزول (العنصر الأول = أول سورة نزلت)
REVELATION_SEQUENCE = [
    96, 68, 73, 74, 1, 111, 81, 87, 92, 89, 93, 94, 103, 100, 108, 102, 107, 109,
    105, 113, 114, 112, 53, 80, 97, 91, 85, 95, 106, 101, 75, 104, 77, 50, 90, 86,
    54, 38, 7, 72, 36, 25, 35, 19, 20, 56, 26, 27, 28, 17, 10, 11, 12, 15, 6, 37,
    31, 34, 39, 40, 41, 42, 43, 44, 45, 46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52,
    67, 69, 70, 78, 79, 82, 84, 30, 29, 83, 2, 8, 3, 33, 60, 4, 99, 57, 47, 13,
    55, 76, 65, 98, 59, 24, 22, 63, 58, 49, 66, 64, 61, 62, 48, 5, 9, 110,
]
REVELATION_ORDER = {sid: i + 1 for i, sid in enumerate(REVELATION_SEQUENCE)}

assert len(NAMES) == 114 and len(RUKU) == 114 and sum(RUKU) == 558
assert sorted(REVELATION_SEQUENCE) == list(range(1, 115))

# ----------------------------------------------------------------------------
# قراءة الملف
# ----------------------------------------------------------------------------
ALIASES = {
    "sura": ["sura_no", "sura", "surah", "surah_no", "sura_id", "surah_id", "soura"],
    "aya": ["aya_no", "aya", "ayah", "ayah_no", "aya_id", "ayah_id"],
    "page": ["page", "page_no", "page_number"],
    "juz": ["jozz", "juz", "juz_no", "joz"],
    "text": ["aya_text", "text", "aya_text_uthmani", "text_uthmani", "aya_text_emlaey"],
    "name_ar": ["sura_name_ar", "surah_name_ar", "sura_name", "name_ar"],
}


def read_text(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1256"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def try_load(s):
    try:
        return json.loads(s)
    except Exception:
        pass
    try:  # مفاتيح بلا اقتباس / اقتباس مفرد (كائن JavaScript)
        s2 = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', s)
        s2 = re.sub(r"'([^'\\]*)'", r'"\1"', s2)
        return json.loads(s2)
    except Exception:
        return None


def records_from_json_objects(text):
    out = []
    for m in re.finditer(r"\{[^{}]*\}", text, re.S):
        s = m.group(0)
        if not re.search(r"sura|surah|soura", s, re.I):
            continue
        d = try_load(s)
        if isinstance(d, dict):
            out.append(d)
    return out


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self._row, self._cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def records_from_html_table(text):
    p = TableParser()
    p.feed(text)
    header, recs = None, []
    for row in p.rows:
        low = [c.strip().lower() for c in row]
        if header is None:
            if any(a in low for a in ALIASES["sura"]) and any(a in low for a in ALIASES["aya"]):
                header = low
            continue
        if len(row) >= len(header):
            recs.append(dict(zip(header, row)))
    return recs


def pick(rec, kind):
    low = {str(k).strip().lower(): v for k, v in rec.items()}
    for a in ALIASES[kind]:
        if a in low and low[a] not in (None, ""):
            return low[a]
    return None


def to_int(v):
    if v is None:
        return None
    m = re.search(r"\d+", str(v))
    return int(m.group(0)) if m else None


def load_ayahs(path):
    text = read_text(path)
    if "&quot;" in text:
        text = html.unescape(text)
    raw = records_from_json_objects(text) or records_from_html_table(text)
    if not raw:
        sys.exit("لم أجد سجلات آيات في الملف. شغّل الأمر مع --inspect وأرسل لي الناتج.")
    ayahs, seen = [], set()
    for r in raw:
        s, a = to_int(pick(r, "sura")), to_int(pick(r, "aya"))
        if s is None or a is None or a == 0:      # تجاهل البسملة المنفصلة (aya 0) إن وُجدت
            continue
        if (s, a) in seen:
            continue
        seen.add((s, a))
        strings = " ".join(str(v) for v in r.values() if isinstance(v, str))
        ayahs.append({
            "sura": s, "aya": a,
            "page": to_int(pick(r, "page")),
            "juz": to_int(pick(r, "juz")),
            "name_ar": pick(r, "name_ar"),
            "all_text": html.unescape(strings),
        })
    ayahs.sort(key=lambda x: (x["sura"], x["aya"]))
    # حقل jozz في الملف يبدأ الجزء 11 عند 9:94، والصحيح (كما في عيّنتك) 9:93
    for x in ayahs:
        if (x["sura"], x["aya"]) == (9, 93) and x["juz"] == 10:
            x["juz"] = 11
    return ayahs


# ----------------------------------------------------------------------------
# البناء
# ----------------------------------------------------------------------------
_DIAC = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")


_SURA_PREFIX = re.compile("^\\s*س[\u064B-\u065F]*و[\u064B-\u065F]*ر[\u064B-\u065F]*ة[\u064B-\u065F]*\\s+")


def clean_name(name):
    return _SURA_PREFIX.sub("", name or "").strip()


def plain(name):
    name = clean_name(name).replace("ٱ", "ا")
    return _DIAC.sub("", name).strip()


def build_chapters(ayahs):
    by_sura = {}
    for a in ayahs:
        by_sura.setdefault(a["sura"], []).append(a)
    out = []
    for sid in range(1, 115):
        rows = by_sura.get(sid)
        if not rows:
            sys.exit(f"السورة {sid} غير موجودة في الملف")
        en, men, fr, mfr = NAMES[sid - 1]
        name_ar = clean_name(rows[0]["name_ar"]) or ""
        out.append({
            "id": sid,
            "name_ar": name_ar,
            "name_plain": plain(name_ar),
            "name_en": en,
            "meaning_en": men,
            "name_fr": fr,
            "meaning_fr": mfr,
            "ayahs": len(rows),
            "meccan": sid not in MADANI,
            "ruku": RUKU[sid - 1],
            "revelation_order": REVELATION_ORDER[sid],
            "page_start": rows[0]["page"],
            "page_end": rows[-1]["page"],
        })
    return out


def build_juz(ayahs):
    out, last = [], None
    for a in ayahs:
        if a["juz"] != last:
            last = a["juz"]
            out.append({"juz": a["juz"], "surah": a["sura"], "ayah": a["aya"], "page": a["page"]})
    return out


def build_hizb_rub(ayahs, juz):
    """علامات ۞ في الملف تغطي ~199 ربعًا فقط؛ الأرباع التي تبدأ عند أول سورة بلا علامة.
    نكمّلها: كل جزء = 8 أرباع بالضبط (بداية الجزء + العلامات + المفقود). المفقود يُختار من بدايات
    السور داخل الجزء بحيث تكون المسافات بين صفحات الأرباع أكثر انتظامًا. النتيجة تُطبع للمراجعة."""
    from itertools import combinations
    page_of = {(a["sura"], a["aya"]): a["page"] for a in ayahs}
    marks = {(a["sura"], a["aya"]) for a in ayahs if RUB_MARK in a["all_text"]}
    jst = [(j["surah"], j["ayah"]) for j in juz]
    total_end = ayahs[-1]["page"] + 1
    starts, inferred = [], []
    for k, j0 in enumerate(jst):
        j1 = jst[k + 1] if k + 1 < len(jst) else (999, 0)
        known = [j0] + sorted(m for m in marks if j0 < m < j1)
        need = 8 - len(known)
        if need < 0:
            sys.exit(f"الجزء {k + 1}: عدد العلامات أكبر من 7")
        if need:
            cands = sorted({(a["sura"], 1) for a in ayahs
                            if a["aya"] == 1 and j0 < (a["sura"], 1) < j1 and (a["sura"], 1) not in marks})
            if j0 == (78, 1):                      # الربع 240 هو 100:9
                cands = [c for c in cands if c < (100, 9)]
            if len(cands) < need:
                sys.exit(f"الجزء {k + 1}: لا مرشحين كافين للأرباع الناقصة")
            end_page = page_of[j1] if j1 in page_of else total_end
            best = None
            for combo in combinations(cands, need):
                pts = sorted(known + list(combo))
                pages_ = [page_of[x] for x in pts] + [end_page]
                d = [b - a_ for a_, b in zip(pages_, pages_[1:])]
                m = sum(d) / len(d)
                score = sum((x - m) ** 2 for x in d)
                if best is None or score < best[0]:
                    best = (score, combo)
            known += list(best[1])
            inferred += list(best[1])
        starts += sorted(known)
    out = []
    for i, (s_, a_) in enumerate(starts, 1):
        out.append({"rub": i, "hizb": (i - 1) // 4 + 1, "quarter": (i - 1) % 4 + 1,
                    "juz": (i - 1) // 8 + 1, "surah": s_, "ayah": a_, "page": page_of[(s_, a_)]})
    if inferred:
        print("أرباع مستنتجة (بدايات سور بلا علامة ۞) — راجعها بـ validate.py:",
              ", ".join(f"{s_}:{a_}" for s_, a_ in inferred))
    return out


def build_pages(ayahs):
    first = {}
    for a in ayahs:
        first.setdefault(a["page"], a)
    return [{"page": p, "surah": a["sura"], "ayah": a["aya"], "juz": a["juz"],
             "continues_prev": False} for p, a in sorted(first.items())]


def build_sajdas(ayahs):
    return [{"surah": a["sura"], "ayah": a["aya"], "page": a["page"]}
            for a in ayahs if SAJDA_MARK in a["all_text"]]


# ----------------------------------------------------------------------------
# التحقق
# ----------------------------------------------------------------------------
def validate(ch, juz, rub, pages, saj):
    errs = []
    if sum(c["ayahs"] for c in ch) != TOTAL_AYAHS:
        errs.append(f"مجموع الآيات {sum(c['ayahs'] for c in ch)} وليس {TOTAL_AYAHS}")
    if len(juz) != 30:
        errs.append(f"عدد الأجزاء {len(juz)} وليس 30")
    if len(rub) != 240:
        errs.append(f"عدد الأرباع {len(rub)} وليس 240")
    if len(pages) != 604:
        errs.append(f"عدد الصفحات {len(pages)} وليس 604")
    if len(saj) != 15:
        errs.append(f"عدد السجدات {len(saj)} وليس 15")
    if pages and (pages[0]["page"], pages[0]["surah"], pages[0]["ayah"]) != (1, 1, 1):
        errs.append("أول صفحة ليست 1 (1:1)")
    if pages and pages[-1]["page"] != 604:
        errs.append("آخر صفحة ليست 604")
    ayah_max = {c["id"]: c["ayahs"] for c in ch}
    for name, lst in (("juz", juz), ("hizb_rub", rub), ("pages", pages)):
        keys = [(x["page"] if name != "pages" else x["page"], ) for x in lst]
        if keys != sorted(keys):
            errs.append(f"{name}: الصفحات غير مرتبة تصاعديًا")
        for x in lst:
            s, a = x.get("surah"), x.get("ayah")
            if s and a and a > ayah_max[s]:
                errs.append(f"{name}: {s}:{a} يتجاوز عدد آيات السورة")
    for k in range(min(30, len(rub) // 8 + 1)):
        if 8 * k < len(rub) and k < len(juz):
            r, j = rub[8 * k], juz[k]
            if (r["surah"], r["ayah"]) != (j["surah"], j["ayah"]):
                errs.append(f"الربع {8 * k + 1} لا يطابق بداية الجزء {k + 1}")
    return errs


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def inspect(path):
    text = read_text(path)
    print("حجم الملف:", len(text), "حرف")
    print("أول 800 حرف:\n", text[:800], "\n...")
    objs = records_from_json_objects(html.unescape(text) if "&quot;" in text else text)
    print("عدد كائنات JSON المطابقة:", len(objs))
    if objs:
        print("عينة:", json.dumps(objs[0], ensure_ascii=False))
        print("عدد ۞ :", text.count(RUB_MARK), "| عدد ۩ :", text.count(SAJDA_MARK))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help=r'مسار الملف مثل D:\hafsData_v2-0.html')
    ap.add_argument("-o", "--out", default="meta", help="مجلد المخرجات (الافتراضي meta)")
    ap.add_argument("--inspect", action="store_true", help="معاينة بنية الملف فقط")
    args = ap.parse_args()

    if args.inspect:
        return inspect(args.input)

    ayahs = load_ayahs(args.input)
    print(f"تمت قراءة {len(ayahs)} آية")
    missing = [a for a in ayahs if a["page"] is None or a["juz"] is None]
    if missing:
        sys.exit(f"{len(missing)} آية بلا صفحة أو جزء، مثال: {missing[0]['sura']}:{missing[0]['aya']}")

    ch = build_chapters(ayahs)
    juz = build_juz(ayahs)
    rub = build_hizb_rub(ayahs, juz)
    pages = build_pages(ayahs)
    saj = build_sajdas(ayahs)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for fname, data in (("chapters.json", ch), ("juz.json", juz), ("hizb_rub.json", rub),
                        ("pages.json", pages), ("sajdas.json", saj)):
        dump(out / fname, data)
        print(f"{fname}: {len(data)} عنصر")

    errs = validate(ch, juz, rub, pages, saj)
    if errs:
        print("\nتنبيهات:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print("\nنجحت كل فحوصات القواعد العامة ✔")


if __name__ == "__main__":
    main()
