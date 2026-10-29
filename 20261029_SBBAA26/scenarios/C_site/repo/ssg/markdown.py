"""A deliberately small Markdown subset: headings, paragraphs, bullet lists, inline code."""
from __future__ import annotations

import html
import re

_CODE = re.compile(r"`([^`]+)`")


def inline(text: str) -> str:
    text = html.escape(text)
    return _CODE.sub(r"<code>\1</code>", text)


def to_html(md: str) -> str:
    out: list[str] = []
    in_list = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if not line:
            continue
        m = re.match(r"^(#{1,3}) (.*)$", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
        else:
            out.append(f"<p>{inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out) + "\n"
