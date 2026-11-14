#!/usr/bin/env python3
"""生成自包含离线页面 offline.html：复制 index.html 并在 <head> 内联 offline_engine.js。"""
import pathlib

base = pathlib.Path(__file__).resolve().parent
index = base / 'static' / 'index.html'
engine = base / 'static' / 'offline_engine.js'
out = base / 'offline.html'

html = index.read_text(encoding='utf-8')
js = engine.read_text(encoding='utf-8')

# 在 </head> 前注入引擎（自动覆盖 window.fetch，前端 apiCall 无需改动）
inject = f"<script>\n{js}\n</script>\n</head>"
assert '</head>' in html, 'index.html 缺少 </head>'
html = html.replace('</head>', inject, 1)

out.write_text(html, encoding='utf-8')
print(f'已生成 {out}  ({len(html)} 字节, 内联引擎 {len(js)} 字节)')
