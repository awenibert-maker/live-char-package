#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manifest.py — 输出「序号 / 角色名 / 文件夹名称 / 上传包」汇总表格。

  manifest.py --root <输出根目录>
"""
import argparse
import os
import re

SKIP = {"_progress", ".DS_Store"}


def role_name(pkg):
    spec = os.path.join(pkg, "character_spec.md")
    if os.path.exists(spec):
        with open(spec, encoding="utf-8") as f:
            head = f.read(1200)
        m = re.search(r"角色名[**\s：:]*([^\n（(]+)", head)
        if m:
            return m.group(1).strip().strip("* ")
        m = re.search(r"^#\s*角色规范[：:]\s*([^\n（(]+)", head, re.M)
        if m:
            return m.group(1).strip()
    return re.sub(r"_\d{3}$", "", os.path.basename(pkg))


def main():
    ap = argparse.ArgumentParser(description="生成汇总表格")
    ap.add_argument("--root", required=True)
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    pkgs = sorted(
        d for d in os.listdir(root)
        if d not in SKIP and os.path.isdir(os.path.join(root, d))
        and os.path.exists(os.path.join(root, d, "soul.md"))
    )
    if not pkgs:
        print("（未找到角色包）")
        return

    lines = ["| 序号 | 角色名 | 文件夹名称 | 上传包 |", "|---|---|---|---|"]
    for i, d in enumerate(pkgs, 1):
        zip_mark = ("`" + d + ".zip`") if os.path.exists(os.path.join(root, d + ".zip")) else "—"
        lines.append("| %d | %s | `%s` | %s |" % (i, role_name(os.path.join(root, d)), d, zip_mark))
    print("输出目录：`%s`\n" % root)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
