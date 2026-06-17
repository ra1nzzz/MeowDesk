"""HTML index generator for MeowDesk file archive."""

import base64
import json
import os
import re
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
    "截图": ("\U0001f4f8", "#F4845F"),
    "图片": ("\U0001f5bc\ufe0f", "#B77DEE"),
    "视频": ("\U0001f3ac", "#F8A6B2"),
    "音频": ("\U0001f3b5", "#FBBF5C"),
    "文档": ("\U0001f4c4", "#889DF0"),
    "压缩包": ("\U0001f4e6", "#82D5BB"),
    "安装包": ("\U0001f4bf", "#F4845F"),
    "代码": ("\U0001f4bb", "#7EC8B8"),
    "设计稿": ("\U0001f3a8", "#C4A1FF"),
    "其他": ("\U0001f4c1", "#A8A4B8"),
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
        emoji, color = CAT_META.get(cn, ("\U0001f4c1", "#A8A4B8"))
        sc.append(
            '        <div class="stat-card" data-cat="' + cn + '">'
            '<div class="stat-icon" style="background:' + color + '22;color:' + color + '">' + emoji + '</div>'
            '<div class="stat-info" style="display:flex;flex-direction:column;gap:2px">'
            '<div class="stat-name">' + cn + '</div>'
            '<div class="stat-detail">' + str(info["count"]) + ' 个文件 · ' + format_size(info["size"]) + '</div>'
            '</div></div>'
        )
    return "\n".join(sc)


def _build_cat_options(cats: Dict[str, Dict[str, Any]]) -> str:
    """Build the <option> blocks for the category filter."""

    co = []
    for cn, info in sorted(cats.items(), key=lambda x: -x[1]["count"]):
        emoji, _ = CAT_META.get(cn, ("\U0001f4c1", "#A8A4B8"))
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
        emoji, color = CAT_META.get(cat, ("\U0001f4c1", "#A8A4B8"))
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
        '<!DOCTYPE html>\n<html lang="zh-CN" data-theme="dark"><head>\n'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
        '<title>妙喵桌宠 MeowDesk - 文件导航</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet">\n'
        '<style>\n'
        ':root{--bg-base:#121218;--bg-elevated:#1A1A24;--bg-card:#22222E;--bg-input:#2A2A38;'
        '--primary:#F4845F;--primary-hover:#F69B7D;--secondary:#7EC8B8;--accent:#C4A1FF;'
        '--text-primary:#F0EDE8;--text-secondary:#A8A4B8;--text-muted:#6B6880;'
        '--danger:#F87171;--success:#6EE7A0;--warning:#FBBF5C;--border:#2D2D3D;--border-hover:#44445A;'
        '--shadow-card:none;--header-grad-start:#1A1A24;--header-grad-end:#22222E;'
        '--cat-purple:#B77DEE;--cat-pink:#F8A6B2;--cat-blue:#889DF0;--cat-coral:#F4845F;'
        '--cat-mint:#7EC8B8;--cat-teal:#82D5BB;--cat-lavender:#C4A1FF;'
        '--row-hover:rgba(244,132,95,0.05);--badge-archived-bg:rgba(110,231,160,0.12);'
        '--badge-recycled-bg:rgba(248,113,113,0.12);--white:#FFFFFF;--font-display:"Nunito","Microsoft YaHei",sans-serif;'
        '--font-body:"Noto Sans SC","Microsoft YaHei",-apple-system,sans-serif}\n'
        '[data-theme="light"]{--bg-base:#FAF7F2;--bg-elevated:#F2EDE4;--bg-card:#FFFFFF;--bg-input:#F0EBE2;'
        '--primary:#E06B45;--primary-hover:#D45A36;--secondary:#5BA896;--accent:#9B72CF;'
        '--text-primary:#2D2A33;--text-secondary:#6B6578;--text-muted:#9C97AA;'
        '--danger:#D94444;--success:#2DA35E;--warning:#C98E20;--border:#DDD8CF;--border-hover:#C4BFB6;'
        '--shadow-card:0 2px 12px rgba(0,0,0,0.06);--header-grad-start:#F2EDE4;--header-grad-end:#FFFFFF;'
        '--cat-purple:#9B5CC6;--cat-pink:#D4707E;--cat-blue:#5A6FCC;--cat-coral:#E06B45;'
        '--cat-mint:#5BA896;--cat-teal:#4AA88A;--cat-lavender:#9B72CF;'
        '--row-hover:rgba(224,107,69,0.04);--badge-archived-bg:rgba(45,163,94,0.1);'
        '--badge-recycled-bg:rgba(217,68,68,0.08)}\n'
        '*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}\n'
        'body{font-family:var(--font-body);font-size:14px;line-height:1.5;background:var(--bg-base);color:var(--text-primary);-webkit-font-smoothing:antialiased;transition:background .3s,color .3s}\n'
        '.page-wrapper{max-width:1200px;margin:0 auto;padding:24px 20px 40px}\n'
        '.header{position:relative;background:linear-gradient(135deg,var(--header-grad-start),var(--header-grad-end));border-radius:14px;padding:40px;margin-bottom:24px;overflow:hidden;border:1px solid var(--border)}\n'
        '.header-title{font-family:var(--font-display);font-size:32px;font-weight:700;letter-spacing:-.02em;color:var(--text-primary);margin-bottom:6px}\n'
        '.header-subtitle{font-size:14px;color:var(--text-secondary);letter-spacing:.02em}\n'
        '.header-ears{position:absolute;top:-1px;left:50px;display:flex;gap:12px}\n'
        '.header-ear{width:28px;height:22px;background:var(--bg-card);clip-path:polygon(50% 0%,0% 100%,100% 100%);border-radius:2px}\n'
        '.header-ear:nth-child(2){width:24px;height:19px;margin-top:3px}\n'
        '.theme-toggle{position:absolute;top:16px;right:16px;width:38px;height:38px;border-radius:10px;border:1px solid var(--border);background:var(--bg-base);color:var(--text-secondary);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s ease;font-size:18px}\n'
        '.theme-toggle:hover{border-color:var(--border-hover);color:var(--primary)}\n'
        '.summary-cards{display:flex;gap:20px;margin-bottom:24px}\n'
        '.summary-card{flex:1;background:var(--bg-card);border-radius:12px;padding:24px;border:1px solid var(--border);position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s;box-shadow:var(--shadow-card)}\n'
        '.summary-card::before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;opacity:.05;border-radius:12px;pointer-events:none}\n'
        '.summary-card[data-accent="coral"]::before{background:linear-gradient(135deg,var(--cat-coral),transparent 70%)}\n'
        '.summary-card[data-accent="mint"]::before{background:linear-gradient(135deg,var(--cat-mint),transparent 70%)}\n'
        '.summary-card[data-accent="lavender"]::before{background:linear-gradient(135deg,var(--cat-lavender),transparent 70%)}\n'
        '.summary-card:hover{transform:translateY(-3px)}\n'
        '.summary-label{font-size:13px;color:var(--text-secondary);margin-bottom:8px;letter-spacing:.02em}\n'
        '.summary-value{font-family:var(--font-display);font-size:36px;font-weight:800;line-height:1.1}\n'
        '.summary-value.coral{color:var(--primary)}.summary-value.mint{color:var(--secondary)}.summary-value.lavender{color:var(--accent)}\n'
        '.summary-unit{font-size:13px;color:var(--text-muted);margin-top:4px}\n'
        '.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-bottom:24px}\n'
        '.stat-card{display:flex;align-items:center;gap:14px;background:var(--bg-card);border-radius:10px;padding:14px 16px;border:1px solid var(--border);cursor:pointer;transition:all .2s;box-shadow:var(--shadow-card)}\n'
        '.stat-card:hover{transform:translateY(-2px)}.stat-card.active{border-width:2px}.stat-card.dimmed{opacity:.4}\n'
        '.stat-icon{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:20px}\n'
        '.stat-name{font-size:15px;font-weight:600;color:var(--text-primary)}\n'
        '.stat-detail{font-size:12px;color:var(--text-muted);margin-top:2px}\n'
        '.toolbar{display:flex;gap:12px;margin-bottom:16px;align-items:center;flex-wrap:wrap}\n'
        '.toolbar input,.toolbar select{background:var(--bg-card);border:1px solid var(--border);color:var(--text-primary);padding:10px 16px;border-radius:8px;font-size:14px;outline:none;transition:border-color .2s;font-family:var(--font-body)}\n'
        '.toolbar input{flex:1;min-width:200px}.toolbar input:focus,.toolbar select:focus{border-color:var(--primary)}\n'
        '.toolbar input::placeholder{color:var(--text-muted)}\n'
        '.toolbar select{min-width:160px;cursor:pointer;appearance:none;-webkit-appearance:none;padding-right:36px;'
        'background-image:url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'12\' height=\'12\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%236B6880\' stroke-width=\'2\'%3E%3Cpath d=\'M6 9l6 6 6-6\'/%3E%3C/svg%3E");'
        'background-repeat:no-repeat;background-position:right 12px center}\n'
        '.btn{padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:none;font-family:var(--font-body);transition:all .2s;white-space:nowrap}\n'
        '.btn-primary{background:var(--primary);color:var(--white)}.btn-primary:hover{background:var(--primary-hover)}\n'
        '.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text-secondary)}.btn-outline:hover{border-color:var(--border-hover);color:var(--text-primary)}\n'
        '.table-wrap{background:var(--bg-card);border-radius:12px;overflow:hidden;border:1px solid var(--border);box-shadow:var(--shadow-card)}\n'
        'table{width:100%;border-collapse:collapse;min-width:780px}\n'
        'thead th{background:var(--bg-elevated);padding:14px 16px;font-size:12px;font-weight:600;color:var(--text-secondary);text-align:left;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid var(--border)}\n'
        'tbody td{padding:12px 16px;border-bottom:1px solid var(--border);font-size:14px;color:var(--text-primary);vertical-align:middle}\n'
        'tbody tr{transition:background .15s}tbody tr:hover{background:var(--row-hover)}tbody tr:last-child td{border-bottom:none}\n'
        '.cat-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:middle}\n'
        '.cell-filename{max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n'
        '.cell-date,.cell-size{color:var(--text-secondary);font-size:13px;white-space:nowrap}\n'
        '.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;letter-spacing:.02em}\n'
        '.badge-archive{background:var(--badge-archived-bg);color:var(--success)}.badge-recycle{background:var(--badge-recycled-bg);color:var(--danger)}\n'
        '.btn-locate{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:6px;border:1px solid var(--primary);background:transparent;color:var(--primary);font-size:12px;cursor:pointer;transition:all .2s;font-family:var(--font-body);text-decoration:none;margin-left:6px}\n'
        '.btn-locate:hover{background:var(--primary);color:var(--white)}\n'
        '.path-cell{font-size:12px;color:var(--text-muted);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n'
        '.load-more{text-align:center;padding:20px}\n'
        '.footer{text-align:center;padding:20px 0;font-size:12px;color:var(--text-muted);border-top:1px solid var(--border)}\n'
        '.footer a{color:var(--text-muted);text-decoration:none;margin-left:12px;transition:color .2s}.footer a:hover{color:var(--primary)}\n'
        'html.theme-transitioning,html.theme-transitioning *,html.theme-transitioning *::before,html.theme-transitioning *::after{transition:background-color .35s ease,color .35s ease,border-color .35s ease,box-shadow .35s ease !important}\n'
        '@media(max-width:768px){.summary-cards{flex-direction:column}.stats-grid{grid-template-columns:1fr}.toolbar{flex-direction:column}.toolbar input,.toolbar select,.btn{width:100%;min-width:unset}.header{padding:28px 20px}.header-title{font-size:24px}}\n'
        '::-webkit-scrollbar{width:6px;height:6px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}::-webkit-scrollbar-thumb:hover{background:var(--border-hover)}\n'
        '</style></head><body>\n'
        '<main class="page-wrapper">\n'
        '<div class="header">\n'
        '  <div class="header-ears"><div class="header-ear"></div><div class="header-ear"></div></div>\n'
        '  <div class="header-title">妙喵桌宠 MeowDesk</div>\n'
        '  <div class="header-subtitle">智能文件分类归档 · 拖拽即整理</div>\n'
        '  <button class="theme-toggle" onclick="toggleTheme()" aria-label="切换主题">\n'
        '    <span class="icon-moon">🌙</span><span class="icon-sun" style="display:none">☀️</span>\n'
        '  </button>\n'
        '</div>\n'
        '<div class="summary-cards">\n'
        '  <div class="summary-card" data-accent="coral"><div class="summary-label">累计处理</div><div class="summary-value coral">' + str(len(records)) + '</div><div class="summary-unit">个文件</div></div>\n'
        '  <div class="summary-card" data-accent="mint"><div class="summary-label">文件分类</div><div class="summary-value mint">' + str(len(cats)) + '</div><div class="summary-unit">个类别</div></div>\n'
        '  <div class="summary-card" data-accent="lavender"><div class="summary-label">归档总大小</div><div class="summary-value lavender">' + format_size(total_size) + '</div><div class="summary-unit">存储空间</div></div>\n'
        '</div>\n'
        '<div class="stats-grid">\n' + stat_cards + '\n</div>\n'
        '<div class="toolbar">\n'
        '  <input type="text" id="search" placeholder="搜索文件名..." oninput="filterTable()">\n'
        '  <select id="catFilter" onchange="filterTable()"><option value="全部">全部分类</option>' + cat_options + '</select>\n'
        '  <button class="btn btn-primary" onclick="location.reload()">刷新</button>\n'
        '  <button class="btn btn-outline" onclick="openArchiveDir()">打开归档目录</button>\n'
        '</div>\n'
        '<div class="table-wrap"><table><thead><tr>'
        '<th>分类</th><th>文件名</th><th>日期</th><th>大小</th><th>状态</th><th>归档路径</th>'
        '</tr></thead><tbody id="fileBody">' + rows_html + '</tbody></table></div>\n'
        '<div id="loadMoreWrap" class="load-more" style="display:none">'
        '<button class="btn btn-outline" onclick="showMore()" style="border-color:var(--primary);color:var(--primary)">加载更多</button>'
        '</div>\n'
        '<div class="footer">妙喵桌宠 MeowDesk · 共 ' + str(len(records)) + ' 个文件'
        '<a href="https://github.com/ra1nzzz/MeowDesk" target="_blank" rel="noopener">GitHub</a></div>\n'
        '</main>\n'
        '<script>\n'
        'function toggleTheme(){var h=document.documentElement,c=h.getAttribute("data-theme"),n=c==="dark"?"light":"dark";'
        'h.classList.add("theme-transitioning");void h.offsetHeight;h.setAttribute("data-theme",n);'
        'var m=h.querySelector(".icon-moon"),s=h.querySelector(".icon-sun");'
        'if(n==="light"){m.style.display="none";s.style.display="inline"}else{m.style.display="inline";s.style.display="none"}'
        'setTimeout(function(){h.classList.remove("theme-transitioning")},400)}\n'
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
