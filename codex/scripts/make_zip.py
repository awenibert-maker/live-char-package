#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_zip.py — 打上传包（内部仅 soul/agent/prologue/livescript 四个文件）。

  make_zip.py --dir <pkg>/Name_001
  → 生成 <pkg>/Name_001/Name_001.zip
"""
import argparse
import os
import sys
import zipfile

FILES = ["soul.md", "agent.md", "prologue.md", "livescript.md"]


def main():
    ap = argparse.ArgumentParser(description="打上传 zip")
    ap.add_argument("--dir", required=True, help="角色包文件夹路径")
    ap.add_argument("--name", help="覆盖 zip 名（默认取文件夹名）")
    a = ap.parse_args()

    pkg = os.path.abspath(a.dir)
    if not os.path.isdir(pkg):
        raise SystemExit("目录不存在: %s" % pkg)

    missing = [f for f in FILES if not os.path.exists(os.path.join(pkg, f))]
    if missing:
        raise SystemExit("缺少文件，无法打包: %s" % ", ".join(missing))

    zip_name = (a.name or os.path.basename(pkg)) + ".zip"
    # 与角色文件夹平级（不放在文件夹内），便于批量选中多个包
    zip_path = os.path.join(os.path.dirname(pkg), zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            z.write(os.path.join(pkg, f), f)
    print("已打包 %s（%d 文件）" % (zip_path, len(FILES)))


if __name__ == "__main__":
    main()
