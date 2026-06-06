"""HTML index generator for MeowDesk file archive."""

import base64
import hashlib
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .utils import get_logger


_log = get_logger(__name__)


SCREENSHOT_RE = re.compile(
    r'^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}'
    r'|^Screenshot[_\s]'
    r'|^微信截图'
    r'|^微信图片_\d{8}'
    r'|^QQ 截图'
    r'|^屏幕截图'
    r'|^Snipaste'
    r'|^截屏'
    r'|^捕获'
    r'|^[Cc]apture'
    r'|^[Ss]creenshot'
    r'|^clip_'
    r'|^paste_'
    r'|^新建 位图图像',
    re.IGNORECASE,
)


EXT_CAT: Dict[str, str] = {
    ".png": "图片", ".jpg": "图片", ".jpeg": "图片", ".gif": "图片", ".bmp": "图片",
    ".webp": "图片", ".svg": "图片", ".ico": "图片", ".tiff": "图片", ".tif": "图片",
    ".mp4": "视频", ".avi": "视频", ".mkv": "视频", ".mov": "视频", ".wmv": "视频",
    ".flv": "视频", ".webm": "视频",
    ".mp3": "音频", ".wav": "音频", ".flac": "音频", ".ogg": "音频", ".aac": "音频",
    ".m4a": "音频",
    ".pdf": "文档", ".doc": "文档", ".docx": "文档", ".xls": "文档", ".xlsx": "文档",
    ".ppt": "文档", ".pptx": "文档", ".txt": "文档", ".csv": "文档", ".md": "文档",
    ".rtf": "文档",
    ".zip": "压缩包", ".rar": "压缩包", ".7z": "压缩包", ".tar": "压缩包", ".gz": "压缩包",
    ".exe": "安装包", ".msi": "安装包",
    ".py": "代码", ".js": "代码", ".html": "代码", ".css": "代码", ".json": "代码",
    ".java": "代码", ".cpp": "代码", ".c": "代码", ".h": "代码", ".bat": "代码",
    ".ps1": "代码", ".sh": "代码",
    ".psd": "设计稿", ".ai": "设计稿", ".sketch": "设计稿",
}


CAT_META: Dict[str, tuple] = {
    "截图": ("\U0001f4f8", "#ef4444"),
    "图片": ("\U0001f5bc\ufe0f", "#8b5cf6"),
    "视频": ("\U0001f3ac", "#ec4899"),
    "音频": ("\U0001f3b5", "#f59e0b"),
    "文档": ("\U0001f4c4", "#3b82f6"),
    "压缩包": ("\U0001f4e6", "#06b6d4"),
    "安装包": ("\U0001f4bf", "#6366f1"),
    "代码": ("\U0001f4bb", "#10b981"),
    "设计稿": ("\U0001f3a8", "#d946ef"),
    "其他": ("\U0001f4c1", "#94a3b8"),
}


def classify_filename(name: str) -> str:
    """Classify a file by extension and screenshot heuristics."""

    ext = os.path.splitext(name)[1].lower()
    base = EXT_CAT.get(ext, "其他")
    if base == "图片" and SCREENSHOT_RE.search(name):
        return "截图"
    return base


def format_size(sz: int) -> str:
    """Format a size in bytes to human-readable string."""

    if sz > 1073741824:
        return "%.1f GB" % (sz / 1073741824)
    if sz > 1048576:
        return "%.1f MB" % (sz / 1048576)
    if sz > 1024:
        return "%.1f KB" % (sz / 1024)
    return "%d B" % sz


def _build_stat_cards(cats: Dict[str, Dict[str, Any]]) -> str:
    """Build the stat-card HTML blocks."""

    sc = []
    for cn, info in sorted(cats.items(), key=lambda x: -x[1]["count"]):
        emoji, color = CAT_META.get(cn, ("\U0001f4c1", "#94a3b8"))
        sc.append(
            '        <div class="stat-card" data-cat="' + cn + '" style="border-left: 3px solid ' + color + '">'
            '<div class="stat-icon">' + emoji + '</div>'
            '<div class="stat-info">'
            '<div class="stat-name">' + cn + '</div>'
            '<div class="stat-detail">' + str(info["count"]) + ' 个文件 · ' + format_size(info["size"]) + '</div>'
            '</div></div>'
        )
    return "\n".join(sc)


def _build_cat_options(cats: Dict[str, Dict[str, Any]]) -> str:
    """Build the <option> blocks for the category filter."""

    co = []
    for cn, info in sorted(cats.items(), key=lambda x: -x[1]["count"]):
        emoji, _ = CAT_META.get(cn, ("\U0001f4c1", "#94a3b8"))
        co.append('<option value="' + cn + '">' + emoji + ' ' + cn + ' (' + str(info["count"]) + ')</option>')
    return "".join(co)


def _build_rows(records: List[Dict[str, Any]]) -> str:
    """Build the table rows HTML."""

    rows = []
    for rec in records:
        cat = rec.get("category", "其他")
        name = rec.get("original_name", "")
        date = rec.get("date", "")
        action = rec.get("action", "")
        dest = rec.get("destination", "")
        sz = rec.get("file_size", 0)
        emoji, color = CAT_META.get(cat, ("\U0001f4c1", "#94a3b8"))
        badge_cls = "badge-recycle" if action == "recycle" else "badge-archive"
        badge_txt = "已回收" if action == "recycle" else "已归档"
        path_short = os.path.basename(dest) if dest and dest != "(已回收)" else "(已回收)"
        locate = ""
        if dest and dest != "(已回收)" and action == "archive":
            enc = base64.b64encode(dest.encode("utf-8")).decode("ascii")
            locate = ' <a class="btn-locate" href="meow-locate://' + enc + '">定位</a>'
        rows.append(
            '<tr>'
            '<td data-cat="' + cat + '"><span class="cat-dot" style="background:' + color + '"></span> ' + emoji + ' ' + cat + '</td>'
            '<td title="' + name + '">' + name + '</td>'
            '<td>' + date + '</td>'
            '<td>' + format_size(sz) + '</td>'
            '<td><span class="badge ' + badge_cls + '">' + badge_txt + '</span>' + locate + '</td>'
            '<td class="path-cell" title="' + dest + '">' + path_short + '</td>'
            '</tr>'
        )
    return "\n".join(rows)


def generate_html(records: List[Dict[str, Any]], archive_dir: str, archive_url: str, page_size: int = 200) -> str:
    """Generate the HTML index page.

    Args:
        records: List of file records from FileDatabase
        archive_dir: Local path to the archive directory (for footer text)
        archive_url: URL / path to use in the "open directory" link
        page_size: Number of items to show per page (client-side pagination)
    """

    records = sorted(records, key=lambda r: r.get("timestamp", ""), reverse=True)
    total_size = sum(r.get("file_size", 0) for r in records)

    cats: Dict[str, Dict[str, Any]] = {}
    for rec in records:
        c = rec.get("category", "其他")
        if c not in cats:
            cats[c] = {"count": 0, "size": 0}
        cats[c]["count"] += 1
        cats[c]["size"] += rec.get("file_size", 0)

    stat_cards = _build_stat_cards(cats)
    cat_options = _build_cat_options(cats)
    rows_html = _build_rows(records)

    html = (
        '<!DOCTYPE html>\n<html lang="zh-CN"><head>\n'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
        '<title>妙喵桌宠 MeowDesk - 文件导航</title>\n'
        '<style>\n'
        ':root{--bg:#0f1117;--bg2:#1a1d27;--bg3:#242837;--fg:#e2e8f0;--fg2:#94a3b8;--accent:#6366f1;--accent2:#818cf8;--border:#2d3348;--radius:12px}\n'
        '*{margin:0;padding:0;box-sizing:border-box}\n'
        'body{font-family:-apple-system,"Microsoft YaHei","Segoe UI",sans-serif;background:var(--bg);color:var(--fg);line-height:1.6;min-height:100vh}\n'
        '.container{max-width:1200px;margin:0 auto;padding:32px 24px}\n'
        '.header{text-align:center;margin-bottom:40px;padding:40px 0;background:linear-gradient(135deg,var(--bg2),var(--bg3));border-radius:var(--radius);border:1px solid var(--border)}\n'
        '.header h1{font-size:32px;font-weight:700;background:linear-gradient(135deg,var(--accent),#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}\n'
        '.header p{color:var(--fg2);font-size:14px}\n'
        '.summary{display:flex;gap:24px;margin-bottom:32px;flex-wrap:wrap}\n'
        '.summary-card{flex:1;min-width:180px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:20px;text-align:center}\n'
        '.summary-card .num{font-size:36px;font-weight:800;color:var(--accent2)}\n'
        '.summary-card .label{color:var(--fg2);font-size:13px;margin-top:4px}\n'
        '.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-bottom:32px}\n'
        '.stat-card{display:flex;align-items:center;gap:14px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px;transition:transform .15s,box-shadow .15s,opacity .15s;cursor:pointer}\n'
        '.stat-card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.3)}\n'
        '.stat-card.active{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent),0 4px 16px rgba(99,102,241,.2)}\n'
        '.stat-card.dimmed{opacity:.4}\n'
        '.stat-icon{font-size:28px}.stat-name{font-weight:600;font-size:15px}.stat-detail{color:var(--fg2);font-size:12px}\n'
        '.toolbar{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;align-items:center}\n'
        '.toolbar input,.toolbar select{background:var(--bg2);border:1px solid var(--border);color:var(--fg);padding:10px 16px;border-radius:8px;font-size:14px;outline:none;transition:border-color .2s}\n'
        '.toolbar input:focus,.toolbar select:focus{border-color:var(--accent)}\n'
        '.toolbar input{flex:1;min-width:200px}.toolbar select{min-width:160px;cursor:pointer}\n'
        '.toolbar .btn{padding:10px 20px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer;font-size:14px;font-weight:500;transition:background .2s}\n'
        '.toolbar .btn:hover{background:var(--accent2)}\n'
        '.table-wrap{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}\n'
        'table{width:100%;border-collapse:collapse}\n'
        'th{background:var(--bg3);padding:14px 16px;text-align:left;font-weight:600;font-size:13px;color:var(--fg2);text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}\n'
        'td{padding:12px 16px;font-size:14px;border-bottom:1px solid var(--border);max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n'
        'tr:last-child td{border-bottom:none}tr:hover td{background:rgba(99,102,241,.06)}\n'
        '.cat-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:middle}\n'
        '.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600}\n'
        '.badge-archive{background:rgba(16,185,129,.15);color:#34d399}.badge-recycle{background:rgba(239,68,68,.15);color:#f87171}\n'
        '.btn-locate{color:var(--accent2);text-decoration:none;margin-left:6px;padding:2px 8px;border:1px solid var(--accent);border-radius:4px;font-size:11px;cursor:pointer;transition:background .2s,color .2s}\n'
        '.btn-locate:hover{background:var(--accent);color:#fff}\n'
        '.path-cell{color:var(--fg2);font-size:12px}\n'
        '.load-more{text-align:center;padding:20px}\n'
        '.footer{text-align:center;margin-top:48px;padding:24px 0;color:var(--fg2);font-size:12px;border-top:1px solid var(--border)}\n'
        '@media(max-width:768px){.summary{flex-direction:column}.stats-grid{grid-template-columns:1fr}.toolbar{flex-direction:column}.toolbar input,.toolbar select{width:100%}th,td{padding:10px 12px;font-size:13px}}\n'
        '</style></head><body>\n<div class="container">\n'
        '<div class="header"><h1>妙喵桌宠 MeowDesk</h1><p>智能文件分类归档 · 拖拽即整理</p></div>\n'
        '<div class="summary">'
        '<div class="summary-card"><div class="num">' + str(len(records)) + '</div><div class="label">累计处理文件</div></div>'
        '<div class="summary-card"><div class="num">' + str(len(cats)) + '</div><div class="label">文件分类数</div></div>'
        '<div class="summary-card"><div class="num">' + format_size(total_size) + '</div><div class="label">归档总大小</div></div>'
        '</div>\n'
        '<div class="stats-grid">\n' + stat_cards + '\n</div>\n'
        '<div class="toolbar">'
        '<input type="text" id="search" placeholder="搜索文件名..." oninput="filterTable()">'
        '<select id="catFilter" onchange="filterTable()"><option value="全部">全部分类</option>' + cat_options + '</select>'
        '<button class="btn" onclick="location.reload()">刷新</button>'
        '<button class="btn" style="background:transparent;border-color:var(--border);color:var(--fg2)" onclick="openArchiveDir()">打开归档目录</button>'
        '</div>\n'
        '<div class="table-wrap"><table><thead><tr>'
        '<th>分类</th><th>文件名</th><th>日期</th><th>大小</th><th>操作</th><th>归档路径</th>'
        '</tr></thead><tbody id="fileBody">' + rows_html + '</tbody></table></div>\n'
        '<div id="loadMoreWrap" class="load-more" style="display:none">'
        '<button class="btn" onclick="showMore()">加载更多</button>'
        '</div>\n'
        '<div class="footer">妙喵桌宠 MeowDesk · 共' + str(len(records)) + '个文件 · 数据存储于本地 ' + archive_dir + '</div>\n' + '        <div class="footer" style="margin-top:4px;font-size:12px;color:#64748b">'
        '        <a href="https://github.com/ra1nzzz/MeowDesk" target="_blank">GitHub 仓库</a>'
        '        · 问题反馈 · 欢迎 Star ✨</div>\n'
        '<script>\n'
        'var PS=' + str(page_size) + ',vc=0,ar=[];\n'
        'function doFilter(catVal){\n'
        '  var kw=document.getElementById("search").value.toLowerCase();\n'
        '  var cat=catVal!==undefined?catVal:document.getElementById("catFilter").value;\n'
        '  if(catVal!==undefined)document.getElementById("catFilter").value=catVal;\n'
        '  ar=document.querySelectorAll("#fileBody tr");\n'
        '  var vis=[];\n'
        '  ar.forEach(function(row){\n'
        '    var cells=row.querySelectorAll("td");\n'
        '    if(cells.length<6)return;\n'
        '    var fn=cells[1].textContent.toLowerCase();\n'
        '    var rc=cells[0].getAttribute("data-cat");\n'
        '    var mk=!kw||fn.indexOf(kw)>=0;\n'
        '    var mc=cat==="全部"||rc===cat;\n'
        '    if(mk&&mc){vis.push(row)}\n'
        '    row.style.display="none";\n'
        '  });\n'
        '  var show=vis.slice(0,PS);\n'
        '  show.forEach(function(r){r.style.display=""});\n'
        '  vc=show.length;\n'
        '  var rem=vis.length-vc;\n'
        '  var wrap=document.getElementById("loadMoreWrap");\n'
        '  wrap.style.display=rem>0?"":"none";\n'
        '  wrap.querySelector("button").textContent="加载更多 ("+rem+" 条)";\n'
        '  document.querySelectorAll(".stat-card").forEach(function(c){\n'
        '    var d=c.getAttribute("data-cat");\n'
        '    c.classList.toggle("active",d===cat&&cat!=="全部");\n'
        '    c.classList.toggle("dimmed",cat!=="全部"&&d!==cat);\n'
        '  });\n'
        '}\n'
        'function showMore(){\n'
        '  var kw=document.getElementById("search").value.toLowerCase();\n'
        '  var cat=document.getElementById("catFilter").value;\n'
        '  var allHidden=[];\n'
        '  ar.forEach(function(row){\n'
        '    if(row.style.display==="none"){\n'
        '      var cells=row.querySelectorAll("td");\n'
        '      if(cells.length<6)return;\n'
        '      var fn=cells[1].textContent.toLowerCase();\n'
        '      var rc=cells[0].getAttribute("data-cat");\n'
        '      var mk=!kw||fn.indexOf(kw)>=0;\n'
        '      var mc=cat==="全部"||rc===cat;\n'
        '      if(mk&&mc)allHidden.push(row);\n'
        '    }\n'
        '  });\n'
        '  var next=allHidden.slice(0,PS);\n'
        '  next.forEach(function(r){r.style.display=""});\n'
        '  vc+=next.length;\n'
        '  var rem=allHidden.length-next.length;\n'
        '  var wrap=document.getElementById("loadMoreWrap");\n'
        '  wrap.style.display=rem>0?"":"none";\n'
        '  wrap.querySelector("button").textContent="加载更多 ("+rem+" 条)";\n'
        '}\n'
        'function openArchiveDir(){\n'
        '  try{if(typeof ActiveXObject!=="undefined"){new ActiveXObject("Shell.Application").Open("' + archive_url + '")}else{alert("归档目录：' + archive_dir.replace("\\", "\\\\") + '")}}catch(e){alert("请手动打开：' + archive_dir.replace("\\", "\\\\") + '")}\n'
        '}\n'
        'document.addEventListener("DOMContentLoaded",function(){\n'
        '  document.querySelectorAll(".stat-card").forEach(function(card){\n'
        '    card.addEventListener("click",function(){\n'
        '      var c=this.getAttribute("data-cat");\n'
        '      doFilter(c===document.getElementById("catFilter").value?"全部":c);\n'
        '    });\n'
        '  });\n'
        '  doFilter();\n'
        '});\n'
        'document.addEventListener("keydown",function(e){\n'
        '  if(e.key==="/"&&document.activeElement.tagName!=="INPUT"){e.preventDefault();document.getElementById("search").focus()}\n'
        '});\n'
        'filterTable=doFilter;\n'
        '</script></body></html>'
    )
    return html


def write_html_index(
    records: List[Dict[str, Any]],
    archive_dir: str,
    archive_url: str,
    page_size: int = 200,
    dry_run: bool = False,
) -> Optional[str]:
    """Generate and write the HTML index to ``archive_dir/index.html``.

    Args:
        records: File records from FileDatabase
        archive_dir: Target archive directory (also where index.html lands)
        archive_url: URL / path used in "open directory" action
        page_size: Client-side pagination size
        dry_run: If True, return the HTML without writing

    Returns:
        Path to the generated file, or None if dry_run.
    """

    html = generate_html(records, archive_dir, archive_url, page_size)

    if dry_run:
        return None

    out = os.path.join(archive_dir, "index.html")
    try:
        os.makedirs(archive_dir, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        _log.info("generated HTML index: %s (%d bytes, %d rows)", out, len(html), len(records))
        return out
    except OSError as e:
        _log.error("failed to write HTML index: %s", e)
        return None


def load_records_from_db(db_path: str) -> List[Dict[str, Any]]:
    """Load raw records from the JSON database file.

    This is a convenience helper for the standalone CLI path.
    In the GUI, callers should pass ``FileDatabase.records`` directly.
    """

    if not os.path.exists(db_path):
        return []
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [r.to_dict() if hasattr(r, "to_dict") else r for r in data]
    except (json.JSONDecodeError, OSError) as e:
        _log.warning("could not load DB %s: %s", db_path, e)
        return []


def main() -> None:
    """Standalone CLI entry point.

    Reads DB_FILE and ARCHIVE_DIR from environment variables if set,
    otherwise falls back to defaults next to this module.
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_file = os.environ.get("MEOWDESK_DB", os.path.join(script_dir, "filedb.json"))
    archive_dir = os.environ.get("MEOWDESK_ARCHIVE", r"D:\meow-file")
    archive_url = archive_dir.replace("\\", "/")

    records = load_records_from_db(db_file)
    out = write_html_index(records, archive_dir, archive_url)
    if out:
        print("Generated:", out)


if __name__ == "__main__":
    main()
