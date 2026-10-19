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
SKIP_FILES = {"manifest.json", ".gitignore", "package.json", "package-lock.json"}


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
            with open(p, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            files.append({"path": rel, "size": os.path.getsize(p), "sha256": h})
    doc = {"dataset_version": version, "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "files": files}
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"manifest.json: {len(files)} ملفًا، الإصدار {version}")


if __name__ == "__main__":
    main()
