# إشعارات الأطراف الثالثة (Third-party notices)

هذا المستودع يجمع بيانات من مصادر لكل منها ترخيصه. **المسؤولية عن الالتزام بالتراخيص عند توزيع التطبيق تقع عليك.**
لست محاميًا، وما يلي ملخص لما وجدته، وليس استشارة قانونية.

| المكوّن | المصدر | الترخيص | الحالة |
|---|---|---|---|
| ملفات `meta/*.json` (السور، الأجزاء، الأرباع، السجدات) | حزمة quran-meta 7.0.0 | MIT (النص أدناه) | ✅ يلزم إبقاء إشعار الترخيص |
| أرقام الصفحات في `meta/` | مشتقّة من بيانات QCF4 (أرقام فقط) | — | ✅ حقائق عددية |
| `tafsir/*.json` | مشروع spa5k/tafsir_api | MIT للمستودع (النص أدناه) | ⚠️ المستودع MIT، لكن حقوق نصوص التفاسير نفسها تعود لأصحابها/ناشريها؛ تحقّق منها |
| `fonts/ui/` (Amiri، Amiri Quran، Scheherazade New) | Google Fonts | SIL Open Font License 1.1 (النصوص في المجلد) | ✅ مسموح بالتضمين والتوزيع مع إبقاء ملفات OFL |
| `fonts/qcf4/` (خطوط مصحف المدينة QCF4) | مجمّع الملك فهد لطباعة المصحف الشريف | ❓ غير مؤكّد | ⚠️ راجع شروط المجمّع قبل التوزيع (`qurancomplex.gov.sa`) |
| `mushaf/qcf4_pages.json` (يُولَّد بالأداة) | مستودع MohamadHajjRabee/quran-qcf4 | ❓ بلا ملف ترخيص؛ يطلب احترام شروط المجمّع | ⚠️ راجع قبل التوزيع/النشر العلني |

## نص ترخيص quran-meta (MIT)

```
MIT License

Copyright (c) 2020 Quran-Center

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## نص ترخيص tafsir_api (MIT)

```
MIT License

Copyright (c) 2023 Spark

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## خطوط الواجهة (OFL)
نصوص الترخيص في `fonts/ui/OFL-*.txt`. شرط OFL الأهم: لا تبع الخط وحده، وأبقِ إشعار حقوق النشر وملف الترخيص مع الخط.
