#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
root.py — 输出根目录的持久化与首次运行引导。

  root.py get                 # 打印已保存的输出根目录；首次运行返回空（stdout 为空）
  root.py set --path <绝对路径>
  root.py set --default       # 重置为 ~/Desktop/Live Input
"""
import argparse
import json
import os
import sys
from datetime import datetime

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(SKILL_DIR, "state.json")
def _default_root():
    """跨平台默认输出目录：优先桌面，找不到桌面就用家目录。"""
    home = os.path.expanduser("~")
    for name in ("Desktop", "桌面", "Bureau", "Schreibtisch", "Escritorio"):
        p = os.path.join(home, name)
        if os.path.isdir(p):
            return os.path.join(p, "Live Input")
    return os.path.join(home, "Live Input")


DEFAULT_ROOT = _default_root()


def _read():
    if not os.path.exists(STATE):
        return {}
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write(d):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def cmd_get(a):
    root = _read().get("output_root")
    if root and os.path.isdir(root):
        print(root)
        return
    # 首次运行：自动创建默认目录，stdout 留空 → 由 agent 弹出位置确认
    os.makedirs(DEFAULT_ROOT, exist_ok=True)
    sys.stderr.write(
        "首次运行：未配置输出根目录。已创建默认目录 %s —— 请询问用户确认使用该目录，"
        "或让用户提供自定义绝对路径（确认后用 root.py set --path 写入）。\n"
        % DEFAULT_ROOT
    )


def cmd_set(a):
    if a.default:
        path = DEFAULT_ROOT
    else:
        path = os.path.abspath(os.path.expanduser(a.path))
    os.makedirs(path, exist_ok=True)
    d = _read()
    d["output_root"] = path
    d["set_at"] = datetime.now().isoformat(timespec="seconds")
    _write(d)
    print(path)


def main():
    p = argparse.ArgumentParser(description="输出根目录管理")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("get")
    s.set_defaults(fn=cmd_get)

    s = sub.add_parser("set")
    s.add_argument("--path")
    s.add_argument("--default", action="store_true")
    s.set_defaults(fn=cmd_set)

    a = p.parse_args()
    if a.cmd == "set" and not a.default and not a.path:
        p.error("需要 --path 或 --default")
    a.fn(a)


if __name__ == "__main__":
    main()
