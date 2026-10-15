#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
intake_server.py — 需求收集表单（本地 HTTP 页面，带真正的「新增」按钮，最多 10 个角色）

  intake_server.py --out <输出根目录> [--port 8733]

行为：
  - 启动 127.0.0.1 上的临时服务，打印 URL 并写入 <out>/_intake/url.txt
  - 页面：每行 = 姓名 / 语言 / 一句话需求；右下角「＋ 新增一个角色」（上限 10）
  - 提交后写入 <out>/_intake/briefs.json，页面提示已提交，服务 1.5s 后自动退出

briefs.json 结构：
  [{"name":"meriam malak","lang":"English","need":"温暖陪伴型互动主播"}, ...]
"""
import argparse
import json
import os
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LANGS = [
    "English", "中文", "Português (巴西)", "العربية", "Español", "日本語",
    "한국어", "Français", "Deutsch", "Bahasa Indonesia", "Українська",
    "Hindi", "Türkçe", "其他（在需求里注明）",
]

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>直播间配置包 · 需求收集</title>
<style>
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;padding:26px 30px 96px;background:#0f1115;color:#e5e7eb;
 font:14px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",Arial,sans-serif}
h1{margin:0 0 4px;font-size:19px;font-weight:600}
.sub{color:#9ca3af;font-size:12px;margin-bottom:20px}
.row{background:#141821;border:1px solid #232936;border-radius:12px;padding:14px 16px;margin-bottom:12px}
.hd{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.idx{width:24px;height:24px;border-radius:7px;background:#1f2937;color:#9ca3af;
 font-size:12px;display:flex;align-items:center;justify-content:center;flex:none}
.hd input{flex:1}
.hd select{width:190px;flex:none}
.hd button{width:28px;height:28px;border-radius:8px;border:1px solid #2b3242;background:#191f2b;
 color:#9ca3af;cursor:pointer;font-size:15px;line-height:1;flex:none}
.hd button:hover{color:#f87171;border-color:#7f1d1d}
input,select,textarea{background:#0f141c;border:1px solid #2b3242;border-radius:8px;color:#e5e7eb;
 padding:8px 10px;font:inherit;outline:none}
input:focus,select:focus,textarea:focus{border-color:#22d3ee}
textarea{width:100%;resize:vertical;min-height:52px}
::placeholder{color:#5b6472}
.bar{position:fixed;left:0;right:0;bottom:0;background:#0f1115;border-top:1px solid #232936;
 padding:14px 30px;display:flex;align-items:center;justify-content:space-between;gap:12px}
.cnt{color:#9ca3af;font-size:12px}
.btns{display:flex;gap:10px}
.btn{border-radius:9px;padding:9px 16px;font:inherit;cursor:pointer;border:1px solid #2b3242;
 background:#191f2b;color:#e5e7eb}
.btn.add:hover{border-color:#34d399;color:#34d399}
.btn.go{background:#22d3ee;border-color:#22d3ee;color:#06222a;font-weight:600}
.btn:disabled{opacity:.45;cursor:not-allowed}
.done{display:none;margin-top:22px;padding:14px 16px;border-radius:12px;
 background:#0c2a20;border:1px solid #1c6b4f;color:#6ee7b7}
.warn{color:#fbbf24;font-size:12px;margin-top:8px;display:none}
</style></head><body>
<h1>直播间配置包 · 需求收集</h1>
<div class="sub">每行一个角色，最多 10 个。填完点右下角「确认提交」，然后回到对话即可。</div>
<div id="list"></div>
<div class="warn" id="warn">请至少填写 1 个角色名。</div>
<div class="done" id="done">✔ 已提交，共 <b id="dn">0</b> 个角色。可以回到 WorkBuddy 对话了。</div>

<div class="bar">
  <div class="cnt" id="cnt">已填 0 / 10</div>
  <div class="btns">
    <button class="btn add" id="add">＋ 新增一个角色</button>
    <button class="btn go" id="go">确认提交</button>
  </div>
</div>

<script>
var MAX = 10;
var LANGS = __LANGS__;
var list = document.getElementById('list');

function optHTML(sel){
  return LANGS.map(function(l){
    return '<option'+(l===sel?' selected':'')+'>'+l+'</option>';
  }).join('');
}

function addRow(){
  if(list.children.length >= MAX) return;
  var d = document.createElement('div');
  d.className = 'row';
  d.innerHTML =
    '<div class="hd">'+
      '<div class="idx"></div>'+
      '<input class="nm" placeholder="角色名（必填，如 meriam malak）">'+
      '<select class="lg">'+optHTML('English')+'</select>'+
      '<button class="rm" title="删除这一行">×</button>'+
    '</div>'+
    '<textarea class="nd" placeholder="一句话角色需求：她是做什么的 / 什么性格 / 面向谁（可多写几句）"></textarea>';
  d.querySelector('.rm').onclick = function(){ d.remove(); refresh(); };
  d.querySelector('.nm').oninput = refresh;
  list.appendChild(d);
  refresh();
}

function refresh(){
  var rows = list.querySelectorAll('.row');
  rows.forEach(function(r,i){ r.querySelector('.idx').textContent = i+1; });
  var filled = 0;
  rows.forEach(function(r){ if(r.querySelector('.nm').value.trim()) filled++; });
  document.getElementById('cnt').textContent = '已填 '+filled+' / '+MAX+'（共 '+rows.length+' 行）';
  document.getElementById('add').disabled = rows.length >= MAX;
}

function collect(){
  var out = [];
  list.querySelectorAll('.row').forEach(function(r){
    var n = r.querySelector('.nm').value.trim();
    if(!n) return;
    out.push({name:n, lang:r.querySelector('.lg').value, need:r.querySelector('.nd').value.trim()});
  });
  return out;
}

document.getElementById('add').onclick = addRow;
document.getElementById('go').onclick = function(){
  var data = collect();
  if(!data.length){ document.getElementById('warn').style.display='block'; return; }
  document.getElementById('warn').style.display='none';
  fetch('/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
    .then(function(){
      document.getElementById('dn').textContent = data.length;
      document.getElementById('done').style.display='block';
      document.getElementById('go').disabled = true;
      document.getElementById('go').textContent = '已提交';
    })
    .catch(function(e){ alert('提交失败：'+e); });
};

addRow(); addRow(); addRow();
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    out_path = None

    def log_message(self, *a):
        pass  # 静音

    def _send(self, body, ctype="text/html; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/ping"):
            self._send(b"ok", "text/plain")
            return
        body = PAGE.replace("__LANGS__", json.dumps(LANGS, ensure_ascii=False)).encode("utf-8")
        self._send(body)

    def do_POST(self):
        if not self.path.startswith("/submit"):
            self._send(b"not found", "text/plain", 404)
            return
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8")
        try:
            data = json.loads(raw)
            assert isinstance(data, list) and data
            data = data[:10]
            for d in data:
                d["name"] = str(d.get("name", "")).strip()
                d["lang"] = str(d.get("lang", "English")).strip()
                d["need"] = str(d.get("need", "")).strip()
            data = [d for d in data if d["name"]]
            assert data
        except Exception as e:
            self._send(json.dumps({"ok": False, "err": str(e)}).encode(),
                       "application/json", 400)
            return
        os.makedirs(os.path.dirname(Handler.out_path), exist_ok=True)
        with open(Handler.out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._send(json.dumps({"ok": True, "n": len(data)}).encode(), "application/json")
        sys.stdout.write("已收到 %d 个角色需求 → %s\n" % (len(data), Handler.out_path))
        sys.stdout.flush()
        threading.Timer(1.5, self.server.shutdown).start()


def free_port(preferred):
    for p in range(preferred, preferred + 40):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise SystemExit("找不到可用端口")


def main():
    ap = argparse.ArgumentParser(description="需求收集表单服务")
    ap.add_argument("--out", required=True, help="输出根目录（briefs.json 写到 <out>/_intake/）")
    ap.add_argument("--port", type=int, default=8733)
    a = ap.parse_args()

    out_dir = os.path.join(os.path.abspath(a.out), "_intake")
    os.makedirs(out_dir, exist_ok=True)
    briefs = os.path.join(out_dir, "briefs.json")
    if os.path.exists(briefs):
        os.remove(briefs)  # 防陈旧数据
    Handler.out_path = briefs

    port = free_port(a.port)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:%d/" % port
    with open(os.path.join(out_dir, "url.txt"), "w") as f:
        f.write(url)
    print(url)
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
