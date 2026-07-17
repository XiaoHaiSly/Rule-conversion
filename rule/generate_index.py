"""
扫描 rule/singbox 和 rule/mihomo，生成 rule/index.html 作为 Cloudflare Pages 的落地页。
由 .github/workflows/deploy-pages.yml 在部署前调用，不需要手动运行。
"""
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # rule/
CATEGORIES = [("sing-box", "singbox"), ("mihomo", "mihomo")]
SUBDIRS = ["domain", "ipcidr"]


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def collect_files(folder):
    if not os.path.isdir(folder):
        return []
    items = []
    for fname in sorted(os.listdir(folder)):
        if fname.startswith('.'):
            continue
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            items.append((fname, os.path.getsize(fpath)))
    return items


def file_rows_html(rel_base, files):
    if not files:
        return '<tr class="empty-row"><td colspan="2">-- empty --</td></tr>'
    rows = []
    for fname, size in files:
        href = f"{rel_base}/{fname}"
        ext = fname.rsplit('.', 1)[-1] if '.' in fname else ''
        rows.append(
            f'<tr><td><a class="fname" href="{href}">{fname}</a></td>'
            f'<td class="ftype">.{ext}</td><td class="fsize">{human_size(size)}</td></tr>'
        )
    return "\n".join(rows)


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    blocks = []
    total_files = 0

    for label, dirname in CATEGORIES:
        sub_blocks = []
        for sub in SUBDIRS:
            folder = os.path.join(BASE_DIR, dirname, sub)
            files = collect_files(folder)
            total_files += len(files)
            rel_base = f"{dirname}/{sub}"
            sub_blocks.append(f'''
      <details class="subtable" open>
        <summary><span class="path">/{dirname}/{sub}/</span><span class="count">{len(files)}</span></summary>
        <table>
          <thead><tr><th>file</th><th>type</th><th>size</th></tr></thead>
          <tbody>
{file_rows_html(rel_base, files)}
          </tbody>
        </table>
      </details>''')
        blocks.append(f'''
    <section class="node">
      <h2>{label}<span class="root">/{dirname}/</span></h2>
      {''.join(sub_blocks)}
    </section>''')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>rule-feed // index</title>
<style>
  @media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
  :root {{
    --bg: #14110c;
    --panel: #1b170f;
    --line: #3a3020;
    --amber: #e8a33d;
    --amber-dim: #a87a35;
    --text: #ede4d3;
    --muted: #8c8271;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: "SFMono-Regular", "JetBrains Mono", Consolas, Menlo, monospace;
    padding: 48px 20px 90px;
    font-size: 14px;
  }}
  a {{ color: inherit; }}
  .wrap {{ max-width: 820px; margin: 0 auto; }}
  .prompt {{ color: var(--amber-dim); font-size: 13px; margin-bottom: 4px; }}
  h1 {{
    font-size: 22px; margin: 0 0 4px; color: var(--amber);
    letter-spacing: 0.02em; font-weight: 600;
  }}
  .sub {{ color: var(--muted); font-size: 13px; margin: 0 0 28px; }}
  .stats {{ display: flex; gap: 24px; margin-bottom: 32px; font-size: 12px; color: var(--muted); }}
  .stats b {{ color: var(--amber); font-weight: 600; }}
  .node {{ margin-bottom: 28px; }}
  .node h2 {{
    font-size: 15px; color: var(--text); margin: 0 0 10px;
    border-bottom: 1px solid var(--line); padding-bottom: 8px;
    display: flex; align-items: baseline; gap: 8px;
  }}
  .node h2 .root {{ color: var(--amber-dim); font-weight: 400; font-size: 12px; }}
  details.subtable {{
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 4px; margin-bottom: 10px; overflow: hidden;
  }}
  details.subtable summary {{
    list-style: none; cursor: pointer; padding: 9px 14px;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 13px; user-select: none;
  }}
  details.subtable summary::-webkit-details-marker {{ display: none; }}
  details.subtable summary::before {{ content: "▸ "; color: var(--amber-dim); }}
  details.subtable[open] summary::before {{ content: "▾ "; }}
  details.subtable summary .path {{ color: var(--amber); }}
  details.subtable summary .count {{
    color: var(--muted); background: var(--bg); border: 1px solid var(--line);
    border-radius: 10px; padding: 1px 8px; font-size: 11px;
  }}
  table {{ width: 100%; border-collapse: collapse; border-top: 1px solid var(--line); }}
  thead th {{
    text-align: left; color: var(--muted); font-weight: 400; font-size: 11px;
    padding: 6px 14px; text-transform: lowercase; letter-spacing: 0.04em;
  }}
  tbody tr {{ border-top: 1px solid var(--line); }}
  tbody tr:hover {{ background: rgba(232, 163, 61, 0.06); }}
  tbody td {{ padding: 7px 14px; font-size: 12.5px; }}
  a.fname {{ text-decoration: none; color: var(--text); }}
  a.fname:hover {{ color: var(--amber); text-decoration: underline; }}
  .ftype {{ color: var(--amber-dim); }}
  .fsize {{ color: var(--muted); text-align: right; }}
  .empty-row td {{ color: var(--muted); font-style: italic; padding: 10px 14px; }}
  footer {{ margin-top: 40px; color: var(--muted); font-size: 11px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="prompt">$ tree rule/ --format=srs,json,mrs,yaml</div>
  <h1>rule-feed index</h1>
  <p class="sub">sing-box / mihomo 规则集自动构建产物 · 按域名(domain) / IP段(ipcidr) 分类</p>
  <div class="stats">
    <span><b>{total_files}</b> files</span>
    <span>built <b>{now}</b></span>
  </div>
  {''.join(blocks)}
  <footer>generated by rule/generate_index.py · deployed via Cloudflare Pages</footer>
</div>
</body>
</html>'''

    out_path = os.path.join(BASE_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"生成 {out_path}，共 {total_files} 个文件")


if __name__ == "__main__":
    main()
