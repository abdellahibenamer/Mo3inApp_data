// يولّد ملفات meta/*.json (رواية حفص) من حزمة quran-meta (رخصة MIT).
// التشغيل:  npm install   ثم   node tools/build_meta.mjs
import fs from 'node:fs';
import { getSurahName, surahNamesAr, surahNamesEn } from 'quran-meta';
import { surahNamesFr } from 'quran-meta/i18n';
import * as H from 'quran-meta/hafs';

const OUT = new URL('../meta/', import.meta.url);
const write = (name, data) => fs.writeFileSync(new URL(name, OUT), JSON.stringify(data, null, 1) + '\n');
const strip = (s) => s.replace(/[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g, '').replace(/[أإآٱ]/g, 'ا');
const pageOf = (id) => H.findPageByAyahId(id);
const sa = (id) => H.findSurahAyahByAyahId(id);

// --- السور (114) ---
const chapters = [];
for (let s = 1; s <= 114; s++) {
  const m = H.getSurahMeta(s);
  const [ar, arPlain] = getSurahName(s, surahNamesAr);
  const [en, meaning] = getSurahName(s, surahNamesEn);
  const [fr, meaningFr] = getSurahName(s, surahNamesFr);
  chapters.push({
    id: s, name_ar: ar, name_plain: arPlain || strip(ar), name_en: en, meaning_en: meaning, name_fr: fr, meaning_fr: meaningFr,
    ayahs: m.ayahCount, meccan: m.isMeccan, ruku: m.rukuCount, revelation_order: m.surahOrder,
    page_start: pageOf(m.firstAyahId), page_end: pageOf(m.lastAyahId),
  });
}
write('chapters.json', chapters);

// --- الأجزاء (30) ---
const juz = H.JuzList.slice(1, 31).map((id, i) => { const [s, a] = sa(id); return { juz: i + 1, surah: s, ayah: a, page: pageOf(id) }; });
write('juz.json', juz);

// --- الأرباع (240): الحزب = 4 أرباع، والجزء = 8 أرباع ---
const rub = H.HizbQuarterList.slice(1, 241).map((id, i) => {
  const [s, a] = sa(id);
  return { rub: i + 1, hizb: Math.floor(i / 4) + 1, quarter: (i % 4) + 1, juz: Math.floor(i / 8) + 1, surah: s, ayah: a, page: pageOf(id) };
});
write('hizb_rub.json', rub);

// --- الصفحات (604): أول آية في كل صفحة ---
const pages = H.PageList.slice(1, 605).map((id, i) => {
  const [s, a] = sa(id);
  return { page: i + 1, surah: s, ayah: a, juz: H.findJuzByAyahId(id) };
});
write('pages.json', pages);

// --- سجدات التلاوة (15) ---
write('sajdas.json', H.SajdaList.map((id) => { const [s, a] = sa(id); return { surah: s, ayah: a, page: pageOf(id) }; }));

write('info.json', {
  riwaya: 'hafs', surahs: 114, ayahs: 6236, pages: 604, juz: 30, hizb: 60, rub: 240,
  source: 'quran-meta@7.0.0 (MIT) https://github.com/quran-center/quran-meta',
  note: 'أرقام الصفحات حسب مصحف المدينة (604 صفحة)',
});
console.log('OK:', chapters.length, 'surahs,', juz.length, 'juz,', rub.length, 'rub,', pages.length, 'pages');
