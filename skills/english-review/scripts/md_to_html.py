"""Convert a markdown study guide into a self-contained, readable HTML file.

Usage:
    python md_to_html.py <input.md> [output.html]
"""

from __future__ import annotations

import sys
from pathlib import Path

import markdown

CSS = """
:root {
  --bg: #fafaf7;
  --fg: #1f2328;
  --muted: #57606a;
  --accent: #0969da;
  --accent-soft: #ddf4ff;
  --border: #d0d7de;
  --code-bg: #f6f8fa;
  --table-stripe: #f6f8fa;
  --good: #1a7f37;
  --warn: #9a6700;
  --bad: #cf222e;
}

* { box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC",
               "PingFang TC", "Microsoft JhengHei", Helvetica, Arial, sans-serif;
  line-height: 1.7;
  color: var(--fg);
  background: var(--bg);
  margin: 0;
  padding: 0;
}

.layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .toc { position: static !important; max-height: none !important; border-right: none !important; border-bottom: 1px solid var(--border); }
}

.toc {
  position: sticky;
  top: 0;
  align-self: start;
  max-height: 100vh;
  overflow-y: auto;
  padding: 24px 16px;
  font-size: 13px;
  border-right: 1px solid var(--border);
  background: var(--bg);
}
.toc h2 {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin: 0 0 12px 0;
}
.toc ul { list-style: none; padding: 0; margin: 0; }
.toc li { margin: 4px 0; }
.toc a {
  color: var(--fg);
  text-decoration: none;
  display: block;
  padding: 4px 8px;
  border-radius: 4px;
  border-left: 3px solid transparent;
}
.toc a:hover { background: var(--accent-soft); border-left-color: var(--accent); }
.toc .toc-h1 { font-weight: 700; margin-top: 14px; font-size: 13px; }
.toc .toc-h1 a { color: var(--accent); }
.toc .toc-h2 { font-weight: 500; padding-left: 14px; }
.toc .toc-h3 { padding-left: 28px; color: var(--muted); font-size: 12px; }

.content {
  padding: 40px 48px 80px 48px;
  max-width: 880px;
  font-size: 16px;
}

h1, h2, h3, h4 {
  line-height: 1.3;
  color: var(--fg);
  scroll-margin-top: 20px;
}
h1 { font-size: 2em; border-bottom: 2px solid var(--border); padding-bottom: 0.3em; margin-top: 0; }
h2 { font-size: 1.5em; border-bottom: 1px solid var(--border); padding-bottom: 0.2em; margin-top: 2em; }
h3 { font-size: 1.2em; margin-top: 1.6em; color: var(--accent); }
h4 { font-size: 1.05em; margin-top: 1.3em; }

p, ul, ol { margin: 0.8em 0; }

ul, ol { padding-left: 1.6em; }
li { margin: 0.3em 0; }

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

code {
  font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, monospace;
  font-size: 0.9em;
  background: var(--code-bg);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--border);
}

pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px 18px;
  overflow-x: auto;
  font-size: 0.85em;
  line-height: 1.5;
}
pre code { background: none; border: none; padding: 0; }

blockquote {
  border-left: 4px solid var(--accent);
  background: var(--accent-soft);
  margin: 1em 0;
  padding: 0.6em 1em;
  color: var(--fg);
  border-radius: 0 6px 6px 0;
}
blockquote p { margin: 0.3em 0; }

table {
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
  font-size: 0.95em;
}
th, td {
  border: 1px solid var(--border);
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
}
th { background: var(--code-bg); font-weight: 600; }
tr:nth-child(even) td { background: var(--table-stripe); }

hr {
  border: none;
  border-top: 2px solid var(--border);
  margin: 2.5em 0;
}

/* Highlight strong tags in tables as soft accents for visual scanning */
td strong { color: var(--good); }

/* Print friendliness */
@media print {
  .toc { display: none; }
  .layout { grid-template-columns: 1fr; }
  .content { padding: 20px; max-width: none; }
}
"""


def build_toc(html: str) -> str:
    """Walk the rendered html and build a minimal table-of-contents from H1/H2/H3 headers.

    Skips the very first H1 (assumed to be the document title)."""
    import re

    pattern = re.compile(r'<h([123]) id="([^"]+)">(.*?)</h\1>', re.DOTALL)
    items = []
    for level, anchor, title in pattern.findall(html):
        clean_title = re.sub(r"<[^>]+>", "", title).strip()
        items.append((level, anchor, clean_title))

    if not items:
        return ""

    # Drop the leading document-title H1.
    if items and items[0][0] == "1":
        items = items[1:]

    lines = ['<nav class="toc"><h2>Contents</h2><ul>']
    for level, anchor, title in items:
        cls = {"1": "toc-h1", "2": "toc-h2", "3": "toc-h3"}[level]
        lines.append(f'<li class="{cls}"><a href="#{anchor}">{title}</a></li>')
    lines.append("</ul></nav>")
    return "\n".join(lines)


def convert(md_path: Path, html_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")

    md = markdown.Markdown(
        extensions=["extra", "tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"permalink": False}},
    )
    body_html = md.convert(text)
    toc_html = build_toc(body_html)

    title = md_path.stem
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
{toc_html}
<main class="content">
{body_html}
</main>
</div>
</body>
</html>
"""
    html_path.write_text(full_html, encoding="utf-8")
    print(f"Wrote: {html_path}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"Input not found: {md_path}")
        return 1
    html_path = Path(sys.argv[2]) if len(sys.argv) > 2 else md_path.with_suffix(".html")
    convert(md_path, html_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
