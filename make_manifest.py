# -*- coding: utf-8 -*-
"""
يكتب manifest.json: قائمة كل ملفات البيانات مع حجمها وبصمتها (SHA-256) ورقم إصدار البيانات.
يستعمله التطبيق (أو سكربت البناء) للتأكد أن الملفات سليمة وكاملة.

التشغيل:  python tools/make_manifest.py --version 2026.10.1
"""
import datetime
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SKIP_DIRS = {".git", "node_modules", "tools", "__pycache__"}
SKIP_FILES = {"manifest.json", ".gitignore", ".gitattributes", "package.json", "package-lock.json"}
TEXT_EXT = (".json", ".txt", ".md", ".mjs", ".py", ".toml")


def content_bytes(path):
    """بايتات الملف لحساب البصمة. الملفات النصية تُوحَّد فيها نهايات الأسطر إلى LF،
    لأن Git على ويندوز يحوّلها (CRLF محليًا وLF في GitHub) فتختلف البصمة دون أي تغيير حقيقي."""
    with open(path, "rb") as f:
        b = f.read()
    return b.replace(b"\r\n", b"\n") if path.lower().endswith(TEXT_EXT) else b


def main():
    version = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else datetime.date.today().strftime("%Y.%m.%d")
    files = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for n in sorted(names):
            if n in SKIP_FILES or n.endswith(".pyc"):
                continue
            p = os.path.join(base, n)
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            if rel.startswith("docs/") or rel in {"README.md", "LICENSES.md", "GITHUB_SETUP_AR.md"}:
                continue
            data = content_bytes(p)
            files.append({"path": rel, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    doc = {"dataset_version": version, "hash_note": "الملفات النصية تُحسب بصمتها بعد توحيد نهايات الأسطر إلى LF", "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "files": files}
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"manifest.json: {len(files)} ملفًا، الإصدار {version}")


if __name__ == "__main__":
    main()
